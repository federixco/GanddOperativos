from copy import deepcopy

def sjf(process_list):
    """
    ALGORITMO SJF (Shortest Job First) - NO EXPULSIVO SIN BLOQUEOS
    
    FUNCIONAMIENTO:
    - Los procesos se ejecutan en orden de duración (el más corto primero)
    - Una vez que un proceso comienza a ejecutarse, no puede ser interrumpido
    - No hay bloqueos de E/S, solo ráfagas de CPU
    - Cada proceso tiene una sola ráfaga de CPU que se ejecuta completamente
    - En cada momento, se selecciona el proceso con menor tiempo de CPU restante
    
    CARACTERÍSTICAS:
    - No expulsivo: no hay preempción una vez que comienza la ejecución
    - Sin bloqueos: no hay operaciones de E/S
    - Optimiza tiempo de respuesta: los trabajos cortos terminan rápido
    - Puede causar inanición: trabajos largos pueden esperar indefinidamente
    
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
    completed = 0  # Contador de procesos completados
    n = len(processes)  # Total de procesos a procesar

    # Verificar que los procesos tengan remaining_time inicializado correctamente
    # (esto es una verificación de seguridad, remaining_time ya viene de Process)
    for p in processes:
        # remaining_time ya viene inicializado de Process(bursts=[cpu])
        pass

    # BUCLE PRINCIPAL: Simular hasta que todos los procesos terminen
    while completed < n:  # Mientras no se completen todos los procesos
        
        # FASE 1: IDENTIFICAR PROCESOS ELEGIBLES
        # Buscar procesos que han llegado y no han terminado
        elegibles = [p for p in processes if p.arrival_time <= time and p.completion_time is None]

        # FASE 2: MANEJAR CPU OCIOSA
        if not elegibles:  # Si no hay procesos elegibles
            time += 1  # Avanzar tiempo y continuar en la siguiente iteración
            continue

        # FASE 3: SELECCIÓN DE PROCESO (CRITERIO SJF)
        # Elegir el proceso con menor remaining_time (trabajo más corto)
        # SJF: Shortest Job First - el trabajo más corto primero
        current = min(elegibles, key=lambda p: p.remaining_time)

        # FASE 4: EJECUTAR PROCESO COMPLETAMENTE
        # Marcar tiempo de inicio si es la primera vez que se ejecuta
        if current.start_time is None:  # Si es la primera vez que se ejecuta
            current.start_time = time  # Marcar tiempo de inicio del proceso

        # Ejecutar el proceso completamente (SJF es no expulsivo)
        start = time  # Guardar tiempo de inicio de esta ejecución
        cpu = current.remaining_time  # Tiempo de CPU restante (equivale a bursts[0])
        time += cpu  # Avanzar el reloj del sistema por el tiempo de CPU completo
        gantt.append((current.pid, start, time))  # Registrar en el diagrama de Gantt

        # FASE 5: MARCAR PROCESO COMO COMPLETADO
        current.completion_time = time  # Marcar tiempo de finalización
        current.calculate_metrics()  # Calcular métricas del proceso (TR, TE, etc.)
        completed += 1  # Incrementar contador de procesos completados

    # Retornar resultados de la simulación
    return gantt, processes
