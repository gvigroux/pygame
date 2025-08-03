import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog

from ui.helper import center_on_parent


class ParameterForm(ttk.Toplevel):
    def __init__(self, master, fields: dict, on_submit):
        super().__init__(master)
        self.transient(master)      # La lie à la fenêtre parente
        self.grab_set()             # Rends cette fenêtre modale
        self.focus_force()          # Force le focus clavier ici
        #self.lift()                 # Monte cette fenêtre au-dessus
        #self.after(100, self.lift)  # Assure le lifting après ouverture du sélecteur de fichier
        self.withdraw()  # Masque la fenêtre avant affichage
        self.after(0, self._finalize_position)

        self.title("Paramètres de l'objet")
        self.resizable(False, False)

        self.fields = self._flatten_fields(fields)
        self.vars = {}
        self.on_submit = on_submit

        self._build_ui()

    def _finalize_position(self):
        center_on_parent(self)
        self.deiconify()   # Montre la fenêtre
        self.lift()
        self.focus_force()

    def _flatten_fields(self, fields, prefix=""):
        flat = {}

        for key, value in fields.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict) and "name" in value:
                flat[full_key] = value

            elif isinstance(value, dict):
                subfields = self._flatten_fields(value, full_key)
                flat.update(subfields)

            elif isinstance(value, list):
                for field in value:
                    if "name" not in field:
                        raise ValueError(f"Champ invalide dans la liste : {field}")
                    subkey = field["name"]
                    flat[f"{full_key}.{subkey}"] = field

            else:
                raise ValueError(f"Champ non reconnu pour la clé '{full_key}' : {value}")

        return flat

    def _group_fields_by_section(self):
        sections = {}
        for key in self.fields:
            parts = key.split(".")
            if len(parts) == 1:
                section = None  # Pas de groupe
                name = key
            else:
                section = parts[0]
                name = ".".join(parts[1:])
            if section not in sections:
                sections[section] = []
            sections[section].append((key, name, self.fields[key]))
        return sections

    def _build_ui(self):
        sections = self._group_fields_by_section()

        for section, fields in sections.items():
            if section is None:
                container = self
            else:
                container = ttk.LabelFrame(self, text=section)
                container.pack(fill="x", padx=15, pady=10)

            for key, label_key, field in fields:
                row = ttk.Frame(container)
                row.pack(fill="x", padx=10, pady=5)

                label = ttk.Label(row, text=label_key)
                label.pack(side="left", padx=(0, 10))

                widget, var = self._create_input_widget(row, field)
                widget.pack(side="left", fill="x", expand=True)

                self.vars[key] = var

        btn = ttk.Button(self, text="Valider", command=self._submit)
        btn.pack(pady=15)

    def _create_input_widget(self, parent, field):
        ftype = field.get("type", "text")
        default = field.get("default", "")
        name = field["name"]

        if ftype == "int":
            var = ttk.IntVar(value=default)
            widget = ttk.Spinbox(parent, from_=field.get("min", 0), to=field.get("max", 10000), textvariable=var)

        elif ftype == "float":
            var = ttk.DoubleVar(value=default)
            widget = ttk.Entry(parent, textvariable=var)

        elif ftype == "file":
            var = ttk.StringVar(value=default)
            widget = ttk.Frame(parent)
            entry = ttk.Entry(widget, textvariable=var, width=30)
            entry.pack(side="left", padx=(0, 5))
            btn = ttk.Button(widget, text="📁", width=3, command=lambda: self._browse_file(var))
            btn.pack(side="left")

        elif ftype == "bool":
            var = ttk.BooleanVar(value=default)
            widget = ttk.Checkbutton(parent, variable=var, text="")

        else:  # default to text
            var = ttk.StringVar(value=default)
            widget = ttk.Entry(parent, textvariable=var)

        return widget, var

    def _browse_file(self, var):
        path = filedialog.askopenfilename(parent=self)
        if path:
            var.set(path)

    def _submit(self):
        try:
            flat_data = {key: var.get() for key, var in self.vars.items()}
            nested = self._rebuild_nested_dict(flat_data)
            self.on_submit(nested)
            self.destroy()
        except Exception as e:
            Messagebox.show_error(f"Erreur lors de la soumission : {e}")

    def _rebuild_nested_dict(self, flat_data):
        result = {}
        for key, value in flat_data.items():
            parts = key.split(".")
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        return result
