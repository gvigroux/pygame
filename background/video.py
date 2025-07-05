import queue
import threading

import cairo
import cv2
import numpy as np  

from background.base import BaseBackground
from element.sound import eSound


class Video(BaseBackground):
    def __init__(self, pygame, width, height, parameters={}):
        super().__init__(pygame, width, height)
        self.parameters = parameters
        self.videos = list(parameters.get("list", []))
        self.loop = False
        self.reverse = False
        self.cap = None
        self.frame_interval = 1.0 / 25
        self.last_frame_surface = None
        self.last_update_time = 0
        self.target_size = None
        self.surface_frames = []
        self.current_frame_index = 0

        self.preload_thread = None
        self.lock = threading.RLock()
        self.video_queue = queue.Queue()

        self.freeze_frame_duration = 0
        self.freeze_frame_start_time = None
        self.freeze_surface = None
        self.skip_after_freeze = False
        self.force_next_frame = False
        self.last_freeze_frame = None
        self.ready = False

        self.load_video()


    def show_freeze_frame(self, frame, duration):
        h, w = frame.shape[:2]
        data = np.ascontiguousarray(frame)
        self.freeze_surface = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)
        self.last_freeze_frame = frame.copy()
        self.freeze_frame_duration = duration
        self.freeze_frame_start_time = None


    def load_video(self):
        if not self.videos:
            print("[Video] No more videos.")
            self.ready = True
            return False

        video = self.videos.pop(0)
        path = video.get("path")
        self.reverse = video.get("reverse", False)
        self.loop = video.get("loop", False)
        freeze_frame = video.get("freeze_frame", None)
        freeze_duration = video.get("freeze_duration", 0)

        

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            print(f"[Video] Failed to open video: {path}")
            return False

        fps = video.get("fps", cap.get(cv2.CAP_PROP_FPS))
        self.frame_interval = 1.0 / (fps if fps > 0 else 25)

        success, frame = cap.read()
        if not success:
            print("[Video] Failed to read initial frame")
            cap.release()
            return False

        h, w = frame.shape[:2]
        self.target_size = (w, h)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        if self.handle_freeze_frame(cap, freeze_frame, freeze_duration):
            self.last_frame_surface = self.numpy_to_cairo_surface(self.last_freeze_frame)
            self.force_next_frame = True

            #TODO: sound can slow down the launch of the app when on first video (so desynchronized)
            self.play_sound(video)
            self.ready = True 

            self.queue_next_video()
            return True

        frames = []
        while True:
            success, frame = cap.read()
            if not success:
                break
            frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
            frames.append(frame)

        cap.release()

        if self.reverse:
            frames.reverse()

        with self.lock:
            self.surface_frames = [self.numpy_to_cairo_surface(f) for f in frames]
            self.current_frame_index = 0

        # ✅ Marque prêt maintenant
        self.ready = True

        self.play_sound(video)
        self.queue_next_video()
        return True

    def play_sound(self, video):
        sound    = eSound(self.pygame, **video.get("sound", {}))
        if( not sound.enabled() ):
            return
        sound.play()

    def handle_freeze_frame(self, cap, freeze_frame, freeze_duration):
        if freeze_frame is None or cap is None:
            return False

        cap.set(cv2.CAP_PROP_POS_FRAMES, freeze_frame)
        success, frame = cap.read()
        if success:
            frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
            self.show_freeze_frame(frame, freeze_duration)
            self.skip_after_freeze = True
        cap.release()
        return success


    def preload_video(self, video_dict):
        path = video_dict.get("path")
        reverse = video_dict.get("reverse", False)
        loop = video_dict.get("loop", False)
        freeze_frame = video_dict.get("freeze_frame")
        freeze_duration = video_dict.get("freeze_duration", 0)

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return None

        fps = video_dict.get("fps", cap.get(cv2.CAP_PROP_FPS))
        target_size = self.target_size
        frames = []
        while True:
            success, frame = cap.read()
            if not success:
                break
            frame = cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
            frames.append(frame)

        cap.release()
        if reverse:
            frames.reverse()

        surface_frames = [self.numpy_to_cairo_surface(f) for f in frames]

        return {
            "surface_frames": surface_frames,
            "reverse": reverse,
            "loop": loop,
            "frame_interval": 1.0 / (fps or 25),
            "preloaded": True,
            "freeze_frame": freeze_frame,
            "freeze_duration": freeze_duration,
            "sound": video_dict.get("sound", {})    
        }


    def queue_next_video(self):
        if self.videos and self.preload_thread is None:
            next_video_dict = self.videos[0]

            def task():
                next_video = self.preload_video(next_video_dict)
                if next_video:
                    self.video_queue.put(next_video)

            self.preload_thread = threading.Thread(target=task)
            self.preload_thread.start()


    def apply_preloaded_video(self, video_data):
        with self.lock:
            print("[Video] apply_preloaded_video")
            self.surface_frames = video_data.get("surface_frames", [])
            self.current_frame_index = 0
            self.reverse = video_data.get("reverse", False)
            self.loop = video_data.get("loop", False)
            self.frame_interval = video_data.get("frame_interval", self.frame_interval)
            
            self.play_sound(video_data)

            self.freeze_surface = None
            self.freeze_frame_duration = 0
            self.freeze_frame_start_time = None

            freeze_frame = video_data.get("freeze_frame")
            freeze_duration = video_data.get("freeze_duration", 0)

            if freeze_frame is not None and 0 <= freeze_frame < len(self.surface_frames):
                self.freeze_surface = self.surface_frames[freeze_frame]
                self.last_frame_surface = self.surface_frames[freeze_frame]
                self.freeze_frame_duration = freeze_duration
                self.freeze_frame_start_time = None
                self.skip_after_freeze = True
                self.force_next_frame = True

            if self.videos and not self.loop:
                self.videos.pop(0)

        self.queue_next_video()


    def switch_to_next_video(self):
        with self.lock:
            self.surface_frames = []
            self.current_frame_index = 0

            try:
                #video_data = self.video_queue.get(timeout=10)
                video_data = self.video_queue.get_nowait()
                self.preload_thread = None
                self.apply_preloaded_video(video_data)
                self.force_next_frame = True
            except queue.Empty:
                self.preload_thread = None
                if not self.load_video():
                    self.done = True
                    print("[Video] No more videos.")
                    return False
        return True


    def read_next_frame(self):
        with self.lock:
            if not self.surface_frames or self.current_frame_index >= len(self.surface_frames):
                if not self.switch_to_next_video():
                    return None
                return None

            surface = self.surface_frames[self.current_frame_index]
            self.current_frame_index += 1
            return surface


    def numpy_to_cairo_surface(self, bgra):
        h, w = bgra.shape[:2]
        data = np.ascontiguousarray(bgra)
        return cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)


    def _draw(self, ctx, current_time, width, height):
        if not self.ready:
            # Fallback = écran noir ou image fixe
            ctx.set_source_rgb(255, 255, 0)  # Noir
            ctx.paint()
            return
    
        if self.freeze_surface:
            if self.freeze_frame_start_time is None:
                self.freeze_frame_start_time = current_time
            elapsed = current_time - self.freeze_frame_start_time
            if elapsed < self.freeze_frame_duration:
                ctx.set_source_surface(self.freeze_surface, 0, 0)
                ctx.paint()
                return
            else:
                self.freeze_surface = None
                self.freeze_frame_start_time = None
                self.freeze_frame_duration = 0

                if self.skip_after_freeze:
                    self.skip_after_freeze = False
                    if not self.switch_to_next_video():
                        return
                    self.force_next_frame = True

        if self.force_next_frame or current_time - self.last_update_time >= self.frame_interval:
            surface = self.read_next_frame()
            if surface is not None:
                self.last_frame_surface = surface
                self.last_update_time = current_time
                self.force_next_frame = False

        if self.last_frame_surface:
            ctx.set_source_surface(self.last_frame_surface, 0, 0)
            ctx.paint()
