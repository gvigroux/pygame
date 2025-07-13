import ttkbootstrap as ttk
from tkinter import Label

from ui.frame.scrollable_frame import ScrollableFrame

class EmptyPanel(ttk.Frame):
    def __init__(self, parent, title, color):
        super().__init__(parent)
        scroll = ScrollableFrame(self)
        scroll.pack(fill='both', expand=True)
        ttk.Label(scroll.inner, text=title, background=color).pack(pady=10)
        for i in range(50):
            ttk.Label(scroll.inner, text=f"{title} Line {i}", background=color).pack()

    def show_object(self, obj):
        pass