import queue
import threading

import cairo
import cv2
import numpy as np  

from background.base import BaseBackground


class Video(BaseBackground):
    def __init__(self, parameters={}):
        super().__init__()
        self.parameters = parameters
        self.videos = list(parameters.get("list", []))
        self.loop = False
        self.reverse = False
        self.cap = None
        self.frame_interval = 1.0 / 25
        self.last_frame_surface = None
        self.last_update_time = 0
        self.last_frame = None
        self.target_size = None

        self.frames = []
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

        self.load_video()


    def show_freeze_frame(self, frame, duration):
        self.freeze_surface = self.numpy_to_cairo_surface(frame)
        self.last_freeze_frame = frame.copy()
        self.freeze_frame_duration = duration
        self.freeze_frame_start_time = None


    def load_video(self):
        if not self.videos:
            return False

        video = self.videos[0]
        path = video.get("path")
        self.reverse = video.get("reverse", False)
        self.loop = video.get("loop", False)
        freeze_frame = video.get("freeze_frame", None)
        freeze_duration = video.get("freeze_duration", 0)

        if self.loop == False and self.videos:
            self.videos.pop(0)

        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            print(f"[Video] Failed to open video: {path}")
            return False

        fps = video.get("fps", self.cap.get(cv2.CAP_PROP_FPS))
        self.frame_interval = 1.0 / (fps if fps > 0 else 25)

        success, frame = self.cap.read()
        if not success:
            print("[Video] Failed to read initial frame")
            self.cap.release()
            self.cap = None
            return False

        h, w = frame.shape[:2]
        self.target_size = (w, h)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        if self.handle_freeze_frame(self.cap, freeze_frame, freeze_duration):
            self.cap = None
            self.last_frame_surface = self.numpy_to_cairo_surface(self.last_freeze_frame)
            self.force_next_frame = True
            self.queue_next_video()
            return True

        if self.reverse:
            read_frames = []
            while True:
                success, frame = self.cap.read()
                if not success:
                    break
                if self.target_size:
                    frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                read_frames.append(frame)
            self.cap.release()
            self.cap = None
            with self.lock:
                self.frames = read_frames[::-1]
                self.current_frame_index = 0

        self.queue_next_video()

        return True


    def handle_freeze_frame(self, cap, freeze_frame, freeze_duration):
        if freeze_frame is None or cap is None:
            return False

        cap.set(cv2.CAP_PROP_POS_FRAMES, freeze_frame)
        success, frame = cap.read()
        if success:
            if self.target_size:
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

        target_size = self.target_size
        if reverse:
            frames = []
            while True:
                success, frame = cap.read()
                if not success:
                    break
                if target_size:
                    frame = cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                frames.append(frame)
            cap.release()
            return {
                "frames": frames[::-1],
                "reverse": True,
                "loop": loop,
                "frame_interval": 1.0 / (cap.get(cv2.CAP_PROP_FPS) or 25),
                "preloaded": True,
                "freeze_frame": None,
                "freeze_duration": 0
            }
        else:
            return {
                "video": video_dict,
                "cap": cap,
                "reverse": False,
                "loop": loop,
                "preloaded": True,
                "freeze_frame": freeze_frame,
                "freeze_duration": freeze_duration
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
            self.frames = []
            self.current_frame_index = 0
            self.last_frame = None
            self.reverse = False
            self.loop = False

            self.freeze_surface = None
            self.freeze_frame_duration = 0
            self.freeze_frame_start_time = None

            if "frames" in video_data:
                self.reverse = video_data.get("reverse", False)
                self.loop = video_data.get("loop", False)
                self.frame_interval = video_data.get("frame_interval", self.frame_interval)
                self.cap = None
                self.frames = video_data["frames"]

            elif "cap" in video_data:
                if self.cap:
                    self.cap.release()
                self.cap = video_data["cap"]
                self.reverse = False
                self.loop = video_data.get("loop", False)
                fps = video_data.get("video", {}).get("fps", self.cap.get(cv2.CAP_PROP_FPS))
                self.frame_interval = 1.0 / (fps if fps > 0 else 25)
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

                freeze_frame = video_data.get("freeze_frame")
                freeze_duration = video_data.get("freeze_duration", 0)

                if self.handle_freeze_frame(self.cap, freeze_frame, freeze_duration):
                    self.last_frame_surface = self.numpy_to_cairo_surface(self.last_freeze_frame)
                    self.force_next_frame = True
                    self.cap = None

            if self.videos and not self.loop:
                self.videos.pop(0)

        self.queue_next_video()


    def switch_to_next_video(self):
        with self.lock:
            if self.cap:
                self.cap.release()
            self.cap = None
            self.frames = []
            self.current_frame_index = 0

            try:
                video_data = self.video_queue.get(timeout=10)
                self.preload_thread = None
                self.apply_preloaded_video(video_data)
                self.force_next_frame = True
            except queue.Empty:
                self.preload_thread = None
                if not self.load_video():
                    print("[Video] No more videos.")
                    return False
        return True


    def read_next_frame(self):
        with self.lock:
            if self.reverse:
                if not self.frames or self.current_frame_index >= len(self.frames):
                    if not self.switch_to_next_video():
                        return None
                    return None
                frame = self.frames[self.current_frame_index]
                self.current_frame_index += 1
                self.last_frame = frame
                return frame

            if not self.cap:
                return None

            success, frame = self.cap.read()
            if not success:
                if not self.switch_to_next_video():
                    return None
                return None

            if self.target_size:
                frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
            self.last_frame = frame
            return frame


    def numpy_to_cairo_surface(self, bgra):
        h, w = bgra.shape[:2]
        data = np.ascontiguousarray(bgra)
        surface = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)
        return surface


    def _draw(self, ctx, current_time, width, height):
        if self.freeze_surface:
            if self.freeze_frame_start_time is None:
                self.freeze_frame_start_time = current_time
            elapsed = current_time - self.freeze_frame_start_time
            if elapsed < self.freeze_frame_duration:
                ctx.save()
                ctx.set_source_surface(self.freeze_surface, 0, 0)
                try:
                    ctx.paint()
                except Exception as e:
                    print(f"[Video] ctx.paint exception (freeze): {e}")
                ctx.restore()
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

        if self.cap is None and not self.reverse and self.last_frame_surface is None:
            return

        if self.force_next_frame or current_time - self.last_update_time >= self.frame_interval:
            frame = self.read_next_frame()
            if frame is not None:
                self.last_frame_surface = self.numpy_to_cairo_surface(frame)
                self.last_update_time = current_time
                self.force_next_frame = False

        if self.last_frame_surface:
            ctx.save()
            ctx.set_source_surface(self.last_frame_surface, 0, 0)
            try:
                ctx.paint()
            except Exception as e:
                print(f"[Video] ctx.paint exception: {e}")
            ctx.restore()
