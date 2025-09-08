from copy import deepcopy

def fifo(process_list):
    """
    FIFO no expulsivo sin bloqueos.
    Usa Process con bursts=[CPU] y remaining_time inicializado.
    Devuelve gantt en 3-tuplas: (pid, start, end).
    """
    processes = deepcopy(process_list)
    time = 0
    gantt = []
    ready = []
    completed = 0
    n = len(processes)

    # ordenar por llegada para consistencia (no obligatorio)
    processes.sort(key=lambda p: p.arrival_time)

    while completed < n:
        # Encolar llegadas al tiempo actual
        for p in processes:
            if p.start_time is None and p.arrival_time <= time and p not in ready and p.completion_time is None:
                ready.append(p)

        if ready:
            current = ready.pop(0)
            if current.start_time is None:
                current.start_time = time

            start = time
            cpu = current.remaining_time  # equivale a bursts[0]
            time += cpu
            gantt.append((current.pid, start, time))

            current.completion_time = time
            current.calculate_metrics()
            completed += 1
        else:
            # No hay listos: avanzar 1 y reintentar
            time += 1

    return gantt, processes
