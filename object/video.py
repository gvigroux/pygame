import os
import threading
import queue
import time
import cv2
import numpy as np
import cairo
from PIL import Image, ImageTk
from element.position import ePosition
from element.size import eSize
from element.step import eStep
from object.object import Object
import pygame


class Video(Object):
    def __init__(self, data, window_size, count, id, on_thumb_ready= None, on_ready=None):
        super().__init__(data, window_size, count, id)
        # Configuration originale
        self.path = self.config("path", "")
        if len(self.label) <= 0:
            self.label = os.path.basename(self.path)
        self.reverse = self.config("reverse", False)
        self.loop = self.config("loop", False)
        self.play_sound = self.config("play_sound", False)
        self.freeze_frame = self.config("freeze_frame", 0)
        self.freeze_duration = self.config("freeze_duration", 0)
        self.start_frame = self.config("start_frame", 0)
        self.end_frame = self.config("end_frame", -1)
        self.total_frame = 0
        self.fps = self.config("fps", -1)
        self.thumb = None


        self.on_thumb_ready_callbacks = []
        self.on_ready_callbacks = []
        if( on_thumb_ready ):
            self.on_thumb_ready_callbacks.append(on_thumb_ready)
        if( on_ready ):
            self.on_ready_callbacks.append(on_ready)
        
        self.position   = ePosition(window_size, count, id, **self.config("position", { "x": 0, "y": 0 }))
        self.raw_size   = eSize(window_size, count, id, **self.config("size", {"width": "100%", "height": "100%"}))
        self.size       = eSize(window_size, count, id, **self.config("size", {"width": "100%", "height": "100%"}))

        # Système de chargement asynchrone
        self._load_thread = None
        self._should_stop = threading.Event()
        self._frames_ready = threading.Event()
        self.surface_frames = []
        
        self.thumb_pil  = None

        # Initialisation
        print(f"[INIT VIDEO] label={self.label} path={self.path}")
        self._metadata_thread = None
        # threading.Thread(
        #     target=self._init_video_metadata_threadsafe,
        #     daemon=True,
        #     name=f"VideoMetadataLoader-{os.path.basename(self.path)}"
        # )

    @classmethod
    def parameter_fields(cls):
        return {
            
            "label" :  {"name": "label", "type": "str", "default": ""},
            "path" :    {"name": "path", "type": "file", "default": ""},
            "reverse":     {"name": "reverse", "type": "bool", "default": False},
            
            "step": eStep.parameter_fields(),
        }
    
    def _prepare(self):
        self.total_frame = len(self.surface_frames)
        if( len(self.surface_frames) == 0 ):
            return
        if( self.surface_frames[0].size[0] != self.size.width  or self.surface_frames[0].size[1] != self.size.height):
            print(f"Recalculating Video size to: {self.size}")
            self.load()
        pass

    def load_metadata_async(self):
        self._metadata_thread = threading.Thread(
            target=self._init_video_metadata_threadsafe,
            daemon=True,
            name=f"VideoMetadataLoader-{os.path.basename(self.path)}"
        )
        self._metadata_thread.start()

    def load_metadata_sync(self):
        self._init_video_metadata_threadsafe()

    def load(self):
        """Démarre le chargement asynchrone si pas déjà fait."""
        if self._load_thread and self._load_thread.is_alive():
            return  # déjà en cours
        self._start_async_load()


    def _init_video_metadata_threadsafe(self):
        cap = cv2.VideoCapture(self.path)
        if not cap.isOpened():
            print(f"[ERROR] Impossible d'ouvrir la vidéo: {self.path}")
            return

        # FPS & dimensions
        original_fps = cap.get(cv2.CAP_PROP_FPS) or 25
        self.fps = self.fps if self.fps > 0 else original_fps

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.total_frame = total_frames
        usable_frames = total_frames
        if self.end_frame > 0:
            usable_frames = max(0, min(total_frames, self.end_frame) - self.start_frame)

        if self.freeze_duration > 0:
            self.step.duration = self.freeze_duration
        elif self.step.duration <= 0:
            self.step.duration = round(usable_frames / self.fps, 2)

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.raw_size.width = w
        self.raw_size.height = h
        self.size.width = w
        self.size.height = h

        self.thumb_pil = None
        if w > 0 and h > 0:
            target_frame_idx = self.freeze_frame if self.freeze_duration > 0 else self.start_frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_idx)
            ret, frame = cap.read()
            if ret and frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                thumb_height = 30
                thumb_width = min(int(30*9/16),int(w * (thumb_height / h)))
                self.thumb_pil = Image.fromarray(frame_rgb).resize((thumb_width, thumb_height), Image.LANCZOS)

        cap.release()

        for cb in self.on_thumb_ready_callbacks:
            cb()

    def get_description(self):
        return self.path

    def get_thumb(self):
        """Retourne la miniature (attend si nécessaire)"""
        if( self.thumb is None ) and ( self.thumb_pil is not None ):
            self.thumb = ImageTk.PhotoImage(self.thumb_pil)
        return self.thumb

    def _start_async_load(self):
        """Démarre le chargement en arrière-plan"""
        if self._load_thread and self._load_thread.is_alive():
            self._should_stop.set()
            self._load_thread.join()

        self._should_stop.clear()
        self._frames_ready.clear()
        self._load_thread = threading.Thread(
            target=self._async_load_task,
            daemon=True,
            name=f"VideoLoader-{os.path.basename(self.path)}"
        )
        self._load_thread.start()


    def _async_load_task(self):
        """Tâche asynchrone de chargement des frames (isolée par instance)"""
        try:
            cap = cv2.VideoCapture(self.path)
            if not cap.isOpened():
                print(f"[ERROR] Cannot open video: {self.path}")
                return

            if self.start_frame > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)

            temp_frames = []
            current_frame = self.start_frame
            while not self._should_stop.is_set():
                if self.end_frame > 0 and current_frame >= self.end_frame:
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                h, w = frame.shape[:2]
                target_w, target_h = self.size.get()

                if (w, h) != (target_w, target_h):
                    frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)
                                    
                # Convertir pour Pygame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                surface = pygame.image.frombuffer(frame_rgb.tobytes(), (target_w, target_h), 'RGB')

                temp_frames.append(surface)
                current_frame += 1

            cap.release()

            self.surface_frames = temp_frames
            self._frames_ready.set()
            
            for cb in self.on_ready_callbacks:
                cb(self)
            print(f"[VIDEO OK] label={self.label} path={self.path} frames={len(self.surface_frames)}")

        except Exception as e:
            print(f"[VIDEO LOAD ERROR] {self.path}: {str(e)}")

    def cairo_surface_to_pil(self, surface):
        """Convertit une surface Cairo (FORMAT_ARGB32) en Image PIL"""
        surface.flush()
        width = surface.get_width()
        height = surface.get_height()
        stride = surface.get_stride()
        data = surface.get_data()
        buf = np.frombuffer(data, np.uint8).reshape((height, stride // 4, 4))[:, :width]
        argb = buf[:, :, [1, 2, 3, 0]]  # ARGB32 → RGBA
        return Image.fromarray(argb, mode="RGBA")

    def rebuild_cairo_from_pil(self):
        """Reconstruit les surfaces Cairo à partir des images PIL (si besoin après clone)."""
        self.surface_frames = [
            self.pil_to_cairo(img) for img in self.surface_frames_pil
        ]
        self._frames_ready.set()

    def pil_to_cairo(self, pil_image):
        rgba = np.array(pil_image).astype(np.uint8)
        return self.numpy_to_cairo_surface(rgba)

    def is_ready(self):
        """Vérifie si le chargement est terminé"""
        return self._frames_ready.is_set()
        #return len(self.surface_frames) > 0

    def _clone(self, base):
        self.surface_frames = base.surface_frames.copy()
        self._frames_ready.set()

    def get_image(self, seconds):
        """Version thread-safe"""
        if not self.is_ready() or not self.surface_frames:
            return None

        if self.fps <= 0:
            return self.surface_frames[0]

        frame_index = int(seconds * self.fps)
        frame_count = len(self.surface_frames)
        if( self.end_frame >= 0 ):
            frame_count = min(frame_count, self.end_frame + 1)
        
        if self.loop:
            frame_index %= frame_count
        else:
            frame_index = max(0, min(frame_index + self.start_frame, frame_count - 1))

        if self.reverse:
            frame_index = max(0, frame_count - 1 - (frame_index + self.start_frame))
        
        return self.surface_frames[frame_index]

    def numpy_to_cairo_surface(self, bgra):
        """Conversion numpy array vers Cairo Surface (thread-safe)"""
        h, w = bgra.shape[:2]
        data = np.ascontiguousarray(bgra)
        return cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)

    def _update(self, dt, step, clock, blocked):
        self.current_frame = self.get_image(self.age)

    def _draw(self, ctx):
        """Dessin thread-safe"""
        #if( self.current_frame ):
        #    ctx.set_source_surface(self.current_frame, 0, 0)
        #    ctx.paint()
        pass

    def _draw_surface(self, screen):
        if self.current_frame:
            screen.blit(self.current_frame, (self.position.x, self.position.y))  


    def adjust_duration(self):
        """Ajuste la durée de la vidéo en fonction de la position du curseur."""

        if self.start_frame < 0:
            start = 0
        else:
            start = self.start_frame
        
        if self.end_frame >= 0 and self.end_frame >= start:
            frame_count = self.end_frame - start + 1
        else:
            frame_count = self.total_frame - start

        frame_count = max(frame_count, 0)  # éviter négatif

        duration = frame_count / self.fps
        self.step.duration = duration

        
    def _schema(self):
        return {
            "path": ("str", "path"),
            "reverse": ("bool", "reverse"),
            "loop": ("bool", "loop"),
            "play_sound": ("bool", "Play sound"),
            "fps": ("int", "FPS"),
            "freeze_frame": ("int", "Freeze frame"),
            "freeze_duration": ("float", "Freeze duration"),
            "total_frame": ("int", "Total frame", False),
            "start_frame": ("int", "Start frame"),
            "end_frame": ("int", "End frame"),           
            "raw_size": ("size", "Orginal Size", False),
            "size": ("size", "Size"),
            "position": ("position", "Position"),
        }


