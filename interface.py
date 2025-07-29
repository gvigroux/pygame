import shutil
import sys
import threading
import time
from tkinter import filedialog, messagebox
import cairo
import cv2
import numpy as np
import pygame
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import os
import tkinter as tk
from PIL import Image, ImageTk
from concurrent.futures import ThreadPoolExecutor

from game import Game
from object.object import Object
from object.object_factory import ObjectFactory
from object.video import Video
from ui.config import load_config, save_config
from ui.frame.clip_library import ClipLibrary
from ui.frame.custom_menu import CustomMenu
from ui.frame.preview_panel import PreviewPanel
from ui.frame.property_panel import PropertyPanel
from ui.helper import center_window, lighten_color
from ui.log import log_message
from ui.tools.downloader import DownloaderWindow
from ui.tools.disk_library import DiskLibraryWindow
from ui.tools.import_video import ImportVideoTool
from ui.tools.xdownloader import XDownloader
from ui.frame.scrollable_frame import ScrollableFrame
from ui.frame.timeline import Timeline
from ui.frame.toolbar import Toolbar
from ui.frame.type_chooser import TypeChooser

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"


state = {
    'log': None,
    "config": {
        "downloader": {
            "url": "",
            "split": "",
        }
    }
}
        



######################################
game = Game(pygame)


######################################
# Callbacks

def handle_time_click(seconds):

    current_time = 0

    for object in game.objects:
        object.reset(time.time()-seconds, 0)

    # Cairo surface et contexte réutilisables
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, *game.window_size)
    ctx     = cairo.Context(surface)
    screen  = pygame.display.set_mode((game.window_size[0], game.window_size[1]), pygame.DOUBLEBUF | pygame.SRCALPHA)
        
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.paint()
    ctx.restore()

    # 2. Dessin du background_image si présent
    background_image = timeline.get_background_image(seconds)
    if background_image:
        ctx.save()
        ctx.set_source_surface(background_image, 0, 0)
        ctx.paint()
        ctx.restore()
      
    dt = (seconds * 0.016 * 60) # - object.step.delay
    game.update(dt, 0, None, 0)

    for object in game.objects:
        if( isinstance(object, Video) ):
            if( not object.is_ready() ):
                original = library_panel.get_video(object.path)
                object.surface_frames = original.surface_frames
                if( len(object.surface_frames) > 0 ):
                    object._frames_ready.set() 

    game.background = None

    
    game.draw(screen, ctx, current_time)
    #game.draw_on_context(ctx, current_time)

    # Cairo → Pygame Surface
    raw_buf = surface.get_data()
    img = pygame.image.frombuffer(raw_buf, game.window_size, "BGRA").convert_alpha()
    
    # Dessine les objets sur la surface pygame (si nécessaire)
    #screen = pygame.Surface(game.window_size, pygame.SRCALPHA)
    screen.blit(img, (0, 0))

    #for obj in game.objects:
    #    obj.draw_surface(temp_surface)

    preview_panel.show_preview(screen)
    
######################################

def handle_video_drop(video, x, y):
    timeline.drop_clip(video, at_position=(x, y))


######################################

def on_video_selected(path):
    data = {
        "type": "video",
        "path": path
    }    
    object = ObjectFactory.create(data, game.window_size, 1, 0) 
    library_panel.add_clip(object)


############################################

def get_subclasses(cls):
    subclasses = set()
    work = [cls]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)
    return subclasses

######################################

def open_type_chooser():
    def handle_choice(choice):
        print("Vous avez choisi :", choice)
        
        track_index = timeline.add_track_top()
        data = json.loads('''
        {{
            "type": "{choice}",
            "label": "New {choice}", 
            "step" : {{"duration": 2}}
        }}
        '''.format(choice=choice))
        object = game.add_object_factory(data)
        timeline.add_clip(object, track=track_index, start=object.step.delay, duration=object.step.duration)

    subclasses = get_subclasses(Object)
    type_list = sorted([cls.__name__ for cls in subclasses])
    TypeChooser(app, type_list, handle_choice)

######################################

def handle_video_click(object):
    preview_panel.show_preview(object)

######################################
          
def handle_video_update(object, seconds):
    original = library_panel.get_video(object.path)
    object.surface_frames = original.surface_frames
    object._frames_ready.set()
    return object.get_image(seconds)


######################################


app = ttk.Window(themename="superhero")
app.title("TikTok Maker")
center_window(app, 1080, 720)
app.resizable(True, True)


style = ttk.Style("superhero")


style.configure("Titlebar.TFrame", background="#0a283b")
style.configure("Titlebar.TLabel", background="#0a283b", foreground="white", font=("Rototo", 10, "bold"))
#style.configure("Titlebar.TFrame", background=style.colors.primary)

# Style pour bloc activé
style.configure("Titlebar.Enabled.TFrame", background="#0a283b")
style.configure("Titlebar.Enabled.TLabel", background="#0a283b", foreground="white")

# Style pour bloc désactivé
style.configure("Titlebar.Disabled.TFrame", background="#A55C21")
style.configure("Titlebar.Disabled.TLabel", background="#A55C21", foreground="#dddddd")

style.configure("Titlebar.Error.TFrame", background="#ffcccc")
style.configure("Titlebar.Error.TLabel", background="#ffcccc", foreground="red")

bg = style.colors.get("secondary")
hover_bg = lighten_color(bg, 0.1)  # éclaircir légèrement pour le hover


style.configure("Tool.TButton",background=bg,relief="flat")
style.map("Tool.TButton", background=[("active", hover_bg)], relief=[("active", "flat")])


menu = CustomMenu(app, state)
menu.pack(fill="x")


# # Crée la barre de menu principale
# menubar = tk.Menu(app, bg="#0a283b", fg="white", activebackground="#1a3b5c", activeforeground="white", borderwidth=0, relief="flat")

# # Menu "Fichier"
# file_menu = tk.Menu(menubar, tearoff=0, bg="#0a283b", fg="white", activebackground="#1a3b5c", activeforeground="white", borderwidth=0, relief="flat")

# file_menu.add_command(label="Open", command=lambda: load_scene_dialog(state))
# file_menu.add_command(label="Save", command=lambda: save_scene(state))
# file_menu.add_command(label="Save As...", command=lambda: save_as_scene_dialog(state))
# file_menu.add_separator()
# file_menu.add_command(label="Exit", command=app.quit)

# menubar.add_cascade(label="File", menu=file_menu)

# # Assigne la barre de menu à la fenêtre
# app.config(menu=menubar)


 # Frame principale qui contient tout
main_frame = ttk.Frame(app)
main_frame.pack(fill="both", expand=True)

# Définir une grille à 3 lignes :
main_frame.rowconfigure(0, weight=0)  # Toolbar / séparateur
main_frame.rowconfigure(1, weight=1)  # Le centre : frame_game + timeline
main_frame.rowconfigure(2, weight=0)  # Log en bas
main_frame.columnconfigure(0, weight=1)



# Séparateur en dessous
separator = ttk.Separator(main_frame, orient="horizontal")
separator.grid(row=0, column=0, sticky="ew", pady=(40,0)) 

#################################################

center_frame = ttk.Frame(main_frame)
center_frame.grid(row=1, column=0, sticky="nsew")
center_frame.rowconfigure(0, weight=1)  # Frame_game
center_frame.rowconfigure(1, weight=0)  # timeline_toolbar
center_frame.rowconfigure(2, weight=0)  # Timeline
center_frame.columnconfigure(0, weight=1)

#paned = ttk.PanedWindow(center_frame, orient="horizontal")
#paned.grid(row=0, column=0, sticky="nsew")

vertical_paned = ttk.PanedWindow(center_frame, orient="vertical")
vertical_paned.grid(row=0, column=0, sticky="nsew")

# Horizontal paned pour les 3 colonnes
paned = ttk.PanedWindow(vertical_paned, orient="horizontal")


# Créer les 3 zones verticales

def on_library_clip_click(object):
    timeline.remove_focus()
    preview_panel.show_preview(object)
    property_panel.show_object(object)

def on_timeline_clip_click(object):
    library_panel.remove_focus()
    property_panel.show_object(object)


preview_panel = PreviewPanel(paned)
library_panel = ClipLibrary(paned, on_drop_callback=handle_video_drop, on_click=on_library_clip_click) 
property_panel = PropertyPanel(state, paned, update_callback=lambda: timeline.redraw())

paned.add(library_panel, weight=1)
paned.add(preview_panel, weight=1)
paned.add(property_panel, weight=1)

############################################

# Frame contenant timeline_toolbar + timeline
timeline_zone = ttk.Frame(vertical_paned)
timeline_zone.columnconfigure(0, weight=1)
timeline_zone.rowconfigure(0, weight=0)  # Toolbar (fixe)
timeline_zone.rowconfigure(1, weight=1)  # Timeline (extensible si nécessaire)


timeline = Timeline(timeline_zone, num_tracks=0, length=120,
                    on_clip_click=on_timeline_clip_click,
                    on_clip_add=game.add_object,
                    on_clip_removed=game.remove_object,
                    on_clip_update=game.reorder_objects,
                    on_time_click=handle_time_click, on_video_update=handle_video_update)   

timeline_toolbar = Toolbar(timeline_zone)
timeline_toolbar.add_icon("ui/icons/icons8-ajouter-24.png", timeline.add_track_top)
timeline_toolbar.add_icon("ui/icons/icons8-ajouter-24.png", open_type_chooser)


#num_tracks = len(game.objects)
timeline.grid(row=1, column=0, sticky="nsew")


vertical_paned.add(paned, weight=3)  # haut
vertical_paned.add(timeline_zone, weight=1)  # bas


#################################################

def reset():
    timeline.reset()
    library_panel.reset()

def test():
    game.run()
    game.deactivate_window()

    
toolbar = Toolbar(main_frame)
toolbar.add_text("TOOLS")

toolbar.add_icon("ui/icons/icons8-importer-24.png", lambda: ImportVideoTool(state), tooltip="Downloader & Splitter")
toolbar.add_icon("ui/icons/icons8-download-from-the-cloud-24.png", lambda: DownloaderWindow(state), tooltip="Downloader & Splitter")
toolbar.add_icon("ui/icons/icons8-video-gallery-24.png", lambda: DiskLibraryWindow(state, on_double_click=on_video_selected), tooltip="Media Library")
toolbar.add_icon("ui/icons/icons8-video-gallery-24.png", lambda: XDownloader(state), tooltip="X Downloader")
toolbar.add_icon("ui/icons/icons8-video-gallery-24.png", lambda: test(), tooltip="TEST")
toolbar.add_separator()



# Toolbar de la timeline
#timeline_toolbar = ttk.Frame(center_frame)
#timeline_toolbar.grid(row=2, column=0, sticky="ew", pady=(0, 10))

############################################
    

#num_tracks = len(game.objects)
#timeline = Timeline(center_frame, num_tracks=num_tracks, length=120, on_clip_click=property_panel.show_object, on_clip_removed=remove_clip, on_time_click=handle_time_click)
#timeline.grid(row=2, column=0, sticky="ew")



# Exemple de bouton :
#ttk.Button(timeline_toolbar, text="Ajouter clip", command=open_type_chooser).pack(side="left")
#ttk.Button(timeline_toolbar, text="Zoom +").pack(side="left")
#ttk.Button(timeline_toolbar, text="Zoom -").pack(side="left")


############################################

# Bas : zone de log partagée
log_frame = ttk.Frame(main_frame)
log_frame.grid(row=2, column=0, sticky="ew")
state['log'] = ttk.Text(log_frame, height=8, state='disabled', wrap='word')
state['log'].pack(fill='both', expand=True, padx=5, pady=0)


state['app']        = app
state['game']       = game
state['timeline']   = timeline
state['library']    = library_panel
state["horizontal_paned"]   = paned
state["vertical_paned"]     = vertical_paned

############################################

load_config(state)

# Sauvegarder à la fermeture
app.protocol("WM_DELETE_WINDOW", lambda: (save_config(state), app.destroy()))

# Lancer l'app
app.mainloop()


