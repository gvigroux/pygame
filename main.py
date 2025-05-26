import json
import os
import pygame
import cairo
import math
import time

from object.arc import Arc
from object.ball import Ball
from video import ffmpeg
from video import opencv
from video.py_save import RecorderPyGame


# --- LOAD CONFIG ---

file_path = os.path.dirname(os.path.realpath(__file__))
file = os.path.join(file_path, "config.json")
if( os.path.isfile(file) == False ):
    exit()
with open(file) as f:
    config = json.load(f)

window_size = config.get("window_size", [540, 960])

WIDTH, HEIGHT = window_size
LINE_WIDTH = 15
GAP_DEGREES = 60



pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.SRCALPHA, vsync=1)



def cairo_to_pygame(surface):
    return pygame.image.frombuffer(
        surface.get_data(), (surface.get_width(), surface.get_height()), "RGBA"
    ).convert_alpha()

# Balls creation
balls = []
for data in config["balls"]:
    count = data.get("count", 1)
    for i in range(count):
        ball = Ball( data, window_size, count, i)
        #if not any(check_ball_collision(ball, other) for other in balls):
        balls.append(ball)

# Arcs creation
arcs = []
for data in config["arcs"]:
    count = data.get("count", 1)
    for i in range(count):
        arcs.append(Arc(data, window_size, count, i))



# Dossier pour stocker les images

#recorder = opencv.RecorderOpenCV(window_size)
#recorder = ffmpeg.RecorderFFMPEG(window_size)
recorder = RecorderPyGame(window_size)


frame_count = 0
dt_history = []
clock = pygame.time.Clock()
start_time = time.perf_counter()
last_time = time.perf_counter()
running = True

while running:
    t0 = time.perf_counter()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = time.perf_counter()
    dt = current_time - last_time
    last_time = current_time

    # ajustement du dt pour éviter les dépassements
    dt_history.append(dt)
    if len(dt_history) > 5:
        dt_history.pop(0)
    dt = sum(dt_history) / len(dt_history)



    elapsed_time = time.perf_counter() - start_time

    # Step 1 : Update logique
    t1 = time.perf_counter()
    for ball in balls:  
        for arc in arcs:
            zone = ball.ball_hits_arc(arc)
    for ball in balls:
        ball.update(dt)
    for arc in arcs:
        arc.update(elapsed_time)
    t2 = time.perf_counter()


    # Step 2 : Cairo rendering
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)

    ctx.set_source_rgba(0, 0, 0, 1)
    ctx.rectangle(0, 0, WIDTH, HEIGHT)
    ctx.fill()
    ctx.set_antialias(cairo.ANTIALIAS_GOOD)  # ANTIALIAS_BEST est très coûteux

    for arc in arcs:
        arc.draw(ctx)

    for ball in balls:
        ball.draw(ctx)
    t3 = time.perf_counter()

    # Step 3 : Cairo to Pygame
    img = cairo_to_pygame(surface)
    t4 = time.perf_counter()

    recorder.write(pygame, screen, frame_count)
    #pygame.image.save(screen, f"captures/frame_{frame_count:04d}.png")
    frame_count += 1
    #if frame_count % 2 == 0:
    #    pixels = pygame.surfarray.array3d(screen)
    #    opencv.write(pixels)

    # Step 4 : Affichage
    screen.blit(img, (0, 0))
    pygame.display.flip()
    t5 = time.perf_counter()
    clock.tick(50)
 
    # Debug print
    #print(f"UPDATE: {(t2 - t1)*1000:.2f} ms | DRAW: {(t3 - t2)*1000:.2f} ms | CONVERT: {(t4 - t3)*1000:.2f} ms | BLIT+DISPLAY: {(t5 - t4)*1000:.2f} ms | TOTAL: {(t5 - t0)*1000:.2f} ms")
    fps = clock.get_fps()
    #pygame.display.set_caption(f"FPS: {fps:.1f}")
    print(f"FPS={clock.get_fps():.2f} | dt={dt*1000:.2f}ms")

recorder.stop()
pygame.quit()
