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
        
        # Variables para el zoom
        self.zoom_level = 1.0
        self.original_xlim = None
        self.original_ylim = None
        self.current_ax = None
        self.current_canvas = None
        
        # Variables para el pan (arrastrar)
        self.pan_start_x = None
        self.pan_start_y = None
        self.is_panning = False

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

        # --- Controles de zoom ---
        zoom_frame = ctk.CTkFrame(self)
        zoom_frame.pack(pady=5)
        
        self.label_zoom = ctk.CTkLabel(zoom_frame, text="Zoom:", font=("Arial", 12, "bold"))
        self.label_zoom.pack(side="left", padx=5)
        
        self.btn_zoom_out = ctk.CTkButton(zoom_frame, text="−", command=self._zoom_out, 
                                        width=30, height=30, font=("Arial", 16, "bold"))
        self.btn_zoom_out.pack(side="left", padx=2)
        
        self.label_zoom_level = ctk.CTkLabel(zoom_frame, text="100%", font=("Arial", 12))
        self.label_zoom_level.pack(side="left", padx=5)
        
        self.btn_zoom_in = ctk.CTkButton(zoom_frame, text="+", command=self._zoom_in, 
                                       width=30, height=30, font=("Arial", 16, "bold"))
        self.btn_zoom_in.pack(side="left", padx=2)
        
        self.btn_zoom_reset = ctk.CTkButton(zoom_frame, text="Reset", command=self._zoom_reset, 
                                          width=50, height=30, fg_color="orange", hover_color="#cc6600")
        self.btn_zoom_reset.pack(side="left", padx=5)
        
        self.btn_open_window = ctk.CTkButton(zoom_frame, text="Abrir en Ventana", 
                                           command=self._open_in_window, 
                                           width=120, height=30, 
                                           fg_color="purple", hover_color="#660066")
        self.btn_open_window.pack(side="left", padx=5)
        
        # Etiqueta informativa
        self.label_zoom_info = ctk.CTkLabel(zoom_frame, 
                                          text="💡 Rueda: Zoom | Click+Arrastrar: Mover", 
                                          font=("Arial", 10), text_color="gray")
        self.label_zoom_info.pack(side="left", padx=10)

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
        
        # Crear canvas directamente en el frame
        canvas = FigureCanvasTkAgg(fig, master=self.frame_gantt)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Almacenar la figura y canvas para zoom
        self.current_fig = fig
        self.current_ax = ax
        self.current_canvas = canvas
        
        # Guardar los límites originales para el zoom
        self.original_xlim = ax.get_xlim()
        self.original_ylim = ax.get_ylim()
        
        # Resetear el nivel de zoom
        self.zoom_level = 1.0
        self._update_zoom_label()
        
        # Variables para el pan (arrastrar)
        self.pan_start_x = None
        self.pan_start_y = None
        self.is_panning = False
        
        # Configurar eventos de mouse
        canvas.mpl_connect("scroll_event", self._on_mouse_wheel)
        canvas.mpl_connect("button_press_event", self._on_mouse_press)
        canvas.mpl_connect("button_release_event", self._on_mouse_release)
        canvas.mpl_connect("motion_notify_event", self._on_mouse_motion)

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

    def _zoom_in(self):
        """Aumenta el nivel de zoom del gráfico."""
        if self.current_ax is None:
            return
        
        self.zoom_level *= 1.2
        self._apply_zoom()
        self._update_zoom_label()

    def _zoom_out(self):
        """Disminuye el nivel de zoom del gráfico."""
        if self.current_ax is None:
            return
        
        self.zoom_level /= 1.2
        self._apply_zoom()
        self._update_zoom_label()

    def _zoom_reset(self):
        """Resetea el zoom a la vista original."""
        if self.current_ax is None or self.original_xlim is None or self.original_ylim is None:
            return
        
        self.zoom_level = 1.0
        self.current_ax.set_xlim(self.original_xlim)
        self.current_ax.set_ylim(self.original_ylim)
        self.current_canvas.draw()
        self._update_zoom_label()
        
        # Resetear variables de pan
        self.is_panning = False
        self.pan_start_x = None
        self.pan_start_y = None

    def _apply_zoom(self):
        """Aplica el nivel de zoom actual al gráfico."""
        if self.current_ax is None or self.original_xlim is None or self.original_ylim is None:
            return
        
        # Calcular los nuevos límites basados en el zoom
        x_center = (self.original_xlim[0] + self.original_xlim[1]) / 2
        y_center = (self.original_ylim[0] + self.original_ylim[1]) / 2
        
        x_range = (self.original_xlim[1] - self.original_xlim[0]) / self.zoom_level
        y_range = (self.original_ylim[1] - self.original_ylim[0]) / self.zoom_level
        
        new_xlim = (x_center - x_range/2, x_center + x_range/2)
        new_ylim = (y_center - y_range/2, y_center + y_range/2)
        
        self.current_ax.set_xlim(new_xlim)
        self.current_ax.set_ylim(new_ylim)
        self.current_canvas.draw()

    def _update_zoom_label(self):
        """Actualiza la etiqueta que muestra el nivel de zoom actual."""
        self.label_zoom_level.configure(text=f"{int(self.zoom_level * 100)}%")

    def _on_mouse_wheel(self, event):
        """Maneja el evento de la rueda del mouse para zoom."""
        if self.current_ax is None:
            return
        
        # Determinar si hacer zoom in o out
        # Manejar diferentes plataformas (Windows usa delta, Linux/Mac usan step)
        delta = getattr(event, 'delta', None)
        if delta is None:
            delta = getattr(event, 'step', 0)
        
        if delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    def _on_mouse_press(self, event):
        """Maneja el evento de presionar el botón del mouse para iniciar pan."""
        if self.current_ax is None or event.inaxes != self.current_ax:
            return
        
        if event.button == 1:  # Botón izquierdo del mouse
            self.is_panning = True
            self.pan_start_x = event.xdata
            self.pan_start_y = event.ydata
            # Cambiar el cursor para indicar que se puede arrastrar
            self.current_canvas.get_tk_widget().configure(cursor="fleur")

    def _on_mouse_release(self, event):
        """Maneja el evento de soltar el botón del mouse para terminar pan."""
        if self.current_ax is None:
            return
        
        if event.button == 1:  # Botón izquierdo del mouse
            self.is_panning = False
            self.pan_start_x = None
            self.pan_start_y = None
            # Restaurar el cursor normal
            self.current_canvas.get_tk_widget().configure(cursor="")

    def _on_mouse_motion(self, event):
        """Maneja el movimiento del mouse para pan."""
        if (self.current_ax is None or not self.is_panning or 
            event.inaxes != self.current_ax or 
            self.pan_start_x is None or self.pan_start_y is None):
            return
        
        # Calcular el desplazamiento
        dx = event.xdata - self.pan_start_x
        dy = event.ydata - self.pan_start_y
        
        # Obtener los límites actuales
        xlim = self.current_ax.get_xlim()
        ylim = self.current_ax.get_ylim()
        
        # Aplicar el desplazamiento
        new_xlim = (xlim[0] - dx, xlim[1] - dx)
        new_ylim = (ylim[0] - dy, ylim[1] - dy)
        
        # Actualizar los límites
        self.current_ax.set_xlim(new_xlim)
        self.current_ax.set_ylim(new_ylim)
        self.current_canvas.draw()
        
        # Actualizar la posición de inicio para el siguiente movimiento
        self.pan_start_x = event.xdata
        self.pan_start_y = event.ydata

    def _open_in_window(self):
        """Abre el gráfico actual en una ventana separada."""
        if self.current_gantt is None or self.current_algorithm is None:
            messagebox.showwarning("Advertencia", "No hay gráfico para abrir. Ejecute un algoritmo primero.")
            return
        
        # Crear y mostrar la ventana separada
        GanttWindow(self.current_gantt, self.current_algorithm)


class GanttWindow:
    """Ventana separada para mostrar el diagrama de Gantt con zoom y pan."""
    
    def __init__(self, gantt_chart, algorithm):
        self.gantt_chart = gantt_chart
        self.algorithm = algorithm
        
        # Crear ventana
        self.window = ctk.CTkToplevel()
        self.window.title(f"Diagrama de Gantt - {algorithm}")
        self.window.geometry("1200x800")
        self.window.resizable(True, True)
        
        # Variables para zoom y pan
        self.zoom_level = 1.0
        self.original_xlim = None
        self.original_ylim = None
        self.current_ax = None
        self.current_canvas = None
        self.pan_start_x = None
        self.pan_start_y = None
        self.is_panning = False
        
        self._create_interface()
        self._create_gantt()
        
        # Centrar la ventana
        self.window.transient()
        self.window.grab_set()
        
    def _create_interface(self):
        """Crea la interfaz de la ventana."""
        # Frame de controles
        control_frame = ctk.CTkFrame(self.window)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Título
        title_label = ctk.CTkLabel(control_frame, text=f"Diagrama de Gantt - {self.algorithm}", 
                                 font=("Arial", 16, "bold"))
        title_label.pack(side="left", padx=10)
        
        # Controles de zoom
        zoom_frame = ctk.CTkFrame(control_frame)
        zoom_frame.pack(side="right", padx=10)
        
        ctk.CTkLabel(zoom_frame, text="Zoom:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        
        btn_zoom_out = ctk.CTkButton(zoom_frame, text="−", command=self._zoom_out, 
                                   width=30, height=30, font=("Arial", 16, "bold"))
        btn_zoom_out.pack(side="left", padx=2)
        
        self.label_zoom_level = ctk.CTkLabel(zoom_frame, text="100%", font=("Arial", 12))
        self.label_zoom_level.pack(side="left", padx=5)
        
        btn_zoom_in = ctk.CTkButton(zoom_frame, text="+", command=self._zoom_in, 
                                  width=30, height=30, font=("Arial", 16, "bold"))
        btn_zoom_in.pack(side="left", padx=2)
        
        btn_zoom_reset = ctk.CTkButton(zoom_frame, text="Reset", command=self._zoom_reset, 
                                     width=50, height=30, fg_color="orange", hover_color="#cc6600")
        btn_zoom_reset.pack(side="left", padx=5)
        
        # Frame para el gráfico
        self.graph_frame = ctk.CTkFrame(self.window)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
    def _create_gantt(self):
        """Crea el diagrama de Gantt en la ventana."""
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        # Normalizar datos del gantt
        norm = []
        for seg in self.gantt_chart:
            if len(seg) == 3:
                pid, start, end = seg
                tipo = "CPU" if pid != "IDLE" else "IDLE"
                norm.append((pid, start, end, tipo))
            elif len(seg) == 4:
                norm.append(seg)

        # Calcular dimensiones
        num_procesos = len(set(pid for pid, _, _, tipo in norm if pid != "IDLE"))
        max_time = max(end for _, _, end, _ in norm) if norm else 1
        
        fig_width = max(15, max_time * 0.25)
        fig_height = max(6, num_procesos * 0.8)
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        
        # Procesar datos
        procesos_unicos = [pid for pid, _, _, tipo in norm if pid != "IDLE"]
        procesos_unicos = list(dict.fromkeys(procesos_unicos))
        y_positions = {pid: i for i, pid in enumerate(procesos_unicos)}

        colors = {}
        color_palette = plt.cm.get_cmap("tab20", len(procesos_unicos) + 1)

        # Dibujar barras
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
                text = f"{pid}\n({tipo})" if tipo == "BLOCK" else str(pid)
                ax.text((start + end) / 2, y, text, ha='center', va='center',
                        fontsize=7, color="white" if tipo == "BLOCK" else "black",
                        weight="bold" if tipo == "BLOCK" else "normal")

        # Configurar ejes
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
        ax.set_title(f"Diagrama de Gantt - {self.algorithm}")
        ax.grid(True, axis='x', linestyle='--', alpha=0.6)
        
        # Leyenda
        legend_elements = [
            plt.Rectangle((0,0),1,1, facecolor='lightblue', edgecolor='black', label='CPU'),
            plt.Rectangle((0,0),1,1, facecolor='darkred', edgecolor='black', hatch='///', label='Bloqueo (E/S)'),
            plt.Rectangle((0,0),1,1, facecolor='lightgray', edgecolor='black', alpha=0.7, label='IDLE')
        ]
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1))

        plt.tight_layout()
        
        # Crear canvas
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Almacenar referencias
        self.current_fig = fig
        self.current_ax = ax
        self.current_canvas = canvas
        self.original_xlim = ax.get_xlim()
        self.original_ylim = ax.get_ylim()
        
        # Configurar eventos de mouse
        canvas.mpl_connect("scroll_event", self._on_mouse_wheel)
        canvas.mpl_connect("button_press_event", self._on_mouse_press)
        canvas.mpl_connect("button_release_event", self._on_mouse_release)
        canvas.mpl_connect("motion_notify_event", self._on_mouse_motion)
        
    def _zoom_in(self):
        """Aumenta el nivel de zoom del gráfico."""
        if self.current_ax is None:
            return
        self.zoom_level *= 1.2
        self._apply_zoom()
        self._update_zoom_label()

    def _zoom_out(self):
        """Disminuye el nivel de zoom del gráfico."""
        if self.current_ax is None:
            return
        self.zoom_level /= 1.2
        self._apply_zoom()
        self._update_zoom_label()

    def _zoom_reset(self):
        """Resetea el zoom a la vista original."""
        if self.current_ax is None or self.original_xlim is None or self.original_ylim is None:
            return
        self.zoom_level = 1.0
        self.current_ax.set_xlim(self.original_xlim)
        self.current_ax.set_ylim(self.original_ylim)
        self.current_canvas.draw()
        self._update_zoom_label()
        self.is_panning = False
        self.pan_start_x = None
        self.pan_start_y = None

    def _apply_zoom(self):
        """Aplica el nivel de zoom actual al gráfico."""
        if self.current_ax is None or self.original_xlim is None or self.original_ylim is None:
            return
        x_center = (self.original_xlim[0] + self.original_xlim[1]) / 2
        y_center = (self.original_ylim[0] + self.original_ylim[1]) / 2
        x_range = (self.original_xlim[1] - self.original_xlim[0]) / self.zoom_level
        y_range = (self.original_ylim[1] - self.original_ylim[0]) / self.zoom_level
        new_xlim = (x_center - x_range/2, x_center + x_range/2)
        new_ylim = (y_center - y_range/2, y_center + y_range/2)
        self.current_ax.set_xlim(new_xlim)
        self.current_ax.set_ylim(new_ylim)
        self.current_canvas.draw()

    def _update_zoom_label(self):
        """Actualiza la etiqueta que muestra el nivel de zoom actual."""
        self.label_zoom_level.configure(text=f"{int(self.zoom_level * 100)}%")

    def _on_mouse_wheel(self, event):
        """Maneja el evento de la rueda del mouse para zoom."""
        if self.current_ax is None:
            return
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    def _on_mouse_press(self, event):
        """Maneja el evento de presionar el botón del mouse para iniciar pan."""
        if self.current_ax is None or event.inaxes != self.current_ax:
            return
        if event.button == 1:
            self.is_panning = True
            self.pan_start_x = event.xdata
            self.pan_start_y = event.ydata
            self.current_canvas.get_tk_widget().configure(cursor="fleur")

    def _on_mouse_release(self, event):
        """Maneja el evento de soltar el botón del mouse para terminar pan."""
        if self.current_ax is None:
            return
        if event.button == 1:
            self.is_panning = False
            self.pan_start_x = None
            self.pan_start_y = None
            self.current_canvas.get_tk_widget().configure(cursor="")

    def _on_mouse_motion(self, event):
        """Maneja el movimiento del mouse para pan."""
        if (self.current_ax is None or not self.is_panning or 
            event.inaxes != self.current_ax or 
            self.pan_start_x is None or self.pan_start_y is None):
            return
        dx = event.xdata - self.pan_start_x
        dy = event.ydata - self.pan_start_y
        xlim = self.current_ax.get_xlim()
        ylim = self.current_ax.get_ylim()
        new_xlim = (xlim[0] - dx, xlim[1] - dx)
        new_ylim = (ylim[0] - dy, ylim[1] - dy)
        self.current_ax.set_xlim(new_xlim)
        self.current_ax.set_ylim(new_ylim)
        self.current_canvas.draw()
        self.pan_start_x = event.xdata
        self.pan_start_y = event.ydata