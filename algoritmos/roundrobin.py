from copy import deepcopy
from collections import deque

def round_robin(process_list, quantum):
    processes = deepcopy(process_list)
    n = len(processes)
    time = 0
    completed = 0
    gantt_chart = []

    ready_queue = deque()
    procesos_pendientes = sorted(processes, key=lambda p: p.arrival_time)

    current_pid = None
    start_time = None

    while completed < n:
        # Agregar procesos que llegan en este instante
        for p in procesos_pendientes:
            if p.arrival_time == time and p not in ready_queue and p.remaining_time > 0:
                ready_queue.append(p)

        if ready_queue:
            current = ready_queue.popleft()

            # Cambio de proceso en ejecución
            if current_pid != current.pid:
                if current_pid is not None:
                    gantt_chart.append((current_pid, start_time, time))
                current_pid = current.pid
                start_time = time
                if current.start_time is None:
                    current.start_time = time

            # Ejecutar hasta quantum o hasta que termine
            exec_time = min(quantum, current.remaining_time)
            current.remaining_time -= exec_time
            time += exec_time

            # Agregar procesos que llegaron mientras este ejecutaba
            for p in procesos_pendientes:
                if time - exec_time < p.arrival_time <= time and p.remaining_time > 0 and p not in ready_queue:
                    ready_queue.append(p)

            if current.remaining_time > 0:
                ready_queue.append(current)
            else:
                current.completion_time = time
                current.calculate_metrics()
                completed += 1
        else:
            # CPU ociosa
            if current_pid != "IDLE":
                if current_pid is not None:
                    gantt_chart.append((current_pid, start_time, time))
                current_pid = "IDLE"
                start_time = time
            time += 1

    # Cerrar el último bloque
    if current_pid is not None:
        gantt_chart.append((current_pid, start_time, time))

    return gantt_chart, processes
