import customtkinter as ctk
from tkinter import messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from models.process import Process
# Algoritmos sin bloqueos
from algoritmos.fifo import fifo
from algoritmos.sjf import sjf
from algoritmos.srtf import srtf
from algoritmos.roundrobin import round_robin
# Algoritmos con bloqueos
from algoritmos.fifo_blocking import fifo_blocking
from algoritmos.sjf_blocking import sjf_blocking
from algoritmos.srtf_blocking import srtf_blocking
from algoritmos.round_robin_blocking import round_robin_blocking

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
        self.option_menu = ctk.CTkOptionMenu(
            self, values=self.algoritmos, variable=self.selected_algo, command=self._on_algo_change
        )
        self.option_menu.pack(pady=5)

        # --- Botones de control ---
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)
        self.btn_run = ctk.CTkButton(btn_frame, text="Ejecutar", command=self._run_algorithm)
        self.btn_run.pack(side="left", padx=5)
        self.btn_new = ctk.CTkButton(btn_frame, text="Nuevo ejercicio", command=self.volver_inicio)
        self.btn_new.pack(side="left", padx=5)
        self.btn_exit = ctk.CTkButton(
            btn_frame, text="Salir", fg_color="red", hover_color="#aa0000", command=self._salir
        )
        self.btn_exit.pack(side="left", padx=5)

        # --- Campo quantum (solo si RR) ---
        self.frame_quantum = ctk.CTkFrame(self)
        self.label_quantum = ctk.CTkLabel(self.frame_quantum, text="Quantum:")
        self.label_quantum.pack(side="left", padx=5)
        self.entry_quantum = ctk.CTkEntry(self.frame_quantum, placeholder_text="Ej: 2", width=60)
        self.entry_quantum.pack(side="left", padx=5)

        # --- Tabla BCP ---
        self.tree = ttk.Treeview(self, columns=("PID", "Llegada", "CPU", "TR", "TE"), show="headings", height=8)
        for col in ("PID", "Llegada", "CPU", "TR", "TE"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor="center")
        self.tree.pack(pady=10, fill="x")

        # --- Label promedios ---
        self.label_promedios = ctk.CTkLabel(self, text="TRM: -    |    TEM: -", font=("Arial", 14))
        self.label_promedios.pack(pady=5)

        # --- Frame gráfico ---
        self.frame_gantt = ctk.CTkFrame(self)
        self.frame_gantt.pack(pady=10, fill="both", expand=True)

    def _on_algo_change(self, value):
        if value == "Round Robin":
            self.frame_quantum.pack(before=self.tree, pady=5)
        else:
            self.frame_quantum.pack_forget()

    def _run_algorithm(self):
        procesos = [Process(p["pid"], p["arrival_time"], p["bursts"]) for p in self.procesos_data]
        algo = self.selected_algo.get()

        try:
            if algo == "FIFO":
                gantt, result = fifo_blocking(procesos)
            elif algo == "SJF":
                gantt, result = sjf_blocking(procesos)
            elif algo == "SRTF":
                gantt, result = srtf_blocking(procesos)
            elif algo == "Round Robin":
                quantum = self._get_quantum()
                if quantum is None:
                    return
                gantt, result = round_robin_blocking(procesos, quantum)
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

        # Actualizar promedios
        self.label_promedios.configure(
            text=f"TRM (Tiempo de Respuesta Medio): {trm:.2f}    |    TEM (Tiempo de Espera Medio): {tem:.2f}"
        )

        # Mostrar gráfico
        self._mostrar_gantt_embebido(gantt, algo)

    def _get_quantum(self):
        try:
            quantum = int(self.entry_quantum.get())
            if quantum <= 0:
                raise ValueError
            return quantum
        except ValueError:
            messagebox.showerror("Error", "Ingrese un quantum válido (> 0)")
            return None

    def _mostrar_gantt_embebido(self, gantt_chart, algo):
        for widget in self.frame_gantt.winfo_children():
            widget.destroy()

        norm = []
        for seg in gantt_chart:
            if len(seg) == 3:
                pid, start, end = seg
                tipo = "CPU" if pid != "IDLE" else "IDLE"
                norm.append((pid, start, end, tipo))
            elif len(seg) == 4:
                norm.append(seg)

        fig, ax = plt.subplots(figsize=(8, 3))
        procesos_unicos = [pid for pid, _, _, tipo in norm if pid != "IDLE"]
        procesos_unicos = list(dict.fromkeys(procesos_unicos))
        y_positions = {pid: i for i, pid in enumerate(procesos_unicos)}

        colors = {}
        color_palette = plt.cm.get_cmap("tab20", len(procesos_unicos) + 1)

        for pid, start, end, tipo in norm:
            if tipo == "IDLE":
                color = "lightgray"
                hatch = None
                y = -1
            elif tipo == "BLOCK":
                color = "black"
                hatch = "//"
                y = y_positions.get(pid, 0)
            else:
                if pid not in colors:
                    colors[pid] = color_palette(len(colors))
                color = colors[pid]
                hatch = None
                y = y_positions.get(pid, 0)

            ax.barh(y, end - start, left=start, height=0.5, color=color, edgecolor='black', hatch=hatch)
            if tipo != "IDLE":
                ax.text((start + end) / 2, y, str(pid), ha='center', va='center',
                        fontsize=8, color="white" if tipo == "BLOCK" else "black")

        if procesos_unicos:
            ax.set_yticks(list(y_positions.values()))
            ax.set_yticklabels(list(y_positions.keys()))
        else:
            ax.set_yticks([])

        if norm:
            max_time = max(end for _, _, end, _ in norm)
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