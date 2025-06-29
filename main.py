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



        
############### Background ###############
background_config = config.get("background", [])
background_backup = BackgroundFactory.create("concentric_wave")
background = BackgroundFactory.create(background_config.get("type", "concentric_wave"), background_config)
#background = BackgroundFactory.create("solid")

# Cairo surface et contexte réutilisables
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, *window_size)
ctx = cairo.Context(surface)

while not background.ready:
    time.sleep(0.01)


pygame.init()
game = Game(pygame, config, window_size)
game.load()

screen = pygame.display.set_mode((window_size[0], window_size[1]), pygame.DOUBLEBUF | pygame.SRCALPHA)
        



# # 1) Cairo → rouge
# ctx.save()
# ctx.set_source_rgb(1, 0, 0)  # Rouge
# ctx.paint()
# ctx.restore()

# # 2) Convertis vers Pygame
# raw_buf = surface.get_data()
# img = pygame.image.frombuffer(raw_buf, window_size, "BGRA").convert_alpha()
# screen.blit(img, (0, 0))
# pygame.display.flip()

# # 3) Maintenant, fais une mini boucle pour traiter les events jusqu’à ce que tout soit prêt :
# while not background.ready:
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             pygame.quit()
#             exit()
#     time.sleep(0.01)







pygame.mixer.init()
pygame.mixer.music.set_volume(0.2)  # 50% du volume


music_detail = config.get("music", {})
if( music_detail.get("file", False) ):
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




end_step = config.get("end_step", {})
frame_count = 0
dt_history = []
clock = pygame.time.Clock()
last_time = time.perf_counter()
running = True
current_step = 0
obj_block = game.block_count(0)
logs = []
total_draw_average = 0 




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

    # End of game
    if( current_step >= end_step.get("step", -1) ): 
        running = False

    #***********************************************************************
    # Destroyed objects
             
    for obj in game.objects:
        if obj.is_destroyed():
            total_draw_average += obj.stat()

    # Nettoyage des objets détruits
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

    #***********************************************************************
    # Update objects

    t1 = time.perf_counter()
    
    for object in game.objects:
        object.update(dt, current_step, clock)

    # Check if we need to explose balls
    arcs_count = sum(1 for obj in game.objects if isinstance(obj, Arc) and obj.is_alive(current_step))
    if( arcs_count == 0 ):        
        for i, obj in enumerate(game.objects):
            if isinstance(obj, Ball):
                obj.explode()

    if( background.is_done() ):
        background = BackgroundFactory.create("concentric_wave")

    #***********************************************************************
    # Cairo rendering

    t2 = time.perf_counter()

    ctx.save()
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.paint()
    ctx.restore()

    t10 = time.perf_counter()    


    #***********************************************************************
    # Draw

    background.draw(ctx, current_time, window_size[0], window_size[1])
  
    t11 = time.perf_counter()

    for object in game.objects:
        object.draw(ctx)

    t3 = time.perf_counter()
    
    # Step 3 : Cairo to Pygame
    raw_buf = surface.get_data()
    img = pygame.image.frombuffer(raw_buf, window_size, "BGRA").convert_alpha()
    t4 = time.perf_counter()

    frame_count += 1

    # Step 4 : Affichage
    screen.blit(img, (0, 0))

    t5 = time.perf_counter()

    for object in game.objects:
        object.draw_surface(screen)

    t6 = time.perf_counter()

    pygame.display.flip()
    t7 = time.perf_counter()
    clock.tick(60)
 
    # Debug print
    logs.append(t3 - t2)
    fps = clock.get_fps()
    #print(f"FIRST: {(t1 - t0)*1000:.2f} ms | UPDATE: {(t2 - t1)*1000:.2f} ms | DRAW: {(t3 - t2)*1000:.2f} ms - SURFACE {(t10 - t2)*1000:.2f}/BACK {(t11 - t10)*1000:.2f}/OBJECTS {(t3 - t11)*1000:.2f}| CONVERT: {(t4 - t3)*1000:.2f} ms | BLIT+DISPLAY: {(t5 - t4)*1000:.2f} ms | TEXT DRAW: {(t6 - t5)*1000:.2f} ms | FLIP : {(t7 - t6)*1000:.2f} ms | TOTAL: {(t7 - t0)*1000:.2f} ms | dt={dt*1000:.2f}ms | FPS={fps:.2f}")
    #print(f"FPS={fps:.2f} | dt={dt*1000:.2f}ms")
    #print(f"STEP: {current_step}")


pygame.quit()


# Moyenne à la fin
average = sum(logs) / len(logs)
print(f"Moyenne : {average*1000:.2f} ms")

background.stat()
total_draw_average += background.stat()
for obj in game.objects:
    total_draw_average += obj.stat()
print(f"Total Obj Draw : {total_draw_average*1000:.2f} ms")

