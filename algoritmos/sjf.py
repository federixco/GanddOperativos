from copy import deepcopy

def sjf(process_list):
    """
    SJF no expulsivo sin bloqueos.
    Usa Process con bursts=[CPU] y remaining_time inicializado.
    Devuelve gantt en 3-tuplas: (pid, start, end).
    """
    processes = deepcopy(process_list)
    time = 0
    gantt = []
    completed = 0
    n = len(processes)

    # Para evitar reuso accidental
    for p in processes:
        # remaining_time ya viene de Process(bursts=[cpu])
        pass

    while completed < n:
        # Elegibles: llegaron y no completados
        elegibles = [p for p in processes if p.arrival_time <= time and p.completion_time is None]

        if not elegibles:
            time += 1
            continue

        # Elegir el de menor remaining_time (única ráfaga de CPU)
        current = min(elegibles, key=lambda p: p.remaining_time)

        if current.start_time is None:
            current.start_time = time

        start = time
        cpu = current.remaining_time
        time += cpu
        gantt.append((current.pid, start, time))

        current.completion_time = time
        current.calculate_metrics()
        completed += 1

    return gantt, processes
