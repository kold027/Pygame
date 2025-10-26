import pygame
import math
import random
import sys

pygame.init()

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
WORLD_WIDTH = 2000
WORLD_HEIGHT = 2000
MINIMAP_SIZE = 150
DAY_COUNTER = 1

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
DARK_GREEN = (0, 128, 0)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)


class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0

    def update(self, player_x, player_y):
        self.x = player_x - SCREEN_WIDTH // 2
        self.y = player_y - SCREEN_HEIGHT // 2

        self.x = max(0, min(self.x, WORLD_WIDTH - SCREEN_WIDTH))
        self.y = max(0, min(self.y, WORLD_HEIGHT - SCREEN_HEIGHT))


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 20
        self.base_speed = 5
        self.speed = 5
        self.color = BLUE
        self.health = 5
        self.max_health = 5
        self.damage_timer = 0
        self.magazine_size = 3
        self.current_ammo = 3
        self.is_reloading = False
        self.reload_timer = 0
        self.reload_time = 300
        self.shoot_cooldown = 0
        self.shoot_delay = 10
        # New survival features
        self.run = False
        self.wood = 0
        self.stones = 0

    def update(self, keys, terrain):
        old_x, old_y = self.x, self.y
        new_x, new_y = self.x, self.y

        # Handle running
        if keys[pygame.K_LSHIFT]:
            self.run = True
            self.speed = self.base_speed * 2
        else:
            self.run = False
            self.speed = self.base_speed

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            new_y -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            new_y += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            new_x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            new_x += self.speed

        # Try moving on X axis only
        self.x = new_x
        if self.check_terrain_collision(terrain):
            self.x = old_x

        # Try moving on Y axis only
        self.y = new_y
        if self.check_terrain_collision(terrain):
            self.y = old_y

        self.x = max(self.size, min(self.x, WORLD_WIDTH - self.size))
        self.y = max(self.size, min(self.y, WORLD_HEIGHT - self.size))

        if self.damage_timer > 0:
            self.damage_timer -= 1

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        
    def check_terrain_collision(self, terrain):
        # Check trees (only if they have size > 0)
        for tree in terrain.trees:
            if tree['size'] > 0:
                distance = math.sqrt((self.x - tree['x']) ** 2 + (self.y - tree['y']) ** 2)
                if distance < self.size + tree['size']:
                    return True

        # Check rocks (only if they have size > 0)
        for rock in terrain.rocks:
            if rock['size'] > 0:
                distance = math.sqrt((self.x - rock['x']) ** 2 + (self.y - rock['y']) ** 2)
                if distance < self.size + rock['size']:
                    return True

        # Check fire collision
        fire_distance = math.sqrt((self.x - WORLD_WIDTH / 2) ** 2 + (self.y - WORLD_HEIGHT / 2) ** 2)
        if fire_distance < self.size + terrain.fire_size:
            return True

        # Check buildings
        for building in terrain.buildings:
            left = building['x'] - building['width'] // 2
            right = building['x'] + building['width'] // 2
            top = building['y'] - building['height'] // 2
            bottom = building['y'] + building['height'] // 2

            closest_x = max(left, min(self.x, right))
            closest_y = max(top, min(self.y, bottom))

            distance = math.sqrt((self.x - closest_x) ** 2 + (self.y - closest_y) ** 2)
            if distance < self.size:
                return True

        return False

    def take_damage(self, amount):
        if self.damage_timer <= 0:
            self.health -= amount
            self.damage_timer = 60
            self.health = max(0, self.health)

    def can_shoot(self):
        return self.stones > 0 and self.shoot_cooldown <= 0

    def shoot(self):
        if self.can_shoot():
            self.stones -= 1
            self.shoot_cooldown = self.shoot_delay
            
            return True
        return False

    def draw(self, screen, camera):
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y
        color = self.color if self.damage_timer <= 0 or self.damage_timer % 10 < 5 else WHITE
        pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), self.size)

        # Draw running indicator
        if self.run:
            pygame.draw.circle(screen, YELLOW, (int(screen_x), int(screen_y)), self.size + 3, 2)


class Zombie:
    def __init__(self, x, y, wave=1):
        self.x = x
        self.y = y
        self.size = 15
        self.speed = 1
        self.color = RED
        self.direction_x = random.choice([-1, 1])
        self.direction_y = random.choice([-1, 1])
        self.change_direction_timer = 0
        self.detection_range = 550 + (wave - 1) * 50
        self.health = 30 + (wave - 1) * 5
        self.max_health = self.health
        self.following_player = False
        self.wave = wave

    def update(self, player, terrain):
        distance_to_player = math.sqrt((self.x - player.x) ** 2 + (self.y - player.y) ** 2)

        if distance_to_player < self.detection_range:
            self.following_player = True
            dx = player.x - self.x
            dy = player.y - self.y
            length = math.sqrt(dx ** 2 + dy ** 2)
            if length > 0:
                self.direction_x = dx / length
                self.direction_y = dy / length
        else:
            self.following_player = False
            self.change_direction_timer += 1
            if self.change_direction_timer > 60:
                self.direction_x = random.uniform(-1, 1)
                self.direction_y = random.uniform(-1, 1)
                self.change_direction_timer = 0

        old_x, old_y = self.x, self.y
        self.x += self.direction_x * self.speed
        self.y += self.direction_y * self.speed

        if self.check_terrain_collision(terrain):
            self.x, self.y = old_x, old_y
            if not self.following_player:
                self.direction_x = random.uniform(-1, 1)
                self.direction_y = random.uniform(-1, 1)

        if self.x <= self.size or self.x >= WORLD_WIDTH - self.size:
            self.direction_x *= -1
        if self.y <= self.size or self.y >= WORLD_HEIGHT - self.size:
            self.direction_y *= -1

        self.x = max(self.size, min(self.x, WORLD_WIDTH - self.size))
        self.y = max(self.size, min(self.y, WORLD_HEIGHT - self.size))

        if distance_to_player < self.size + player.size:
            player.take_damage(1)

    def check_terrain_collision(self, terrain):
        # Check trees (only if they have size > 0)
        for tree in terrain.trees:
            if tree['size'] > 0:
                distance = math.sqrt((self.x - tree['x']) ** 2 + (self.y - tree['y']) ** 2)
                if distance < self.size + tree['size']:
                    return True

        # Check rocks (only if they have size > 0)
        for rock in terrain.rocks:
            if rock['size'] > 0:
                distance = math.sqrt((self.x - rock['x']) ** 2 + (self.y - rock['y']) ** 2)
                if distance < self.size + rock['size']:
                    return True

        # Check fire collision
        fire_distance = math.sqrt((self.x - WORLD_WIDTH / 2) ** 2 + (self.y - WORLD_HEIGHT / 2) ** 2)
        if fire_distance < self.size + terrain.fire_size:
            return True

        # Check buildings
        for building in terrain.buildings:
            left = building['x'] - building['width'] // 2
            right = building['x'] + building['width'] // 2
            top = building['y'] - building['height'] // 2
            bottom = building['y'] + building['height'] // 2

            closest_x = max(left, min(self.x, right))
            closest_y = max(top, min(self.y, bottom))

            distance = math.sqrt((self.x - closest_x) ** 2 + (self.y - closest_y) ** 2)
            if distance < self.size:
                return True

        return False

    def take_damage(self, amount):
        self.health -= amount
        return self.health <= 0

    def draw(self, screen, camera):
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y
        if -self.size <= screen_x <= SCREEN_WIDTH + self.size and -self.size <= screen_y <= SCREEN_HEIGHT + self.size:
            pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), self.size)
            if self.following_player:
                pygame.draw.circle(screen, ORANGE, (int(screen_x), int(screen_y)), self.size + 5, 2)

            # Draw health bar
            bar_width = 30
            bar_height = 4
            bar_x = screen_x - bar_width // 2
            bar_y = screen_y - self.size - 8

            health_ratio = self.health / self.max_health

            pygame.draw.rect(screen, BLACK, (int(bar_x - 1), int(bar_y - 1), bar_width + 2, bar_height + 2))
            pygame.draw.rect(screen, RED, (int(bar_x), int(bar_y), bar_width, bar_height))
            pygame.draw.rect(screen, GREEN, (int(bar_x), int(bar_y), int(bar_width * health_ratio), bar_height))


class Terrain:
    def __init__(self):
        self.trees = []
        self.rocks = []
        self.buildings = []
        self.fire_size = 25

        # Trees with resource harvesting properties
        for _ in range(15):
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            size = random.randint(15, 30)
            self.trees.append({
                'x': x, 'y': y, 'size': size,
                'value': size, 'cut': pygame.time.get_ticks()
            })

        # Rocks with resource harvesting properties
        for _ in range(8):
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            size = random.randint(10, 20)
            self.rocks.append({
                'x': x, 'y': y, 'size': size,
                'value': size, 'cut': pygame.time.get_ticks()
            })

        # Add buildings
        for _ in range(8):
            width = random.randint(80, 150)
            height = random.randint(60, 120)
            x = random.randint(width // 2, WORLD_WIDTH - width // 2)
            y = random.randint(height // 2, WORLD_HEIGHT - height // 2)
            # Avoid spawning buildings too close to fire
            if math.sqrt((x - WORLD_WIDTH / 2) ** 2 + (y - WORLD_HEIGHT / 2) ** 2) > 100:
                self.buildings.append({'x': x, 'y': y, 'width': width, 'height': height})

    def draw(self, screen, camera):
        # Draw buildings first
        for building in self.buildings:
            screen_x = building['x'] - camera.x - building['width'] // 2
            screen_y = building['y'] - camera.y - building['height'] // 2
            if (-building['width'] <= screen_x <= SCREEN_WIDTH + building['width'] and
                    -building['height'] <= screen_y <= SCREEN_HEIGHT + building['height']):
                pygame.draw.rect(screen, DARK_GRAY,
                                 (int(screen_x), int(screen_y), building['width'], building['height']))
                pygame.draw.rect(screen, BLACK, (int(screen_x), int(screen_y), building['width'], building['height']),
                                 2)
                # Windows
                window_size = 8
                for wx in range(int(screen_x) + 15, int(screen_x) + building['width'] - 10, 20):
                    for wy in range(int(screen_y) + 15, int(screen_y) + building['height'] - 10, 20):
                        pygame.draw.rect(screen, LIGHT_GRAY, (wx, wy, window_size, window_size))

        # Draw trees (only if they have size > 0)
        for tree in self.trees:
            if tree['size'] > 0:
                screen_x = tree['x'] - camera.x
                screen_y = tree['y'] - camera.y
                if -tree['size'] <= screen_x <= SCREEN_WIDTH + tree['size'] and -tree[
                    'size'] <= screen_y <= SCREEN_HEIGHT + tree['size']:
                    pygame.draw.circle(screen, DARK_GREEN, (int(screen_x), int(screen_y)), tree['size'])

        # Draw rocks (only if they have size > 0)
        for rock in self.rocks:
            if rock['size'] > 0:
                screen_x = rock['x'] - camera.x
                screen_y = rock['y'] - camera.y
                if -rock['size'] <= screen_x <= SCREEN_WIDTH + rock['size'] and -rock[
                    'size'] <= screen_y <= SCREEN_HEIGHT + rock['size']:
                    pygame.draw.circle(screen, GRAY, (int(screen_x), int(screen_y)), rock['size'])

        # Draw fire
        screen_x = (WORLD_WIDTH / 2) - camera.x
        screen_y = (WORLD_HEIGHT / 2) - camera.y
        pygame.draw.circle(screen, ORANGE, (int(screen_x), int(screen_y)), self.fire_size)
        pygame.draw.circle(screen, YELLOW, (int(screen_x), int(screen_y)), self.fire_size - 7)
        pygame.draw.circle(screen, WHITE, (int(screen_x), int(screen_y)), self.fire_size * 4, 2)

    def fuel_fire(self, x, y, player):
        fire_distance = math.sqrt((x - WORLD_WIDTH / 2) ** 2 + (y - WORLD_HEIGHT / 2) ** 2)
        if fire_distance < self.fire_size and player.wood >= 1:
            player.wood -= 1
            self.fire_size += 0.5

    def terrain_damage_handler(self, player, x, y):
        # Handle tree harvesting
        for tree in self.trees:
            if tree['size'] > 0:
                distance = math.sqrt((tree['x'] - x) ** 2 + (tree['y'] - y) ** 2)
                if distance < tree['size']:
                    tree['size'] -= 2
                    if tree['size'] <= tree['value'] / 2 and tree['size'] >= 1:
                        tree['size'] = 0
                        player.wood += 3
                        tree['cut'] = pygame.time.get_ticks()

        # Handle rock harvesting
        for rock in self.rocks:
            if rock['size'] > 0:
                distance = math.sqrt((rock['x'] - x) ** 2 + (rock['y'] - y) ** 2)
                if distance < rock['size']:
                    rock['size'] -= 1
                    if rock['size'] <= rock['value'] / 2 and rock['size'] >= 1:
                        rock['size'] = 0
                        player.stones += 3
                        rock['cut'] = pygame.time.get_ticks()

    def grow_terrain(self):
        current_time = pygame.time.get_ticks()
        # Regrow trees after 60 seconds
        for tree in self.trees:
            if current_time - tree['cut'] > 60000 and tree['size'] == 0:
                tree['size'] = tree['value']

        # Regrow rocks after 45 seconds
        for rock in self.rocks:
            if current_time - rock['cut'] > 45000 and rock['size'] == 0:
                rock['size'] = rock['value']


class Projectile:
    def __init__(self, x, y, target_x, target_y):
        self.x = x
        self.y = y
        self.size = 3
        self.speed = 10
        dx = target_x - x
        dy = target_y - y
        length = math.sqrt(dx ** 2 + dy ** 2)
        if length > 0:
            self.direction_x = dx / length
            self.direction_y = dy / length
        else:
            self.direction_x = 1
            self.direction_y = 0
        self.active = True

    def update(self):
        if self.active:
            self.x += self.direction_x * self.speed
            self.y += self.direction_y * self.speed

            if self.x < 0 or self.x > WORLD_WIDTH or self.y < 0 or self.y > WORLD_HEIGHT:
                self.active = False

    def draw(self, screen, camera):
        if self.active:
            screen_x = self.x - camera.x
            screen_y = self.y - camera.y
            if 0 <= screen_x <= SCREEN_WIDTH and 0 <= screen_y <= SCREEN_HEIGHT:
                pygame.draw.circle(screen, DARK_GRAY, (int(screen_x), int(screen_y)), self.size)


class Inventory:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player

    def draw(self):
        font = pygame.font.SysFont('Times New Roman', 24)
        wood_text = font.render(f'Wood: {self.player.wood}', True, WHITE)
        stone_text = font.render(f'Stone: {self.player.stones}', True, WHITE)

        self.screen.blit(wood_text, (10, 40))
        self.screen.blit(stone_text, (10, 65))


class Minimap:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.scale = MINIMAP_SIZE / max(WORLD_WIDTH, WORLD_HEIGHT)

    def draw(self, screen, player, zombies, terrain):
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, MINIMAP_SIZE + 4, MINIMAP_SIZE + 4))
        pygame.draw.rect(screen, WHITE, (self.x, self.y, MINIMAP_SIZE, MINIMAP_SIZE))

        # Draw terrain on minimap
        for tree in terrain.trees:
            if tree['size'] > 0:
                mini_x = int(tree['x'] * self.scale) + self.x
                mini_y = int(tree['y'] * self.scale) + self.y
                pygame.draw.circle(screen, DARK_GREEN, (mini_x, mini_y), 2)

        for rock in terrain.rocks:
            if rock['size'] > 0:
                mini_x = int(rock['x'] * self.scale) + self.x
                mini_y = int(rock['y'] * self.scale) + self.y
                pygame.draw.circle(screen, GRAY, (mini_x, mini_y), 1)

        for building in terrain.buildings:
            mini_x = int(building['x'] * self.scale) + self.x - int(building['width'] * self.scale) // 2
            mini_y = int(building['y'] * self.scale) + self.y - int(building['height'] * self.scale) // 2
            mini_width = int(building['width'] * self.scale)
            mini_height = int(building['height'] * self.scale)
            pygame.draw.rect(screen, DARK_GRAY, (mini_x, mini_y, mini_width, mini_height))

        # Draw fire on minimap
        mini_fire_x = int((WORLD_WIDTH / 2) * self.scale) + self.x
        mini_fire_y = int((WORLD_HEIGHT / 2) * self.scale) + self.y
        pygame.draw.circle(screen, ORANGE, (mini_fire_x, mini_fire_y), 8, 3)

        # Draw zombies
        for zombie in zombies:
            mini_x = int(zombie.x * self.scale) + self.x
            mini_y = int(zombie.y * self.scale) + self.y
            color = ORANGE if zombie.following_player else RED
            pygame.draw.circle(screen, color, (mini_x, mini_y), 3)

        # Draw player
        player_mini_x = int(player.x * self.scale) + self.x
        player_mini_y = int(player.y * self.scale) + self.y
        pygame.draw.circle(screen, BLUE, (player_mini_x, player_mini_y), 4)


class Store:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player

    def draw_store(self, screen):
        self.surface = pygame.Surface((MINIMAP_SIZE+10, SCREEN_HEIGHT-210),pygame.SRCALPHA)
        pygame.draw.rect(self.surface, (0, 0, 0, 191), (0, 0, MINIMAP_SIZE+10, SCREEN_HEIGHT-210))
        self.screen.blit(self.surface,(860, 180))
        


def draw_health_bar(screen, player):
    bar_width = 200
    bar_height = 20
    bar_x = 10
    bar_y = 10

    health_ratio = player.health / player.max_health

    pygame.draw.rect(screen, BLACK, (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
    pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_width * health_ratio), bar_height))


def draw_ui(screen, player, wave):
    font = pygame.font.Font(None, 32)
    small_font = pygame.font.Font(None, 24)
    big_font = pygame.font.SysFont("Times New Roman", 35)

    wave_text = font.render(f"Wave: {wave}", True, WHITE)
    screen.blit(wave_text, (SCREEN_WIDTH - 150, 10))

    # Show Day Counter
    controls_text = big_font.render(f"Day {DAY_COUNTER}", True, WHITE)
    screen.blit(controls_text, (SCREEN_WIDTH/2-35, 10)) 

       
        
    # Show controls
    controls_text = small_font.render("Left Click: Harvest/Fuel  Right Click: Shoot  Shift: Run", True,
                                      WHITE)
    screen.blit(controls_text, (10, SCREEN_HEIGHT - 25))

    

def spawn_wave(wave_number, terrain):
    zombie_count = 5 + (wave_number - 1) * 2
    zombies = []

    for _ in range(zombie_count):
        zombie_x, zombie_y = find_safe_spawn_location(terrain, 15)
        zombies.append(Zombie(zombie_x, zombie_y, wave_number))

    return zombies


def find_safe_spawn_location(terrain, size):
    max_attempts = 100
    for _ in range(max_attempts):
        x = random.randint(size + 50, WORLD_WIDTH - size - 50)
        y = random.randint(size + 50, WORLD_HEIGHT - size - 50)

        # Avoid spawning too close to fire
        if math.sqrt((x - WORLD_WIDTH / 2) ** 2 + (y - WORLD_HEIGHT / 2) ** 2) < 150:
            continue

        collision = False
        for tree in terrain.trees:
            if tree['size'] > 0:
                distance = math.sqrt((x - tree['x']) ** 2 + (y - tree['y']) ** 2)
                if distance < size + tree['size'] + 20:
                    collision = True
                    break

        if not collision:
            for rock in terrain.rocks:
                if rock['size'] > 0:
                    distance = math.sqrt((x - rock['x']) ** 2 + (y - rock['y']) ** 2)
                    if distance < size + rock['size'] + 20:
                        collision = True
                        break

        if not collision:
            return x, y

    return WORLD_WIDTH // 4, WORLD_HEIGHT // 4


def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Survival Forest Game")
    clock = pygame.time.Clock()

    camera = Camera()
    terrain = Terrain()

    player_x, player_y = find_safe_spawn_location(terrain, 20)
    player = Player(player_x, player_y)

    store = Store(screen, player)

    inventory = Inventory(screen, player)
    minimap = Minimap(SCREEN_WIDTH - MINIMAP_SIZE - 10, 10)
    projectiles = []

    current_wave = 1
    zombies = spawn_wave(current_wave, terrain)

    day_timer = pygame.time.get_ticks()    
    running = True
    if day_timer >= 180000:
        DAY_COUNTER+=current_wave
        day_timer = pygame.time.get_ticks()
        

    while running:
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if len(zombies) == 0:
                current_wave+=1
                zombies = spawn_wave(current_wave, terrain)
                

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:  # Right click
                    world_mouse_x = mouse_x + camera.x
                    world_mouse_y = mouse_y + camera.y
                    

                    # Try to shoot first
                    if player.shoot():
                        projectiles.append(Projectile(player.x, player.y, world_mouse_x, world_mouse_y))
                        
                elif event.button == 1:  # Left click
                    world_mouse_x = mouse_x + camera.x
                    world_mouse_y = mouse_y + camera.y
                    terrain.fuel_fire(world_mouse_x, world_mouse_y, player)
                    terrain.terrain_damage_handler(player, world_mouse_x, world_mouse_y)

        keys = pygame.key.get_pressed()

        if player.health <= 0:
            font = pygame.font.Font(None, 72)
            game_over_text = font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 36))
            pygame.display.flip()
            pygame.time.wait(3000)
            running = False
            continue

        # Update game objects
        terrain.grow_terrain()
        player.update(keys, terrain)
        camera.update(player.x, player.y)

        # Update projectiles
        for projectile in projectiles[:]:
            projectile.update()
            if not projectile.active:
                projectiles.remove(projectile)

        # Update zombies and handle combat
        for zombie in zombies[:]:
            zombie.update(player, terrain)

           
            for projectile in projectiles[:]:
                if projectile.active:
                    distance = math.sqrt((projectile.x - zombie.x) ** 2 + (projectile.y - zombie.y) ** 2)
                    if distance < projectile.size + zombie.size:
                        if zombie.take_damage(30):
                            zombies.remove(zombie)
                        projectiles.remove(projectile)
                        break

        # Draw everything
        screen.fill(GREEN)

        terrain.draw(screen, camera)

        for projectile in projectiles:
            projectile.draw(screen, camera)

        for zombie in zombies:
            zombie.draw(screen, camera)

        player.draw(screen, camera)

        minimap.draw(screen, player, zombies, terrain)
        store.draw_store(screen)
        draw_health_bar(screen, player)
        draw_ui(screen, player, current_wave)
        inventory.draw()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()