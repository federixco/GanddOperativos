import customtkinter as ctk
from tkinter import messagebox

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
