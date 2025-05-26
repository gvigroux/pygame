
import os
import subprocess
import threading
import cv2
import numpy as np


class RecorderPyGame:
    def __init__(self, window_size):
        os.makedirs("captures", exist_ok=True)
        pass

    def write(self, pygame, screen, frame_count):
        #if frame_count % 2 == 0:
        #    return
        pygame.image.save(screen, f"captures/frame_{frame_count:04d}.png")

    def stop(self):
        # .\ffmpeg.exe -y -framerate 50 -i captures/frame_%04d.png -c:v libx264 -crf 20 -pix_fmt yuv420p output.mp4
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-framerate", "50",
            "-i", "captures/frame_%04d.png",
            "-c:v", "libx264",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "output.avi"
        ]
        self.video_process = subprocess.Popen(
                             ffmpeg_cmd,
                             stdin=subprocess.PIPE,
                             creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        threading.Thread(target=self.wait_for_ffmpeg_ready, args=(self.video_process,), daemon=True).start()
        self.video_process.wait()

    def wait_for_ffmpeg_ready(process):
        while True:
            line = process.stderr.readline()
            if not line:
                break
            decoded = line.decode('utf-8').strip()
            print(decoded)  # Debug
            if "Press [q] to stop" in decoded or "frame=" in decoded:
                print("FFmpeg is ready.")
                break        