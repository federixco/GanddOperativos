# gui/name_input_screen.py

import customtkinter as ctk
from tkinter import messagebox

class NameInputScreen(ctk.CTkFrame):
    def __init__(self, master, cantidad_procesos, on_continue):
        """
        Pantalla para ingresar los nombres de los procesos.

        :param master: ventana o frame padre
        :param cantidad_procesos: número de procesos a crear
        :param on_continue: función que recibe la lista de nombres y avanza a la siguiente pantalla
        """
        super().__init__(master)
        self.cantidad_procesos = cantidad_procesos
        self.on_continue = on_continue
        self.entries = []

        # Título
        self.label_title = ctk.CTkLabel(self, text="Asignar nombres a los procesos", font=("Arial", 18, "bold"))
        self.label_title.pack(pady=20)

        # Campos dinámicos
        for i in range(cantidad_procesos):
            frame = ctk.CTkFrame(self)
            frame.pack(pady=5, padx=10, fill="x")

            label = ctk.CTkLabel(frame, text=f"Proceso {i+1}:")
            label.pack(side="left", padx=5)

            entry = ctk.CTkEntry(frame, placeholder_text=f"P{i+1}")
            entry.pack(side="left", padx=5, fill="x", expand=True)
            self.entries.append(entry)

        # Botón continuar
        self.btn_continue = ctk.CTkButton(self, text="Continuar", command=self._continue_clicked)
        self.btn_continue.pack(pady=20)

    def _continue_clicked(self):
        """Valida y envía la lista de nombres."""
        nombres = []
        for i, entry in enumerate(self.entries):
            nombre = entry.get().strip()
            if not nombre:
                nombre = f"P{i+1}"  # Si está vacío, asigna nombre por defecto
            nombres.append(nombre)

        # Validar que no haya nombres repetidos
        if len(nombres) != len(set(nombres)):
            messagebox.showerror("Error", "Los nombres de los procesos deben ser únicos.")
            return

        self.on_continue(nombres)
