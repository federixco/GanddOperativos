import customtkinter as ctk
from tkinter import messagebox, ttk
from utils import historial

class DataInputScreen(ctk.CTkFrame):
    def __init__(self, master, nombres_procesos, on_continue):
        super().__init__(master)
        self.nombres_procesos = nombres_procesos
        self.on_continue = on_continue

        self.entries_ta = []
        self.entries_cpu1 = []
        self.entries_bloq = []
        self.entries_cpu2 = []
        self.check_vars = []  # Estado de cada checkbox

        self.label_title = ctk.CTkLabel(self, text="Ingresar datos de procesos", font=("Arial", 18, "bold"))
        self.label_title.pack(pady=20)

        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(padx=10, pady=10, fill="both", expand=True)

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
            row = ctk.CTkFrame(self.form_frame)
            row.pack(pady=5, fill="x")

            ctk.CTkLabel(row, text=nombre, width=80).pack(side="left", padx=5)

            ta = ctk.CTkEntry(row, placeholder_text="Llegada", width=60)
            ta.pack(side="left", padx=5)
            self.entries_ta.append(ta)

            cpu1 = ctk.CTkEntry(row, placeholder_text="CPU1", width=60)
            cpu1.pack(side="left", padx=5)
            self.entries_cpu1.append(cpu1)

            var = ctk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(row, text="Tiene bloqueo", variable=var,
                                  command=lambda v=var, r=row: self._toggle_block_fields(v, r))
            chk.pack(side="left", padx=5)
            self.check_vars.append(var)

            # Campos de bloqueo ocultos por defecto
            bloq = ctk.CTkEntry(row, placeholder_text="Bloqueo (E/S)", width=80)
            cpu2 = ctk.CTkEntry(row, placeholder_text="CPU2", width=60)
            self.entries_bloq.append(bloq)
            self.entries_cpu2.append(cpu2)

    def _toggle_block_fields(self, var, row):
        idx = self.check_vars.index(var)
        bloq = self.entries_bloq[idx]
        cpu2 = self.entries_cpu2[idx]
        if var.get():
            bloq.pack(side="left", padx=5)
            cpu2.pack(side="left", padx=5)
        else:
            bloq.pack_forget()
            cpu2.pack_forget()
            bloq.delete(0, "end")
            cpu2.delete(0, "end")

    def _continue_clicked(self):
        procesos_data = []
        try:
            for i, nombre in enumerate(self.nombres_procesos):
                ta_str = self.entries_ta[i].get().strip()
                cpu1_str = self.entries_cpu1[i].get().strip()

                if not ta_str or not cpu1_str:
                    raise ValueError

                ta = int(ta_str)
                cpu1 = int(cpu1_str)
                if ta < 0 or cpu1 <= 0:
                    raise ValueError

                bursts = [cpu1]

                if self.check_vars[i].get():
                    bloq_str = self.entries_bloq[i].get().strip()
                    cpu2_str = self.entries_cpu2[i].get().strip()
                    if not bloq_str or not cpu2_str:
                        raise ValueError
                    bloq = int(bloq_str)
                    cpu2 = int(cpu2_str)
                    if bloq < 0 or cpu2 <= 0:
                        raise ValueError
                    bursts.extend([bloq, cpu2])

                procesos_data.append({"pid": nombre, "arrival_time": ta, "bursts": bursts})

        except ValueError:
            messagebox.showerror(
                "Error",
                "Verifique que:\n- Llegada ≥ 0\n- CPU1 > 0\n- Si marca bloqueo, complete Bloqueo y CPU2\n- Todos los valores sean enteros."
            )
            return

        self.on_continue(procesos_data)

    def _guardar_configuracion(self):
        """Guarda la configuración actual de inputs."""
        # Crear ventana de diálogo para ingresar nombre
        dialog = ctk.CTkToplevel(self)
        dialog.title("Guardar configuración")
        dialog.geometry("400x150")
        dialog.transient(self)
        
        # Centrar la ventana
        dialog.geometry("+%d+%d" % (self.winfo_rootx() + 50, self.winfo_rooty() + 50))
        
        # Configuraciones específicas para ZorinOS/Linux
        dialog.configure(fg_color=("gray95", "gray10"))
        dialog.lift()
        dialog.focus_force()
        
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
                for i, nombre_proceso in enumerate(self.nombres_procesos):
                    # Obtener tiempo de llegada
                    ta_str = self.entries_ta[i].get().strip()
                    arrival = int(ta_str) if ta_str else 0
                    
                    # Obtener ráfagas
                    cpu1_str = self.entries_cpu1[i].get().strip()
                    cpu1 = int(cpu1_str) if cpu1_str else 0
                    
                    bursts = [cpu1]
                    
                    if self.check_vars[i].get():
                        bloq_str = self.entries_bloq[i].get().strip()
                        cpu2_str = self.entries_cpu2[i].get().strip()
                        bloq = int(bloq_str) if bloq_str else 0
                        cpu2 = int(cpu2_str) if cpu2_str else 0
                        bursts.extend([bloq, cpu2])
                    
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
        
        # Forzar actualización para ZorinOS
        dialog.update_idletasks()
        dialog.update()
        dialog.lift()
        dialog.focus_force()
        
        # Hacer grab_set después de que la ventana sea visible (solo en Linux)
        try:
            dialog.grab_set()
        except:
            pass  # Si falla, no es crítico

    def _cargar_configuracion(self):
        """Carga una configuración guardada con mejoras para ZorinOS."""
        try:
            # Intentar con CustomTkinter primero
            self._cargar_configuracion_ctk()
        except Exception as e:
            print(f"Error con CustomTkinter: {e}")
            # Si falla, usar tkinter nativo
            self._cargar_configuracion_fallback()

    def _cargar_configuracion_ctk(self):
        """Versión con CustomTkinter optimizada para ZorinOS."""
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
        
        # Centrar la ventana
        dialog.geometry("+%d+%d" % (self.winfo_rootx() + 50, self.winfo_rooty() + 50))
        
        # Configuraciones específicas para ZorinOS/Linux
        dialog.configure(fg_color=("gray95", "gray10"))
        dialog.lift()
        dialog.focus_force()
        
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
        
        # Forzar actualización y renderizado en ZorinOS
        dialog.update_idletasks()
        dialog.update()
        dialog.lift()
        dialog.focus_force()
        
        # Hacer grab_set después de que la ventana sea visible (solo en Linux)
        try:
            dialog.grab_set()
        except:
            pass  # Si falla, no es crítico
        
        # Configurar evento de cierre
        def on_closing():
            try:
                dialog.grab_release()
            except:
                pass
            dialog.destroy()
        
        dialog.protocol("WM_DELETE_WINDOW", on_closing)

    def _cargar_configuracion_fallback(self):
        """Versión alternativa usando tkinter nativo para ZorinOS."""
        from tkinter import Toplevel, Label, Button, Listbox, Scrollbar, Frame
        from tkinter import messagebox as tk_messagebox
        
        # Obtener lista de configuraciones guardadas
        configs = historial.listar_input_configs()
        
        if not configs:
            tk_messagebox.showinfo("Información", "No hay configuraciones guardadas")
            return
        
        # Crear ventana de diálogo
        dialog = Toplevel(self)
        dialog.title("Cargar configuración")
        dialog.geometry("600x400")
        dialog.transient(self)
        
        # Centrar la ventana
        dialog.geometry("+%d+%d" % (self.winfo_rootx() + 50, self.winfo_rooty() + 50))
        
        # Frame principal
        main_frame = Frame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        label_titulo = Label(main_frame, text="Seleccionar configuración a cargar:", font=("Arial", 14, "bold"))
        label_titulo.pack(pady=(0, 10))
        
        # Frame para la lista
        list_frame = Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Listbox con scrollbar
        listbox = Listbox(list_frame, height=10)
        scrollbar = Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Llenar la lista
        for indice, nombre, fecha, num_procesos in configs:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(fecha)
                fecha_formateada = dt.strftime("%d/%m/%Y %H:%M")
            except:
                fecha_formateada = fecha
            
            listbox.insert("end", f"{nombre} - {fecha_formateada} - {num_procesos} procesos")
        
        # Botones
        btn_frame = Frame(main_frame)
        btn_frame.pack()
        
        def cargar():
            seleccion = listbox.curselection()
            if not seleccion:
                tk_messagebox.showwarning("Advertencia", "Seleccione una configuración para cargar")
                return
            
            indice = seleccion[0]
            
            try:
                # Cargar la configuración
                config = historial.cargar_input_config(indice)
                if config is None:
                    tk_messagebox.showerror("Error", "No se pudo cargar la configuración seleccionada")
                    return
                
                # Aplicar la configuración
                self._aplicar_configuracion(config)
                
                tk_messagebox.showinfo("Éxito", f"Configuración '{config['nombre']}' cargada exitosamente")
                dialog.destroy()
                
            except Exception as e:
                tk_messagebox.showerror("Error", f"Error al cargar la configuración: {e}")
        
        def eliminar():
            seleccion = listbox.curselection()
            if not seleccion:
                tk_messagebox.showwarning("Advertencia", "Seleccione una configuración para eliminar")
                return
            
            if not tk_messagebox.askyesno("Confirmar", "¿Está seguro de que desea eliminar esta configuración?"):
                return
            
            indice = seleccion[0]
            
            try:
                nombre_eliminado = historial.eliminar_input_config(indice)
                if nombre_eliminado:
                    listbox.delete(seleccion[0])
                    tk_messagebox.showinfo("Éxito", f"Configuración '{nombre_eliminado}' eliminada exitosamente")
                
            except Exception as e:
                tk_messagebox.showerror("Error", f"Error al eliminar la configuración: {e}")
        
        btn_cargar = Button(btn_frame, text="Cargar", command=cargar, bg="green", fg="white")
        btn_cargar.pack(side="left", padx=5)
        
        btn_eliminar = Button(btn_frame, text="Eliminar", command=eliminar, bg="red", fg="white")
        btn_eliminar.pack(side="left", padx=5)
        
        btn_cancelar = Button(btn_frame, text="Cancelar", command=dialog.destroy)
        btn_cancelar.pack(side="left", padx=5)
        
        # Forzar actualización
        dialog.update_idletasks()
        dialog.update()
        dialog.lift()
        dialog.focus_force()
        
        # Hacer grab_set después de que la ventana sea visible
        try:
            dialog.grab_set()
        except:
            pass  # Si falla, no es crítico

    def _aplicar_configuracion(self, config):
        """Aplica una configuración cargada a los campos de entrada."""
        try:
            # Limpiar todos los campos actuales
            self._limpiar_campos()
            
            # Aplicar los datos de cada proceso
            for proceso_config in config["procesos"]:
                nombre_proceso = proceso_config["nombre"]
                
                # Buscar el índice del proceso
                try:
                    idx = self.nombres_procesos.index(nombre_proceso)
                except ValueError:
                    continue  # Si no encuentra el proceso, continuar con el siguiente
                
                # Aplicar tiempo de llegada
                if proceso_config["arrival"] is not None:
                    self.entries_ta[idx].delete(0, "end")
                    self.entries_ta[idx].insert(0, str(proceso_config["arrival"]))
                
                # Aplicar ráfagas
                bursts = proceso_config["bursts"]
                if bursts:
                    # CPU1
                    if len(bursts) > 0:
                        self.entries_cpu1[idx].delete(0, "end")
                        self.entries_cpu1[idx].insert(0, str(bursts[0]))
                    
                    # Si hay más ráfagas, activar bloqueo
                    if len(bursts) > 1:
                        self.check_vars[idx].set(True)
                        self._toggle_block_fields(self.check_vars[idx], None)
                        
                        # Bloqueo
                        if len(bursts) > 1:
                            self.entries_bloq[idx].delete(0, "end")
                            self.entries_bloq[idx].insert(0, str(bursts[1]))
                        
                        # CPU2
                        if len(bursts) > 2:
                            self.entries_cpu2[idx].delete(0, "end")
                            self.entries_cpu2[idx].insert(0, str(bursts[2]))
                        
        except Exception as e:
            messagebox.showerror("Error", f"Error al aplicar la configuración: {e}")

    def _limpiar_campos(self):
        """Limpia todos los campos de entrada."""
        for i in range(len(self.nombres_procesos)):
            # Limpiar tiempo de llegada
            self.entries_ta[i].delete(0, "end")
            
            # Limpiar CPU1
            self.entries_cpu1[i].delete(0, "end")
            
            # Desactivar bloqueo y limpiar campos
            self.check_vars[i].set(False)
            self._toggle_block_fields(self.check_vars[i], None)
