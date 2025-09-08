# utils/parsers.py

def parse_bursts(input_str):
    """
    Convierte una cadena como '3,(2),5' en [3, 2, 5].
    Los números entre paréntesis se interpretan como bloqueos (E/S).
    """
    bursts = []
    # Eliminamos espacios y separamos por comas
    parts = input_str.replace(" ", "").split(",")
    for part in parts:
        if part.startswith("(") and part.endswith(")"):
            # Bloqueo
            val = int(part.strip("()"))
            bursts.append(val)
        else:
            # CPU
            bursts.append(int(part))
    return bursts
