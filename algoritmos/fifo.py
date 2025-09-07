from copy import deepcopy

def fifo(process_list):
    """
    Simula la planificación FIFO (First In First Out).

    :param process_list: lista de objetos Process
    :return: (gantt_chart, procesos_con_metricas)
    """
    # Trabajamos sobre una copia para no modificar la lista original
    processes = deepcopy(process_list)

    # Ordenar por tiempo de llegada
    processes.sort(key=lambda p: p.arrival_time)

    time = 0
    gantt_chart = []

    for process in processes:
        # Si el CPU está ocioso antes de que llegue el proceso
        if time < process.arrival_time:
            gantt_chart.append(("IDLE", time, process.arrival_time))
            time = process.arrival_time

        # Asignar start_time si no lo tenía
        process.start_time = time

        # Ejecutar el proceso
        start = time
        end = time + process.burst_time
        gantt_chart.append((process.pid, start, end))

        # Actualizar tiempos
        time = end
        process.completion_time = end
        process.calculate_metrics()

    return gantt_chart, processes
