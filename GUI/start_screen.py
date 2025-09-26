import customtkinter as ctk
from tkinter import messagebox, ttk
from utils import historial

class StartScreen(ctk.CTkFrame):
    def __init__(self, master, on_continue):
        """
        Pantalla inicial:
          - Crear ejercicio nuevo (ingresar cantidad de procesos)
          - Configuraciones de INPUT guardadas (abrir / eliminar)
        on_continue(payload):
          - Si es int  -> cantidad de procesos para DataInputScreen (flujo clásico)
          - Si es dict -> {"action": "load_config", "data": {...}}
        """
        super().__init__(master)
        self.on_continue = on_continue

        self.label_title = ctk.CTkLabel(self, text="Planificación de CPU", font=("Arial", 20, "bold"))
        self.label_title.pack(pady=(16, 8))

        # ---------- Nueva sección: crear ejercicio desde cero ----------
        new_box = ctk.CTkFrame(self)
        new_box.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(new_box, text="Nuevo ejercicio", font=("Arial", 14, "bold")).pack(anchor="w", pady=(10, 4), padx=10)
        row = ctk.CTkFrame(new_box); row.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(row, text="Cantidad de procesos:").pack(side="left", padx=(0, 8))
        self.entry_count = ctk.CTkEntry(row, placeholder_text="Ej: 4", width=120)
        self.entry_count.pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Continuar", command=self._continue_clicked).pack(side="left")

        # ---------- Historial de CONFIGURACIONES DE INPUT ----------
        conf_box = ctk.CTkFrame(self)
        conf_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        ctk.CTkLabel(conf_box, text="Configuraciones guardadas (inputs)", font=("Arial", 14, "bold")).pack(anchor="w", pady=(10, 4), padx=10)
        conf_frame = ctk.CTkFrame(conf_box); conf_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        cols2 = ("Nombre", "Fecha", "Procesos")
        self.tree_conf = ttk.Treeview(conf_frame, columns=cols2, show="headings", height=10)
        for c, w in zip(cols2, (260, 180, 100)):
            self.tree_conf.heading(c, text=c)
            self.tree_conf.column(c, width=w, anchor="w")

        scr2 = ttk.Scrollbar(conf_frame, orient="vertical", command=self.tree_conf.yview)
        self.tree_conf.configure(yscrollcommand=scr2.set)
        self.tree_conf.pack(side="left", fill="both", expand=True)
        scr2.pack(side="right", fill="y")

        btns2 = ctk.CTkFrame(conf_box); btns2.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(btns2, text="Abrir configuración", command=self._abrir_config, fg_color="green").pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns2, text="Eliminar", command=self._eliminar_config, fg_color="red").pack(side="left")
        ctk.CTkButton(btns2, text="Refrescar", command=self._refrescar_confs).pack(side="right")

        # cargar datos iniciales
        self._refrescar_confs()

    # ===== nuevo ejercicio =====
    def _continue_clicked(self):
        try:
            n = int(self.entry_count.get())
            if n <= 0:
                raise ValueError
            self.on_continue(n)  # flujo clásico
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido mayor a 0")

    # ===== historial configuraciones =====
    def _refrescar_confs(self):
        for i in self.tree_conf.get_children():
            self.tree_conf.delete(i)
        for idx, nombre, fecha, nproc in historial.listar_input_configs():
            try:
                from datetime import datetime
                fecha_fmt = datetime.fromisoformat(fecha).strftime("%d/%m/%Y %H:%M")
            except Exception:
                fecha_fmt = fecha
            iid = f"cfg-{idx}"
            self.tree_conf.insert("", "end", iid=iid, values=(nombre, fecha_fmt, nproc))

    def _abrir_config(self):
        sel = self.tree_conf.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una configuración.")
            return
        iid = sel[0]
        idx = int(iid.split("-")[1])
        data = historial.cargar_input_config(idx)
        if not data:
            messagebox.showerror("Error", "No se pudo cargar la configuración.")
            return
        # llevar directo a simulación (main.py ya soporta este payload)
        self.on_continue({"action": "load_config", "data": data})

    def _eliminar_config(self):
        sel = self.tree_conf.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una configuración para eliminar.")
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar la configuración?"):
            return
        iid = sel[0]
        idx = int(iid.split("-")[1])
        nombre = historial.eliminar_input_config(idx)
        if nombre:
            self._refrescar_confs()
