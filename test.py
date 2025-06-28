import json
import os
import random
from moviepy import VideoFileClip
import pygame
import cairo
import math
import time

from background.backgrounds import BackgroundFactory
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
#background = BackgroundFactory.create(background_config.get("type", "concentric_wave"), background_config)

background = BackgroundFactory.create("solid")

# Cairo surface et contexte réutilisables
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, *window_size)
ctx = cairo.Context(surface)

while not background.ready:
    time.sleep(0.01)

pygame.init()


objects = []
for data in config.get("objects", []):

    count = data.get("count", 1) 

    # Automatically split text
    if( data.get("type") == "text" ) and data.get("split", False):
        if( count > 1 ):
            print(f"\033[38;5;208mWarning (Text): The count property is ignored for text objects!\033[0m")
        parts = data.get("text").get("value").split('\\n')
        count = len(parts)
        
    for i in range(count):

        # Update text value
        if( data.get("type") == "text" ) and data.get("split", False):
            data["text"]["value"] = parts[i]

        object = ObjectFactory.create(data, pygame, None, window_size, count, i)
        if( isinstance(object, Ball) ):
            if not any(object.check_ball_collision(other) for other in objects if isinstance(other, Ball)):
                objects.append(object)
        else:
            objects.append(object)

obj_block = sum(1 for obj in objects if obj.block(0))






screen = pygame.display.set_mode((window_size[0], window_size[1]), pygame.DOUBLEBUF | pygame.SRCALPHA)
        



# 1) Cairo → rouge
ctx.save()
ctx.set_source_rgb(1, 0, 0)  # Rouge
ctx.paint()
ctx.restore()

# 2) Convertis vers Pygame
raw_buf = surface.get_data()
img = pygame.image.frombuffer(raw_buf, window_size, "BGRA").convert_alpha()
screen.blit(img, (0, 0))
pygame.display.flip()

# 3) Maintenant, fais une mini boucle pour traiter les events jusqu’à ce que tout soit prêt :
while not background.ready:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    time.sleep(0.01)





end_step = config.get("end_step", {})

frame_count = 0
dt_history = []
clock = pygame.time.Clock()


pygame.mixer.init()
pygame.mixer.music.set_volume(0.2)  # 50% du volume


music_detail = config.get("music", {})
if( music_detail.get("file", False) ):
    pygame.mixer.music.load(music_detail.get("file"))
    start = music_detail.get("start", 0)
    fade_ms = music_detail.get("fade_ms", 0)
    loops = 0
    if( music_detail.get("loop", True) ):
        loops = 1
    pygame.mixer.music.play(loops=loops, start=start, fade_ms=fade_ms)





logs = []
current_step = 0
total_draw_average = 0 
last_time = time.perf_counter()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = time.perf_counter()
    dt = current_time - last_time
    last_time = current_time


    ctx.save()
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.paint()
    ctx.restore()

    background.draw(ctx, current_time, window_size[0], window_size[1])

    raw_buf = surface.get_data()
    img = pygame.image.frombuffer(raw_buf, (window_size[0], window_size[1]), "BGRA").convert_alpha()
    screen.blit(img, (0, 0))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
