import time
import pygame
import moderngl
import numpy as np
import cairo
import math
import random
from pygame.locals import DOUBLEBUF, OPENGL

from background.pulse import Pulse
from background.pulse_colored   import PulseColored
from background.dots import Dots
from background.gradient import Gradient
from background.grid import Grid
from background.damier import Damier
from background.plasma import Plasma
from background.wave import Wave

from object.arc import Arc
from object.ball import Ball
from object.particule_system import ParticleSystem
from object.text import Text

import conf


# --- INITIALISATION ---
pygame.init()
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)  # VSync
pygame.display.set_mode(conf.WINDOW_SIZE, DOUBLEBUF | OPENGL)
clock = pygame.time.Clock()

ctx = moderngl.create_context()
ctx.enable(moderngl.BLEND)
ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

# VBO quad partagé
quad = np.array([
    -1.0, -1.0, 0.0, 0.0,
     1.0, -1.0, 1.0, 0.0,
    -1.0,  1.0, 0.0, 1.0,
     1.0,  1.0, 1.0, 1.0,
], dtype='f4')
vbo = ctx.buffer(quad.tobytes())


def ortho_projection(width, height):
    return np.array([
        [2 / width, 0, 0, -1],
        [0, -2 / height, 0, 1],
        [0, 0, -1, 0],
        [0, 0, 0, 1]
    ], dtype='f4')


# --- GÉNÉRATION DES ARCS ---
arcs = []
for i in range(conf.ARC_COUNT):
    arcs.append(Arc(ctx, vbo, conf.ARC_START_RADIUS + i*conf.ARC_SPACE, (i+1)*conf.ARC_ANGLE_START, conf.ARC_ANGLE_END))


    
font = pygame.font.SysFont("Arial", 20)
fps = Text(ctx, vbo, font)
show_fps = True

       
particle_system = ParticleSystem(ctx, vbo)
particle_system.warm_up()

ball = Ball(ctx, vbo)
points = ball.get_fragment_points()
for pt in points: 
    angle = np.random.uniform(0, 2 * np.pi)
    speed = np.random.uniform(30, 80)  # pixels/sec
    vx = np.cos(angle) * speed
    vy = np.sin(angle) * speed
    particle_system.spawn(pt, (vx, vy), ball.color, lifetime=1.0)

background = PulseColored(ctx, vbo)


# --- BOUCLE PRINCIPALE ---
running = True
last_explosion = time.time()

while running:
    ctx.clear(0.1, 0.1, 0.1, 0.0)
    dt = clock.tick(60) / 1000.0  # en secondes

    background.Draw()
    

    for arc in arcs:
        arc.update(dt)

    # Remove dead arcs
    arcs = [arc for arc in arcs if not arc.is_destroyed()]

    # --- Particules ---
    particle_system.update(dt)
    particle_system.draw()

    # Ball
    ball.update(dt)

    for arc in arcs:
        if( arc.is_exploding() ):
            continue

        zone = ball.collision_zone(arc)
        if( zone is not None ):
            print(arc.id, " touche ", zone)

        if( zone == 'arc' ):
            ball.collision_with_arc(arc)
            points = ball.get_fragment_points()
            for pt in points: 
                angle = np.random.uniform(0, 2 * np.pi)
                speed = np.random.uniform(30, 80)  # pixels/sec
                vx = np.cos(angle) * speed
                vy = np.sin(angle) * speed
                particle_system.spawn(pt, (vx, vy), arc.color, lifetime=1.0)

        elif( zone == 'hole' ):
            arc.explode()
            particle_system.clean()
            points = arc.get_fragment_points()
            for pt in points: 
                angle = np.random.uniform(0, 2 * np.pi)
                speed = np.random.uniform(30, 80)  # pixels/sec
                vx = np.cos(angle) * speed
                vy = np.sin(angle) * speed
                particle_system.spawn(pt, (vx, vy), arc.color, lifetime=1.0)

    # if( len(arcs) == 0 ):
    #     pt = ball.get_fragment_points()
    #     particle_system.clean()
    #     for pt in points: 
    #         angle = np.random.uniform(0, 2 * np.pi)
    #         speed = np.random.uniform(30, 80)  # pixels/sec
    #         vx = np.cos(angle) * speed
    #         vy = np.sin(angle) * speed
    #         particle_system.spawn(pt, (vx, vy), ball.color, lifetime=1.0)
         
    # Ball
    ball.draw()

    if show_fps:
        fps_value = int(clock.get_fps())
        fps.update(f"FPS: {fps_value}", (50, 20), alpha=0.8, scale=1.0)

    pygame.display.flip()
    #clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
