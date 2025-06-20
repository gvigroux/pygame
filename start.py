import json
import os
import time
import pygame
import moderngl
import numpy as np
import cairo
import math
import random
import win32gui

from pygame.locals import DOUBLEBUF, OPENGL

from background.fill import Fill
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
from object.OLD_text import Text
from video.ffmpeg import Capture
from moviepy import *

# --- LOAD CONFIG ---

file_path = os.path.dirname(os.path.realpath(__file__))
file = os.path.join(file_path, "config.json")
if( os.path.isfile(file) == False ):
    exit()
with open(file) as f:
    config = json.load(f)

window_size = config.get("window_size", [540, 960])


# --- INITIALISATION OPENGL ---
pygame.init()
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)  # VSync
pygame.display.set_mode(window_size, DOUBLEBUF | OPENGL)
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



# def check_ball_collision(ball1, ball2):
#     dx = ball2.position[0] - ball1.position[0]
#     dy = ball2.position[1] - ball1.position[1]
#     distance = math.hypot(dx, dy)
#     val = distance < (ball1.radius + ball2.radius)
#     if( val ):
#         print("Collision", ball1.id, ball2.id)
#     return val


def check_ball_collision(ball1, ball2):
    dx = ball1.position[0] - ball2.position[0]
    dy = ball1.position[1] - ball2.position[1]
    distance = (dx**2 + dy**2)**0.5

    # Convert radius pixels to GL space
    radius1_x = ball1.radius / (window_size[0] / 2)
    radius1_y = ball1.radius / (window_size[1] / 2)
    radius2_x = ball2.radius / (window_size[0] / 2)
    radius2_y = ball2.radius / (window_size[1] / 2)

    # Approximate combined radius (you can also use ellipse distance if needed)
    radius_gl = max(radius1_x + radius2_x, radius1_y + radius2_y)
    return distance < radius_gl
        

capture = Capture()
    
font = pygame.font.SysFont("Arial", 20)
#fps = Text(ctx, vbo, font, window_size)
#show_fps = True

       
particle_system = ParticleSystem(ctx, vbo, config["fragments"], window_size)
particle_system.warm_up()

# Balls creation
balls = []
for data in config["balls"]:
    count = data.get("count", 1)
    for i in range(count):
        ball = Ball(ctx, vbo, data, window_size, count, i)
        if not any(check_ball_collision(ball, other) for other in balls):
            balls.append(ball)
        

# Arcs creation
arcs = []
for data in config["arcs"]:
    count = data.get("count", 1)
    for i in range(count):
        arcs.append(Arc(ctx, vbo, data, window_size, count, i))


# Background creation
background = Fill(ctx, vbo, window_size)

#Top Text
texts = []
for data in config.get("texts", []):
    for _ in range(data.get("count", 1)):
        texts.append(Text(ctx, vbo, data, window_size))

# --- BOUCLE PRINCIPALE ---
running = True
sound1 = pygame.mixer.Sound('media/sound/jump.wav') 

last_time = time.time()
last_time2 = time.perf_counter()
frame_count = 0

if( running ):
    #capture.start("pygame window")
    pass

while running:
    ctx.clear(0.1, 0.1, 0.1, 0.0)
    
    # Calculate DT
    #dt = clock.tick(60) / 1000.0  # en secondes
    current_time = time.perf_counter()
    dt = current_time - last_time2
    last_time2 = current_time


    background.Draw()
    
    for arc in arcs:
        arc.update(dt)

    # Remove dead arcs
    arcs = [arc for arc in arcs if not arc.is_destroyed()]


    for i in range(len(balls)):
        for j in range(i + 1, len(balls)):
            if( check_ball_collision(balls[i], balls[j]) ):
                # Switch velocity
                v = balls[i].velocity
                balls[i].velocity = balls[j].velocity
                balls[j].velocity = v

    # Ball
    for ball in balls:
        ball.update(dt)

    for arc in arcs:
        if( arc.is_exploding() ):
            continue

        for ball in balls:
            zone = ball.collision_zone(arc)
            if( zone == 'arc' ):
                sound1.play()
                ball.collision_with_arc(arc)
                points = ball.get_fragment_points()
                for pt in points: 
                    angle = np.random.uniform(0, 2 * np.pi)
                    speed = np.random.uniform(30, 80)  # pixels/sec
                    vx = np.cos(angle) * speed
                    vy = np.sin(angle) * speed
                    particle_system.spawn(pt, (vx, vy), arc.color, lifetime=1.0)

            elif( zone == 'hole' ):
                sound1.play()
                arc.explode(particle_system)
         
    # Ball
    for ball in balls:
        ball.draw()

    for arc in arcs:
        arc.draw()

    # --- Particules ---
    particle_system.update(dt)
    particle_system.draw()

    #if show_fps:
    #    fps_value = int(clock.get_fps())
    #    fps.update(f"FPS: {fps_value}", (50, 20), alpha=0.8, scale=1.0)

    #top.update(f"fg rdg sdfg fd gfd gdhgh g hdgh gd hdgh  dg", (window_size[0]//2, 100), alpha=1.0, scale=1.0)

    # Texts
    for text in texts:
        text.draw()

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # FPS
    frame_count += 1
    if time.time() - last_time >= 1.0:
        #print("FPS:", frame_count)
        frame_count = 0
        last_time = time.time()
            
capture.stop()


def add_audio(video, audios):
    audioclip   = AudioFileClip("media/sound/jump.wav")
    clips = []
    for audio in audios:
        start_in    = audio[0]
        end_in      = audioclip.duration
        clips.append(video.subclipped(start_in, end_in).with_audio(audioclip))    
    return clips




# # Chargement de la vidéo
# video = VideoFileClip("output.mp4")

# # Charger l'effet sonore à insérer (ex: rebond)
# bounce_sound = AudioFileClip("media/sound/jump.wav")

# # Moments où la balle rebondit (en secondes)
# bounce_times = [1.2, 1.5, 1.6, 2]  # À adapter selon ton jeu

# # Créer un effet sonore décalé pour chaque rebond
# bounce_clips = [
#     bounce_sound.with_start(t)
#     for t in bounce_times
# ]
# # Optionnel : fond sonore global (ex: musique)
# # background_audio = AudioFileClip("music.mp3").with_duration(video.duration)

# # Composer tous les sons (rebonds + musique de fond)
# final_audio = CompositeAudioClip(bounce_clips)  # ou [background_audio] + bounce_clips si tu veux les 2

# # Associer l’audio à la vidéo
# video_with_audio = video.with_audio(final_audio)

# # Export
# video_with_audio.write_videofile("result.mp4", codec="libx264", audio_codec="aac")




pygame.quit()
