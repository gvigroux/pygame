import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui.helper import center_on_parent, place_under_mouse



class TypeChooser(tk.Toplevel):
    def __init__(self, master, type_list, on_validate, under_mouse=False):
        super().__init__(master)
        self.title("Choisir un type")
        self.grab_set()
        self.resizable(False, False)

        self.on_validate = on_validate

        ttk.Label(self, text="Sélectionnez le type :").pack(padx=10, pady=(10, 0))

        self.type_var = tk.StringVar(value=type_list[0])
        self.combobox = ttk.Combobox(self, values=type_list, textvariable=self.type_var, state="readonly")
        self.combobox.pack(padx=10, pady=10)

        btn = ttk.Button(self, text="OK", command=self.validate)
        btn.pack(padx=10, pady=(0, 10))

        self.update_idletasks()

        if under_mouse:
            place_under_mouse(self)
        else:
            center_on_parent(self)

        self.minsize(250, 100)

    def validate(self):
        choice = self.type_var.get()
        self.on_validate(choice)
        self.destroy()