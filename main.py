import pygame
import sys
import json
import Engine as E
from enum import Enum
from copy import deepcopy
import random
import time

class Direction(Enum):
    UP = 0
    LEFT = 1
    DOWN = 2
    RIGHT = 3

class GhostMode(Enum):
    CHASE = 0
    SCATTER = 1
    FRIGHTENED = 2

pygame.init()

class Coin:
    def __init__(self, x, y, img: pygame.Surface):
        self.img = img
        self.rect = pygame.Rect(x+3, y+3, 2, 2)
        
    def draw(self, surf):
        surf.blit(self.img, (self.rect.x-3, self.rect.y-3))

class BigCoin:
    def __init__(self, x, y, img: pygame.Surface):
        self.img = img
        self.rect = self.img.get_rect(center=(x+4, y+4))
        
    def draw(self, surf):
        surf.blit(self.img, self.rect)

class Player:
    def __init__(self, x, y):
        self.img = pygame.Surface((16, 16))
        self.img.fill((255, 0, 0))
        self.rect = pygame.Rect(x, y, 8, 8)
        self.rect.center = (x+4, y+4)
        self.lives = 3
        self.vel = 1.5
        self.direction = Direction.RIGHT
        self.states = {Direction.RIGHT: ([1, 0], "right"), Direction.LEFT:([-1, 0], "left"), Direction.DOWN:([0, 1], "down"), Direction.UP:([0, -1], "up")} # movement directions
        self.physics_obj = E.Physics(self.rect.x, self.rect.y, self.rect.width, self.rect.height)
        self.animation = E.Animation()
        self.input = [] # to replicate movement in pacman, I will do this by having an input list and let pacman turn once he can execute that input
        self.collisions = {"right":False,"left":False,"top":False,"bottom":False}
        self.lives = 3
        
        self.animation.load_anim("death", "data/images/animations/player/death", "png", [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3], 1, colorkey=(0, 0, 0))
        self.animation.load_anim("left", "data/images/animations/player/left", "png", [5, 5], 1, colorkey=(0, 0, 0))
        self.animation.load_anim("right", "data/images/animations/player/right", "png", [5, 5], 1,colorkey=(0, 0, 0))
        self.animation.load_anim("up", "data/images/animations/player/up", "png", [5, 5], 1, colorkey=(0, 0, 0))
        self.animation.load_anim("down", "data/images/animations/player/down", "png", [5, 5], 1, colorkey=(0, 0, 0))
    
    def draw(self, surf):
        
        if not self.collisions[self.states[self.direction][1]]:
            self.animation.animate(self.states[self.direction][1])
        self.img = self.animation.image
        surf.blit(self.img, (self.rect.x-3, self.rect.y-3))
        
        #pygame.draw.rect(surf, (0, 255, 0), self.rect, 1)
    
    def move(self, turns, tiles):
        if len(self.input) > 0 and turns != None:
            #print(turns, self.input, turns[self.input[0]])
            if turns[self.input[0]] == [True, 0]:
                self.direction = self.input[0]
                self.input.pop(0)
        
        movement = deepcopy(self.states[self.direction][0])
        movement[0] *= self.vel
        movement[1] *= self.vel
        
        self.collisions = self.physics_obj.movement(movement, tiles)
        self.rect.center = self.physics_obj.rect.center 

class Ghost:
    def __init__(self, game, x, y, type):
        self.game = game
        self.image = pygame.Surface((16, 16))
        self.image.fill((127, 127, 127))
        self.rect = pygame.Rect(x, y, 8, 8)
        self.level = game.level
        self.vel = 1
        self.target = [0, 0]
        self.next_move = None
        self.next_tile = None
        self.get_next_move = True
        self.state = "idle" 
        self.mode = GhostMode.CHASE
        self.type = type
        self.direction = random.choice([Direction.RIGHT])
        self.img = pygame.Surface((8, 8))
        self.img.fill((255, 0, 0))
        self.states = {Direction.RIGHT: ([1, 0], "right"), Direction.LEFT:([-1, 0], "left"), Direction.DOWN:([0, 1], "down"), Direction.UP:([0, -1], "up")}
        self.physics_obj = E.Physics(self.rect.x, self.rect.y, self.rect.width, self.rect.height)
        self.animation = E.Animation()
        
        self.animation.load_anim(f"{self.type}_left", f"data/images/animations/ghost/{self.type}_left", "png", [5, 5], 1, colorkey=(0, 0, 0))
        self.animation.load_anim(f"{self.type}_right", f"data/images/animations/ghost/{self.type}_right", "png", [5, 5], 1, colorkey=(0, 0, 0))
        self.animation.load_anim(f"{self.type}_down", f"data/images/animations/ghost/{self.type}_down", "png", [5, 5], 1, colorkey=(0, 0, 0))
        self.animation.load_anim(f"{self.type}_up", f"data/images/animations/ghost/{self.type}_up", "png", [5, 5], 1, colorkey=(0, 0, 0))
        
        # Eaten
        self.animation.load_anim("eaten_left", "data/images/animations/ghost/eaten_left", "png", [1], 1, colorkey=(0, 0, 0))
        self.animation.load_anim("eaten_right", "data/images/animations/ghost/eaten_right", "png", [1], 1, colorkey=(0, 0, 0))
        self.animation.load_anim("eaten_down", "data/images/animations/ghost/eaten_down", "png", [1], 1, colorkey=(0, 0, 0))
        self.animation.load_anim("eaten_up", "data/images/animations/ghost/eaten_up", "png", [1], 1, colorkey=(0, 0, 0))
        
        # Scatter
        self.animation.load_anim("scatter1_", "data/images/animations/ghost/scatter1_", "png", [1], 1, colorkey=(0, 0, 0))
        self.animation.load_anim("scatter2_", "data/images/animations/ghost/scatter2_", "png", [1], 1, colorkey=(0, 0, 0))
        
    def draw(self, surf):
        state = f"{self.type}_{self.states[self.direction][1]}"
        self.animation.animate(state)
        self.img = self.animation.image
        
        surf.blit(self.img, (self.rect.x-3, self.rect.y-3))
    
    def set_target(self):
        # target is in tile position
        self.target = self.game.tile_positions["player"]
    
    def navigate(self, tiles):
        # This maze navigation applies to all modes, the only that is changes is the target
        remaining_directions = [Direction.UP, Direction.LEFT, Direction.DOWN, Direction.RIGHT]
        x = self.game.tile_positions[self.type][0]
        y = self.game.tile_positions[self.type][1]
        turns = {Direction.RIGHT: [self.level[y][x+1] == 0, self.rect.y % 8], Direction.LEFT: [self.level[y][x-1] == 0, self.rect.y % 8], Direction.DOWN: [self.level[y+1][x] == 0, self.rect.x % 8], Direction.UP: [self.level[y-1][x] == 0, self.rect.x % 8]}
        if self.get_next_move:
            self.set_target()
            
            current_tile_pos = deepcopy(self.game.tile_positions[self.type])
            next_tile = [current_tile_pos[0]+self.states[self.direction][0][0], current_tile_pos[1]+self.states[self.direction][0][1]]
            
            if self.direction == Direction.RIGHT:
                opposite_direction = Direction.LEFT
            if self.direction == Direction.LEFT:
                opposite_direction = Direction.RIGHT
            if self.direction == Direction.DOWN:
                opposite_direction = Direction.UP
            if self.direction == Direction.UP:
                opposite_direction = Direction.DOWN
            
            remaining_directions.pop(remaining_directions.index(opposite_direction))
            
            valid_turns = []
            for direction in remaining_directions:
                tile = [next_tile[0]+self.states[direction][0][0], next_tile[1]+self.states[direction][0][1]]
                if self.level[tile[1]][tile[0]] == 0:
                    valid_turns.append([tile, direction])
            
            dis = 9999
            for tile in valid_turns:
                distance = E.dis_between_points(tile[0], self.target)
                if distance < dis:
                    dis = distance
                    self.next_move = tile[1]
                    next_tile = tile[0]
                    self.get_next_move = False
                if distance == dis:
                    if tile[1].value < self.next_move.value:
                        self.next_move = direction
                        next_tile = tile[0]
                        self.get_next_move = False
        else:
            if turns[self.next_move] == [True, 0]:
                self.direction = self.next_move
                self.get_next_move = True
            
        movement = deepcopy(self.states[self.direction][0])
        movement[0] *= self.vel
        movement[1] *= self.vel
        
        self.collisions = self.physics_obj.movement(movement, tiles)
        self.rect.center = self.physics_obj.rect.center 

class Fruit:
    def __init__(self, x, y, type):
        self.img = E.ImageManager.load(f"data/images/{type}.png", colorkey=(0, 0, 0))
        self.rect = self.img.get_rect(topleft=(x, y))
    
    def draw(self, surf):
        surf.blit(self.img, self.rect)
    
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((224*2, 308*2))
        pygame.display.set_caption("Pacman Clone")
        self.display =  pygame.Surface((224, 308))
        self.clock = pygame.time.Clock()
        self.fps = 30
        self.TILESIZE = 8
        self.running = True
        self.level = []
        self.tileset = {}
        self.coin_img = None
        self.big_coin_img = None
        self.coins = []
        self.big_coins = []
        self.player = Player(14*self.TILESIZE, 26*self.TILESIZE)
        # pos for fruit: 13*self.TILESIZE, 25.5*self.TILESIZE
        self.fruit_list = ["cherry", "strawberry", "orange", "apple", "melon", "galaxian", "bell", "key"]
        self.fruit_index = 0
        self.fruit = None
        self.tiles = []
        self.score = 0
        self.highscore = 0
        self.spawn_timer = E.Timer(30)
        self.font = E.Text("data/images/font.png", 1, 1)
        
        self.ghosts = {
            "red": Ghost(self, 11*self.TILESIZE, 26*self.TILESIZE, "red"), 
            "orange": Ghost(self, 10*self.TILESIZE, 26*self.TILESIZE, "orange"), 
            "pink": Ghost(self, 8*self.TILESIZE, 26*self.TILESIZE, "pink"), 
            "blue": Ghost(self, 7*self.TILESIZE, 26*self.TILESIZE, "blue")
            }
        
        self.sounds = {"chomp":pygame.mixer.Sound("data/audio/pacman_chomp.wav")}
        
        self.tile_positions = {
            "player": [int(self.player.rect.centerx/self.TILESIZE), int(self.player.rect.centery/self.TILESIZE)], 
            "red":[int(self.ghosts["red"].rect.centerx/self.TILESIZE), int(self.ghosts["red"].rect.centery/self.TILESIZE)],
            "orange":[int(self.ghosts["orange"].rect.centerx/self.TILESIZE), int(self.ghosts["orange"].rect.centery/self.TILESIZE)],
            "pink":[int(self.ghosts["pink"].rect.centerx/self.TILESIZE), int(self.ghosts["pink"].rect.centery/self.TILESIZE)],
            "blue":[int(self.ghosts["blue"].rect.centerx/self.TILESIZE), int(self.ghosts["blue"].rect.centery/self.TILESIZE)]
            } # tile positions of entities in the game
        
        self.load_tileset()
        self.load_level()
        
    
    def load_tileset(self):
        tile_count = 1    
        temp_img = E.ImageManager.load("data/images/Arcade - Pac-Man - General Sprites.png")
        self.coin_img = E.ImageManager.get_image(temp_img, 1 * self.TILESIZE, 1*self.TILESIZE, self.TILESIZE, self.TILESIZE, 1)
        self.big_coin_img = E.ImageManager.get_image(temp_img, 1 * self.TILESIZE, 3*self.TILESIZE, self.TILESIZE, self.TILESIZE, 1)
        for y in range(int(temp_img.get_height() / self.TILESIZE)):
            for x in range(int(temp_img.get_width() / self.TILESIZE)):
                self.tileset[tile_count] = E.ImageManager.get_image(
                    temp_img,
                    x * self.TILESIZE,
                    y * self.TILESIZE,
                    self.TILESIZE,
                    self.TILESIZE,
                    1)

                tile_count += 1
    
    def load_level(self):
        with open("data/levels/level.json", "rb") as file:
            data = json.load(file)
            file.close()
            
        
        for y in range(36):
            self.level.append([])
            for x in range(28):
                tile = data["layers"][0]["data"][(y*28)+x]
                if tile not in [87, 282]:
                    self.level[y].append(tile)
                    if tile != 0:
                        self.tiles.append(pygame.Rect(x*self.TILESIZE, y*self.TILESIZE, self.TILESIZE, self.TILESIZE))
                else:
                    self.level[y].append(0)
                    if tile == 87:
                        self.coins.append(Coin(x*self.TILESIZE, y*self.TILESIZE, self.coin_img))
                    if tile == 282:
                        self.big_coins.append(BigCoin(x*self.TILESIZE, y*self.TILESIZE, self.big_coin_img))
        
        self.spawn_timer.set()
    
    def run(self):
        while self.running:
            self.screen.fill((0, 0, 0))
            self.display.fill((0, 0, 0))
            self.clock.tick(self.fps)
            
            for y, row in enumerate(self.level):
                for x, tile in enumerate(row):
                    if tile in self.tileset:
                        self.display.blit(self.tileset[tile], (x*self.TILESIZE, y*self.TILESIZE))
            
            #for tile in self.tiles:
                #pygame.draw.rect(self.display, (255, 0, 0), tile, 1)
            
            for i, coin in sorted(enumerate(self.coins), reverse=True):
                coin.draw(self.display)
                if self.player.rect.colliderect(coin.rect):
                    self.coins.pop(i)
                    self.score += 10
                    #self.sounds["chomp"].play(maxtime=100)
            
            for i, big_coin in sorted(enumerate(self.big_coins), reverse=True):
                big_coin.draw(self.display)
                if self.player.rect.colliderect(big_coin.rect):
                    self.big_coins.pop(i)
                    self.score += 50
            
            turns = None
            
            if self.player.rect.x > self.display.get_width():
                self.player.physics_obj.x = -7
            if self.player.rect.topright[0] < 0:
                self.player.physics_obj.x = self.display.get_width()
            
            try:
                x = self.tile_positions["player"][0]
                y = self.tile_positions["player"][1]
                turns = {Direction.RIGHT: [self.level[y][x+1] == 0, self.player.rect.y % self.TILESIZE], Direction.LEFT: [self.level[y][x-1] == 0, self.player.rect.y % self.TILESIZE], Direction.DOWN: [self.level[y+1][x] == 0, self.player.rect.x % self.TILESIZE], Direction.UP: [self.level[y-1][x] == 0, self.player.rect.x % self.TILESIZE]}
            except Exception as e:
                pass
        
            if self.spawn_timer.timed_out() and self.fruit_index < len(self.fruit_list):
                self.fruit = Fruit(13*self.TILESIZE, 25.5*self.TILESIZE, self.fruit_list[self.fruit_index])
                self.fruit_index += 1
                self.spawn_timer.set()
        
            if self.fruit:
                self.fruit.draw(self.display)
                if self.player.rect.colliderect(self.fruit.rect):
                    self.fruit = None
                
            self.player.move(turns, self.tiles)
            self.player.draw(self.display)
            
            for g in self.ghosts:
                ghost = self.ghosts[g]
                ghost.navigate(self.tiles)
                ghost.draw(self.display)
            
            self.font.render(self.display, "SCORE: ", 6, 3, (0, 0, 255))
            self.font.render(self.display, "SCORE: ", 5, 2, (255, 255, 255))
            self.font.render(self.display, f"{self.score}", 6, 13, (0, 0, 255))
            self.font.render(self.display, f"{self.score}", 5, 12, (255, 255, 255))
            
            self.tile_positions["player"] = [int(self.player.rect.centerx/self.TILESIZE), int(self.player.rect.centery/self.TILESIZE)]
            self.tile_positions["red"] = [int(self.ghosts["red"].rect.centerx/self.TILESIZE), int(self.ghosts["red"].rect.centery/self.TILESIZE)]
            self.tile_positions["orange"] = [int(self.ghosts["orange"].rect.centerx/self.TILESIZE), int(self.ghosts["orange"].rect.centery/self.TILESIZE)]
            self.tile_positions["pink"] = [int(self.ghosts["pink"].rect.centerx/self.TILESIZE), int(self.ghosts["pink"].rect.centery/self.TILESIZE)]
            self.tile_positions["blue"] = [int(self.ghosts["blue"].rect.centerx/self.TILESIZE), int(self.ghosts["blue"].rect.centery/self.TILESIZE)]
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        if len(self.player.input) < 2:
                            self.player.input.append(Direction.LEFT)
                        else:
                            self.player.input = []
                            self.player.input.append(Direction.LEFT)
                    if event.key == pygame.K_RIGHT:
                        if len(self.player.input) < 2:
                            self.player.input.append(Direction.RIGHT)
                        else:
                            self.player.input = []
                            self.player.input.append(Direction.RIGHT)
                    if event.key == pygame.K_UP:
                        if len(self.player.input) < 2:
                            self.player.input.append(Direction.UP)
                        else:
                            self.player.input = []
                            self.player.input.append(Direction.UP)
                    if event.key == pygame.K_DOWN:
                        if len(self.player.input) < 2:
                            self.player.input.append(Direction.DOWN)
                        else:
                            self.player.input = []
                            self.player.input.append(Direction.DOWN)
            
            self.screen.blit(pygame.transform.scale(self.display, (self.screen.get_width(), self.screen.get_height())), (0, 0))
            pygame.display.update()
            self.spawn_timer.update()


Game().run()

pygame.quit()
sys.exit()
