import json
import os
import random
import pygame
import cairo
import math
import time

from backgrounds import BackgroundFactory
from object.arc import Arc
from object.ball import Ball
from object.counter import Counter
from object.text import Text
from object.text_tiktok import TextTikTok
from video import ffmpeg
from video import opencv
from video.empty import RecorderEmpty
from video.py_save import RecorderPyGame


# --- LOAD CONFIG ---

file_path = os.path.dirname(os.path.realpath(__file__))
file = os.path.join(file_path, "config.json")
if( os.path.isfile(file) == False ):
    exit()
with open(file) as f:
    config = json.load(f)

window_size = config.get("window_size", [540, 960])


pygame.init()
screen = pygame.display.set_mode((window_size[0], window_size[1]), pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.SRCALPHA, vsync=1)
        

def cairo_to_pygame(surface):
    return pygame.image.frombuffer(
        surface.get_data(), (surface.get_width(), surface.get_height()), "RGBA"
    ).convert_alpha()

# Balls creation
balls = []
for data in config["balls"]:
    count = data.get("count", 1)
    while( len(balls) < count ):
        ball = Ball( data, pygame, window_size, count, len(balls))
        if not any(ball.check_ball_collision(other) for other in balls):
            balls.append(ball)

# Arcs creation
arcs = []
for data in config["arcs"]:
    count = data.get("count", 1)
    for i in range(count):
        arcs.append(Arc(data, pygame, window_size, count, i))

# Texts creation
texts = []
for data in config.get("texts", []):
    for i in range(data.get("count", 1)):
        texts.append(Text(data, pygame, window_size, count, i))

counter = Counter({}, pygame, window_size, 1, 0)


frame_count = 0
dt_history = []
clock = pygame.time.Clock()
start_time = time.perf_counter()
last_time = time.perf_counter()
running = True

pygame.mixer.init()
pygame.mixer.music.set_volume(0.2)  # 50% du volume
bounce_sound    = pygame.mixer.Sound("media/sound/retro/SoundJump2.wav")
bounce_sound.set_volume(0.1)
explosion_sound = pygame.mixer.Sound("media/sound/retro/SoundLand2.wav")
bounce_sound.set_volume(0.1)


background = BackgroundFactory.create("concentric_wave")

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

    for i in range(len(balls)):
        for j in range(i + 1, len(balls)):
            if( balls[i].check_ball_collision(balls[j]) ):
                balls[i].ball_collision(balls[j])
                bounce_sound.play()
                


    # Step 1 : Update logique
    t1 = time.perf_counter()
    for ball in balls:
        for arc in arcs:
            zone = ball.check_arc_collision(arc)
            if( zone == "hit_hole" ):
                arc.explode()
                explosion_sound.play()
            elif( zone == "hit_arc" ):
                ball.arc_collision(arc)
                bounce_sound.play()

    for ball in balls:
        ball.update(dt)
    for arc in arcs:
        #arc.update(elapsed_time)
        arc.update(dt)
    counter.update(dt)
    t2 = time.perf_counter()


    # Remove dead objects
    arcs    = [obj for obj in arcs  if not obj.destroyed]
    balls   = [obj for obj in balls if not obj.is_destroyed()]

    if( len(arcs) == 0 ):
        for ball in balls:
            ball.explode()


    # Step 2 : Cairo rendering
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, window_size[0], window_size[1])
    ctx = cairo.Context(surface)    
    #ctx.set_antialias(cairo.ANTIALIAS_NONE)
    
    
    ctx.set_source_rgba(0, 0, 0, 1)
    ctx.rectangle(0, 0, window_size[0], window_size[1])
    ctx.fill()

    background.draw(ctx, current_time, window_size[0], window_size[1])
    ctx.set_antialias(cairo.ANTIALIAS_BEST)

    counter.draw(ctx)

    for arc in arcs:
        arc.draw(ctx)

    for ball in balls:
        ball.draw(ctx)

    #for text in texts:
    #    text.draw(ctx)


    


    t3 = time.perf_counter()

    
    # Step 3 : Cairo to Pygame
    img = cairo_to_pygame(surface)
    t4 = time.perf_counter()

    frame_count += 1

    # Step 4 : Affichage
    screen.blit(img, (0, 0))

    #font = pygame.font.SysFont("TikTok Text", 50)  # Police système (Arial, Verdana...)
    #text = font.render("Votre texte ici", True, (255, 255, 255))  # Couleur blanche
    #screen.blit(text, (100, 400))  # Position (x, y)



    pygame.display.flip()
    t5 = time.perf_counter()
    clock.tick(60)
 
    # Debug print
    #print(f"UPDATE: {(t2 - t1)*1000:.2f} ms | DRAW: {(t3 - t2)*1000:.2f} ms | CONVERT: {(t4 - t3)*1000:.2f} ms | BLIT+DISPLAY: {(t5 - t4)*1000:.2f} ms | TOTAL: {(t5 - t0)*1000:.2f} ms")
    fps = clock.get_fps()
    print(f"FPS={clock.get_fps():.2f} | dt={dt*1000:.2f}ms")


pygame.quit()
