import tkinter as tk
from tkinter import filedialog
from ttkbootstrap import Style

from ui.config import save_config
from ui.file import load_scene, save_scene


class CustomMenu(tk.Frame):
    def __init__(self, master, state, **kwargs):
        super().__init__(master, **kwargs)
               
        self.style = Style()
        self.state = state
        
        # Récupération des couleurs du thème actif
        self.menu_bg = self.style.colors.get('bg')
        self.menu_fg = self.style.colors.get('light')
        self.hover_bg = self.style.colors.get('secondary')
        self.border_color    = self.style.colors.get('selectbg')  # Bordure standard
        self.primary_color   = self.style.colors.get('primary')  # Couleur principale
        
        self.configure(background="#0a283b", bd=0, highlightthickness=0)

        # Bouton "File"
        self.btn_file = tk.Label(
            self, 
            text="File", 
            bg=self.menu_bg, 
            fg=self.menu_fg, 
            padx=10, 
            pady=5, 
            cursor="hand2",
            font=('Helvetica', 10)
        )
        self.btn_file.pack(side="left")
        self.btn_file.bind("<Button-1>", self.toggle_file_menu)
        self.btn_file.bind("<Enter>", lambda e: e.widget.config(bg=self.hover_bg))
        self.btn_file.bind("<Leave>", lambda e: e.widget.config(bg=self.menu_bg))
        
        # Menu déroulant
        self.file_menu = tk.Frame(
            master, 
            background=self.menu_bg, 
            bd=0, 
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.border_color,
            highlightcolor=self.primary_color
        )
        
        # Options du menu
        options = [("Open", self.open_cmd),
                    ("Save", self.save_cmd),
                    ("Save As...", self.save_as_cmd),
                    ("-", None), 
                    ("Exit", self.safe_quit)]
        
        for text, cmd in options:
            if text == "-":  # Création du séparateur
                separator = tk.Canvas(self.file_menu, height=1, bg=self.border_color, highlightthickness=0)
                separator.create_line(0, 1, 400, 1, fill=self.border_color, width=2)  # x1,y1,x2,y2
                separator.pack(fill='x', pady=1) 
                continue
            else:
                lbl = tk.Label(
                self.file_menu, 
                text=text, 
                bg=self.menu_bg, 
                fg=self.menu_fg, 
                anchor="w", 
                padx=20, 
                pady=5, 
                cursor="hand2",
                font=('Helvetica', 9)
            )
            lbl.pack(fill="x")
            #lbl.bind("<Button-1>", lambda e, c=cmd: c())
            lbl.bind("<Button-1>", lambda e, c=cmd, t=text: (print(f"Click on: {t}"), c())[1])
            lbl.bind("<Enter>", lambda e: e.widget.config(bg=self.hover_bg))
            lbl.bind("<Leave>", lambda e: e.widget.config(bg=self.menu_bg))
        
        # Force l'application du style initial
        self.file_menu.update_idletasks()
        
        self.menu_visible = False
        self.master.bind("<Button-1>", self.on_click_outside)
        self.file_menu.bind("<Button-1>", lambda e: "break")
    
    def toggle_file_menu(self, event=None):
        if self.menu_visible:
            self.file_menu.place_forget()
            self.menu_visible = False
        else:
            x = self.btn_file.winfo_x()
            y = self.btn_file.winfo_height()
            
            # Réapplique les couleurs au cas où
            for child in self.file_menu.winfo_children():
                child.config(bg=self.menu_bg)
                if isinstance(child, (tk.Label, tk.Button)):
                    child.config(fg=self.menu_fg)
            
            self.file_menu.lift()
            self.file_menu.place(
                in_=self, 
                x=x, 
                y=y, 
                width=120,
                bordermode="outside"
            )
            self.menu_visible = True
        return "break"
    
    def safe_quit(self):
        """Ferme proprement l'application en sauvegardant"""
        save_config(self.state)  # Sauvegarde d'abord
        self.master.destroy()    # Puis fermeture
        
    def on_click_outside(self, event):
        if self.menu_visible:
            if (not self.btn_file.winfo_containing(event.x_root, event.y_root) and 
                not self.file_menu.winfo_containing(event.x_root, event.y_root)):
                self.file_menu.place_forget()
                self.menu_visible = False
    
    def open_cmd(self):
        self.toggle_file_menu()
        filepath = filedialog.askopenfilename(
        title="Open scene",
        defaultextension=".json",
        filetypes=[("JSON files", "*.json")])
        if filepath:
            self.state["config"].setdefault("current", {})["file_path"] = filepath
            load_scene(self.state)
    
    def save_cmd(self):
        save_scene(self.state)
        self.toggle_file_menu()
    
    def save_as_cmd(self):
        self.toggle_file_menu()
        filepath = filedialog.asksaveasfilename(
                defaultextension=".json", 
                filetypes=[("JSON files", "*.json")] )
        if filepath:
            self.state["config"].setdefault("current", {})["file_path"] = filepath
            save_scene(self.state)


