from copy import deepcopy

def fifo(process_list):
    """
    FIFO no expulsivo sin bloqueos.
    Usa Process con bursts=[CPU] y remaining_time inicializado.
    Devuelve gantt en 3-tuplas: (pid, start, end).
    """
    # Crear copia profunda para no modificar la lista original
    processes = deepcopy(process_list)
    time = 0  # Reloj del sistema
    gantt = []  # Lista para almacenar el diagrama de Gantt
    ready = []  # Cola de procesos listos para ejecutar
    completed = 0  # Contador de procesos completados
    n = len(processes)  # Total de procesos

    # Ordenar por llegada para consistencia (no obligatorio)
    processes.sort(key=lambda p: p.arrival_time)

    while completed < n:  # Mientras no se completen todos los procesos
        # Encolar llegadas al tiempo actual
        for p in processes:
            # Verificar si el proceso:
            # - No ha empezado a ejecutarse (start_time is None)
            # - Ya llegó al sistema (arrival_time <= time)
            # - No está ya en la cola de listos
            # - No ha terminado (completion_time is None)
            if p.start_time is None and p.arrival_time <= time and p not in ready and p.completion_time is None:
                ready.append(p)  # Agregar a la cola de listos

        if ready:  # Si hay procesos listos para ejecutar
            current = ready.pop(0)  # Tomar el primero de la cola (FIFO)
            if current.start_time is None:  # Si es la primera vez que se ejecuta
                current.start_time = time  # Marcar tiempo de inicio

            start = time  # Guardar tiempo de inicio de esta ejecución
            cpu = current.remaining_time  # Tiempo de CPU restante (equivale a bursts[0])
            time += cpu  # Avanzar el reloj del sistema
            gantt.append((current.pid, start, time))  # Registrar en el diagrama de Gantt

            current.completion_time = time  # Marcar tiempo de finalización
            current.calculate_metrics()  # Calcular métricas del proceso
            completed += 1  # Incrementar contador de completados
        else:
            # No hay procesos listos: avanzar 1 unidad de tiempo y reintentar
            time += 1

    return gantt, processes
