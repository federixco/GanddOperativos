import customtkinter as ctk
from tkinter import messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from models.process import Process
from algoritmos.fifo import fifo
from algoritmos.sjf import sjf
from algoritmos.srtf import srtf
from algoritmos.roundrobin import round_robin
from utils.metricas import calcular_metricas

class AlgorithmScreen(ctk.CTkFrame):
    def __init__(self, master, procesos_data, volver_inicio):
        super().__init__(master)
        self.procesos_data = procesos_data
        self.volver_inicio = volver_inicio

        # --- Selección de algoritmo ---
        self.label_title = ctk.CTkLabel(self, text="Seleccionar algoritmo", font=("Arial", 18, "bold"))
        self.label_title.pack(pady=10)

        self.algoritmos = ["FIFO", "SJF", "SRTF", "Round Robin"]
        self.selected_algo = ctk.StringVar(value=self.algoritmos[0])
        self.option_menu = ctk.CTkOptionMenu(self, values=self.algoritmos, variable=self.selected_algo, command=self._on_algo_change)
        self.option_menu.pack(pady=5)

        # --- Botones de control ---
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)
        self.btn_run = ctk.CTkButton(btn_frame, text="Ejecutar", command=self._run_algorithm)
        self.btn_run.pack(side="left", padx=5)
        self.btn_new = ctk.CTkButton(btn_frame, text="Nuevo ejercicio", command=self.volver_inicio)
        self.btn_new.pack(side="left", padx=5)
        self.btn_exit = ctk.CTkButton(btn_frame, text="Salir", fg_color="red", hover_color="#aa0000", command=self._salir)
        self.btn_exit.pack(side="left", padx=5)

        # --- Campo quantum (fijo arriba de la tabla) ---
        self.frame_quantum = ctk.CTkFrame(self)
        self.label_quantum = ctk.CTkLabel(self.frame_quantum, text="Quantum:")
        self.label_quantum.pack(side="left", padx=5)
        self.entry_quantum = ctk.CTkEntry(self.frame_quantum, placeholder_text="Ej: 2", width=60)
        self.entry_quantum.pack(side="left", padx=5)
        # No lo mostramos aún, solo cuando se elija RR

        # --- Tabla BCP ---
        self.tree = ttk.Treeview(self, columns=("PID", "Llegada", "CPU", "TR", "TE"), show="headings", height=8)
        for col in ("PID", "Llegada", "CPU", "TR", "TE"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor="center")

        # Empaquetamos quantum y tabla en orden fijo
        self.frame_quantum.pack_forget()  # Oculto por defecto
        self.tree.pack(pady=10, fill="x")

        # --- Label para mostrar TRM y TEM ---
        self.label_promedios = ctk.CTkLabel(self, text="TRM: -    |    TEM: -", font=("Arial", 14))
        self.label_promedios.pack(pady=5)

        # --- Frame para gráfico ---
        self.frame_gantt = ctk.CTkFrame(self)
        self.frame_gantt.pack(pady=10, fill="both", expand=True)

    def _on_algo_change(self, value):
        if value == "Round Robin":
            self.frame_quantum.pack(before=self.tree, pady=5)  # Siempre antes de la tabla
        else:
            self.frame_quantum.pack_forget()

    def _run_algorithm(self):
        procesos = [Process(p["pid"], p["arrival_time"], p["burst_time"]) for p in self.procesos_data]
        algo = self.selected_algo.get()

        try:
            if algo == "FIFO":
                gantt, result = fifo(procesos)
            elif algo == "SJF":
                gantt, result = sjf(procesos)
            elif algo == "SRTF":
                gantt, result = srtf(procesos)
            elif algo == "Round Robin":
                try:
                    quantum = int(self.entry_quantum.get())
                    if quantum <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Error", "Ingrese un quantum válido (> 0)")
                    return
                gantt, result = round_robin(procesos, quantum)
            else:
                messagebox.showerror("Error", "Algoritmo no reconocido")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al ejecutar: {e}")
            return

        # Calcular métricas
        metricas, trm, tem = calcular_metricas(result)

        # Actualizar tabla
        for row in self.tree.get_children():
            self.tree.delete(row)
        for m in metricas:
            self.tree.insert("", "end", values=(m["PID"], m["Llegada"], m["CPU"], m["TR"], m["TE"]))

        # Actualizar label de promedios
        self.label_promedios.configure(
            text=f"TRM (Tiempo de Respuesta Medio): {trm:.2f}    |    TEM (Tiempo de Espera Medio): {tem:.2f}"
        )

        # Mostrar gráfico embebido
        self._mostrar_gantt_embebido(gantt, algo)

    def _mostrar_gantt_embebido(self, gantt_chart, algo):
        # Limpiar gráfico anterior
        for widget in self.frame_gantt.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(8, 3))
        procesos_unicos = [pid for pid, _, _ in gantt_chart if pid != "IDLE"]
        procesos_unicos = list(dict.fromkeys(procesos_unicos))
        y_positions = {pid: i for i, pid in enumerate(procesos_unicos)}
        colors = {}
        color_palette = plt.cm.get_cmap("tab20", len(procesos_unicos) + 1)

        for i, (pid, start, end) in enumerate(gantt_chart):
            if pid not in colors:
                colors[pid] = "lightgray" if pid == "IDLE" else color_palette(len(colors))
            y = y_positions.get(pid, -1)
            ax.barh(y, end - start, left=start, height=0.5, color=colors[pid], edgecolor='black')
            ax.text((start + end) / 2, y, pid, ha='center', va='center', fontsize=8)

        ax.set_yticks(list(y_positions.values()))
        ax.set_yticklabels(list(y_positions.keys()))
        max_time = max(end for _, _, end in gantt_chart)
        ax.set_xticks(range(0, max_time + 1))
        ax.set_xlim(0, max_time)
        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Procesos")
        ax.set_title(f"Diagrama de Gantt - {algo}")
        ax.grid(True, axis='x', linestyle='--', alpha=0.6)

        canvas = FigureCanvasTkAgg(fig, master=self.frame_gantt)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _salir(self):
        self.master.destroy()
