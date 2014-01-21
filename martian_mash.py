"""
MARTIAN MASH

"""

import sys
import random
import math
import os
import getopt
import pygame
import numpy
import PixelPerfect
from socket import *
from pygame.locals import *

black = (0, 0, 0)
white = (255, 255, 255)
green = (0, 255, 0)
red = (255, 0, 0)

# -------------------- Sprites--------------------
class Health_Bar(pygame.sprite.Sprite):
    def __init__(self, x, y):
        """A blue-green gradient bar (representing health) and black bar (representing lost health)"""
        self.image = pygame.image.load("Screen Objects/Health Bar.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        #Create a black surface with a rect that is equal to the health bar rect, and has a le:ft edge that is
        #at the right edge of the health bar
        self.empty_bar_width = 0
        self.empty_bar = pygame.Surface([(self.empty_bar_width), (self.rect.height)])
        self.empty_bar_rect = pygame.Rect(x+self.rect.width, y, self.rect.width, self.rect.height)
        
    def lose_health(self, hp):
        #As the black empty bar grows by hp, move it left by hp so it covers the colored health bar
        if self.empty_bar_width + hp < self.rect.width:
            self.empty_bar_width+=hp
            self.empty_bar = pygame.Surface([(self.empty_bar_width), (self.rect.height)]) #BETTER WAY TO UPDATE?
            self.empty_bar_rect.right-=hp

class Animated_Character(pygame.sprite.Sprite):
    def __init__(self, run_right_images, run_left_images, punch_right_images, x, y, fps = 60):
        """A video game character
        Arguments: A list of images for running right, running left...
        Functions: Running, kicking, jumping, fighting, and interacting with items"""
        pygame.sprite.Sprite.__init__(self)

        #Image/Animation
        self.run_right_images = run_right_images 
        self.run_left_images = run_left_images
        self.punch_right_images = punch_right_images
        self.image = self.run_left_images[1]
        self.rect = self.image.get_rect()
        self.hitmask = pygame.surfarray.array_alpha(self.image)
        self.delay = 2000/fps #amount of time an image remains on the screen
        self.frame = 0 #marks the current animation frame
        #Update markers for each function.  These could, theoretically, be combined into one
        #update marker, but they tend to interfere with one another and confuse the system
        self.last_run_update=0
        self.last_gravity_update=0
        self.last_air_move_update=0
        self.last_punch_update=0

        #Speed/position
        self.x = x 
        self.dx = 0 
        self.y = y
        self.dy = 0
        self.gravity_strength = 3
        self.max_dy = 15

        #States
        self.state = {
            'on_ground':0,
            'facing_left':0, #facing right isn't necessary, becuase character is always facing either left or right
            'moving_horz':0 #moving horizontally
            }

        #Controls
        self.controls = {
            'f':0
            }

        #Health
        self.health_bar = Health_Bar(10, 10)
        
    def check_ground(self, platform):
        """Checks if the character's rectangle is colliding with the ground rectangle and updates
        the state dictionary.  If the character is not on the ground/clipping the ground excessively,
        check_ground() resets the character's position so that the bottom of the character rectangle
        clips the top ofthe ground rectangle"""
        if pygame.sprite.collide_rect(self, platform):
            if not self.state['on_ground']:
                self.state['on_ground']=1
                self.dy=0
            if self.rect.bottom != platform.rect.top+1:
                self.rect.bottom = platform.rect.top+1
        else:
            if self.state['on_ground']:
                self.state['on_ground']=0

    def stand(self):
        if self.state['facing_left']:
            self.image = self.run_left_images[1]
        else:
            self.image = self.run_right_images[1] #TO DO: CHANGE THESE IMAGES

    def run(self):
        if pygame.time.get_ticks() - self.last_run_update > self.delay:
            self.frame+=1
            if self.state['facing_left']:
                self.dx=-8 
                if self.frame >= len(self.run_left_images):
                    self.frame = 0
                self.image = self.run_left_images[self.frame]
            else:
                self.dx=+8 
                if self.frame >= len(self.run_right_images):
                    self.frame = 0
                self.image = self.run_right_images[self.frame]

            self.last_run_update = pygame.time.get_ticks()

    def punch(self):
        if pygame.time.get_ticks() - self.last_punch_update > self.delay:
            if not self.state['facing_left']:
                if self.frame >= len(self.punch_right_images):
                    self.frame = 0
                self.image = self.punch_right_images[self.frame]
            self.last_punch_update = pygame.time.get_ticks()
                

    def jump(self):
        self.dy=-10

    def gravity(self):
        """Reduces a players height by the a speed self.dy based on self.gravity.  Will not exceed a specified
        terminal velocity self.max_dy"""
        if pygame.time.get_ticks() - self.last_gravity_update > self.delay:
            #Make sure not to exceed the world's terminal velocity, or else the player could move fast enough
            #to pass through objects
            self.dy+=self.gravity_strength
            self.last_gravity_update = pygame.time.get_ticks()

    def air_move(self):
        if pygame.time.get_ticks() - self.last_air_move_update > self.delay:
            if self.state['facing_left']:
                self.dx=-8
                self.image=self.run_left_images[1]
            else:
                self.dx=+8
                self.image=self.run_right_images[1]
            self.last_air_move_update = pygame.time.get_ticks()

    def check_damage(self, opponent):
        if PixelPerfect._pixelPerfectCollisionDetection(self, opponent):
            hp=1  
            self.health_bar.lose_health(hp)
                
    def clear_all_states(self):
        for a, b in self.state.iteritems():
            b = 0

    def check_moving(self):
        for a, b in self.state.iteritems():
            #1 means movement, except in the case of facing_left (which doesn't have anything to do with
            #movement), and on_ground, where a value of 0 indicates movement
            if b==1:
               if a!=('facing_left' or 'on_ground'): 
                   return 1
            if a=='on_ground':
                if b==0:
                    return 1 
        return 0

    def update(self, opponent):
        #Manipulate image/position
        moving = self.check_moving()
        if moving:
            if self.state['on_ground']:
                if self.controls['f']:
                    self.punch()
                    "punch called"
                elif self.state['moving_horz']:
                    self.run()
            else:
                self.gravity()
                if self.state['moving_horz']:
                    self.air_move()
        else:       
            stand()
        
        self.check_damage(opponent)
        
        #Get a new rect update position based on speed
        self.rect = self.image.get_rect()
        self.x+=self.dx
        self.rect.centerx = self.x
        self.y+=self.dy
        self.rect.bottom = self.y
        
class Platform(pygame.sprite.Sprite):
    """A simple, rectangular sprite object"""
    def __init__(self, color, width, height, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.top = y
                
# -------------------- Game Class--------------------

class Game(object):

    def __init__(self):

        pygame.init() 

        #Screen/background
        size = (1000, 600)
        self.screen = pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()
        self.background = pygame.image.load("earth wallpaper.png")
        pygame.display.flip()

        #Load player animations and create player
        run_right_1 = pygame.image.load("runright/run_right_1.png")
        run_right_2 = pygame.image.load("runright/run_right_2.png")
        run_right_3 = pygame.image.load("runright/run_right_3.png")
        run_right_4 = pygame.image.load("runright/run_right_4.png")
        run_right_5 = pygame.image.load("runright/run_right_5.png")
        run_right_6 = pygame.image.load("runright/run_right_6.png")
        run_right_7 = pygame.image.load("runright/run_right_7.png")
        run_right_8 = pygame.image.load("runright/run_right_8.png")
        run_right_9 = pygame.image.load("runright/run_right_9.png")
        run_right_10 = pygame.image.load("runright/run_right_10.png")

        run_left_1 = pygame.image.load("runleft/run_left_1.png")
        run_left_2 = pygame.image.load("runleft/run_left_2.png")
        run_left_3 = pygame.image.load("runleft/run_left_3.png")
        run_left_4 = pygame.image.load("runleft/run_left_4.png")
        run_left_5 = pygame.image.load("runleft/run_left_5.png")
        run_left_6 = pygame.image.load("runleft/run_left_6.png")
        run_left_7 = pygame.image.load("runleft/run_left_7.png")
        run_left_8 = pygame.image.load("runleft/run_left_8.png")
        run_left_9 = pygame.image.load("runleft/run_left_9.png")
        run_left_10 = pygame.image.load("runleft/run_left_10.png")

        punch_right_1 = pygame.image.load("punch_right/punch_right_1.png")
        punch_right_2 = pygame.image.load("punch_right/punch_right_2.png")
        punch_right_3 = pygame.image.load("punch_right/punch_right_3.png")
        punch_right_4 = pygame.image.load("punch_right/punch_right_4.png")
        punch_right_5 = pygame.image.load("punch_right/punch_right_5.png")
        punch_right_6 = pygame.image.load("punch_right/punch_right_6.png")

        self.punch_right_images = [punch_right_1, punch_right_2, punch_right_3, punch_right_4, punch_right_5, punch_right_6]
        self.run_right_images = [run_right_1, run_right_2, run_right_3, run_right_4, run_right_5, run_right_6, run_right_7, run_right_8, run_right_9, run_right_10]
        self.run_left_images = [run_left_1, run_left_2, run_left_3, run_left_4, run_left_5, run_left_6, run_left_7, run_left_8, run_left_9, run_left_10]

        self.player1 = Animated_Character(self.run_right_images, self.run_left_images, self.punch_right_images, 100, 299)
        self.player2 = Animated_Character(self.run_right_images, self.run_left_images, self.punch_right_images, 500, 299)

        #Environment
        self.platform_main = Platform(white, 800, 5, 100, 350)

        #Sprite groups
        self.player_sprites = pygame.sprite.RenderUpdates()
        self.player_sprites.add(self.player1) #COMBINE!!
        
        self.environment_sprites = pygame.sprite.RenderUpdates()
        self.environment_sprites.add(self.platform_main) #COMBINE!!

    def events(self):

        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            if event.type == KEYDOWN:
                if event.key == K_a:
                    self.player1.state['facing_left']=1
                    self.player1.state['moving_horz']=1
                if event.key == K_d:
                    self.player1.state['facing_left']=0 
                    self.player1.state['moving_horz']=1
                if event.key == K_SPACE:
                    self.player1.jump() #this function doesn't belong in update, becuase it only occurs at an isntant
                if event.key == K_f:
                    self.player1.controls['f']=1
            if event.type == KEYUP:
                if event.key == K_a or event.key == K_d: #MAKE SURE THIS ORDER OF OPERATIONS WORKS CORRECTLY
                    self.player1.state['moving_horz']=0
                    self.player1.dx=0
                if event.key == K_f:
                    self.player1.controls['f']=0
        return True

    def run(self):

        running = True
        while running:

            self.clock.tick(60)
            self.screen.fill(white)

            #Draw environment
            self.screen.blit(self.background, [0,0])
            self.environment_sprites.draw(self.screen)

            running = self.events()

            #Check collisions
            self.player1.check_ground(self.platform_main)
            self.player2.check_ground(self.platform_main)

            #Update player
            self.player1.update(self.player2)
            self.player2.update(self.player1)

            #NEED TO CLEAN THIS UP!!
            self.screen.blit(self.player1.image, self.player1.rect)
            self.screen.blit(self.player2.image, self.player2.rect)
            self.screen.blit(self.player1.health_bar.image, self.player1.health_bar.rect)
            self.screen.blit(self.player1.health_bar.empty_bar, self.player1.health_bar.empty_bar_rect)
            pygame.display.update()

            #self.sprites.clear(self.screen, self.background)
            #dirty = self.sprites.draw(self.screen)
            #pygame.display.update(dirty)

        pygame.quit()

# -------------------- Run the Game--------------------

if __name__ == '__main__':
    game = Game()
    game.run()

    
