
import os
import subprocess
import threading
import cv2
import numpy as np


class RecorderEmpty:
    def __init__(self, window_size):
        pass

    def write(self, pygame, screen, frame_count):
        pass


    def stop(self):
        pass