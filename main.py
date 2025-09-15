import customtkinter as ctk
from GUI.start_screen import StartScreen
from GUI.name_input_screen import NameInputScreen
from GUI.data_input_screen import DataInputScreen
from GUI.algorithm_screen import AlgorithmScreen

# --- Funciones de navegación entre pantallas ---

def ir_a_nombres(cantidad):
    limpiar_ventana()
    name_screen = NameInputScreen(root, cantidad, ir_a_tiempos)
    name_screen.pack(fill="both", expand=True)

def ir_a_tiempos(nombres):
    limpiar_ventana()
    data_screen = DataInputScreen(root, nombres, ir_a_algoritmo)
    data_screen.pack(fill="both", expand=True)

def ir_a_algoritmo(procesos_data):
    limpiar_ventana()
    algo_screen = AlgorithmScreen(root, procesos_data, volver_inicio)
    algo_screen.pack(fill="both", expand=True)

def volver_inicio():
    limpiar_ventana()
    start_screen = StartScreen(root, ir_a_nombres)
    start_screen.pack(fill="both", expand=True)

def limpiar_ventana():
    """Elimina todos los widgets de la ventana principal."""
    for widget in root.winfo_children():
        widget.destroy()

# --- Configuración inicial de la app ---
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")  # Modo oscuro
    ctk.set_default_color_theme("blue")  # Tema azul

    root = ctk.CTk()
    root.title("TimeSlice - Simulador de Planificación de CPU")
    root.geometry("800x600")

    # Pantalla inicial
    start_screen = StartScreen(root, ir_a_nombres)
    start_screen.pack(fill="both", expand=True)

    root.mainloop()
