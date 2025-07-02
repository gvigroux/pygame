import json
import os
import random
from moviepy import VideoFileClip
import pygame
import cairo
import math
import time

from background.backgrounds import BackgroundFactory
from game import Game
from object.arc import Arc
from object.ball import Ball
from object.object_factory import ObjectFactory



pygame.init()
game = Game(pygame)

# Load config
game.load()

# Cairo surface et contexte réutilisables
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, *game.window_size)
ctx     = cairo.Context(surface)
screen  = pygame.display.set_mode((game.window_size[0], game.window_size[1]), pygame.DOUBLEBUF | pygame.SRCALPHA)
        



dt_history = []
clock = pygame.time.Clock()
last_time = time.perf_counter()
running = True
current_step = 0
obj_block = game.block_count(0)


game.debug(False)

while running:
    t0 = time.perf_counter()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False           
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  
                x, y = event.pos
                print(f"{x*100/game.window_size[0]:.1f}% / {y*100/game.window_size[1]:.1f}% at {game.age:.1f}s")
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                print("Ctrl+C détecté via clavier (pas SIGINT)")
                running = False

    current_time = time.perf_counter()
    dt = current_time - last_time
    last_time = current_time

    # ajustement du dt pour éviter les dépassements
    dt_history.append(dt)
    if len(dt_history) > 5:
        dt_history.pop(0)
    dt = sum(dt_history) / len(dt_history)

    # End of game
    if( game.is_finished(current_step) ):
        running = False


    #***********************************************************************
    # Destroyed objects

    game.clean()

    # Comptage des objets bloquants avant mise à jour
    prev_block_count = obj_block
    obj_block = game.block_count(current_step)

    # Avancement du step si plus de blocage
    if prev_block_count > 0 and obj_block == 0:
        current_step += 1

    #***********************************************************************
    # Check collisions 

    game.check_collisions()
   
    game.update(dt, current_step, clock, obj_block)

    #***********************************************************************
    # Cairo rendering

    ctx.save()
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.paint()
    ctx.restore()

    #***********************************************************************
    # Draw

    game.draw_on_context(ctx, current_time)

  
    
    # Step 3 : Cairo to Pygame
    raw_buf = surface.get_data()
    img = pygame.image.frombuffer(raw_buf, game.window_size, "BGRA").convert_alpha()
 

    # Step 4 : Affichage
    screen.blit(img, (0, 0))


    for object in game.objects:
        object.draw_surface(screen)


    pygame.display.flip()
    t7 = time.perf_counter()
    clock.tick(60)
 
    # Debug print
    #fps = clock.get_fps()
    if( (t7-t0)*1000 > 14000 ):
        print("WARNING")
    #print(f"FIRST: {(t1 - t0)*1000:.2f} ms | UPDATE: {(t2 - t1)*1000:.2f} ms | DRAW: {(t3 - t2)*1000:.2f} ms - SURFACE {(t10 - t2)*1000:.2f}/BACK {(t11 - t10)*1000:.2f}/OBJECTS {(t3 - t11)*1000:.2f}| CONVERT: {(t4 - t3)*1000:.2f} ms | BLIT+DISPLAY: {(t5 - t4)*1000:.2f} ms | TEXT DRAW: {(t6 - t5)*1000:.2f} ms | FLIP : {(t7 - t6)*1000:.2f} ms | TOTAL: {(t7 - t0)*1000:.2f} ms | dt={dt*1000:.2f}ms | FPS={fps:.2f}")

pygame.quit()



