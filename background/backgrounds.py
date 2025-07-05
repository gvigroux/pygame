# backgrounds.py
import colorsys
import math
import random
import threading

import queue

import cairo
import cv2
import numpy as np

from background.base import BaseBackground
from background.video import Video

def hsv_to_rgb(h, s, v):
    import colorsys
    return colorsys.hsv_to_rgb(h, s, v)

class SolidColorBackground(BaseBackground):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.ready = True 
        
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
    def __init__(self, pygame, width, height, parameters={}):
        super().__init__(pygame, width, height)
        self.width = width
        self.height = height

        self.num_rings = 30
        self.max_radius = math.hypot(width, height)
        self.spacing = self.max_radius / self.num_rings

        self.base_radii = [i * self.spacing for i in range(self.num_rings)]
        self.alpha_table = [max(0.05, 0.15 - i * 0.003) for i in range(self.num_rings)]

    def _draw(self, ctx, time, width, height):
        ctx.set_source_rgb(0, 0, 0)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        cx, cy = width / 2, height / 2

        ctx.set_line_width(3)  # Une seule fois

        for i, base_radius in enumerate(self.base_radii):
            radius = base_radius + math.sin(time * 2 + i * 0.5) * 20

            hue = (time * 0.2 + i * 0.05) % 1.0
            r, g, b = hsv_to_rgb(hue, 1.0, 1.0)

            alpha = self.alpha_table[i]
            ctx.set_source_rgba(r, g, b, alpha)

            ctx.arc(cx, cy, radius, 0, 2 * math.pi)
            ctx.stroke()



class StarfieldBackground(BaseBackground):
    def __init__(self, width, height, num_stars=200):
        super().__init__(width, height)
        self.width = width
        self.height = height
        self.num_stars = num_stars

        self.stars = []
        for _ in range(num_stars):
            star = {
                'x': random.uniform(0, width),
                'y': random.uniform(0, height),
                'size': random.uniform(0.5, 2.5),
                'speed': random.uniform(10, 60),  # pixels per second
                'twinkle': random.uniform(0, 2 * math.pi)
            }
            self.stars.append(star)

    def _draw(self, ctx, time, width, height):
        # Fond noir profond
        ctx.set_source_rgb(0, 0, 0)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        for star in self.stars:
            # Mouvement vertical
            star['y'] += star['speed'] * (1 / 60)  # Assumes ~60fps

            # Si sortie d'écran -> repositionne en haut
            if star['y'] > height:
                star['x'] = random.uniform(0, width)
                star['y'] = 0
                star['size'] = random.uniform(0.5, 2.5)
                star['speed'] = random.uniform(10, 60)
                star['twinkle'] = random.uniform(0, 2 * math.pi)

            # Scintillement : alpha varie légèrement
            alpha = 0.5 + 0.5 * math.sin(time * 2 + star['twinkle'])
            alpha = max(0, min(1, alpha))  # clamp

            ctx.set_source_rgba(1, 1, 1, alpha)
            ctx.arc(star['x'], star['y'], star['size'], 0, 2 * math.pi)
            ctx.fill()



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
    "startfield": StarfieldBackground,
}


class BackgroundFactory:
    @staticmethod
    def create(pygame, style, width, height, p1 = None):
        cls = BACKGROUND_CLASSES.get(style, SolidColorBackground)
        if( p1 == None):
            return cls(pygame, width, height)
        return cls(pygame, width, height, p1)
