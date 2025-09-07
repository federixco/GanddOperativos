import customtkinter as ctk
from tkinter import messagebox

class StartScreen(ctk.CTkFrame):
    def __init__(self, master, on_continue):
        """
        Pantalla inicial para ingresar la cantidad de procesos.

        :param master: ventana o frame padre
        :param on_continue: función que recibe la cantidad de procesos y avanza a la siguiente pantalla
        """
        super().__init__(master)
        self.on_continue = on_continue

        # Título
        self.label_title = ctk.CTkLabel(self, text="Planificación de CPU", font=("Arial", 20, "bold"))
        self.label_title.pack(pady=20)

        # Instrucción
        self.label_instruction = ctk.CTkLabel(self, text="Ingrese la cantidad de procesos:")
        self.label_instruction.pack(pady=10)

        # Campo de entrada
        self.entry_count = ctk.CTkEntry(self, placeholder_text="Ej: 4")
        self.entry_count.pack(pady=10)

        # Botón continuar
        self.btn_continue = ctk.CTkButton(self, text="Continuar", command=self._continue_clicked)
        self.btn_continue.pack(pady=20)

    def _continue_clicked(self):
        """Valida la entrada y llama a la función on_continue."""
        try:
            n = int(self.entry_count.get())
            if n <= 0:
                raise ValueError
            self.on_continue(n)
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido mayor a 0")
