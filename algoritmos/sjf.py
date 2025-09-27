from copy import deepcopy

def sjf(process_list):
    """
    SJF (Shortest Job First) no expulsivo, SIN bloqueos.
    Criterio: menor ráfaga total de CPU del proceso (inmutable), sin usar “tiempo restante”.
    Retorna: gantt = [(pid, start, end)], processes
    """

    processes = deepcopy(process_list)

    # --- Init por proceso ---
    for idx, p in enumerate(processes):
        # Foto original por si otros módulos mutan bursts
        if not hasattr(p, "bursts_original"):
            p.bursts_original = p.bursts[:]

        # ráfaga única de CPU (sin bloqueos). Si falta, asumimos 0.
        p.cpu_burst = p.bursts_original[0] if p.bursts_original else 0

        p._seq = idx
        if not hasattr(p, "arrival_time"):
            p.arrival_time = getattr(p, "arrival", 0)
        if not hasattr(p, "start_time"):
            p.start_time = None
        p.completion_time = None

    time = 0
    gantt = []
    completed = 0
    n = len(processes)

    # Bucle principal
    safe_iters = 0
    while completed < n and safe_iters < 200000:
        safe_iters += 1

        # Elegibles que ya llegaron y no terminaron
        elegibles = [p for p in processes if p.arrival_time <= time and p.completion_time is None]

        if not elegibles:
            # Saltar al próximo arribo (evitar time += 1 en vacío)
            future_arrivals = [p.arrival_time for p in processes if p.completion_time is None and p.arrival_time > time]
            if not future_arrivals:
                # Nada más por llegar: estamos ociosos pero no hay trabajo -> cortar
                break
            time = min(future_arrivals)
            continue

        # Selección SJF: por ráfaga inmutable, luego FIFO por llegada y orden estable
        elegibles.sort(key=lambda x: (x.cpu_burst, x.arrival_time, x._seq))
        current = elegibles[0]

        # Marcar inicio si corresponde
        if current.start_time is None:
            current.start_time = time

        # Ejecutar COMPLETO (no apropiativo)
        start = time
        cpu = max(0, int(current.cpu_burst))  # sanidad: entero >= 0
        time += cpu
        gantt.append((current.pid, start, time))

        # Terminar proceso y métricas
        current.completion_time = time
        if hasattr(current, "calculate_metrics"):
            try:
                current.calculate_metrics()
            except Exception:
                pass
        completed += 1

    return gantt, processes
