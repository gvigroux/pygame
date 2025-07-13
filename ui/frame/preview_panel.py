import tkinter as tk
import ttkbootstrap as ttk
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

    # def _show_pil_image(self, image):
    #     photo = ImageTk.PhotoImage(image)
    #     label = ttk.Label(self.preview_area, image=photo)
    #     label.image = photo  # garder une référence
    #     label.pack(padx=10, pady=10)

    def _show_pil_image(self, image):
        # Forcer une mise à jour pour connaître la taille réelle du conteneur
        self.update_idletasks()

        # On prend la taille réelle affichable de la frame de scroll
        container_width = self.scroll_frame.winfo_width()
        container_height = self.scroll_frame.winfo_height()

        if container_width <= 1 or container_height <= 1:
            container_width, container_height = 800, 600  # fallback

        # Redimensionner proprement
        img_copy = image.copy()
        img_copy.thumbnail((container_width - 20, container_height - 20), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(img_copy)

        # Créer une frame fixe pour éviter que le label agrandisse la scroll zone
        frame = ttk.Frame(self.preview_area, width=container_width, height=container_height)
        frame.pack_propagate(False)  # important pour que le label reste borné
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        label = ttk.Label(frame, image=photo, anchor="center")
        label.image = photo
        label.pack(expand=True)




    def _show_tk_image(self, photo):
        label = ttk.Label(self.preview_area, image=photo)
        label.image = photo
        label.pack(padx=10, pady=10)

    def _show_pygame_surface(self, surface):
        """Affiche une surface Pygame dans le panneau de prévisualisation avec redimensionnement auto."""
        # Convertir la surface Pygame en image PIL
        raw_data = pygame.image.tostring(surface, "RGBA")
        size = surface.get_size()
        image = Image.frombytes("RGBA", size, raw_data)

        # Auto-scale : redimensionner si l'image dépasse les limites
        max_width, max_height = 800, 600
        if image.width > max_width or image.height > max_height:
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        self._show_pil_image(image)


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
