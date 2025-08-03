import tkinter as tk
import ttkbootstrap as ttk

from ui.frame.scrollable_frame import ScrollableFrame
from ui.helper import get_calculated_value
from ui.log import log_message

class PropertyPanel(ttk.Frame):
    def __init__(self, state, parent, update_callback, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.state  = state
        self.update_callback = update_callback
        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)
        self.content = self.scroll_frame.get_content_frame()

    def show_object(self, obj):
        # Nettoie le panneau
        for widget in self.content.winfo_children():
            widget.destroy()

        self.content.columnconfigure(0, weight=1)
        self._show_object_section(obj, "main", obj.data, obj, self.content, show_children=False, updateable=True)

        for key, value in obj.schema().items():
            if value[0] not in ("str", "int",  "inteval", "float", "floateval",  "bool", "booleval"):
                updateable = True
                if( len(value) > 2  ):
                    updateable = value[2]
                sub_obj = getattr(obj, key, {})
                self._show_object_section(obj, key, obj.data.get(key, {}), sub_obj, self.content, True, updateable)

    def _show_object_section(self, parent_obj, name, data, obj, parent, show_children=True, updateable=True):
        spec = obj.schema()
        if not spec:
            ttk.Label(parent, text=f"{name.upper()}: no spec").grid(sticky="w", padx=5, pady=5)
            return

        container = ttk.Frame(parent, borderwidth=1, relief="solid")
        container.grid(sticky="ew", padx=5, pady=5)
        container.columnconfigure(0, weight=1)

        frame_style = "Titlebar.Enabled.TFrame" if obj.enabled() else "Titlebar.Disabled.TFrame"
        label_style = "Titlebar.Enabled.TLabel" if obj.enabled() else "Titlebar.Disabled.TLabel"

        header = ttk.Frame(container, style=frame_style)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        arrow = ttk.Label(header, text="►", style=label_style)
        arrow.grid(row=0, column=0, sticky="w", padx=5)

        title = ttk.Label(header, text=name.upper(), style=label_style)
        title.grid(row=0, column=1, sticky="w", padx=5)

        # Pour pouvoir mettre à jour dynamiquement le style plus tard
        def update_section_style(error=False):
            if error:
                frame_style = "Titlebar.Error.TFrame"
                label_style = "Titlebar.Error.TLabel"
            elif obj.enabled():
                frame_style = "Titlebar.Enabled.TFrame"
                label_style = "Titlebar.Enabled.TLabel"
            else:
                frame_style = "Titlebar.Disabled.TFrame"
                label_style = "Titlebar.Disabled.TLabel"

            header.configure(style=frame_style)
            arrow.configure(style=label_style)
            title.configure(style=label_style)

        content = None

        def toggle():
            nonlocal content
            if content is None:
                content = self._build_content(container, parent_obj, data, obj, spec, show_children, updateable, update_section_style)
                arrow.config(text="▼")
            elif content.winfo_ismapped():
                content.grid_remove()
                arrow.config(text="►")
            else:
                content.grid()
                arrow.config(text="▼")

        header.bind("<Button-1>", lambda e: toggle())
        for child in header.winfo_children():
            child.bind("<Button-1>", lambda e: toggle())


    def _build_content(self, parent, parent_obj, data, obj, spec, show_children, updateable, update_section_style):
        frame = ttk.Frame(parent, padding=10)
        frame.grid(row=1, column=0, sticky="ew")
        frame.columnconfigure(0, weight=0, minsize=70)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

        row = 0
        all_vars = {}

        for key, value  in spec.items():
            ftype = value[0]
            label = value[1]
            raw = data.get(key, "")
            calc = get_calculated_value(obj, key)

            if ftype in ("int", "inteval", "float", "floateval", "str"):
                ttk.Label(frame, text=f"{label}:").grid(row=row, column=0, sticky="e", padx=5, pady=2)

                if updateable:
                    var = tk.StringVar(value=str(raw))
                    result_var = tk.StringVar(value=str(calc))
                    entry = ttk.Entry(frame, textvariable=var)
                    entry.grid(row=row, column=1, sticky="ew", padx=(0, 2), pady=2)
                    entry2 = ttk.Entry(frame, textvariable=result_var, state="readonly")
                    entry2.grid(row=row, column=2, sticky="ew", padx=(2, 0), pady=2)
                else:
                    entry = ttk.Entry(frame)
                    entry.insert(0, str(calc))
                    entry.configure(state="readonly")
                    entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=2)



                def make_recalc(var, key, ftype):
                    def recalc(event=None):
                        val = var.get()
                        error = False

                        try:
                            # Tentative de conversion (validation uniquement)
                            parsed_val = val
                            if ftype == "int":
                                parsed_val = int(val)
                            elif ftype == "float":
                                parsed_val = float(val)
                            elif ftype == "bool":
                                parsed_val = bool(val)
                            # Pour "str", "inteval", "floateval" => pas de conversion immédiate
                        except Exception as e:
                            log_message(self.state, f"Invalid value for {key}: {e}")
                            error = True

                        try:
                            if not error:
                                setattr(obj, key, parsed_val)

                                if hasattr(data, "set"):
                                    data.set(key, parsed_val)
                                else:
                                    data[key] = parsed_val

                                obj.prepare()
                                parent_obj.prepare()
                        except Exception as e:
                            log_message(self.state, f"Object update error for {key}: {e}")
                            error = True

                        # Met à jour TOUS les champs visibles
                        for k, (v2, r2) in all_vars.items():
                            v2.set(str(data.get(k, "")))
                            try:
                                calculated = get_calculated_value(obj, k)
                            except Exception as e:
                                calculated = f"ERR: {e}"
                                error = True
                            r2.set(str(calculated))

                        update_section_style(error)
                        self.update_callback(parent_obj)

                    return recalc

                #all_vars[key] = (var, result_var)
                if updateable:
                    all_vars[key] = (var, result_var)
                    entry.bind("<FocusOut>", make_recalc(var, key, ftype))
                    entry.bind("<Return>", make_recalc(var, key, ftype))
                else:
                    pass
                    #all_vars[key] = (None, result_var)
                row += 1

            elif ftype == "bool":

                def on_checkbox_click(var, key):
                    val = var.get()
                    setattr(obj, key, val)

                    if hasattr(data, "set"):
                        data.set(key, val)
                    else:
                        data[key] = val

                    obj.prepare()
                    parent_obj.prepare()
                    pass
                ttk.Label(frame, text=f"{label}:").grid(row=row, column=0, sticky="e", padx=5, pady=2)
                var = tk.BooleanVar(value=bool(raw))
                check = ttk.Checkbutton(
                    frame,
                    variable=var,
                    onvalue=True,
                    offvalue=False,
                    bootstyle="primary-round-toggle",
                    command=lambda var=var, key=key: on_checkbox_click(var, key) 
                )
                check.grid(row=row, column=1, sticky="w", padx=5, pady=2)
      
           

                row += 1

            elif show_children:
                subframe = ttk.Frame(frame)
                subframe.grid(row=row, column=0, columnspan=3, sticky="ew", padx=20)
                self._show_object_section(parent_obj, key, data.get(key, {}), getattr(obj, key, ""), subframe)
                row += 1

        return frame


    # def _build_content(self, parent, parent_obj, data, obj, spec, show_children, update_section_style):
    #     frame = ttk.Frame(parent, padding=10)
    #     frame.grid(row=1, column=0, sticky="ew")
    #     frame.columnconfigure(0, weight=0, minsize=70)
    #     frame.columnconfigure(1, weight=1)
    #     frame.columnconfigure(2, weight=1)

    #     row = 0
    #     all_vars = {}

    #     for key, (ftype, label) in spec.items():
    #         raw = data.get(key, "")
    #         calc = get_calculated_value(obj, key)

    #         if ftype in ("int", "inteval", "float", "floateval", "str"):
    #             ttk.Label(frame, text=f"{label}:").grid(row=row, column=0, sticky="e", padx=5, pady=2)
    #             var = tk.StringVar(value=str(raw))
    #             result_var = tk.StringVar(value=str(calc))

    #             entry = ttk.Entry(frame, textvariable=var)
    #             entry.grid(row=row, column=1, sticky="ew", padx=(0, 2), pady=2)
    #             entry2 = ttk.Entry(frame, textvariable=result_var, state="readonly")
    #             entry2.grid(row=row, column=2, sticky="ew", padx=(2, 0), pady=2)

    #             def make_recalc(var, key, ftype):
    #                 def recalc(*_):
    #                     val = var.get()
    #                     error = False

    #                     try:
    #                         # Tentative de conversion (validation uniquement)
    #                         parsed_val = val
    #                         if ftype == "int":
    #                             parsed_val = int(val)
    #                         elif ftype == "float":
    #                             parsed_val = float(val)
    #                         elif ftype == "bool":
    #                             parsed_val = bool(val)
    #                         # Pour "str", "inteval", "floateval" => pas de conversion immédiate
    #                     except Exception as e:
    #                         log_message(self.state, f"Invalid value for {key}: {e}")
    #                         error = True

    #                     try:
    #                         if not error:
    #                             setattr(obj, key, parsed_val)

    #                             if hasattr(data, "set"):
    #                                 data.set(key, parsed_val)
    #                             else:
    #                                 data[key] = parsed_val

    #                             obj.prepare()
    #                             parent_obj.prepare()
    #                     except Exception as e:
    #                         log_message(self.state, f"Object update error for {key}: {e}")
    #                         error = True

    #                     # Met à jour TOUS les champs visibles
    #                     for k, (v2, r2, trace_id) in all_vars.items():
    #                         v2.trace_remove("write", trace_id)
    #                         v2.set(str(data.get(k, "")))

    #                         try:
    #                             calculated = get_calculated_value(obj, k)
    #                         except Exception as e:
    #                             calculated = f"ERR: {e}"
    #                             error = True

    #                         r2.set(str(calculated))

    #                         # ✅ important : ici on utilise le BON ftype pour le champ k
    #                         new_trace = v2.trace_add("write", make_recalc(v2, k, spec[k][0]))
    #                         all_vars[k] = (v2, r2, new_trace)

    #                     update_section_style(error)
    #                     self.update_callback()

    #                 return recalc


    #             trace_id = var.trace_add("write", make_recalc(var, key, ftype))
    #             all_vars[key] = (var, result_var, trace_id)
    #             row += 1

    #         elif ftype == "bool":
    #             ttk.Label(frame, text=f"{label}:").grid(row=row, column=0, sticky="e", padx=5, pady=2)
    #             var = tk.BooleanVar(value=bool(raw))
    #             ttk.Checkbutton(frame, variable=var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
    #             row += 1

    #         elif show_children:
    #             subframe = ttk.Frame(frame)
    #             subframe.grid(row=row, column=0, columnspan=3, sticky="ew", padx=20)
    #             self._show_object_section(parent_obj, key, data.get(key, {}), getattr(obj, key, ""), subframe)
    #             row += 1

    #     return frame
