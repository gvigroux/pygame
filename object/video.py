import os
import threading
import queue
import cv2
import numpy as np
import cairo
from PIL import Image, ImageTk
from element.step import eStep
from object.object import Object
import pygame


class Video(Object):
    def __init__(self, data, window_size, count, id):
        #data = data.deepcopy()
        super().__init__(data, window_size, count, id)
        # Configuration originale
        self.path = self.config("path", "")
        if len(self.label) <= 0:
            self.label = os.path.basename(self.path)
        self.reverse = self.config("reverse", False)
        self.loop = self.config("loop", False)
        self.freeze_frame = self.config("freeze_frame", 0)
        self.freeze_duration = self.config("freeze_duration", 0)
        self.start_frame = self.config("start_frame", 0)
        self.end_frame = self.config("end_frame", -1)
        self.fps = self.config("fps", -1)
        self.thumb = None
        self._thumb_ready = threading.Event()


        # Système de chargement asynchrone
        self._load_thread = None
        self._should_stop = threading.Event()
        self._frames_ready = threading.Event()
        self.surface_frames = []
        self.target_size = None

        # Initialisation
        #print(f"[INIT VIDEO] label={self.label} path={self.path}")
        self._init_video_metadata()
        self._start_async_load()

    # def __getstate__(self):
    #     state = self.__dict__.copy()
    #     # Supprimer les attributs non-copiables
    #     for key in ['_load_thread', '_should_stop', '_frames_ready', '_thumb_ready', 'thumb']:
    #         if key in state:
    #             del state[key]
    #     return state

    # def __setstate__(self, state):
    #     self.__dict__.update(state)
    #     # Recrée les éléments exclus
    #     self._should_stop = threading.Event()
    #     self._frames_ready = threading.Event()
    #     self._thumb_ready = threading.Event()
    #     self._load_thread = None
    #     self.thumb = None

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
        self.target_size = (640, 480)  # fallback

        ret, frame = cap.read()
        if ret and frame is not None:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame_rgb.shape[:2]
            self.target_size = (w, h)

            # Création miniature PIL (30px hauteur)
            thumb_height = 30
            thumb_width = int(w * (thumb_height / h))
            resized = cv2.resize(frame_rgb, (thumb_width, thumb_height), interpolation=cv2.INTER_AREA)
            self.thumb_pil = Image.fromarray(resized)

        cap.release()


    # def _init_video_metadata(self):
    #     """Charge les métadonnées synchrones (rapide)"""
    #     cap = cv2.VideoCapture(self.path)
    #     if not cap.isOpened():
    #         print(f"[ERROR] Impossible d'ouvrir la vidéo: {self.path}")
    #         return

    #     # Configuration FPS et durée
    #     original_fps = cap.get(cv2.CAP_PROP_FPS)
    #     self.fps = self.fps if self.fps > 0 else original_fps
        
    #     frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    #     if self.end_frame > 0:
    #         frame_count = min(frame_count, self.end_frame) - self.start_frame
        
    #     # Définition de la durée
    #     if self.freeze_duration > 0:
    #         self.step.duration = self.freeze_duration
    #     elif self.step.duration == -1:
    #         self.step.duration = round(frame_count / self.fps,2)

    #     # Création de la miniature
    #     target_frame = self.freeze_frame if self.freeze_duration > 0 else self.start_frame
    #     cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    #     ret, frame = cap.read()
    #     if ret:
    #         frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #         h, w, _ = frame_rgb.shape
    #         height = 30
    #         scale = height / h
    #         resized = cv2.resize(frame_rgb, (int(w * scale), height), interpolation=cv2.INTER_AREA)
    #         self.thumb = ImageTk.PhotoImage(Image.fromarray(resized))
        
    #     # Définit la taille cible pour les frames
    #     self.target_size = (int(w), int(h)) if ret else (640, 480)
    #     cap.release()

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

                frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                surface = self.numpy_to_cairo_surface(frame)
                temp_frames.append(surface)
                current_frame += 1

            cap.release()

            if self.reverse:
                temp_frames.reverse()

            self.surface_frames = temp_frames

            # Générer une miniature depuis la première image chargée
            # if temp_frames:
            #     thumb_image = self.cairo_surface_to_pil(temp_frames[0])
            #     thumb_resized = thumb_image.resize((thumb_image.width * 30 // thumb_image.height, 30), Image.Resampling.LANCZOS)
            #     self.thumb = thumb_resized #ImageTk.PhotoImage(thumb_resized)
            #     self._thumb_ready.set()

            self._frames_ready.set()

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

    def _draw(self, ctx, current_time, width, height):
        """Dessin thread-safe"""
        surface = self.get_image(current_time)
        if surface:
            ctx.set_source_surface(surface, 0, 0)
            ctx.paint()

    def clone(self):
        """Clonage thread-safe"""
        new_video = Video(self.data, self.window_size, self.count, self.index)
        # Copie des frames déjà chargés si disponible
        if self.is_ready():
            new_video.surface_frames = self.surface_frames.copy()
            new_video._frames_ready.set()
        return new_video

    def __del__(self):
        """Nettoyage des ressources"""
        self._should_stop.set()
        if self._load_thread:
            self._load_thread.join()


    def schema(self):
        return {
            "label": ("str", "Label"),
            "enable": ("bool", "Enable"),
            "path": ("str", "path"),
            "reverse": ("bool", "reverse"),
            "loop": ("bool", "loop"),
            "fps": ("int", "FPS"),
            "freeze_frame": ("int", "Freeze frame"),
            "freeze_duration": ("float", "Freeze duration"),
            "start_frame": ("int", "Start frame"),
            "end_frame": ("int", "End frame"),
            "step": ("step", "Step"),
            "on_spawn": ("event", "On Spawn"),
            "on_destroy": ("event", "On Destroy"),
            "on_collision": ("event", "On Collision"),
        }


