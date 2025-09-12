from copy import deepcopy

def srtf(process_list):
    """
    Simula la planificación SRTF (Shortest Remaining Time First, expulsivo).

    :param process_list: lista de objetos Process
    :return: (gantt_chart, procesos_con_metricas)
    """
    # Crear copia profunda para no modificar la lista original
    processes = deepcopy(process_list)
    n = len(processes)  # Total de procesos
    completed = 0  # Contador de procesos completados
    time = 0  # Reloj del sistema
    gantt_chart = []  # Lista para almacenar el diagrama de Gantt

    # Para controlar cambios de proceso
    current_pid = None  # PID del proceso actualmente en ejecución
    start_time = None  # Tiempo de inicio del bloque actual en Gantt

    while completed < n:  # Mientras no se completen todos los procesos
        # Filtrar procesos listos y no completados
        ready_queue = [p for p in processes if p.arrival_time <= time and p.remaining_time > 0]

        if ready_queue:  # Si hay procesos listos para ejecutar
            # Elegir el de menor tiempo restante, con desempate por FIFO
            ready_queue.sort(key=lambda x: (
                x.remaining_time,  # SRTF: menor tiempo restante (prioridad principal)
                x.arrival_time,    # FIFO en empates (desempate por llegada)
                x.pid             # estabilidad (desempate por PID)
            ))
            current = ready_queue[0]  # Tomar el proceso con menor tiempo restante

            # Si cambia el proceso en ejecución, cerramos el bloque anterior
            if current_pid != current.pid:  # Si cambió el proceso
                if current_pid is not None:  # Si había un proceso anterior
                    gantt_chart.append((current_pid, start_time, time))  # Cerrar bloque anterior
                current_pid = current.pid  # Actualizar PID actual
                start_time = time  # Marcar inicio del nuevo bloque
                if current.start_time is None:  # Si es la primera vez que se ejecuta
                    current.start_time = time  # Marcar tiempo de inicio del proceso

            # Ejecutar 1 unidad de tiempo (SRTF es expulsivo)
            current.remaining_time -= 1  # Reducir tiempo restante
            time += 1  # Avanzar el reloj del sistema

            # Si termina
            if current.remaining_time == 0:  # Si el proceso terminó
                current.completion_time = time  # Marcar tiempo de finalización
                current.calculate_metrics()  # Calcular métricas del proceso
                completed += 1  # Incrementar contador de completados
        else:  # No hay procesos listos
            # CPU ociosa
            if current_pid != "IDLE":  # Si no está marcado como IDLE
                if current_pid is not None:  # Si había un proceso anterior
                    gantt_chart.append((current_pid, start_time, time))  # Cerrar bloque anterior
                current_pid = "IDLE"  # Marcar como IDLE
                start_time = time  # Marcar inicio del período IDLE
            time += 1  # Avanzar tiempo sin ejecutar nada

    # Cerrar el último bloque
    if current_pid is not None:
        gantt_chart.append((current_pid, start_time, time))

    return gantt_chart, processes
