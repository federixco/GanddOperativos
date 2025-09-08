import customtkinter as ctk
from tkinter import messagebox

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
