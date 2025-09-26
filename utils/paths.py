# utils/paths.py
import os, sys

APP_NAME = "TimeSlice"

def _is_frozen():
    return getattr(sys, "frozen", False)

def _exe_dir():
    # Directorio donde está el ejecutable (cuando está congelado)
    if _is_frozen():
        return os.path.dirname(sys.executable)
    # En desarrollo: carpeta del repo (ajusta si preferís otro)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _writable(path):
    try:
        os.makedirs(path, exist_ok=True)
        testfile = os.path.join(path, ".wtest")
        with open(testfile, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(testfile)
        return True
    except Exception:
        return False

def get_storage_dir():
    """
    Devuelve el directorio PERSISTENTE para guardar JSON/archivos de la app.
    Modos:
      - PORTABLE: si existe variable de entorno TIMESLICE_PORTABLE=1,
                  o si en la carpeta del exe hay un archivo 'portable.flag',
                  intentamos guardar junto al exe.
      - NORMAL:   usamos %APPDATA%\\TimeSlice en Windows, o ~/.local/share/TimeSlice en *nix.
    Si el destino no es escribible (ej. Program Files), falla a modo NORMAL.
    """
    # 1) ¿Portable activado?
    exe_dir = _exe_dir()
    portable_env = os.environ.get("TIMESLICE_PORTABLE", "").strip() == "1"
    portable_flag = os.path.exists(os.path.join(exe_dir, "portable.flag"))
    if portable_env or portable_flag:
        # intentar junto al exe
        data_dir = os.path.join(exe_dir, "data")
        if _writable(data_dir):
            return data_dir
        # si no se puede escribir (Program Files), caemos a normal
        # (no tiramos excepción; hacemos fallback silencioso)

    # 2) Modo NORMAL (user data)
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~\\AppData\\Roaming")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")

    data_dir = os.path.join(base, APP_NAME)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def data_path(*parts):
    """Arma una ruta dentro del storage dir."""
    return os.path.join(get_storage_dir(), *parts)
