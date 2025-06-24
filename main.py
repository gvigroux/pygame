import json
import os
import random
from moviepy import VideoFileClip
import pygame
import cairo
import math
import time

from backgrounds import BackgroundFactory
from object.arc import Arc
from object.ball import Ball
from object.counter import Counter
from object.pytext import Text


# --- LOAD CONFIG ---

file_path = os.path.dirname(os.path.realpath(__file__))
file = os.path.join(file_path, "config.json")
if( os.path.isfile(file) == False ):
    exit()

# Lecture avec encodage UTF-8 explicite et gestion d'erreur
try:
    with open(file, 'r', encoding='utf-8') as f:
        config = json.load(f)
except UnicodeDecodeError:
    # Fallback si UTF-8 échoue (pour les fichiers mal encodés)
    try:
        with open(file, 'r', encoding='latin-1') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Erreur de décodage JSON: {e}")
        exit()
except json.JSONDecodeError as e:
    print(f"Erreur de syntaxe JSON: {e}")
    exit()
except Exception as e:
    print(f"Erreur inattendue: {e}")
    exit()

window_size = config.get("window_size", [540, 960])


pygame.init()
screen = pygame.display.set_mode((window_size[0], window_size[1]), pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.SRCALPHA, vsync=1)
        
end_step = config.get("end_step", {})


def cairo_to_pygame(surface):
    return pygame.image.frombuffer(
        surface.get_data(), (surface.get_width(), surface.get_height()), "BGRA"
    ).convert_alpha()

# Balls creation
balls = []
for data in config["balls"]:
    count = data.get("count", 1)
    while( len(balls) < count ):
        ball = Ball( data, pygame, screen, window_size, count, len(balls))
        if not any(ball.check_ball_collision(other) for other in balls):
            balls.append(ball)

# Arcs creation
arcs = []
for data in config["arcs"]:
    count = data.get("count", 1)
    for i in range(count):
        arcs.append(Arc(data, pygame, screen, window_size, count, i))

# Texts creation
texts = []
for data in config.get("texts", []):
    count = 1
    parts = [data.get("text").get("value")]
    if( data.get("split", False) ):
        parts = data.get("text").get("value").split('\\n')
        count = len(parts)
    for i in range(count):
        data["text"]["value"] = parts[i]
        texts.append(Text(data, pygame, screen, window_size, count, i))
counter = Counter({}, pygame, screen, window_size, 1, 0)



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


music_detail = config.get("music", [])
if( music_detail.get("file") ):
    pygame.mixer.music.load(music_detail.get("file"))
    #pygame.mixer.music.set_volume(music_detail.get("volume", 0.2))
    start = music_detail.get("start", 0)
    fade_ms = music_detail.get("fade_ms", 0)
    loops = 0
    if( music_detail.get("loop", True) ):
        loops = 1
    pygame.mixer.music.play(loops=loops, start=start, fade_ms=fade_ms)
##pygame.mixer.music.load("media/music/Sam Gellaitry - Assumptions.mp3")
#pygame.mixer.music.play(loops=0, start=24.0, fade_ms=200)



background_config = config.get("background", [])
#background = BackgroundFactory.create("concentric_wave")
background = BackgroundFactory.create(background_config.get("type", "concentric_wave"), background_config)
current_step = 0

arcs_block  = sum(1 for obj in arcs if obj.block(current_step))
balls_block = sum(1 for obj in balls if obj.block(current_step))
texts_block = sum(1 for obj in texts if obj.block(current_step))



import tracemalloc
tracemalloc.start()
logs = []

#save = ffmpeg.RecorderFFMPEG(window_size)
while running:
    t0 = time.perf_counter()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False           
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

    elapsed_time = time.perf_counter() - start_time


    # End of game
    if( current_step >= end_step.get("step", -1) ): 
        running = False


    #***********************************************************************
    # Step Progression
            
    for obj in arcs:
        if obj.destroyed:
            obj.stat()
    for obj in balls:
        if obj.is_destroyed():
            obj.stat()
    for obj in texts:
        if obj.is_destroyed():
            obj.stat()


    
    # Remove dead objects
    a, b, t = len(arcs), len(balls), len(texts)
    arcs    = [obj for obj in arcs  if not obj.destroyed]
    balls   = [obj for obj in balls if not obj.is_destroyed()]
    texts   = [obj for obj in texts if not obj.is_destroyed()]
    
    # List of object groups and their corresponding block counts
    object_groups = [
        (arcs, arcs_block),
        (balls, balls_block),
        (texts, texts_block)
    ]

    # Temporary storage for new block counts
    new_block_counts = []

    # Check each group for blocking objects and update current_step if needed
    for objects, prev_block_count in object_groups:
        current_blocks = sum(1 for obj in objects if obj.block(current_step))
        new_block_counts.append(current_blocks)
        
        # Increment step if previously blocked and now clear
        if prev_block_count > 0 and current_blocks == 0:
            current_step += 1

    # Update block counts for next iteration
    arcs_block, balls_block, texts_block = new_block_counts



    #***********************************************************************
    # Update objects

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
        ball.update(dt, current_step)

    for arc in arcs:
        arc.update(dt, current_step)

    counter.update(dt, current_step)
    
    for text in texts:
        text.update(dt, current_step)

    if( len(arcs) == 0 ):
        for ball in balls:
            ball.explode()


    t2 = time.perf_counter()


    # Step 2 : Cairo rendering
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, window_size[0], window_size[1])
    ctx = cairo.Context(surface)    
    
    ctx.set_source_rgba(0, 0, 0, 1)
    ctx.rectangle(0, 0, window_size[0], window_size[1])
    ctx.fill()
    ctx.set_antialias(cairo.ANTIALIAS_BEST)


    # TODO: It's more efficient to draw the background but there are artifacts
    #ctx.set_operator(cairo.OPERATOR_SOURCE)
    #ctx.set_source_rgba(0, 0, 0, 1)
    #ctx.paint()

    t10 = time.perf_counter()    

    background.draw(ctx, current_time, window_size[0], window_size[1])
    counter.draw(ctx)
    t11 = time.perf_counter()

    for arc in arcs:
        arc.draw(ctx)
    t12 = time.perf_counter()

    for ball in balls:
        ball.draw(ctx)

    t3 = time.perf_counter()

    #for text in texts:
    #    text.draw(ctx)
    
    # Step 3 : Cairo to Pygame
    img = cairo_to_pygame(surface)
    t4 = time.perf_counter()

    frame_count += 1

    # Step 4 : Affichage
    screen.blit(img, (0, 0))


    t5 = time.perf_counter()
    for text in texts:
        text.draw(ctx)

    t6 = time.perf_counter()

    pygame.display.flip()
    t7 = time.perf_counter()
    clock.tick(60)
 
    # Debug print
    logs.append(t6 - t5)
    print(f"UPDATE: {(t2 - t1)*1000:.2f} ms | DRAW: {(t3 - t2)*1000:.2f} ms - SURFACE {(t10 - t2)*1000:.2f}/BACK {(t11 - t10)*1000:.2f}/ARCS {(t12 - t11)*1000:.2f}/BALLS {(t3 - t12)*1000:.2f}| CONVERT: {(t4 - t3)*1000:.2f} ms | BLIT+DISPLAY: {(t5 - t4)*1000:.2f} ms | TEXT DRAW: {(t6 - t5)*1000:.2f} ms | FLIP : {(t7 - t6)*1000:.2f} ms | TOTAL: {(t7 - t0)*1000:.2f} ms | dt={dt*1000:.2f}ms | FPS={clock.get_fps():.2f}")
    fps = clock.get_fps()
    #print(f"FPS={clock.get_fps():.2f} | dt={dt*1000:.2f}ms")

        
    current, peak = tracemalloc.get_traced_memory()
    #print(f"RAM utilisée : {current/1024:.1f} Ko | Pic : {peak/1024:.1f} Ko")


#save.stop()

pygame.quit()


# Moyenne à la fin
average = sum(logs) / len(logs)
print(f"Moyenne : {average*1000:.2f} ms")

background.stat()
for obj in arcs:
    obj.stat()
for obj in balls:
    obj.stat()
for obj in texts:
    obj.stat()

