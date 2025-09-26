from copy import deepcopy

def priority(process_list):
    """
    ALGORITMO DE PRIORIDADES - NO EXPULSIVO SIN BLOQUEOS
    
    FUNCIONAMIENTO:
    - Los procesos se ejecutan en orden de prioridad (mayor número = mayor prioridad)
    - Una vez que un proceso comienza a ejecutarse, no puede ser interrumpido
    - No hay bloqueos de E/S, solo ráfagas de CPU
    - Cada proceso tiene una sola ráfaga de CPU que se ejecuta completamente
    - En caso de empate de prioridad, se aplica FIFO (orden de llegada)
    
    CARACTERÍSTICAS:
    - No expulsivo: no hay preempción una vez que comienza la ejecución
    - Sin bloqueos: no hay operaciones de E/S
    - Basado en prioridades: mayor número = mayor prioridad
    - Desempate FIFO: en caso de empate de prioridad, el primero en llegar se ejecuta primero
    - Puede causar inanición: procesos de baja prioridad pueden esperar indefinidamente
    
    PARÁMETROS:
    - process_list: Lista de objetos Process con bursts=[CPU] y priority asignada
    
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

    # Verificar que los procesos tengan prioridad asignada
    for p in processes:
        # Verificar que el proceso tenga prioridad asignada (por defecto es 0)
        if not hasattr(p, 'priority'):
            p.priority = 0

    # BUCLE PRINCIPAL: Simular hasta que todos los procesos terminen
    while completed < n:  # Mientras no se completen todos los procesos
        
        # FASE 1: IDENTIFICAR PROCESOS ELEGIBLES
        # Buscar procesos que han llegado y no han terminado
        elegibles = [p for p in processes if p.arrival_time <= time and p.completion_time is None]

        # FASE 2: MANEJAR CPU OCIOSA
        if not elegibles:  # Si no hay procesos elegibles
            time += 1  # Avanzar tiempo y continuar en la siguiente iteración
            continue

        # FASE 3: SELECCIÓN DE PROCESO (CRITERIO DE PRIORIDADES)
        # Ordenar por prioridad (mayor número = mayor prioridad), luego FIFO en empates
        elegibles.sort(key=lambda p: (
            -p.priority,  # Prioridad descendente (mayor número primero)
            p.arrival_time,  # FIFO en empates (menor tiempo de llegada primero)
            p.pid  # Estabilidad (desempate por PID)
        ))
        
        # Seleccionar el proceso con mayor prioridad
        current = elegibles[0]  # Tomar el proceso con mayor prioridad

        # FASE 4: EJECUTAR PROCESO COMPLETAMENTE
        # Marcar tiempo de inicio si es la primera vez que se ejecuta
        if current.start_time is None:  # Si es la primera vez que se ejecuta
            current.start_time = time  # Marcar tiempo de inicio del proceso

        # Ejecutar el proceso completamente (algoritmo de prioridades es no expulsivo)
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

