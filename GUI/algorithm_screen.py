import customtkinter as ctk
from tkinter import messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from utils import historial

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
from utils.excel_export import exportar_a_excel


class AlgorithmScreen(ctk.CTkFrame):
    def __init__(self, master, procesos_data, volver_inicio):
        super().__init__(master)
        self.procesos_data = procesos_data
        self.volver_inicio = volver_inicio
        
        # Variables para almacenar el gráfico actual
        self.current_gantt = None
        self.current_algorithm = None
        self.current_fig = None
        self.current_metricas = None
        self.current_trm = None
        self.current_tem = None
        self.current_quantum = None

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
        self.btn_export = ctk.CTkButton(btn_frame, text="Exportar PNG", command=self._export_png, 
                                      fg_color="green", hover_color="#006600")
        self.btn_export.pack(side="left", padx=5)
        self.btn_export_excel = ctk.CTkButton(btn_frame, text="Exportar Excel", command=self._export_excel, 
                                            fg_color="purple", hover_color="#660066")
        self.btn_export_excel.pack(side="left", padx=5)
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
        # Crear copias de los procesos para no modificar los originales
        from copy import deepcopy
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
                # Detectar si los procesos tienen bloqueos
                tiene_bloqueos = any(len(p["bursts"]) > 1 for p in self.procesos_data)
                if tiene_bloqueos:
                    gantt, result = round_robin_blocking(procesos, quantum)
                else:
                    gantt, result = round_robin(procesos, quantum)
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

        # Almacenar datos del gráfico para exportación
        self.current_gantt = gantt
        self.current_algorithm = algo
        self.current_metricas = metricas
        self.current_trm = trm
        self.current_tem = tem
        
        # Obtener quantum si es Round Robin
        if algo == "Round Robin":
            self.current_quantum = self._get_quantum()
        else:
            self.current_quantum = None
        
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

        # Ajustar el tamaño del gráfico según el número de procesos y duración total
        num_procesos = len(set(pid for pid, _, _, tipo in norm if pid != "IDLE"))
        max_time = max(end for _, _, end, _ in norm) if norm else 1
        
        # Calcular dimensiones adaptativas - más ancho para mostrar todos los ticks
        fig_width = max(15, max_time * 0.25)  # Ancho basado en duración total, más generoso
        fig_height = max(4, num_procesos * 0.8)  # Altura basada en número de procesos
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        
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
                alpha = 0.7
            elif tipo == "BLOCK":
                color = "darkred"
                hatch = "///"
                y = y_positions.get(pid, 0)
                alpha = 0.8
            else:  # CPU
                if pid not in colors:
                    colors[pid] = color_palette(len(colors))
                color = colors[pid]
                hatch = None
                y = y_positions.get(pid, 0)
                alpha = 1.0

            ax.barh(y, end - start, left=start, height=0.6, color=color, 
                   edgecolor='black', hatch=hatch, alpha=alpha)
            
            if tipo != "IDLE":
                # Mostrar el PID y el tipo de ráfaga
                text = f"{pid}\n({tipo})" if tipo == "BLOCK" else str(pid)
                ax.text((start + end) / 2, y, text, ha='center', va='center',
                        fontsize=7, color="white" if tipo == "BLOCK" else "black",
                        weight="bold" if tipo == "BLOCK" else "normal")

        if procesos_unicos:
            ax.set_yticks(list(y_positions.values()))
            ax.set_yticklabels(list(y_positions.keys()))
        else:
            ax.set_yticks([])

        if norm:
            max_time = max(end for _, _, end, _ in norm)
            
            # Mostrar TODOS los ticks del 0 al tiempo máximo
            ax.set_xticks(range(0, max_time + 1))
            ax.set_xlim(0, max_time)
        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Procesos")
        ax.set_title(f"Diagrama de Gantt - {algo}")
        ax.grid(True, axis='x', linestyle='--', alpha=0.6)
        
        # Agregar leyenda explicativa
        legend_elements = [
            plt.Rectangle((0,0),1,1, facecolor='lightblue', edgecolor='black', label='CPU'),
            plt.Rectangle((0,0),1,1, facecolor='darkred', edgecolor='black', hatch='///', label='Bloqueo (E/S)'),
            plt.Rectangle((0,0),1,1, facecolor='lightgray', edgecolor='black', alpha=0.7, label='IDLE')
        ]
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1))

        # Ajustar el layout para mejor uso del espacio
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.frame_gantt)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Almacenar la figura para exportación
        self.current_fig = fig
        
        # Configurar scroll horizontal si es necesario
        if fig_width > 15:
            # Para gráficos muy anchos, permitir scroll horizontal
            canvas.get_tk_widget().configure(scrollregion=canvas.get_tk_widget().bbox("all"))

    def _export_png(self):
        """Exporta el gráfico actual como PNG."""
        if self.current_fig is None:
            messagebox.showwarning("Advertencia", "No hay gráfico para exportar. Ejecute un algoritmo primero.")
            return
        
        try:
            from tkinter import filedialog
            import os
            from datetime import datetime
            
            # Generar nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"gantt_{self.current_algorithm}_{timestamp}.png"
            
            # Abrir diálogo para seleccionar ubicación
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                initialfile=default_filename,
                title="Guardar gráfico como PNG"
            )
            
            if file_path:
                # Exportar con alta resolución
                self.current_fig.savefig(file_path, dpi=300, bbox_inches='tight', 
                                       facecolor='white', edgecolor='none')
                messagebox.showinfo("Éxito", f"Gráfico exportado exitosamente:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar el gráfico:\n{str(e)}")

    def _export_excel(self):
        """Exporta los resultados actuales a un archivo Excel."""
        if (self.current_gantt is None or self.current_algorithm is None or 
            self.current_metricas is None):
            messagebox.showwarning("Advertencia", "No hay datos para exportar. Ejecute un algoritmo primero.")
            return
        
        try:
            from tkinter import filedialog
            import os
            from datetime import datetime
            
            # Generar nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"resultados_{self.current_algorithm}_{timestamp}.xlsx"
            
            # Abrir diálogo para seleccionar ubicación
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=default_filename,
                title="Guardar resultados como Excel"
            )
            
            if file_path:
                # Crear archivo temporal
                temp_file = exportar_a_excel(
                    procesos_data=self.procesos_data,
                    algoritmo=self.current_algorithm,
                    gantt_data=self.current_gantt,
                    metricas=self.current_metricas,
                    trm=self.current_trm,
                    tem=self.current_tem,
                    quantum=self.current_quantum
                )
                
                # Mover el archivo a la ubicación seleccionada
                import shutil
                shutil.move(temp_file, file_path)
                
                messagebox.showinfo("Éxito", f"Resultados exportados exitosamente a:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar a Excel:\n{str(e)}")

    def _salir(self):
        self.master.destroy()