# backgrounds.py
import colorsys
import math
import random
import time as timestd

import cairo
import cv2
from moviepy import VideoFileClip
import numpy as np
from PIL import Image

def hsv_to_rgb(h, s, v):
    import colorsys
    return colorsys.hsv_to_rgb(h, s, v)

class BaseBackground:
    def __init__(self):
        self.log_draw_durations = []

    def draw(self, ctx, time, width, height):
        t0 = timestd.perf_counter()
        self._draw(ctx, time, width, height)
        self.log_draw_durations.append(timestd.perf_counter() - t0)

    def stat(self):            
        average = sum(self.log_draw_durations) / len(self.log_draw_durations)
        print(f"AVG {type(self)} : {average*1000:.2f} ms")    
        pass

class SolidColorBackground(BaseBackground):
    def _draw(self, ctx, time, width, height):
        ctx.set_source_rgb(0.2, 0.2, 0.2)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()


class VerticalGradientBackground(BaseBackground):
    def _draw(self, ctx, time, width, height):
        gradient = cairo.LinearGradient(0, 0, 0, height)
        gradient.add_color_stop_rgba(0.0, 0.2, 0.6, 1.0, 1)  # Bleu clair
        gradient.add_color_stop_rgba(1.0, 0.8, 0.9, 1.0, 1)  # Blanc bleuté

        ctx.set_source(gradient)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()


class AnimatedWaveBackground(BaseBackground):
    def _draw(self, ctx, time, width, height):
        ctx.set_source_rgb(0.0, 0.0, 0.1)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        ctx.set_line_width(2)
        ctx.set_source_rgb(0.1, 0.6, 1.0)

        for i in range(5):
            y_offset = height * (i + 1) / 6
            ctx.new_path()
            for x in range(width):
                y = y_offset + 20 * math.sin((x * 0.03) + time + i)
                if x == 0:
                    ctx.move_to(x, y)
                else:
                    ctx.line_to(x, y)
            ctx.stroke()


class GridBackground(BaseBackground):
    def _draw(self, ctx, time, width, height):
        ctx.set_source_rgb(1, 1, 1)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        ctx.set_line_width(1)
        ctx.set_source_rgba(0, 0, 0, 0.1)
        for x in range(0, width, 20):
            ctx.move_to(x, 0)
            ctx.line_to(x, height)
        for y in range(0, height, 20):
            ctx.move_to(0, y)
            ctx.line_to(width, y)
        ctx.stroke()


# ... Add 16 more classes with variations (dots, stars, noise, rings, etc.)
class StarsBackground(BaseBackground):
    def _draw(self, ctx, time, width, height):
        ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        ctx.set_source_rgb(1, 1, 1)
        for _ in range(100):
            x = random.randint(0, width)
            y = random.randint(0, height)
            r = random.uniform(0.5, 2.5)
            ctx.arc(x, y, r, 0, 2 * math.pi)
            ctx.fill()


class PulseBackground(BaseBackground):
    def _draw(self, ctx, time, width, height, count=5):
        cx, cy = width // 2, height // 2
        for i in range(count):
            radius = 100 + (i * 30) + 20 * math.sin(time * 0.8 + i)
            alpha = max(0.0, 0.05 - i * 0.008)
            ctx.set_source_rgba(0.3, 0.6, 1.0, alpha)
            ctx.arc(cx, cy, radius, 0, 2 * math.pi)
            ctx.fill()

# Pour faire court, imaginons qu'on ait 20 classes de fond, comme ci-dessus
# et on les liste ici :

class Wave2Background(BaseBackground):
    def _draw(self, ctx, time, width, height, layers=3):
        for i in range(layers):
            y_offset = height / layers * i
            wave_height = 20 + 5 * math.sin(time + i)
            wave_freq = 0.015 + i * 0.005
            ctx.set_source_rgba(0.1, 0.6, 0.9, 0.05 + i * 0.02)

            ctx.move_to(0, y_offset)
            for x in range(0, width + 10, 10):
                y = y_offset + math.sin(x * wave_freq + time + i) * wave_height
                ctx.line_to(x, y)
            ctx.line_to(width, height)
            ctx.line_to(0, height)
            ctx.close_path()
            ctx.fill()


class FloatingGridBackground(BaseBackground):
    def _draw(self, ctx, time, width, height, spacing=80):
        # Dessin des points animés
        for x in range(0, width + spacing, spacing):
            for y in range(0, height + spacing, spacing):
                dx = 10 * math.sin(time + x * 0.05)
                dy = 10 * math.cos(time + y * 0.05)
                cx = x + dx
                cy = y + dy
                ctx.set_source_rgba(1, 1, 1, 0.15)  # Plus visible
                ctx.arc(cx, cy, 5, 0, 2 * math.pi)  # Plus gros rayon
                ctx.fill()


class AnimatedBackground(BaseBackground):
    def _draw(self, ctx, time, width, height):
        # Dégradé linéaire qui se déplace horizontalement
        grad = cairo.LinearGradient((time * 0.05) % width, 0, (time * 0.05 + width) % width, height)
        grad.add_color_stop_rgb(0, 0.1, 0.1, 0.4)  # bleu foncé
        grad.add_color_stop_rgb(1, 0.4, 0.6, 1.0)  # bleu clair

        ctx.set_source(grad)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()
        

class ParticuleBackground(BaseBackground):
    def _draw(self, ctx, time, width, height, count=30):
        random.seed(0)  # Fixe les positions pour qu'elles soient stables d'une frame à l'autre

        for i in range(count):
            # Position pseudo-aléatoire, mais déterministe
            rand_x = random.uniform(0, width)
            rand_y = random.uniform(0, height)
            
            # Ajoute un mouvement subtil en sinus
            x = rand_x + 20 * math.sin(time * 0.5 + i)
            y = rand_y + 20 * math.cos(time * 0.3 + i)

            # Rayon et opacité
            r = 30 + 10 * math.sin(time * 0.7 + i)
            alpha = 0.05 + 0.05 * math.sin(time + i)

            # Couleur blanche translucide
            ctx.set_source_rgba(1, 1, 1, alpha)
            ctx.arc(x, y, r, 0, 2 * math.pi)
            ctx.fill()

class Wave3Background(BaseBackground):
    def _draw(self, ctx, time, width, height):
        ctx.set_source_rgb(0.9, 0.95, 1)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        ctx.set_source_rgba(0.7, 0.85, 1, 0.3)
        for i in range(10):
            y = height / 10 * i + 20 * math.sin(time + i)
            ctx.arc(width/2, y, width, 0, 2*math.pi)
            ctx.fill()

class RipplesBackground(BaseBackground):
    def _draw(self, ctx, time, width, height):
        ctx.set_source_rgb(1, 1, 1)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        cx, cy = width / 2, height / 2
        for r in range(0, int(width), 40):
            alpha = max(0, 1 - (r + (time * 50 % 40)) / width)
            ctx.set_source_rgba(0.2, 0.4, 1, alpha)
            ctx.arc(cx, cy, r + (time * 50 % 40), 0, 2 * math.pi)
            ctx.stroke()

class Stars2Background(BaseBackground):
    def _draw(self, ctx, time, width, height):
        ctx.set_source_rgb(0, 0, 0.1)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        random.seed(0)
        for i in range(50):
            x = random.randint(0, width)
            y = random.randint(0, height)
            brightness = 0.5 + 0.5 * math.sin(time * 5 + i)
            ctx.set_source_rgba(1, 1, 1, brightness)
            ctx.arc(x, y, 1.5, 0, 2 * math.pi)
            ctx.fill()

class RainbowBackground(BaseBackground):
    def _draw(self, ctx, time, width, height):
        grad = cairo.LinearGradient(0, 0, width, 0)
        for i in range(6):
            r, g, b = colorsys.hsv_to_rgb((i/6 + time/5) % 1, 1, 1)
            grad.add_color_stop_rgb(i / 6, r, g, b)
        ctx.set_source(grad)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

class BubblesBackground(BaseBackground):
    def _draw(self, ctx, time, width, height):
        ctx.set_source_rgb(0.95, 1, 1)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        random.seed(1)
        for i in range(30):
            x = random.randint(0, width)
            y = (random.randint(0, height) + int(100 * math.sin(time + i))) % height
            r = random.uniform(5, 15)
            ctx.set_source_rgba(0.6, 0.8, 1, 0.3)
            ctx.arc(x, y, r, 0, 2 * math.pi)
            ctx.fill()

class TrianglesBackground(BaseBackground):
    def _draw(self, ctx, time, width, height):
        ctx.set_source_rgb(1, 1, 1)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        size = 60
        for y in range(0, height + size, size):
            for x in range(0, width + size, size):
                offset = (time * 50) % size
                ctx.set_source_rgba(0.1, 0.3, 0.6, 0.5)
                ctx.move_to(x, y - offset)
                ctx.line_to(x + size / 2, y + size / 2 - offset)
                ctx.line_to(x - size / 2, y + size / 2 - offset)
                ctx.close_path()
                ctx.fill()

      
class ConcentricWaveBackground(BaseBackground):
    def _draw(self, ctx, time, width, height):
        # Fond noir
        ctx.set_source_rgb(0, 0, 0)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        # Centre de l'écran
        cx, cy = width / 2, height / 2

        max_radius = math.hypot(width, height)
        num_rings = 30
        spacing = max_radius / num_rings

        for i in range(num_rings):
            radius = i * spacing + (math.sin(time * 2 + i * 0.5) * 20)

            # Couleur arc-en-ciel selon l'angle et le temps
            hue = (time * 0.2 + i * 0.05) % 1.0
            r, g, b = hsv_to_rgb(hue, 1.0, 1.0)

            alpha = max(0.05, 0.15 - i * 0.003)
            ctx.set_source_rgba(r, g, b, alpha)

            ctx.arc(cx, cy, radius, 0, 2 * math.pi)
            ctx.set_line_width(3)
            ctx.stroke()



# class Video2(BaseBackground):
#     def __init__(self, parameters = []):
#         super().__init__()
#         self.parameters = parameters
#         self.videos = list(parameters.get("list", []))
#         self.loop   = parameters.get("loop", False)
#         self.load_video()

#     def load_video(self):
#         if( len(self.videos) == 0 ):
#             self.videos = list(self.parameters.get("list", []))
#         path = self.videos.pop(0)
#         self.cap = cv2.VideoCapture(path)

#         # Lecture de FPS réel depuis la vidéo (fallback à 25 si échec)
#         fps = self.cap.get(cv2.CAP_PROP_FPS)
#         self.frame_interval = 1.0 / (fps if fps > 0 else 25)

#         self.last_frame_surface = None
#         self.last_update_time = 0

#     def read_next_frame(self, width, height):
#         success, frame = self.cap.read()
#         if not success:
#             if( self.load_video() == False ):
#                 # Remettre sur la dernière frame
#                 return self.last_frame
#             return self.read_next_frame(width, height)

#         # Convertir BGR (OpenCV) → RGBA
#         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
#         #frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
#         self.last_frame = frame
#         return frame

#     def numpy_to_cairo_surface(self, rgba):
#         rgba = np.array(rgba)
#         bgra = rgba[..., [0, 1, 2, 3]]  # B, G, R, A
#         data = np.ascontiguousarray(bgra)
#         h, w = rgba.shape[:2]
#         return cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)

#     def _draw(self, ctx, current_time, width, height):
#         if current_time - self.last_update_time >= self.frame_interval:
#             frame = self.read_next_frame(width, height)
#             if frame is not None:
#                 self.last_frame_surface = self.numpy_to_cairo_surface(frame)
#                 self.last_update_time = current_time

#         if self.last_frame_surface:
#             ctx.save()
#             ctx.set_source_surface(self.last_frame_surface, 0, 0)
#             ctx.paint()
#             ctx.restore()
        
    

""" 
class Video(BaseBackground):
    def __init__(self, parameters={}):
        super().__init__()
        self.parameters = parameters
        self.videos = list(parameters.get("list", []))
        self.loop = parameters.get("loop", False)
        self.cap = None
        self.frame_interval = 1.0 / 25  # fallback
        self.last_frame_surface = None
        self.last_update_time = 0
        self.last_frame = None
        self.target_size = None

        self.load_video()

    def load_video(self):
        if not self.videos:
            self.videos = list(self.parameters.get("list", []))
        if not self.videos:
            self.cap = None
            return False

        video = self.videos.pop(0)
        self.cap = cv2.VideoCapture(video.get("path"))

        if not self.cap.isOpened():
            print(f"[Video] Failed to open video: {video.get("path")}")
            return False

        fps = video.get("fps", self.cap.get(cv2.CAP_PROP_FPS))
        self.frame_interval = 1.0 / (fps if fps > 0 else 25)

        # Lecture d'une première frame pour fixer la taille
        success, frame = self.cap.read()
        if success:
            h, w = frame.shape[:2]
            self.target_size = (w, h)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # retour au début
        else:
            print("[Video] Failed to read initial frame")
            self.cap = None
            return False

        return True

    def read_next_frame(self):
        if not self.cap:
            return None

        success, frame = self.cap.read()
        if not success:
            if not self.load_video():
                return self.last_frame  # dernier frame statique
            return self.read_next_frame()

        # Resize une seule fois si nécessaire
        if self.target_size:
            frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)

        # Convertir BGR → BGRA en une seule étape
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
        self.last_frame = frame
        return frame

    def numpy_to_cairo_surface(self, bgra):
        # Évite les copies si déjà OK
        if not isinstance(bgra, np.ndarray):
            bgra = np.array(bgra)
        h, w = bgra.shape[:2]
        data = np.ascontiguousarray(bgra)
        return cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)
    
  
    def _draw(self, ctx, current_time, width, height):
        if not self.cap:
            return

        if current_time - self.last_update_time >= self.frame_interval:
            frame = self.read_next_frame()
            if frame is not None:
                self.last_frame_surface = self.numpy_to_cairo_surface(frame)
                self.last_update_time = current_time

        if self.last_frame_surface:
            ctx.save()
            ctx.set_source_surface(self.last_frame_surface, 0, 0)
            ctx.paint()
            ctx.restore()
 """

class Video(BaseBackground):
    def __init__(self, parameters={}):
        super().__init__()
        self.parameters = parameters
        self.videos = list(parameters.get("list", []))
        self.loop = False  # défini plus tard selon chaque vidéo
        self.reverse = False
        self.cap = None
        self.frame_interval = 1.0 / 25
        self.last_frame_surface = None
        self.last_update_time = 0
        self.last_frame = None
        self.target_size = None

        self.frames = []  # cache mémoire si reverse
        self.current_frame_index = 0

        self.load_video()

    def load_video(self):
        if not self.videos:
            self.videos = list(self.parameters.get("list", []))
        if not self.videos:
            self.cap = None
            return False

        video = self.videos.pop(0)
        path = video.get("path")
        self.reverse = video.get("reverse", False)
        self.loop = video.get("loop", False)

        self.cap = cv2.VideoCapture(path)

        if not self.cap.isOpened():
            print(f"[Video] Failed to open video: {path}")
            return False

        fps = video.get("fps", self.cap.get(cv2.CAP_PROP_FPS))
        self.frame_interval = 1.0 / (fps if fps > 0 else 25)

        success, frame = self.cap.read()
        if not success:
            print("[Video] Failed to read initial frame")
            self.cap = None
            return False

        h, w = frame.shape[:2]
        self.target_size = (w, h)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        if self.reverse:
            self.frames = []
            while True:
                success, frame = self.cap.read()
                if not success:
                    break
                if self.target_size:
                    frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                self.frames.append(frame)
            self.cap.release()
            self.cap = None
            self.current_frame_index = len(self.frames) - 1

        return True

    def read_next_frame(self):
        if self.reverse:
            if not self.frames:
                return None

            frame = self.frames[self.current_frame_index]
            self.current_frame_index -= 1

            if self.current_frame_index < 0:
                if self.loop:
                    self.current_frame_index = len(self.frames) - 1
                else:
                    if not self.load_video():  # passe à la vidéo suivante
                        return self.last_frame
                    return self.read_next_frame()

            self.last_frame = frame
            return frame


        if not self.cap:
            return None

        success, frame = self.cap.read()
        if not success:
            if not self.load_video():
                return self.last_frame
            return self.read_next_frame()

        if self.target_size:
            frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
        self.last_frame = frame
        return frame

    def numpy_to_cairo_surface(self, bgra):
        if not isinstance(bgra, np.ndarray):
            bgra = np.array(bgra)
        h, w = bgra.shape[:2]
        data = np.ascontiguousarray(bgra)
        return cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)

    def _draw(self, ctx, current_time, width, height):
        if not self.cap and not self.reverse:
            return

        if current_time - self.last_update_time >= self.frame_interval:
            frame = self.read_next_frame()
            if frame is not None:
                self.last_frame_surface = self.numpy_to_cairo_surface(frame)
                self.last_update_time = current_time

        if self.last_frame_surface:
            ctx.save()
            ctx.set_source_surface(self.last_frame_surface, 0, 0)
            ctx.paint()
            ctx.restore()



BACKGROUND_CLASSES = {
    "solid": SolidColorBackground,
    "gradient": VerticalGradientBackground,
    "grid": GridBackground,
    "stars": StarsBackground,
    "pulse": PulseBackground,
    "wave": AnimatedWaveBackground,
    "wave2": Wave2Background,
    "floating_grid": FloatingGridBackground,
    "particule": ParticuleBackground,
    "animated": AnimatedBackground,
    "ripples": RipplesBackground,
    "stars2": Stars2Background,
    "wave3": Wave3Background,
    "rainbow": RainbowBackground,
    "bubbles": BubblesBackground,
    "triangles": TrianglesBackground,
    "concentric_wave": ConcentricWaveBackground,
    "video": Video,
}


class BackgroundFactory:
    @staticmethod
    def create(style, p1 = None):
        cls = BACKGROUND_CLASSES.get(style, SolidColorBackground)
        if( p1 == None):
            return cls()
        return cls(p1)
