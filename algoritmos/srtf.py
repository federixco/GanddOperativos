from copy import deepcopy

def srtf(process_list):
    """
    Simula la planificación SRTF (Shortest Remaining Time First, expulsivo).

    :param process_list: lista de objetos Process
    :return: (gantt_chart, procesos_con_metricas)
    """
    processes = deepcopy(process_list)
    n = len(processes)
    completed = 0
    time = 0
    gantt_chart = []

    # Para controlar cambios de proceso
    current_pid = None
    start_time = None

    while completed < n:
        # Filtrar procesos listos y no completados
        ready_queue = [p for p in processes if p.arrival_time <= time and p.remaining_time > 0]

        if ready_queue:
            # Elegir el de menor tiempo restante, con desempate por FIFO
            ready_queue.sort(key=lambda x: (
                x.remaining_time,  # SRTF: menor tiempo restante
                x.arrival_time,    # FIFO en empates
                x.pid             # estabilidad
            ))
            current = ready_queue[0]

            # Si cambia el proceso en ejecución, cerramos el bloque anterior
            if current_pid != current.pid:
                if current_pid is not None:
                    gantt_chart.append((current_pid, start_time, time))
                current_pid = current.pid
                start_time = time
                if current.start_time is None:
                    current.start_time = time

            # Ejecutar 1 unidad de tiempo
            current.remaining_time -= 1
            time += 1

            # Si termina
            if current.remaining_time == 0:
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
