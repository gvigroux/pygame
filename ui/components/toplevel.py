
import ttkbootstrap as ttk
from ui.helper import center_on_parent

class Toplevel(ttk.Toplevel):
    def __init__(self, state, title) :
        self.state = state
        super().__init__(state["app"])
        
        self.title(title)

        self.transient(self.state["app"])      # La lie à la fenêtre parente
        self.grab_set()             # Rends cette fenêtre modale
        self.focus_force()          # Force le focus clavier ici
        #self.lift()                 # Monte cette fenêtre au-dessus
        #self.after(100, self.lift)  # Assure le lifting après ouverture du sélecteur de fichier
        self.withdraw()  # Masque la fenêtre avant affichage
        self.after(0, self._finalize_position)

        # Gestion de la fermeture
        self.protocol("WM_DELETE_WINDOW", self.on_close)


    def _finalize_position(self):
        center_on_parent(self)
        self.deiconify()   # Montre la fenêtre
        self.lift()
        self.focus_force()


    def on_close(self):
        if( hasattr(self, "_on_close") ):
            self._on_close()
        self.destroy()