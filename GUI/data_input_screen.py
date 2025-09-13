import customtkinter as ctk
from tkinter import messagebox, ttk
from utils import historial

class DataInputScreen(ctk.CTkFrame):
    def __init__(self, master, nombres_procesos, on_continue):
        super().__init__(master)
        self.nombres_procesos = nombres_procesos
        self.on_continue = on_continue

        # Estructura de datos para múltiples ráfagas
        self.process_data = {}  # {nombre: {"arrival": int, "bursts": [int, int, ...]}}
        
        self.label_title = ctk.CTkLabel(self, text="Ingresar datos de procesos", font=("Arial", 18, "bold"))
        self.label_title.pack(pady=20)

        # Frame con scroll para muchos procesos
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=400)
        self.scroll_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self._build_rows()

        # Botones de historial
        btn_historial_frame = ctk.CTkFrame(self)
        btn_historial_frame.pack(pady=10)
        
        self.btn_save_config = ctk.CTkButton(btn_historial_frame, text="Guardar configuración", 
                                           command=self._guardar_configuracion, fg_color="blue", hover_color="#003366")
        self.btn_save_config.pack(side="left", padx=5)
        
        self.btn_load_config = ctk.CTkButton(btn_historial_frame, text="Cargar configuración", 
                                           command=self._cargar_configuracion, fg_color="orange", hover_color="#cc6600")
        self.btn_load_config.pack(side="left", padx=5)

        self.btn_continue = ctk.CTkButton(self, text="Continuar", command=self._continue_clicked)
        self.btn_continue.pack(pady=20)

    def _build_rows(self):
        for nombre in self.nombres_procesos:
            # Inicializar datos del proceso
            self.process_data[nombre] = {
                "arrival": None,
                "bursts": []
            }
            
            # Frame principal del proceso
            process_frame = ctk.CTkFrame(self.scroll_frame)
            process_frame.pack(pady=10, fill="x", padx=5)
            
            # Título del proceso
            title_frame = ctk.CTkFrame(process_frame)
            title_frame.pack(fill="x", padx=5, pady=5)
            
            ctk.CTkLabel(title_frame, text=f"Proceso: {nombre}", font=("Arial", 14, "bold")).pack(side="left")
            
            # Tiempo de llegada
            arrival_frame = ctk.CTkFrame(process_frame)
            arrival_frame.pack(fill="x", padx=5, pady=2)
            
            ctk.CTkLabel(arrival_frame, text="Tiempo de llegada:", width=120).pack(side="left", padx=5)
            arrival_entry = ctk.CTkEntry(arrival_frame, placeholder_text="Ej: 0", width=80)
            arrival_entry.pack(side="left", padx=5)
            
            # Frame para las ráfagas
            bursts_frame = ctk.CTkFrame(process_frame)
            bursts_frame.pack(fill="x", padx=5, pady=5)
            
            ctk.CTkLabel(bursts_frame, text="Secuencia de ráfagas:", font=("Arial", 12, "bold")).pack(anchor="w", padx=5, pady=2)
            
            # Frame para los controles de ráfagas
            controls_frame = ctk.CTkFrame(bursts_frame)
            controls_frame.pack(fill="x", padx=5, pady=2)
            
            # Botón para agregar ráfaga
            add_btn = ctk.CTkButton(controls_frame, text="+ Agregar ráfaga", width=120, 
                                   command=lambda n=nombre: self._add_burst(n))
            add_btn.pack(side="left", padx=5)
            
            # Frame para mostrar las ráfagas
            bursts_display_frame = ctk.CTkFrame(bursts_frame)
            bursts_display_frame.pack(fill="x", padx=5, pady=5)
            
            # Almacenar referencias para este proceso
            self.process_data[nombre]["arrival_entry"] = arrival_entry
            self.process_data[nombre]["bursts_display_frame"] = bursts_display_frame
            self.process_data[nombre]["burst_entries"] = []
            
            # Agregar primera ráfaga de CPU por defecto
            self._add_burst(nombre, burst_type="CPU")

    def _add_burst(self, process_name, burst_type=None):
        """Agrega una nueva ráfaga al proceso especificado."""
        process_info = self.process_data[process_name]
        burst_entries = process_info["burst_entries"]
        display_frame = process_info["bursts_display_frame"]
        
        # Determinar el tipo de ráfaga si no se especifica
        if burst_type is None:
            # Si no hay ráfagas, empezar con CPU
            if not burst_entries:
                burst_type = "CPU"
            else:
                # Alternar entre CPU y Bloqueo
                last_type = burst_entries[-1]["type"]
                burst_type = "Bloqueo" if last_type == "CPU" else "CPU"
        
        # Frame para esta ráfaga
        burst_frame = ctk.CTkFrame(display_frame)
        burst_frame.pack(fill="x", padx=2, pady=2)
        
        # Tipo de ráfaga
        type_label = ctk.CTkLabel(burst_frame, text=f"{burst_type}:", width=80)
        type_label.pack(side="left", padx=5)
        
        # Campo de entrada
        burst_entry = ctk.CTkEntry(burst_frame, placeholder_text=f"Duración {burst_type}", width=100)
        burst_entry.pack(side="left", padx=5)
        
        # Botón para eliminar
        remove_btn = ctk.CTkButton(burst_frame, text="✕", width=30, height=25,
                                  command=lambda: self._remove_burst(process_name, burst_frame))
        remove_btn.pack(side="left", padx=5)
        
        # Almacenar información de la ráfaga
        burst_info = {
            "frame": burst_frame,
            "entry": burst_entry,
            "type": burst_type
        }
        burst_entries.append(burst_info)
        
        # Actualizar la secuencia visual
        self._update_sequence_display(process_name)
    
    def _remove_burst(self, process_name, burst_frame):
        """Elimina una ráfaga del proceso especificado."""
        process_info = self.process_data[process_name]
        burst_entries = process_info["burst_entries"]
        
        # Encontrar y eliminar la ráfaga
        for i, burst_info in enumerate(burst_entries):
            if burst_info["frame"] == burst_frame:
                burst_entries.pop(i)
                burst_frame.destroy()
                break
        
        # Actualizar la secuencia visual
        self._update_sequence_display(process_name)
    
    def _update_sequence_display(self, process_name):
        """Actualiza la visualización de la secuencia de ráfagas."""
        process_info = self.process_data[process_name]
        burst_entries = process_info["burst_entries"]
        
        # Crear texto descriptivo de la secuencia
        if burst_entries:
            sequence_parts = []
            for i, burst_info in enumerate(burst_entries):
                sequence_parts.append(f"{burst_info['type']}{i+1}")
            sequence_text = " → ".join(sequence_parts)
        else:
            sequence_text = "Sin ráfagas"
        
        # Actualizar o crear label de secuencia
        if "sequence_label" not in process_info:
            sequence_label = ctk.CTkLabel(process_info["bursts_display_frame"], 
                                        text=f"Secuencia: {sequence_text}", 
                                        font=("Arial", 10, "italic"))
            sequence_label.pack(anchor="w", padx=5, pady=2)
            process_info["sequence_label"] = sequence_label
        else:
            process_info["sequence_label"].configure(text=f"Secuencia: {sequence_text}")

    def _continue_clicked(self):
        procesos_data = []
        try:
            for nombre in self.nombres_procesos:
                process_info = self.process_data[nombre]
                
                # Validar tiempo de llegada
                arrival_str = process_info["arrival_entry"].get().strip()
                if not arrival_str:
                    raise ValueError(f"Proceso {nombre}: Tiempo de llegada requerido")
                
                arrival_time = int(arrival_str)
                if arrival_time < 0:
                    raise ValueError(f"Proceso {nombre}: Tiempo de llegada debe ser ≥ 0")
                
                # Validar ráfagas
                burst_entries = process_info["burst_entries"]
                if not burst_entries:
                    raise ValueError(f"Proceso {nombre}: Debe tener al menos una ráfaga")
                
                bursts = []
                for burst_info in burst_entries:
                    duration_str = burst_info["entry"].get().strip()
                    if not duration_str:
                        raise ValueError(f"Proceso {nombre}: Todas las duraciones son requeridas")
                    
                    duration = int(duration_str)
                    if duration < 0:
                        raise ValueError(f"Proceso {nombre}: Las duraciones deben ser ≥ 0")
                    
                    bursts.append(duration)
                
                # Validar que termine con CPU (índice par)
                if len(bursts) % 2 == 0:
                    # Termina con CPU, está bien
                    pass
                else:
                    # Termina con bloqueo, agregar CPU de 0
                    bursts.append(0)
                
                # Validar que tenga al menos una ráfaga de CPU
                cpu_bursts = [bursts[i] for i in range(0, len(bursts), 2)]
                if not any(cpu > 0 for cpu in cpu_bursts):
                    raise ValueError(f"Proceso {nombre}: Debe tener al menos una ráfaga de CPU > 0")
                
                procesos_data.append({
                    "pid": nombre, 
                    "arrival_time": arrival_time, 
                    "bursts": bursts
                })

        except ValueError as e:
            messagebox.showerror("Error de validación", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {e}")
            return

        self.on_continue(procesos_data)

    def _guardar_configuracion(self):
        """Guarda la configuración actual de inputs."""
        # Crear ventana de diálogo para ingresar nombre
        dialog = ctk.CTkToplevel(self)
        dialog.title("Guardar configuración")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrar la ventana
        dialog.geometry("+%d+%d" % (self.winfo_rootx() + 50, self.winfo_rooty() + 50))
        
        # Frame principal
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Label y entry para el nombre
        label_nombre = ctk.CTkLabel(main_frame, text="Nombre de la configuración:", font=("Arial", 12))
        label_nombre.pack(pady=(0, 10))
        
        entry_nombre = ctk.CTkEntry(main_frame, placeholder_text="Ej: Configuración 3 procesos", width=300)
        entry_nombre.pack(pady=(0, 20))
        entry_nombre.focus()
        
        # Botones
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack()
        
        def guardar():
            nombre = entry_nombre.get().strip()
            if not nombre:
                messagebox.showerror("Error", "Debe ingresar un nombre para la configuración")
                return
            
            try:
                # Recopilar datos actuales
                config_procesos = []
                for nombre_proceso in self.nombres_procesos:
                    process_info = self.process_data[nombre_proceso]
                    
                    # Obtener tiempo de llegada
                    arrival_str = process_info["arrival_entry"].get().strip()
                    arrival = int(arrival_str) if arrival_str else 0
                    
                    # Obtener ráfagas
                    bursts = []
                    for burst_info in process_info["burst_entries"]:
                        duration_str = burst_info["entry"].get().strip()
                        duration = int(duration_str) if duration_str else 0
                        bursts.append(duration)
                    
                    config_procesos.append({
                        "nombre": nombre_proceso,
                        "arrival": arrival,
                        "bursts": bursts
                    })
                
                # Guardar en historial
                historial.guardar_input_config(nombre, config_procesos)
                
                messagebox.showinfo("Éxito", f"Configuración '{nombre}' guardada exitosamente")
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Error en los datos. Asegúrese de que todos los valores sean números válidos.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar la configuración: {e}")
        
        btn_guardar = ctk.CTkButton(btn_frame, text="Guardar", command=guardar, fg_color="green")
        btn_guardar.pack(side="left", padx=5)
        
        btn_cancelar = ctk.CTkButton(btn_frame, text="Cancelar", command=dialog.destroy)
        btn_cancelar.pack(side="left", padx=5)
        
        # Permitir guardar con Enter
        entry_nombre.bind("<Return>", lambda e: guardar())

    def _cargar_configuracion(self):
        """Carga una configuración guardada."""
        # Obtener lista de configuraciones guardadas
        configs = historial.listar_input_configs()
        
        if not configs:
            messagebox.showinfo("Información", "No hay configuraciones guardadas")
            return
        
        # Crear ventana de diálogo para seleccionar configuración
        dialog = ctk.CTkToplevel(self)
        dialog.title("Cargar configuración")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrar la ventana
        dialog.geometry("+%d+%d" % (self.winfo_rootx() + 50, self.winfo_rooty() + 50))
        
        # Frame principal
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        label_titulo = ctk.CTkLabel(main_frame, text="Seleccionar configuración a cargar:", font=("Arial", 14, "bold"))
        label_titulo.pack(pady=(0, 10))
        
        # Frame para la lista
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Crear Treeview para mostrar las configuraciones
        columns = ("Nombre", "Fecha", "Procesos")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # Configurar columnas
        tree.heading("Nombre", text="Nombre")
        tree.heading("Fecha", text="Fecha")
        tree.heading("Procesos", text="N° Procesos")
        
        tree.column("Nombre", width=300)
        tree.column("Fecha", width=150)
        tree.column("Procesos", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Llenar la lista
        for indice, nombre, fecha, num_procesos in configs:
            # Formatear fecha para mostrar
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(fecha)
                fecha_formateada = dt.strftime("%d/%m/%Y %H:%M")
            except:
                fecha_formateada = fecha
            
            tree.insert("", "end", values=(nombre, fecha_formateada, num_procesos), tags=(str(indice),))
        
        # Botones
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack()
        
        def cargar():
            seleccion = tree.selection()
            if not seleccion:
                messagebox.showwarning("Advertencia", "Seleccione una configuración para cargar")
                return
            
            # Obtener el índice de la configuración seleccionada
            item = tree.item(seleccion[0])
            indice = int(item['tags'][0])
            
            try:
                # Cargar la configuración
                config = historial.cargar_input_config(indice)
                if config is None:
                    messagebox.showerror("Error", "No se pudo cargar la configuración seleccionada")
                    return
                
                # Aplicar la configuración
                self._aplicar_configuracion(config)
                
                messagebox.showinfo("Éxito", f"Configuración '{config['nombre']}' cargada exitosamente")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar la configuración: {e}")
        
        def eliminar():
            seleccion = tree.selection()
            if not seleccion:
                messagebox.showwarning("Advertencia", "Seleccione una configuración para eliminar")
                return
            
            # Confirmar eliminación
            if not messagebox.askyesno("Confirmar", "¿Está seguro de que desea eliminar esta configuración?"):
                return
            
            # Obtener el índice de la configuración seleccionada
            item = tree.item(seleccion[0])
            indice = int(item['tags'][0])
            
            try:
                # Eliminar la configuración
                nombre_eliminado = historial.eliminar_input_config(indice)
                if nombre_eliminado:
                    # Actualizar la lista
                    tree.delete(seleccion[0])
                    messagebox.showinfo("Éxito", f"Configuración '{nombre_eliminado}' eliminada exitosamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar la configuración: {e}")
        
        btn_cargar = ctk.CTkButton(btn_frame, text="Cargar", command=cargar, fg_color="green")
        btn_cargar.pack(side="left", padx=5)
        
        btn_eliminar = ctk.CTkButton(btn_frame, text="Eliminar", command=eliminar, fg_color="red")
        btn_eliminar.pack(side="left", padx=5)
        
        btn_cancelar = ctk.CTkButton(btn_frame, text="Cancelar", command=dialog.destroy)
        btn_cancelar.pack(side="left", padx=5)

    def _aplicar_configuracion(self, config):
        """Aplica una configuración cargada a los campos de entrada."""
        try:
            # Limpiar todos los campos actuales
            self._limpiar_campos()
            
            # Aplicar los datos de cada proceso
            for proceso_config in config["procesos"]:
                nombre_proceso = proceso_config["nombre"]
                
                if nombre_proceso in self.process_data:
                    process_info = self.process_data[nombre_proceso]
                    
                    # Aplicar tiempo de llegada
                    if proceso_config["arrival"] is not None:
                        process_info["arrival_entry"].delete(0, "end")
                        process_info["arrival_entry"].insert(0, str(proceso_config["arrival"]))
                    
                    # Aplicar ráfagas
                    bursts = proceso_config["bursts"]
                    if bursts:
                        # Limpiar ráfagas existentes
                        for burst_info in process_info["burst_entries"][:]:
                            self._remove_burst(nombre_proceso, burst_info["frame"])
                        
                        # Añadir ráfagas de la configuración
                        for i, duration in enumerate(bursts):
                            # Determinar tipo de ráfaga (alternando CPU y Bloqueo)
                            burst_type = "CPU" if i % 2 == 0 else "Bloqueo"
                            self._add_burst(nombre_proceso, burst_type)
                            
                            # Establecer el valor
                            if process_info["burst_entries"]:
                                last_burst = process_info["burst_entries"][-1]
                                last_burst["entry"].delete(0, "end")
                                last_burst["entry"].insert(0, str(duration))
                        
        except Exception as e:
            messagebox.showerror("Error", f"Error al aplicar la configuración: {e}")

    def _limpiar_campos(self):
        """Limpia todos los campos de entrada."""
        for nombre_proceso in self.nombres_procesos:
            if nombre_proceso in self.process_data:
                process_info = self.process_data[nombre_proceso]
                
                # Limpiar tiempo de llegada
                process_info["arrival_entry"].delete(0, "end")
                
                # Limpiar ráfagas
                for burst_info in process_info["burst_entries"][:]:
                    self._remove_burst(nombre_proceso, burst_info["frame"])
