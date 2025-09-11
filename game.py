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
        self.speed = 5
        self.color = BLUE
        self.run = False
                    
    def update(self, keys, terrain):
        old_x, old_y = self.x, self.y
        new_x, new_y = self.x, self.y
    
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            new_y -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            new_y += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            new_x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            new_x += self.speed
        if keys[pygame.K_LSHIFT]:
            self.run = True
        else:
            self.run = False
                       
        if self.run == True:
            self.speed = 10
        else:
            self.speed = 5

        # Try moving on X axis only
        self.x = new_x
                
        # Try moving on Y axis only
        self.y = new_y

        for tree in terrain.trees:
            if ((self.x-tree['x'])**2+(self.y-tree['y'])**2) < (tree['size']+(self.size))**2:
                self.x = old_x
                self.y = old_y 

        for rock in terrain.rocks:
            if ((self.x-rock['x'])**2+(self.y-rock['y'])**2) < (rock['size']+(self.size))**2:
                self.x = old_x
                self.y = old_y

        if ((self.x-(WORLD_WIDTH/2))**2+(self.y-(WORLD_HEIGHT/2))**2) < (terrain.fire_size+(self.size))**2:
            self.x = old_x
            self.y = old_y                            

        self.x = max(self.size, min(self.x, WORLD_WIDTH - self.size))
        self.y = max(self.size, min(self.y, WORLD_HEIGHT - self.size))
                
    def draw(self, screen, camera):
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), self.size)

class Terrain:
    def __init__(self):
        self.trees = []
        self.rocks = []
        self.fire_size = 25
        self.cut_at = pygame.time.get_ticks()

        # Reduced terrain - only 10% of original trees and 10% of rocks
        for _ in range(10):
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            size = random.randint(15, 30)
            self.trees.append({'x': x, 'y': y, 'size': size})
        
        for _ in range(10):
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            size = random.randint(10, 20)
            self.rocks.append({'x': x, 'y': y, 'size': size})
        
    def draw(self, screen, camera):        
        for tree in self.trees:
            screen_x = tree['x'] - camera.x
            screen_y = tree['y'] - camera.y
            if -tree['size'] <= screen_x <= SCREEN_WIDTH + tree['size'] and -tree['size'] <= screen_y <= SCREEN_HEIGHT + tree['size']:
                pygame.draw.circle(screen, DARK_GREEN, (int(screen_x), int(screen_y)), tree['size'])
        
        for rock in self.rocks:
            screen_x = rock['x'] - camera.x
            screen_y = rock['y'] - camera.y
            if -rock['size'] <= screen_x <= SCREEN_WIDTH + rock['size'] and -rock['size'] <= screen_y <= SCREEN_HEIGHT + rock['size']:
                pygame.draw.circle(screen, GRAY, (int(screen_x), int(screen_y)), rock['size'])

        # Drawing fire
        screen_x = (WORLD_WIDTH/2) - camera.x
        screen_y = (WORLD_HEIGHT/2) - camera.y
        pygame.draw.circle(screen, ORANGE, (int(screen_x), int(screen_y)), self.fire_size)
        pygame.draw.circle(screen, YELLOW, (int(screen_x), int(screen_y)), self.fire_size-7)
        pygame.draw.circle(screen, WHITE, (int(screen_x), int(screen_y)), self.fire_size*4, 2)
        
    def terrain_damage_handler(self, player, x, y):
        for tree in self.trees:
            if ((tree['x']-x)**2+(tree['y']-y)**2) < (tree['size'])**2:
                tree['size'] -= 2
    def grow_tree(self):
        for tree in self.trees:
            if tree['size'] <= tree['size']/2:
                tree['size'] = 0
                self.cut_at = pygame.time.get_ticks()
            if pygame.time.get_ticks-self.cut_at > 60000:
                tree['size'] = random.randint(15,30)
def find_safe_spawn_location(terrain, size):
    max_attempts = 100
    for _ in range(max_attempts):
        x = random.randint(size + 50, WORLD_WIDTH - size - 50)
        y = random.randint(size + 50, WORLD_HEIGHT - size - 50)
        
        collision = False
        for tree in terrain.trees:
            distance = math.sqrt((x - tree['x'])**2 + (y - tree['y'])**2)
            if distance < size + tree['size'] + 20:
                collision = True
                break
        
        if not collision:
            for rock in terrain.rocks:
                distance = math.sqrt((x - rock['x'])**2 + (y - rock['y'])**2)
                if distance < size + rock['size'] + 20:
                    collision = True
                    break
        
        if not collision:
            return x, y
    
    return WORLD_WIDTH // 2, WORLD_HEIGHT // 2

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Game")
    clock = pygame.time.Clock()
    
    camera = Camera()
    terrain = Terrain()
    
    player_x, player_y = find_safe_spawn_location(terrain, 20)
    player = Player(player_x, player_y)
    
    projectiles = []
      
    running = True
    while running:        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    x, y=pygame.mouse.get_pos()
                    x += camera.x
                    y += camera.y
                    terrain.terrain_damage_handler(player, x, y)
                    terrain.grow_tree()        
        keys = pygame.key.get_pressed()
                        
        player.update(keys, terrain)
        camera.update(player.x, player.y)       
               
        screen.fill(GREEN)
        
        terrain.draw(screen, camera)
        
        for projectile in projectiles:
            projectile.draw(screen, camera)
                       
        player.draw(screen, camera)
                                       
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()