from copy import deepcopy
from collections import deque

def round_robin(process_list, quantum):
    """
    ALGORITMO ROUND ROBIN (RR) - EXPULSIVO SIN BLOQUEOS
    
    FUNCIONAMIENTO:
    - Los procesos se ejecutan en turnos de tiempo fijo (quantum)
    - Cuando un proceso termina su quantum, se suspende y va al final de la cola
    - El siguiente proceso en la cola toma el CPU
    - Si un proceso termina antes de completar su quantum, libera el CPU inmediatamente
    - No hay bloqueos de E/S, solo ráfagas de CPU
    
    CARACTERÍSTICAS:
    - Expulsivo: los procesos pueden ser interrumpidos por el quantum
    - Sin bloqueos: no hay operaciones de E/S
    - Justo: todos los procesos reciben tiempo de CPU equitativo
    - Responsivo: los procesos no esperan mucho tiempo para ejecutarse
    
    PARÁMETROS:
    - process_list: Lista de objetos Process con bursts=[CPU]
    - quantum: Tiempo máximo que un proceso puede ejecutarse continuamente
    
    RETORNA:
    - gantt_chart: Lista de tuplas (pid, start, end) para el diagrama de Gantt
    - processes: Lista de procesos con métricas calculadas
    """
    
    # Crear copia profunda para no modificar la lista original
    processes = deepcopy(process_list)
    
    # Inicializar variables del simulador
    n = len(processes)  # Total de procesos a procesar
    time = 0  # Reloj del sistema (tiempo actual de simulación)
    completed = 0  # Contador de procesos completados
    gantt_chart = []  # Lista para almacenar el diagrama de Gantt

    # Estructuras de datos para Round Robin
    ready_queue = deque()  # Cola de procesos listos (FIFO con deque para eficiencia)
    
    # Ordenar procesos por tiempo de llegada, luego por PID para consistencia
    # Esto asegura un orden predecible cuando hay empates en llegada
    procesos_pendientes = sorted(processes, key=lambda p: (p.arrival_time, p.pid))

    # Variables para controlar cambios de proceso en el diagrama de Gantt
    current_pid = None  # PID del proceso actualmente en ejecución
    start_time = None  # Tiempo de inicio del bloque actual en Gantt

    # BUCLE PRINCIPAL: Simular hasta que todos los procesos terminen
    while completed < n:  # Mientras no se completen todos los procesos
        
        # FASE 1: ENCOLAR LLEGADAS AL TIEMPO ACTUAL
        # Buscar procesos que llegan exactamente en este momento
        procesos_que_llegan = []
        for p in procesos_pendientes:
            # Verificar si el proceso cumple las condiciones para ser encolado:
            # - Llega exactamente en este momento (arrival_time == time)
            # - No está ya en la cola de listos
            # - Aún tiene tiempo restante para ejecutar
            if p.arrival_time == time and p not in ready_queue and p.remaining_time > 0:
                procesos_que_llegan.append(p)
        
        # Ordenar por PID para mantener consistencia y agregar al final de la cola
        procesos_que_llegan.sort(key=lambda p: p.pid)
        for p in procesos_que_llegan:
            ready_queue.append(p)  # Agregar al final de la cola (FIFO)

        # FASE 2: EJECUTAR PROCESO
        if ready_queue:  # Si hay procesos listos para ejecutar
            
            # Seleccionar proceso: Round Robin = FIFO con quantum
            current = ready_queue.popleft()  # Tomar el primero de la cola

            # CONTROL DE CAMBIOS DE PROCESO EN GANTT
            if current_pid != current.pid:  # Si cambió el proceso
                if current_pid is not None:  # Si había un proceso anterior
                    gantt_chart.append((current_pid, start_time, time))  # Cerrar bloque anterior
                current_pid = current.pid  # Actualizar PID actual
                start_time = time  # Marcar inicio del nuevo bloque
                
                # Marcar tiempo de inicio si es la primera vez que se ejecuta
                if current.start_time is None:  # Si es la primera vez que se ejecuta
                    current.start_time = time  # Marcar tiempo de inicio del proceso

            # FASE 3: EJECUTAR PROCESO POR QUANTUM
            # Ejecutar hasta quantum o hasta que termine (lo que ocurra primero)
            exec_time = min(quantum, current.remaining_time)  # Tiempo a ejecutar
            current.remaining_time -= exec_time  # Reducir tiempo restante del proceso
            time += exec_time  # Avanzar el reloj del sistema

            # FASE 4: ENCOLAR LLEGADAS DURANTE LA EJECUCIÓN
            # Buscar procesos que llegaron durante la ejecución del proceso actual
            procesos_nuevos = []
            for p in procesos_pendientes:
                # Verificar si llegó durante la ejecución del proceso actual
                # (entre time - exec_time y time)
                if time - exec_time < p.arrival_time <= time and p.remaining_time > 0 and p not in ready_queue:
                    procesos_nuevos.append(p)
            
            # Ordenar por PID y agregar al final de la cola
            procesos_nuevos.sort(key=lambda p: p.pid)
            for p in procesos_nuevos:
                ready_queue.append(p)  # Agregar al final de la cola

            # FASE 5: DECIDIR QUÉ HACER CON EL PROCESO ACTUAL
            if current.remaining_time > 0:  # Si el proceso no terminó
                # Agregar el proceso actual al final de la cola (Round Robin)
                # Esto implementa la rotación de procesos
                ready_queue.append(current)
            else:  # Si el proceso terminó
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
