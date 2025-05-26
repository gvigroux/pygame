
import os
import cv2
import numpy as np


class RecorderOpenCV:
    def __init__(self, window_size):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        
        fps = 30
        fourcc = cv2.VideoWriter_fourcc(*'XVID')  # ou 'mp4v' pour .mp4
        self.video_writer = cv2.VideoWriter('output.avi', fourcc, fps, (window_size[0], window_size[1]))

    def write(self, pygame, screen, frame_count):
        if frame_count % 2 == 0:
            return
        pixels = pygame.surfarray.pixels3d(screen)
        frame = np.rot90(pixels)              # rotation pour corriger l'orientation
        frame = np.fliplr(frame)              # miroir horizontal si besoin
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        self.video_writer.write(frame)


    def stop(self):
        self.video_writer.release()  