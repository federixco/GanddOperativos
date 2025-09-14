from copy import deepcopy
from collections import deque

def round_robin(process_list, quantum):
    # Crear copia profunda para no modificar la lista original
    processes = deepcopy(process_list)
    n = len(processes)  # Total de procesos
    time = 0  # Reloj del sistema
    completed = 0  # Contador de procesos completados
    gantt_chart = []  # Lista para almacenar el diagrama de Gantt

    ready_queue = deque()  # Cola de procesos listos (FIFO con deque)
    # Ordenar por tiempo de llegada, luego por PID para consistencia
    procesos_pendientes = sorted(processes, key=lambda p: (p.arrival_time, p.pid))

    current_pid = None  # PID del proceso actualmente en ejecución
    start_time = None  # Tiempo de inicio del bloque actual en Gantt

    while completed < n:  # Mientras no se completen todos los procesos
        # Agregar procesos que llegan en este instante
        # Ordenar por PID para mantener consistencia
        procesos_que_llegan = []
        for p in procesos_pendientes:
            # Verificar si el proceso:
            # - Llega exactamente en este momento (arrival_time == time)
            # - No está ya en la cola de listos
            # - Aún tiene tiempo restante para ejecutar
            if p.arrival_time == time and p not in ready_queue and p.remaining_time > 0:
                procesos_que_llegan.append(p)
        
        # Ordenar por PID y agregar al final de la cola
        procesos_que_llegan.sort(key=lambda p: p.pid)
        for p in procesos_que_llegan:
            ready_queue.append(p)  # Agregar al final de la cola

        if ready_queue:  # Si hay procesos listos para ejecutar
            current = ready_queue.popleft()  # Tomar el primero de la cola

            # Cambio de proceso en ejecución
            if current_pid != current.pid:  # Si cambió el proceso
                if current_pid is not None:  # Si había un proceso anterior
                    gantt_chart.append((current_pid, start_time, time))  # Cerrar bloque anterior
                current_pid = current.pid  # Actualizar PID actual
                start_time = time  # Marcar inicio del nuevo bloque
                if current.start_time is None:  # Si es la primera vez que se ejecuta
                    current.start_time = time  # Marcar tiempo de inicio del proceso

            # Ejecutar hasta quantum o hasta que termine
            exec_time = min(quantum, current.remaining_time)  # Tiempo a ejecutar
            current.remaining_time -= exec_time  # Reducir tiempo restante
            time += exec_time  # Avanzar el reloj del sistema

            # Agregar procesos que llegaron durante la ejecución
            procesos_nuevos = []
            for p in procesos_pendientes:
                # Verificar si llegó durante la ejecución del proceso actual
                if time - exec_time < p.arrival_time <= time and p.remaining_time > 0 and p not in ready_queue:
                    procesos_nuevos.append(p)
            
            # Ordenar por PID y agregar al final
            procesos_nuevos.sort(key=lambda p: p.pid)
            for p in procesos_nuevos:
                ready_queue.append(p)  # Agregar al final de la cola

            if current.remaining_time > 0:  # Si el proceso no terminó
                # Agregar el proceso actual al final si no terminó (Round Robin)
                ready_queue.append(current)
            else:  # Si el proceso terminó
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
