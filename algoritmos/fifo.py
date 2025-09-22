from copy import deepcopy

def fifo(process_list):
    """
    ALGORITMO FIFO (First In, First Out) - NO EXPULSIVO SIN BLOQUEOS
    
    FUNCIONAMIENTO:
    - Los procesos se ejecutan en el orden de llegada (FIFO)
    - Una vez que un proceso comienza a ejecutarse, no puede ser interrumpido
    - No hay bloqueos de E/S, solo ráfagas de CPU
    - Cada proceso tiene una sola ráfaga de CPU que se ejecuta completamente
    
    CARACTERÍSTICAS:
    - No expulsivo: no hay preempción
    - Sin bloqueos: no hay operaciones de E/S
    - Simple y justo: el primero en llegar es el primero en ejecutarse
    
    PARÁMETROS:
    - process_list: Lista de objetos Process con bursts=[CPU]
    
    RETORNA:
    - gantt: Lista de tuplas (pid, start, end) para el diagrama de Gantt
    - processes: Lista de procesos con métricas calculadas
    """
    
    # Crear copia profunda para no modificar la lista original
    processes = deepcopy(process_list)
    
    # Inicializar variables del simulador
    time = 0  # Reloj del sistema (tiempo actual de simulación)
    gantt = []  # Lista para almacenar el diagrama de Gantt
    ready = []  # Cola de procesos listos para ejecutar (FIFO)
    completed = 0  # Contador de procesos completados
    n = len(processes)  # Total de procesos a procesar

    # Ordenar procesos por tiempo de llegada para consistencia
    # Esto asegura que si hay empates en llegada, se mantenga un orden predecible
    processes.sort(key=lambda p: p.arrival_time)

    # BUCLE PRINCIPAL: Simular hasta que todos los procesos terminen
    while completed < n:  # Mientras no se completen todos los procesos
        
        # FASE 1: ENCOLAR LLEGADAS
        # Revisar todos los procesos para ver cuáles han llegado al tiempo actual
        for p in processes:
            # Verificar si el proceso cumple todas las condiciones para ser encolado:
            # - No ha empezado a ejecutarse (start_time is None)
            # - Ya llegó al sistema (arrival_time <= time)
            # - No está ya en la cola de listos
            # - No ha terminado (completion_time is None)
            if p.start_time is None and p.arrival_time <= time and p not in ready and p.completion_time is None:
                ready.append(p)  # Agregar a la cola de listos (al final de la cola)

        # FASE 2: EJECUTAR PROCESO
        if ready:  # Si hay procesos listos para ejecutar
            
            # Seleccionar proceso: FIFO = First In, First Out
            current = ready.pop(0)  # Tomar el primero de la cola (el que llegó primero)
            
            # Marcar tiempo de inicio si es la primera vez que se ejecuta
            if current.start_time is None:  # Si es la primera vez que se ejecuta
                current.start_time = time  # Marcar tiempo de inicio del proceso

            # Ejecutar el proceso completamente (FIFO es no expulsivo)
            start = time  # Guardar tiempo de inicio de esta ejecución
            cpu = current.remaining_time  # Tiempo de CPU restante (equivale a bursts[0])
            time += cpu  # Avanzar el reloj del sistema por el tiempo de CPU completo
            gantt.append((current.pid, start, time))  # Registrar en el diagrama de Gantt

            # Marcar proceso como completado
            current.completion_time = time  # Marcar tiempo de finalización
            current.calculate_metrics()  # Calcular métricas del proceso (TR, TE, etc.)
            completed += 1  # Incrementar contador de procesos completados
            
        else:
            # No hay procesos listos: CPU ociosa
            # Avanzar 1 unidad de tiempo y reintentar en la siguiente iteración
            time += 1

    # Retornar resultados de la simulación
    return gantt, processes
