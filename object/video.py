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
    def __init__(self, data, window_size, count, id):
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
        self.fps = self.config("fps", -1)
        self.thumb = None
        self.is_copy = False

        
        self.position   = ePosition(window_size, count, id, **self.config("position", { "x": 0, "y": 0 }))
        self.raw_size   = eSize(window_size, count, id, **self.config("size", {"width": "100%", "height": "100%"}))
        self.size       = eSize(window_size, count, id, **self.config("size", {"width": "100%", "height": "100%"}))

        # Système de chargement asynchrone
        self._load_thread = None
        self._should_stop = threading.Event()
        self._frames_ready = threading.Event()
        self.surface_frames = []
        
        self.target_size = None

        # Initialisation
        print(f"[INIT VIDEO] label={self.label} path={self.path}")
        self._init_video_metadata()
        self._start_async_load()

    def __getstate__(self):
        state = self.__dict__.copy()
        # Supprimer les attributs non-copiables
        for key in ['_load_thread', '_should_stop', '_frames_ready', 'thumb', 'surface_frames', 'current_frame']:
            if key in state:
                del state[key]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Recrée les éléments exclus
        self._should_stop = threading.Event()
        self._frames_ready = threading.Event()
        self._load_thread = None
        self.thumb = None
        self.surface_frames = []
        self.current_frame = None
        self.is_copy = True
        #self._start_async_load()

    def _init_video_metadata(self):
        """Charge les métadonnées de la vidéo (synchrone, rapide)"""
        cap = cv2.VideoCapture(self.path)
        if not cap.isOpened():
            print(f"[ERROR] Impossible d'ouvrir la vidéo: {self.path}")
            return

        # FPS
        original_fps = cap.get(cv2.CAP_PROP_FPS) or 25  # fallback utile
        self.fps = self.fps if self.fps > 0 else original_fps

        # Nombre de frames total
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        usable_frames = total_frames
        if self.end_frame > 0:
            usable_frames = max(0, min(total_frames, self.end_frame) - self.start_frame)

        # Définir la durée
        if self.freeze_duration > 0:
            self.step.duration = self.freeze_duration
        elif self.step.duration <= 0:
            self.step.duration = round(usable_frames / self.fps, 2)

        # Déterminer quelle frame utiliser pour la miniature
        target_frame_idx = self.freeze_frame if self.freeze_duration > 0 else self.start_frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_idx)

        self.thumb_pil = None
        #self.target_size = (640, 480)  # fallback
        #self.size.x = self.size.width

        ret, frame = cap.read()
        if ret and frame is not None:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame_rgb.shape[:2]
            #self.target_size = (w, h)
            self.raw_size.width = w
            self.raw_size.height = h
            self.size.width = w
            self.size.height = h

            # Création miniature PIL (30px hauteur)
            thumb_height = 30
            thumb_width = int(w * (thumb_height / h))
            resized = cv2.resize(frame_rgb, (thumb_width, thumb_height), interpolation=cv2.INTER_AREA)
            self.thumb_pil = Image.fromarray(resized)

        cap.release()


    def get_thumb(self):
        """Retourne la miniature (attend si nécessaire)"""
        if( self.thumb is None ):
            self.thumb = ImageTk.PhotoImage(self.thumb_pil)
        return  self.thumb

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
    
                #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                #surface = self.numpy_to_cairo_surface(frame)

                                
                # Convertir pour Pygame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                #surface = pygame.surfarray.make_surface(np.flipud(np.rot90(frame_rgb)))
                surface = pygame.image.frombuffer(frame_rgb.tobytes(), (target_w, target_h), 'RGB')
                #surface = surface.convert()

                temp_frames.append(surface)
                current_frame += 1

            cap.release()

            if self.reverse:
                temp_frames.reverse()

            self.surface_frames = temp_frames
            self._frames_ready.set()
            
            print(f"[VIDEO OK] label={self.label} path={self.path}")

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

    def get_image(self, seconds):
        """Version thread-safe"""
        if not self.is_ready() or not self.surface_frames:
            return None

        if self.fps <= 0:
            return self.surface_frames[0]

        frame_index = int(seconds * self.fps)
        
        if self.loop:
            frame_index %= len(self.surface_frames)
        else:
            frame_index = max(0, min(frame_index, len(self.surface_frames) - 1))

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
            screen.blit(self.current_frame, (0, 0))    

    def schema(self):
        return {
            "label": ("str", "Label"),
            "enable": ("bool", "Enable"),
            "path": ("str", "path"),
            "reverse": ("bool", "reverse"),
            "loop": ("bool", "loop"),
            "play_sound": ("bool", "Play sound"),
            "fps": ("int", "FPS"),
            "freeze_frame": ("int", "Freeze frame"),
            "freeze_duration": ("float", "Freeze duration"),
            "start_frame": ("int", "Start frame"),
            "end_frame": ("int", "End frame"),
            "step": ("step", "Step"),
            "raw_size": ("size", "Orginal Size"),
            "size": ("size", "Size"),
            "position": ("position", "Position"),
            "on_spawn": ("event", "On Spawn"),
            "on_destroy": ("event", "On Destroy"),
            "on_collision": ("event", "On Collision"),
        }


