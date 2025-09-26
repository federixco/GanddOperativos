import customtkinter as ctk
from tkinter import messagebox, ttk
from utils import historial

class DataInputScreen(ctk.CTkFrame):
    def __init__(self, master, nombres_procesos, on_continue):
        super().__init__(master)
        self.nombres_procesos = nombres_procesos
        self.on_continue = on_continue

        # Estructura de datos para múltiples ráfagas
        self.process_data = {}  # {nombre: {"arrival": int, "priority": int, "bursts": [int, int, ...]}}
        
        self.label_title = ctk.CTkLabel(self, text="Ingresar datos de procesos", font=("Arial", 18, "bold"))
        self.label_title.pack(pady=20)

        # Frame con scroll para muchos procesos
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=400)
        self.scroll_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self._build_rows()

        # Barra inferior (solo guardar + continuar)
        btn_historial_frame = ctk.CTkFrame(self)
        btn_historial_frame.pack(pady=10)
        
        self.btn_save_config = ctk.CTkButton(
            btn_historial_frame,
            text="Guardar configuración",
            command=self._guardar_configuracion,
            fg_color="blue",
            hover_color="#003366"
        )
        self.btn_save_config.pack(side="left", padx=5)

        self.btn_continue = ctk.CTkButton(self, text="Continuar", command=self._continue_clicked)
        self.btn_continue.pack(pady=20)

    def _build_rows(self):
        for nombre in self.nombres_procesos:
            self.process_data[nombre] = {
                "arrival": None,
                "priority": 0,
                "bursts": []
            }
            process_frame = ctk.CTkFrame(self.scroll_frame)
            process_frame.pack(pady=10, fill="x", padx=5)
            title_frame = ctk.CTkFrame(process_frame)
            title_frame.pack(fill="x", padx=5, pady=5)
            ctk.CTkLabel(title_frame, text=f"Proceso: {nombre}", font=("Arial", 14, "bold")).pack(side="left")

            # llegada
            arrival_frame = ctk.CTkFrame(process_frame); arrival_frame.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(arrival_frame, text="Tiempo de llegada:", width=120).pack(side="left", padx=5)
            arrival_entry = ctk.CTkEntry(arrival_frame, placeholder_text="Ej: 0", width=80)
            arrival_entry.pack(side="left", padx=5)

            # prioridad
            priority_frame = ctk.CTkFrame(process_frame); priority_frame.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(priority_frame, text="Prioridad (0-9):", width=120).pack(side="left", padx=5)
            priority_entry = ctk.CTkEntry(priority_frame, placeholder_text="Ej: 5", width=80)
            priority_entry.pack(side="left", padx=5)
            ctk.CTkLabel(priority_frame, text="(9=mayor, 0=menor)", font=("Arial", 10), text_color="gray").pack(side="left", padx=10)

            # ráfagas
            bursts_frame = ctk.CTkFrame(process_frame); bursts_frame.pack(fill="x", padx=5, pady=5)
            ctk.CTkLabel(bursts_frame, text="Secuencia de ráfagas:", font=("Arial", 12, "bold")).pack(anchor="w", padx=5, pady=2)

            controls_frame = ctk.CTkFrame(bursts_frame); controls_frame.pack(fill="x", padx=5, pady=2)
            add_btn = ctk.CTkButton(controls_frame, text="+ Agregar ráfaga", width=120, command=lambda n=nombre: self._add_burst(n))
            add_btn.pack(side="left", padx=5)

            bursts_display_frame = ctk.CTkFrame(bursts_frame); bursts_display_frame.pack(fill="x", padx=5, pady=5)

            self.process_data[nombre]["arrival_entry"] = arrival_entry
            self.process_data[nombre]["priority_entry"] = priority_entry
            self.process_data[nombre]["bursts_display_frame"] = bursts_display_frame
            self.process_data[nombre]["burst_entries"] = []

            # primera CPU por defecto
            self._add_burst(nombre, burst_type="CPU")

    def _add_burst(self, process_name, burst_type=None):
        process_info = self.process_data[process_name]
        burst_entries = process_info["burst_entries"]
        display_frame = process_info["bursts_display_frame"]
        if burst_type is None:
            if not burst_entries:
                burst_type = "CPU"
            else:
                last_type = burst_entries[-1]["type"]
                burst_type = "Bloqueo" if last_type == "CPU" else "CPU"

        burst_frame = ctk.CTkFrame(display_frame); burst_frame.pack(fill="x", padx=2, pady=2)
        ctk.CTkLabel(burst_frame, text=f"{burst_type}:", width=80).pack(side="left", padx=5)
        burst_entry = ctk.CTkEntry(burst_frame, placeholder_text=f"Duración {burst_type}", width=100)
        burst_entry.pack(side="left", padx=5)
        remove_btn = ctk.CTkButton(burst_frame, text="✕", width=30, height=25,
                                   command=lambda: self._remove_burst(process_name, burst_frame))
        remove_btn.pack(side="left", padx=5)

        burst_entries.append({"frame": burst_frame, "entry": burst_entry, "type": burst_type})
        self._update_sequence_display(process_name)

    def _remove_burst(self, process_name, burst_frame):
        process_info = self.process_data[process_name]
        burst_entries = process_info["burst_entries"]
        for i, b in enumerate(burst_entries):
            if b["frame"] == burst_frame:
                burst_entries.pop(i)
                burst_frame.destroy()
                break
        self._update_sequence_display(process_name)

    def _update_sequence_display(self, process_name):
        process_info = self.process_data[process_name]
        burst_entries = process_info["burst_entries"]
        if burst_entries:
            parts = [f"{b['type']}{i+1}" for i, b in enumerate(burst_entries)]
            seq = " → ".join(parts)
        else:
            seq = "Sin ráfagas"
        if "sequence_label" not in process_info:
            lbl = ctk.CTkLabel(process_info["bursts_display_frame"], text=f"Secuencia: {seq}", font=("Arial", 10, "italic"))
            lbl.pack(anchor="w", padx=5, pady=2)
            process_info["sequence_label"] = lbl
        else:
            process_info["sequence_label"].configure(text=f"Secuencia: {seq}")

    def _continue_clicked(self):
        procesos_data = []
        try:
            for nombre in self.nombres_procesos:
                info = self.process_data[nombre]
                arrival_str = info["arrival_entry"].get().strip()
                if not arrival_str:
                    raise ValueError(f"Proceso {nombre}: Tiempo de llegada requerido")
                arrival_time = int(arrival_str)
                if arrival_time < 0:
                    raise ValueError(f"Proceso {nombre}: Tiempo de llegada debe ser ≥ 0")

                priority_str = info["priority_entry"].get().strip()
                priority = int(priority_str) if priority_str else 0
                if priority < 0 or priority > 9:
                    raise ValueError(f"Proceso {nombre}: Prioridad debe estar entre 0 y 9")

                burst_entries = info["burst_entries"]
                if not burst_entries:
                    raise ValueError(f"Proceso {nombre}: Debe tener al menos una ráfaga")

                bursts = []
                for b in burst_entries:
                    s = b["entry"].get().strip()
                    if not s:
                        raise ValueError(f"Proceso {nombre}: Todas las duraciones son requeridas")
                    d = int(s)
                    if d < 0:
                        raise ValueError(f"Proceso {nombre}: Las duraciones deben ser ≥ 0")
                    bursts.append(d)

                # si termina en BLOQ, agregar CPU=0 para cerrar
                if len(bursts) % 2 == 1:
                    bursts.append(0)

                cpu_bursts = [bursts[i] for i in range(0, len(bursts), 2)]
                if not any(c > 0 for c in cpu_bursts):
                    raise ValueError(f"Proceso {nombre}: Debe tener al menos una ráfaga de CPU > 0")

                procesos_data.append({
                    "pid": nombre,
                    "arrival_time": arrival_time,
                    "priority": priority,
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
        dialog = ctk.CTkToplevel(self)
        dialog.title("Guardar configuración")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("+%d+%d" % (self.winfo_rootx() + 50, self.winfo_rooty() + 50))

        main = ctk.CTkFrame(dialog); main.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(main, text="Nombre de la configuración:", font=("Arial", 12)).pack(pady=(0, 10))
        entry_nombre = ctk.CTkEntry(main, placeholder_text="Ej: Configuración 3 procesos", width=300)
        entry_nombre.pack(pady=(0, 20)); entry_nombre.focus()

        btns = ctk.CTkFrame(main); btns.pack()

        def guardar():
            nombre_cfg = entry_nombre.get().strip()
            if not nombre_cfg:
                messagebox.showerror("Error", "Ingrese un nombre para la configuración")
                return
            try:
                config_procesos = []
                for nombre_proceso in self.nombres_procesos:
                    info = self.process_data[nombre_proceso]
                    arrival = int(info["arrival_entry"].get().strip() or 0)
                    priority = int(info["priority_entry"].get().strip() or 0)
                    bursts = []
                    for b in info["burst_entries"]:
                        bursts.append(int(b["entry"].get().strip() or 0))
                    config_procesos.append({
                        "nombre": nombre_proceso,
                        "arrival": arrival,
                        "priority": priority,
                        "bursts": bursts
                    })
                historial.guardar_input_config(nombre_cfg, config_procesos)
                messagebox.showinfo("Éxito", f"Configuración '{nombre_cfg}' guardada.")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}")

        ctk.CTkButton(btns, text="Guardar", command=guardar, fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Cancelar", command=dialog.destroy).pack(side="left", padx=5)
        entry_nombre.bind("<Return>", lambda e: guardar())
