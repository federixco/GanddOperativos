from copy import deepcopy

def srtf(process_list):
    """
    ALGORITMO SRTF (Shortest Remaining Time First) - EXPULSIVO SIN BLOQUEOS
    
    FUNCIONAMIENTO:
    - Los procesos se ejecutan en orden de tiempo restante (el más corto primero)
    - En cada unidad de tiempo, se selecciona el proceso con menor tiempo restante
    - Los procesos pueden ser interrumpidos si llega uno con menor tiempo restante
    - No hay bloqueos de E/S, solo ráfagas de CPU
    - Cada proceso tiene una sola ráfaga de CPU que se ejecuta por unidades de tiempo
    
    CARACTERÍSTICAS:
    - Expulsivo: los procesos pueden ser preemptados en cualquier momento
    - Sin bloqueos: no hay operaciones de E/S
    - Optimiza tiempo de respuesta: los trabajos cortos tienen prioridad
    - Puede causar inanición: trabajos largos pueden ser postergados indefinidamente
    - Muy responsivo: responde inmediatamente a trabajos más cortos
    
    PARÁMETROS:
    - process_list: Lista de objetos Process con bursts=[CPU]
    
    RETORNA:
    - gantt_chart: Lista de tuplas (pid, start, end) para el diagrama de Gantt
    - processes: Lista de procesos con métricas calculadas
    """
    
    # Crear copia profunda para no modificar la lista original
    processes = deepcopy(process_list)
    
    # Inicializar variables del simulador
    n = len(processes)  # Total de procesos a procesar
    completed = 0  # Contador de procesos completados
    time = 0  # Reloj del sistema (tiempo actual de simulación)
    gantt_chart = []  # Lista para almacenar el diagrama de Gantt

    # Variables para controlar cambios de proceso en el diagrama de Gantt
    current_pid = None  # PID del proceso actualmente en ejecución
    start_time = None  # Tiempo de inicio del bloque actual en Gantt

    # BUCLE PRINCIPAL: Simular hasta que todos los procesos terminen
    while completed < n:  # Mientras no se completen todos los procesos
        
        # FASE 1: IDENTIFICAR PROCESOS LISTOS
        # Filtrar procesos que han llegado y aún tienen tiempo restante
        ready_queue = [p for p in processes if p.arrival_time <= time and p.remaining_time > 0]

        # FASE 2: SELECCIÓN DE PROCESO (CRITERIO SRTF)
        if ready_queue:  # Si hay procesos listos para ejecutar
            
            # Ordenar por criterio SRTF con desempates
            ready_queue.sort(key=lambda x: (
                x.remaining_time,  # SRTF: menor tiempo restante (prioridad principal)
                x.arrival_time,    # FIFO en empates (desempate por llegada)
                x.pid             # Estabilidad (desempate por PID)
            ))
            
            # Seleccionar el proceso con menor tiempo restante
            current = ready_queue[0]  # Tomar el proceso con menor tiempo restante

            # FASE 3: CONTROL DE CAMBIOS DE PROCESO EN GANTT
            # Si cambia el proceso en ejecución, cerrar el bloque anterior
            if current_pid != current.pid:  # Si cambió el proceso
                if current_pid is not None:  # Si había un proceso anterior
                    gantt_chart.append((current_pid, start_time, time))  # Cerrar bloque anterior
                current_pid = current.pid  # Actualizar PID actual
                start_time = time  # Marcar inicio del nuevo bloque
                
                # Marcar tiempo de inicio si es la primera vez que se ejecuta
                if current.start_time is None:  # Si es la primera vez que se ejecuta
                    current.start_time = time  # Marcar tiempo de inicio del proceso

            # FASE 4: EJECUTAR PROCESO POR 1 UNIDAD DE TIEMPO
            # Ejecutar 1 unidad de tiempo (SRTF es expulsivo por unidades)
            current.remaining_time -= 1  # Reducir tiempo restante del proceso
            time += 1  # Avanzar el reloj del sistema

            # FASE 5: VERIFICAR SI EL PROCESO TERMINÓ
            if current.remaining_time == 0:  # Si el proceso terminó
                current.completion_time = time  # Marcar tiempo de finalización
                current.calculate_metrics()  # Calcular métricas del proceso (TR, TE, etc.)
                completed += 1  # Incrementar contador de procesos completados
                
        else:  # No hay procesos listos: CPU ociosa
            # CONTROL DE PERÍODOS IDLE EN GANTT
            if current_pid != "IDLE":  # Si no está marcado como IDLE
                if current_pid is not None:  # Si había un proceso anterior
                    gantt_chart.append((current_pid, start_time, time))  # Cerrar bloque anterior
                current_pid = "IDLE"  # Marcar como IDLE
                start_time = time  # Marcar inicio del período IDLE
            
            # Avanzar tiempo sin ejecutar nada
            time += 1

    # Cerrar el último bloque del diagrama de Gantt
    if current_pid is not None:
        gantt_chart.append((current_pid, start_time, time))

    # Retornar resultados de la simulación
    return gantt_chart, processes
