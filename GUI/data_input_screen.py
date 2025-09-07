# gui/data_input_screen.py

import customtkinter as ctk
from tkinter import messagebox

class DataInputScreen(ctk.CTkFrame):
    def __init__(self, master, nombres_procesos, on_continue):
        """
        Pantalla para ingresar tiempos de llegada y ejecución de cada proceso.

        :param master: ventana o frame padre
        :param nombres_procesos: lista con los nombres de los procesos
        :param on_continue: función que recibe una lista de diccionarios con los datos y avanza
        """
        super().__init__(master)
        self.nombres_procesos = nombres_procesos
        self.on_continue = on_continue
        self.entries_ta = []
        self.entries_cpu = []

        # Título
        self.label_title = ctk.CTkLabel(self, text="Ingresar datos de procesos", font=("Arial", 18, "bold"))
        self.label_title.pack(pady=20)

        # Campos dinámicos
        for nombre in nombres_procesos:
            frame = ctk.CTkFrame(self)
            frame.pack(pady=5, padx=10, fill="x")

            label = ctk.CTkLabel(frame, text=nombre, width=80)
            label.pack(side="left", padx=5)

            entry_ta = ctk.CTkEntry(frame, placeholder_text="Tiempo llegada")
            entry_ta.pack(side="left", padx=5)
            self.entries_ta.append(entry_ta)

            entry_cpu = ctk.CTkEntry(frame, placeholder_text="Tiempo CPU")
            entry_cpu.pack(side="left", padx=5)
            self.entries_cpu.append(entry_cpu)

        # Botón continuar
        self.btn_continue = ctk.CTkButton(self, text="Continuar", command=self._continue_clicked)
        self.btn_continue.pack(pady=20)

    def _continue_clicked(self):
        """Valida y envía los datos."""
        procesos_data = []
        try:
            for i, nombre in enumerate(self.nombres_procesos):
                ta = int(self.entries_ta[i].get())
                cpu = int(self.entries_cpu[i].get())
                if ta < 0 or cpu <= 0:
                    raise ValueError
                procesos_data.append({
                    "pid": nombre,
                    "arrival_time": ta,
                    "burst_time": cpu
                })
        except ValueError:
            messagebox.showerror("Error", "Ingrese valores válidos (TA >= 0, CPU > 0)")
            return

        self.on_continue(procesos_data)
