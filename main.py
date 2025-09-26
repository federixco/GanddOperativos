import customtkinter as ctk
from GUI.start_screen import StartScreen
from GUI.name_input_screen import NameInputScreen
from GUI.data_input_screen import DataInputScreen
from GUI.algorithm_screen import AlgorithmScreen

# --- Funciones de navegación entre pantallas ---

def ir_a_nombres(payload):
    """
    payload puede ser:
      - int: cantidad de procesos (flujo clásico: Start -> NameInput)
      - dict con:
          {"action": "load_config", "data": {...}}  -> ABRIR CONFIG directamente en AlgorithmScreen
          {"action": "open_exercise", "data": {...}}-> ABRIR EJERCICIO directamente en AlgorithmScreen
    """
    # Caso clásico: número de procesos -> NameInput
    if isinstance(payload, int):
        limpiar_ventana()
        name_screen = NameInputScreen(root, payload, ir_a_tiempos)
        name_screen.pack(fill="both", expand=True)
        return

    # Casos nuevos: dict con acciones
    if isinstance(payload, dict):
        action = payload.get("action")
        data = payload.get("data")

        # A) Cargar CONFIGURACIÓN guardada (inputs) -> convertir a procesos_data y saltar a AlgorithmScreen
        if action == "load_config" and isinstance(data, dict):
            # data esperado: {"nombre","fecha","procesos":[{"nombre","arrival","priority","bursts"}, ...]}
            procesos_cfg = data.get("procesos", [])
            procesos_data = []

            for item in procesos_cfg:
                nombre = item.get("nombre", "P?")
                arrival = int(item.get("arrival", 0))
                priority = int(item.get("priority", 0))
                bursts = list(item.get("bursts", []))

                # Normalizar: si quedó en BLOQ, cerramos con CPU=0 (pares = CPU, impares = BLOQ)
                if len(bursts) % 2 == 1:
                    bursts.append(0)

                procesos_data.append({
                    "pid": nombre,               # usamos el nombre guardado -> no hay mismatch
                    "arrival_time": arrival,
                    "priority": priority,
                    "bursts": bursts
                })

            # Ir directo a simulación/algoritmos
            ir_a_algoritmo(procesos_data)
            return

        # B) Abrir EJERCICIO guardado -> ya trae procesos_data listos
        if action == "open_exercise" and isinstance(data, dict):
            # data esperado: {"nombre","fecha","algoritmo","quantum","procesos":[{pid,arrival_time,bursts,...}]}
            procesos_data = data.get("procesos", [])
            ir_a_algoritmo(procesos_data)
            return

    # Si llega algo raro:
    raise TypeError(f"ir_a_nombres: payload no soportado: {type(payload)}")


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
