import time
from tkinter import filedialog
import cairo
import cv2
import pygame
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import os
import tkinter as tk
from PIL import Image, ImageTk

from background.video import Video
from game import Game
from object.object import Object
from object.object_factory import ObjectFactory
from ui.frame.clip_library import ClipLibrary
from ui.frame.empty_panel import EmptyPanel
from ui.frame.library_panel import VideoLibraryPanel
from ui.frame.preview_panel import PreviewPanel
from ui.frame.property_panel import PropertyPanel
from ui.helper import center_window, lighten_color
from ui.log import log_message
from ui.tools.downloader import DownloaderWindow
from ui.tools.disk_library import DiskLibraryWindow
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


def save_scene(state, scene_filepath, game):

    # 1️⃣ Charger le JSON existant
    with open(scene_filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["objects"] = []
    for object in game.objects:
        data["objects"].append(object.data) 
        
    # 3️⃣ Réécrire le fichier avec la nouvelle config
    with open(scene_filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

        
def load_scene_dialog(state, game):
    file_path = filedialog.askopenfilename(
        title="Open scene",
        filetypes=[("Scene", "*.json")]
    )
    load_scene(state, game, file_path)



def load_scene(state, game, file_path):
 
    if len(file_path) <= 0:
        return
    
    timeline.reset()
    game.reset()
    
    game.load(file_path, avoid_debug=False)
  
    i = len(game.objects)-1
    for object in game.objects:
        timeline.add_track_top(False)
        timeline.add_clip( object, track=i, start=object.step.delay, duration=object.step.duration)
        library_panel.add_unique_clip(object)
        i-=1

    if( game.background is not None ):
        background = game.background
        if( isinstance(background, Video) ):
            i = 0
            last_end = 0
            for data in background.raw_videos:
                data["type"] = "Video"
                object = ObjectFactory.create(data, game.window_size, 1, 0)
                object.step.delay = last_end
                last_end = object.step.delay + object.step.duration
                timeline.add_clip(object, track="background", start=object.step.delay, duration=object.step.duration)

                #library_panel.add_video(object)
                library_panel.add_unique_clip(object)
                i+=1

    timeline._draw_tracks()




######################################


######################################
pygame.init()
game = Game(pygame)
start_time = time.time()
game.load(filename="config.json", avoid_debug=False)
execution_time = time.time() - start_time
print(f"Temps d'exécution : {execution_time:.4f} secondes")
######################################


######################################
# Callbacks


def remove_clip(object):
    game.remove_object(object)        

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

    game.background = None
    game.draw_on_context(ctx, current_time)


    
    # Cairo → Pygame Surface
    raw_buf = surface.get_data()
    img = pygame.image.frombuffer(raw_buf, game.window_size, "BGRA").convert_alpha()
    
    # Dessine les objets sur la surface pygame (si nécessaire)
    temp_surface = pygame.Surface(game.window_size, pygame.SRCALPHA)
    temp_surface.blit(img, (0, 0))

    for obj in game.objects:
        obj.draw_surface(temp_surface)
        
    raw_string = pygame.image.tostring(temp_surface, "RGBA")
    img = Image.frombytes("RGBA", temp_surface.get_size(), raw_string)
    preview_panel.show_preview(img)

def handle_video_drop(video, x, y):
    print(f"Vidéo lâchée à {x}, {y} : {video.path}")
    #timeline.add_background_video(video, at_position=(x, y))
    timeline.drop_clip(video, at_position=(x, y))



def on_video_selected(path):
    data = {
        "type": "video",
        "path": path
    }    
    object = ObjectFactory.create(data, game.window_size, 1, 0) 
    library_panel.add_video(object)


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
        object = game.add_object(data)
        timeline.add_clip(object, track=track_index, start=object.step.delay, duration=object.step.duration)

    subclasses = get_subclasses(Object)
    type_list = sorted([cls.__name__ for cls in subclasses])
    TypeChooser(app, type_list, handle_choice)



def handle_video_click(object):
    preview_panel.show_preview(object)

######################################



CONFIG_FILE = "ui.json"


def save_config(app, state):

    # 1️⃣ Charger le JSON existant
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["config"] = state["config"]

    is_maximized = app.state() == "zoomed"
    layout = {
        "pane_sizes": [paned.sashpos(0), paned.sashpos(1)],
        "vertical_sash": vertical_paned.sashpos(0),
        "window_size": (app.winfo_width(), app.winfo_height()),
        "maximized": is_maximized
    }
    data["layout"] = layout

        
    # 3️⃣ Réécrire le fichier avec la nouvelle config
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

        
  

def load_config(app, state):
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            state["config"] = data["config"]

            layout = data["layout"]

            if layout.get("maximized"):
                app.state("zoomed")
            
            #app.update_idletasks()
            if "pane_sizes" in layout:
                def apply_pane_sizes():
                    app.update_idletasks()
                    # ✅ Forcer une taille minimale
                    total_width = paned.winfo_width()
                    if total_width < 50:  # trop petit, pas encore affiché
                        app.after(100, apply_pane_sizes)
                        return
                    try:
                        paned.sashpos(0, layout["pane_sizes"][0])
                        paned.sashpos(1, layout["pane_sizes"][1])
                    except Exception as e:
                        print("Erreur lors de la restauration du layout :", e)
                app.after(200, apply_pane_sizes)

            if "window_size" in layout:            
                app.geometry(f"{layout['window_size'][0]}x{layout['window_size'][1]}")

            if "vertical_sash" in layout:
                def apply_vertical_pane_sizes():
                    app.update_idletasks()
                    # ✅ Forcer une taille minimale
                    total_height = vertical_paned.winfo_height()
                    if total_height < 50:  # trop petit, pas encore affiché
                        app.after(100, apply_vertical_pane_sizes)
                        return
                    try:
                        vertical_paned.sashpos(0, layout["vertical_sash"])
                    except Exception as e:
                        print("Erreur vertical sash :", e)
                app.after(200, apply_vertical_pane_sizes)
                    


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

bg = style.colors.get("secondary")
hover_bg = lighten_color(bg, 0.1)  # éclaircir légèrement pour le hover



style.configure("Tool.TButton",background=bg,relief="flat")
style.map("Tool.TButton", background=[("active", hover_bg)], relief=[("active", "flat")])


state['app'] = app

 # Frame principale qui contient tout
main_frame = ttk.Frame(app)
main_frame.pack(fill="both", expand=True)

# Définir une grille à 3 lignes :
main_frame.rowconfigure(0, weight=0)  # Toolbar / séparateur
main_frame.rowconfigure(1, weight=1)  # Le centre : frame_game + timeline
main_frame.rowconfigure(2, weight=0)  # Log en bas
main_frame.columnconfigure(0, weight=1)


#################################################

toolbar = Toolbar(main_frame)
toolbar.add_icon("ui/icons/icons8-document-24.png", lambda: load_scene_dialog(state, game), tooltip="Load scene")
toolbar.add_icon("ui/icons/icons8-save-24.png", lambda: save_scene(state, "config.json", game), tooltip="Save scene")
toolbar.add_separator()
toolbar.add_text("TOOLS")
toolbar.add_icon("ui/icons/icons8-download-from-the-cloud-24.png", lambda: DownloaderWindow(state), tooltip="Downloader & Splitter")
toolbar.add_icon("ui/icons/icons8-video-gallery-24.png", lambda: DiskLibraryWindow(state, on_double_click=on_video_selected), tooltip="Media Library")

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

preview_panel = PreviewPanel(paned)
library_panel = ClipLibrary(paned, on_drop_callback=handle_video_drop, on_click=preview_panel.show_preview) 
property_panel = PropertyPanel(paned, update_callback=lambda: timeline.redraw())

#library_panel = EmptyPanel(paned, title="Library", color="red")
#preview_panel = EmptyPanel(paned, title="Preview", color="blue")
#property_panel = EmptyPanel(paned, title="Property", color="green")


paned.add(library_panel, weight=1)
paned.add(preview_panel, weight=1)
paned.add(property_panel, weight=1)



############################################

# Frame contenant timeline_toolbar + timeline
timeline_zone = ttk.Frame(vertical_paned)
timeline_zone.columnconfigure(0, weight=1)
timeline_zone.rowconfigure(0, weight=0)  # Toolbar (fixe)
timeline_zone.rowconfigure(1, weight=1)  # Timeline (extensible si nécessaire)
#timeline_toolbar = ttk.Frame(timeline_zone)
#timeline_toolbar.pack(fill="x", pady=(0, 10))


timeline_toolbar = Toolbar(timeline_zone)
timeline_toolbar.add_icon("ui/icons/icons8-ajouter-24.png", open_type_chooser)



#num_tracks = len(game.objects)
timeline = Timeline(timeline_zone, num_tracks=0, length=120,
                    on_clip_click=property_panel.show_object,
                    on_clip_removed=remove_clip,
                    on_time_click=handle_time_click)
timeline.grid(row=1, column=0, sticky="nsew")


vertical_paned.add(paned, weight=3)  # haut
vertical_paned.add(timeline_zone, weight=1)  # bas


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



############################################


load_config(app, state)
load_scene(state, game, "config.json")

# i = num_tracks-1
# for object in game.objects:
#     timeline.add_clip( object, track=i, start=object.step.delay, duration=object.step.duration)
#     i-=1
#     pass


# if( game.background is not None ):
#     background = game.background
#     if( isinstance(background, Video) ):
#         i = 0
#         last_end = 0
#         for data in background.raw_videos:
#             data["type"] = "Video"
#             object = ObjectFactory.create(data, game.pygame, game.window_size, 1, 0)
#             object.step.delay = last_end
#             last_end = object.step.delay + object.step.duration
#             timeline.add_clip( object, track="background", start=object.step.delay, duration=object.step.duration)

#             #add_thumbnail_library(zone1_content, object, on_drop_callback=handle_video_drop)
#             library_panel.add_video(object)
#             i+=1


# Sauvegarder à la fermeture
app.protocol("WM_DELETE_WINDOW", lambda: (save_config(app, state), app.destroy()))

# Lancer l'app
app.mainloop()


