import json
import os
from datetime import datetime

HISTORIAL_FILE = os.path.join(os.path.dirname(__file__), "historial.json")

def _leer_historial():
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def _guardar_historial(data):
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def guardar_ejercicio(nombre, procesos, algoritmo, quantum=None):
    """
    Guarda un ejercicio en el historial.
    procesos: lista de dicts con {"pid":..., "arrival_time":..., "bursts": [...]}
    """
    historial = _leer_historial()
    entrada = {
        "nombre": nombre,
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "algoritmo": algoritmo,
        "quantum": quantum,
        "procesos": procesos
    }
    historial.append(entrada)
    _guardar_historial(historial)

def listar_historial():
    """Devuelve una lista de (indice, nombre, fecha, algoritmo) para mostrar en la GUI."""
    historial = _leer_historial()
    return [(i, h["nombre"], h["fecha"], h["algoritmo"]) for i, h in enumerate(historial)]

def cargar_ejercicio(indice):
    """Devuelve el ejercicio guardado en la posición 'indice'."""
    historial = _leer_historial()
    if 0 <= indice < len(historial):
        return historial[indice]
    return None

# ===== FUNCIONES PARA INPUTS DE DATOS =====

INPUT_HISTORIAL_FILE = os.path.join(os.path.dirname(__file__), "input_historial.json")

def _leer_input_historial():
    """Lee el historial de inputs desde el archivo JSON."""
    if os.path.exists(INPUT_HISTORIAL_FILE):
        with open(INPUT_HISTORIAL_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def _guardar_input_historial(data):
    """Guarda el historial de inputs en el archivo JSON."""
    with open(INPUT_HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def guardar_input_config(nombre, procesos_config):
    """
    Guarda una configuración de inputs en el historial.
    procesos_config: lista de dicts con {"nombre": str, "arrival": int, "bursts": [int, ...]}
    """
    historial = _leer_input_historial()
    entrada = {
        "nombre": nombre,
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "procesos": procesos_config
    }
    historial.append(entrada)
    _guardar_input_historial(historial)

def listar_input_configs():
    """Devuelve una lista de (indice, nombre, fecha, num_procesos) para mostrar en la GUI."""
    historial = _leer_input_historial()
    return [(i, h["nombre"], h["fecha"], len(h["procesos"])) for i, h in enumerate(historial)]

def cargar_input_config(indice):
    """Devuelve la configuración de inputs guardada en la posición 'indice'."""
    historial = _leer_input_historial()
    if 0 <= indice < len(historial):
        return historial[indice]
    return None

def eliminar_input_config(indice):
    """Elimina una configuración de inputs del historial."""
    historial = _leer_input_historial()
    if 0 <= indice < len(historial):
        nombre_eliminado = historial[indice]["nombre"]
        del historial[indice]
        _guardar_input_historial(historial)
        return nombre_eliminado
    return None