import time
import cairo
import pygame
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import os


from game import Game
from object.object import Object
from object.object_factory import ObjectFactory
from object.video import Video
from ui.config import load_config, save_config
from ui.frame.custom_menu import CustomMenu
from ui.panel.preview import PreviewPanel
from ui.panel.property import PropertyPanel
from ui.helper import center_window, lighten_color
from ui.tools.downloader import DownloaderWindow
from ui.tools.disk_library import DiskLibraryWindow
from ui.tools.import_video import ImportVideoTool
from ui.tools.xdownloader import XDownloader
from ui.frame.toolbar import Toolbar
from ui.frame.type_chooser import TypeChooser


from ui.panel.timeline import TimelinePanel
from ui.panel.preview import PreviewPanel
from ui.panel.library import LibraryPanel
from ui.panel.property import PropertyPanel

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
    screen = game.image_at_time(seconds) 
    preview_panel.show_preview(screen)
    
######################################

def handle_video_drop(video, x, y):
    timeline.drop_clip(video, at_position=(x, y))


######################################

def add_video_to_library(path):
    data = {
        "type": "video",
        "path": path
    }    
    object = ObjectFactory.create(data, game.window_size, 1, 0) 
    object.load_metadata_sync()
    object.load()
    library_panel.add_clip(object)

    
    base, _ = os.path.splitext(path)
    mp3_path = base + ".mp3"
    if(os.path.isfile(mp3_path)):
        data = {
            "type": "sound",
            "label": os.path.basename(mp3_path),
            "sound": {"path": mp3_path}
        }    
        object = ObjectFactory.create(data, game.window_size, 1, 0) 
        #object.load_metadata_sync()
        #object.load()
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

def on_property_panel_update(object):
    timeline.redraw()
    handle_time_click(timeline.current_time)
    #preview_panel.show_preview(object)


preview_panel = PreviewPanel(paned)
library_panel = LibraryPanel(state, paned, on_drop_callback=handle_video_drop, on_click=on_library_clip_click) 
property_panel = PropertyPanel(state, paned, update_callback=on_property_panel_update)

paned.add(library_panel, weight=1)
paned.add(preview_panel, weight=1)
paned.add(property_panel, weight=1)



############################################

# Frame contenant timeline_toolbar + timeline
timeline_zone = ttk.Frame(vertical_paned)
timeline_zone.columnconfigure(0, weight=1)
timeline_zone.rowconfigure(0, weight=0)  # Toolbar (fixe)
timeline_zone.rowconfigure(1, weight=1)  # Timeline (extensible si nécessaire)


timeline = TimelinePanel(timeline_zone, num_tracks=0, length=120,
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


def test():
    game.run()
    game.deactivate_window()

    
toolbar = Toolbar(main_frame)
toolbar.add_text("TOOLS")

toolbar.add_icon("ui/icons/icons8-importer-24.png", lambda: ImportVideoTool(state), tooltip="Downloader & Splitter")
toolbar.add_icon("ui/icons/icons8-download-from-the-cloud-24.png", lambda: DownloaderWindow(state), tooltip="Downloader & Splitter")
toolbar.add_icon("ui/icons/icons8-video-gallery-24.png", lambda: DiskLibraryWindow(state, on_double_click=add_video_to_library), tooltip="Media Library")
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


def read_templates(directory):
    fichiers_json = [f for f in os.listdir(directory) if f.endswith('.json')]
    resultats = []

    for nom_fichier in fichiers_json:
        chemin_complet = os.path.join(directory, nom_fichier)
        try:
            with open(chemin_complet, 'r', encoding='utf-8') as f:
                donnees = json.load(f)
                resultats.append((nom_fichier, donnees))
        except Exception as e:
            print(f"Erreur dans {nom_fichier} : {e}")

    return resultats


jsons = read_templates("templates")

for nom, contenu in jsons:
    library_panel.add_clip(ObjectFactory.create(contenu, state["game"].window_size, 1, 0))

# Sauvegarder à la fermeture
app.protocol("WM_DELETE_WINDOW", lambda: (save_config(state), app.destroy()))

# Lancer l'app
app.mainloop()


