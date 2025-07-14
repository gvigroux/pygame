import tkinter as tk
import numpy as np
import ttkbootstrap as ttk
from object.video import Video
from ui.frame.scrollable_frame import ScrollableFrame
from PIL import Image, ImageTk
import vlc
import os
import pygame

class PreviewPanel(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)

        self.preview_area = self.scroll_frame.get_content_frame()

        self.instance = vlc.Instance()
        self.player = None
        self.video_widget = None
        self.current_preview = None
        self.preview_label = None  # référence persistante

    def clear(self):
        """Efface la prévisualisation et arrête la vidéo si besoin."""
        if self.player:
            self.player.stop()
            self.player.release()
            self.player = None

        if self.video_widget:
            self.video_widget.destroy()
            self.video_widget = None

        for widget in self.preview_area.winfo_children():
            widget.destroy()

    def show_preview(self, media):
        self.clear()

        if isinstance(media, str) and os.path.isfile(media):
            if media.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
                self._show_image(media)
            elif media.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
                self._show_video(media)

        elif( isinstance(media, Video) ):
            self._show_video(media.path)
            
        elif isinstance(media, Image.Image):
            self._show_pil_image(media)

        elif isinstance(media, tk.PhotoImage):
            self._show_tk_image(media)

        elif isinstance(media, pygame.Surface):
            self._show_pygame_surface(media)

        else:
            ttk.Label(
                self.preview_area,
                text="Format non supporté",
                font=("Segoe UI", 10, "italic")
            ).pack(padx=10, pady=10)

    def _show_image(self, path):
        image = Image.open(path)
        self._show_pil_image(image)


    def _show_pil_image(self, image):
        # Forcer une mise à jour pour connaître la taille réelle du conteneur
        self.update_idletasks()

        # On prend la taille réelle affichable de la frame de scroll
        container_width = self.scroll_frame.winfo_width()
        container_height = self.scroll_frame.winfo_height()

        if container_width <= 1 or container_height <= 1:
            container_width, container_height = 800, 600  # fallback

        # Calculer la taille cible avec une marge
        target_width = max(1, container_width - 20)
        target_height = max(1, container_height - 20)

        # Calculer la taille de destination sans modifier l’image originale
        img_w, img_h = image.size
        ratio = min(target_width / img_w, target_height / img_h)
        new_size = (int(img_w * ratio), int(img_h * ratio))

        # Redimensionner plus rapidement avec BILINEAR (≈ qualité LANCZOS, mais plus rapide)
        resized = image.resize(new_size, Image.Resampling.BILINEAR)

        photo = ImageTk.PhotoImage(resized)
        
        # Réutiliser le label s’il existe
        if self.preview_label is None or not self.preview_label.winfo_exists():
            self.preview_label = ttk.Label(self.preview_area, anchor="center")
            self.preview_label.pack(fill="both", expand=True, padx=10, pady=10)

        # Mettre à jour l’image
        self.preview_label.configure(image=photo)
        self.preview_label.image = photo  # garder la référence




    def _show_tk_image(self, photo):
        label = ttk.Label(self.preview_area, image=photo)
        label.image = photo
        label.pack(padx=10, pady=10)


    def _show_pygame_surface(self, surface):
        """Affiche une surface Pygame dans le panneau de prévisualisation avec redimensionnement auto."""
        # Convertir la surface Pygame en image PIL
        #raw_data = pygame.image.tostring(surface, "RGBA")
        #size = surface.get_size()
        #image = Image.frombytes("RGBA", size, raw_data)

        image = self._surface_to_image_fast(surface)

        # Auto-scale : redimensionner si l'image dépasse les limites
        #max_width, max_height = 800, 600
        #if image.width > max_width or image.height > max_height:
        #    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        self._show_pil_image(image)

    def _surface_to_image_fast(self, surface: pygame.Surface) -> Image.Image:
        # Malgré le warning, c'est 3× plus rapide que surfarray, car c’est une méthode C optimisée
        raw = pygame.image.tostring(surface, "RGBA", False)
        w, h = surface.get_size()
        return Image.frombytes("RGBA", (w, h), raw)

    def _surface_to_image(self, surface: pygame.Surface) -> Image.Image:
        """
        Convertit une surface Pygame en une image PIL.Image avec orientation correcte (RGBA).
        """
        # S'assurer que la surface a un canal alpha (RGBA)
        surface = surface.convert_alpha()

        # Extraire les pixels RGB et alpha
        rgb_array = pygame.surfarray.pixels3d(surface)
        alpha_array = pygame.surfarray.pixels_alpha(surface)

        # Fusionner les canaux
        rgba = np.dstack((rgb_array, alpha_array)) 
        rgba = np.transpose(rgba, (1, 0, 2)) 

        # Rendre contigu pour PIL (sinon crash possible avec fromarray)
        rgba = np.ascontiguousarray(rgba)

        # Créer l'image PIL
        return Image.fromarray(rgba, "RGBA")


    def _show_video(self, path):
        """Lit une vidéo avec VLC intégré dans un widget Tkinter."""
        self.video_widget = ttk.Frame(self.preview_area, width=400, height=300)
        self.video_widget.pack(padx=10, pady=10, fill="both", expand=True)

        self.video_widget.update_idletasks()
        window_id = self.video_widget.winfo_id()

        self.player = self.instance.media_player_new()
        media = self.instance.media_new(path)
        self.player.set_media(media)

        if os.name == "nt":  # Windows
            self.player.set_hwnd(window_id)
        elif os.name == "posix":
            self.player.set_xwindow(window_id)  # Linux
        else:
            print("OS non supporté pour l'intégration VLC")

        self.player.play()
