from copy import deepcopy

def sjf(process_list):
    """
    Simula la planificación SJF (Shortest Job First, no expropiativo).

    :param process_list: lista de objetos Process
    :return: (gantt_chart, procesos_con_metricas)
    """
    processes = deepcopy(process_list)
    n = len(processes)
    completed = 0
    time = 0
    gantt_chart = []
    ready_queue = []

    # Para evitar reprocesar, marcamos procesos completados
    procesos_pendientes = processes[:]

    while completed < n:
        # Agregar a la cola de listos los procesos que ya llegaron
        for p in procesos_pendientes:
            if p.arrival_time <= time and p not in ready_queue:
                ready_queue.append(p)

        # Filtrar solo los que no han terminado
        ready_queue = [p for p in ready_queue if p.completion_time is None]

        if ready_queue:
            # Elegir el de menor burst_time
            ready_queue.sort(key=lambda x: x.burst_time)
            current = ready_queue.pop(0)

            # Si el CPU estaba ocioso antes de este proceso
            if time < current.arrival_time:
                gantt_chart.append(("IDLE", time, current.arrival_time))
                time = current.arrival_time

            # Asignar start_time
            current.start_time = time

            # Ejecutar el proceso
            start = time
            end = time + current.burst_time
            gantt_chart.append((current.pid, start, end))

            # Actualizar tiempos
            time = end
            current.completion_time = end
            current.calculate_metrics()

            completed += 1
        else:
            # No hay procesos listos → CPU ociosa
            next_arrival = min(p.arrival_time for p in procesos_pendientes if p.completion_time is None)
            gantt_chart.append(("IDLE", time, next_arrival))
            time = next_arrival

    return gantt_chart, processes
