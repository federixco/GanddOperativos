from copy import deepcopy

def sjf(process_list):
    """
    SJF no expulsivo sin bloqueos.
    Usa Process con bursts=[CPU] y remaining_time inicializado.
    Devuelve gantt en 3-tuplas: (pid, start, end).
    """
    # Crear copia profunda para no modificar la lista original
    processes = deepcopy(process_list)
    time = 0  # Reloj del sistema
    gantt = []  # Lista para almacenar el diagrama de Gantt
    completed = 0  # Contador de procesos completados
    n = len(processes)  # Total de procesos

    # Para evitar reuso accidental
    for p in processes:
        # remaining_time ya viene de Process(bursts=[cpu])
        pass

    while completed < n:  # Mientras no se completen todos los procesos
        # Elegibles: llegaron y no completados
        elegibles = [p for p in processes if p.arrival_time <= time and p.completion_time is None]

        if not elegibles:  # Si no hay procesos elegibles
            time += 1  # Avanzar tiempo y continuar
            continue

        # Elegir el de menor remaining_time (única ráfaga de CPU)
        # SJF: Shortest Job First - el trabajo más corto primero
        current = min(elegibles, key=lambda p: p.remaining_time)

        if current.start_time is None:  # Si es la primera vez que se ejecuta
            current.start_time = time  # Marcar tiempo de inicio

        start = time  # Guardar tiempo de inicio de esta ejecución
        cpu = current.remaining_time  # Tiempo de CPU restante
        time += cpu  # Avanzar el reloj del sistema
        gantt.append((current.pid, start, time))  # Registrar en el diagrama de Gantt

        current.completion_time = time  # Marcar tiempo de finalización
        current.calculate_metrics()  # Calcular métricas del proceso
        completed += 1  # Incrementar contador de completados

    return gantt, processes
