# utils/historial.py
import json
import os
from datetime import datetime
from .paths import data_path  # usa storage persistente (AppData o modo portable)

# Un único archivo para TODO el historial de inputs
INPUT_HIST_FILE = data_path("input_historial.json")


# ------------ utilidades de IO ------------
def _safe_load_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

def _safe_save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    try:
        os.replace(tmp, path)
    except Exception:
        # Fallback si os.replace no está disponible
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        try:
            os.remove(tmp)
        except Exception:
            pass


# ===== HISTORIAL DE CONFIGURACIONES DE INPUT =====
def _leer_input_historial():
    return _safe_load_json(INPUT_HIST_FILE)

def _guardar_input_historial(data):
    _safe_save_json(INPUT_HIST_FILE, data)

def guardar_input_config(nombre, procesos_config):
    """
    Guarda una configuración de inputs.
    procesos_config: lista de dicts con:
      {"nombre": str, "arrival": int, "priority": int (opcional), "bursts": [int, ...]}
    """
    data = _leer_input_historial()
    entrada = {
        "nombre": nombre,
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "procesos": procesos_config
    }
    data.append(entrada)
    _guardar_input_historial(data)
    return entrada

def listar_input_configs():
    """
    Devuelve lista de (indice, nombre, fecha, num_procesos) para mostrar en la GUI.
    """
    data = _leer_input_historial()
    return [
        (i, it.get("nombre", f"Config {i+1}"),
         it.get("fecha", ""),
         len(it.get("procesos", [])))
        for i, it in enumerate(data)
    ]

def cargar_input_config(indice):
    """
    Devuelve la configuración de inputs guardada en la posición 'indice'.
    """
    data = _leer_input_historial()
    if 0 <= indice < len(data):
        return data[indice]
    return None

def eliminar_input_config(indice):
    """
    Elimina una configuración de inputs del historial y devuelve su nombre.
    """
    data = _leer_input_historial()
    if 0 <= indice < len(data):
        nombre = data[indice].get("nombre")
        del data[indice]
        _guardar_input_historial(data)
        return nombre
    return None
# DEBUG/ayuda: devolver la ruta donde realmente se guarda
def input_historial_path():
    return INPUT_HIST_FILE
