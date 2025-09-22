from copy import deepcopy

def sjf_blocking(process_list):
    """
    ALGORITMO SJF (Shortest Job First) - NO EXPULSIVO CON BLOQUEOS
    
    FUNCIONAMIENTO:
    - Los procesos se ejecutan en orden de duración total de CPU restante (el más corto primero)
    - Una vez que un proceso comienza a ejecutarse, no puede ser interrumpido
    - Los procesos pueden tener múltiples ráfagas de CPU y E/S (bloqueos)
    - Cuando un proceso termina una ráfaga de CPU, puede ir a bloqueo o continuar con otra CPU
    - Cuando un proceso termina un bloqueo, regresa a la cola de listos
    - Se respeta la prioridad: procesos que terminan CPU tienen prioridad sobre los que salen de bloqueo
    
    CARACTERÍSTICAS:
    - No expulsivo: no hay preempción una vez que comienza la ejecución
    - Con bloqueos: maneja operaciones de E/S (Entrada/Salida)
    - Optimiza tiempo de respuesta: los trabajos cortos terminan rápido
    - Puede causar inanición: trabajos largos pueden esperar indefinidamente
    - Maneja múltiples ráfagas: CPU → E/S → CPU → E/S → ...
    
    PARÁMETROS:
    - process_list: Lista de objetos Process con bursts=[CPU, E/S, CPU, E/S, ...]
    
    RETORNA:
    - gantt: Lista de tuplas (pid, start, end, tipo) para el diagrama de Gantt
    - processes: Lista de procesos con métricas calculadas
    """
    
    # Crear copia profunda para no modificar la lista original
    processes = deepcopy(process_list)

    def cpu_total_restante(p):
        """
        FUNCIÓN AUXILIAR: Calcula el total de CPU restante desde la posición actual.
        
        Esta función es crucial para SJF ya que determina la prioridad del proceso.
        Calcula cuánto tiempo de CPU le queda al proceso desde su posición actual.
        
        Args:
            p: Proceso del cual calcular el tiempo restante
            
        Returns:
            int: Total de tiempo de CPU restante
        """
        idx = p.current_burst_index  # Índice de la ráfaga actual
        if idx >= len(p.bursts):  # Si el proceso terminó
            return 0
        
        total = 0
        # Si estamos en una ráfaga de CPU (índice par)
        if idx % 2 == 0:
            # El burst actual YA refleja lo que queda (se va descontando)
            total += p.bursts[idx]
            start = idx + 2  # Siguiente CPU (saltar el bloqueo)
        else:
            # Si estamos en bloqueo, la próxima CPU es idx+1
            start = idx + 1
        
        # Sumar las ráfagas de CPU futuras
        for i in range(start, len(p.bursts), 2):  # Solo índices pares (CPU)
            total += p.bursts[i]
        
        return total

    # FASE DE INICIALIZACIÓN
    # Configurar atributos necesarios para cada proceso
    for idx, p in enumerate(processes):
        # Guardar copia original de bursts para referencia
        if not hasattr(p, "bursts_original"):
            p.bursts_original = p.bursts[:]
        
        # Asignar secuencia para desempates
        p._seq = idx
        
        # Calcular tiempo total de CPU (solo ráfagas pares)
        p.remaining_time = sum(b for i, b in enumerate(p.bursts) if i % 2 == 0)
        
        # Inicializar atributos de tiempo
        p.ready_since = None  # Tiempo desde que está listo
        p.start_time = None  # Tiempo de primera ejecución
        p.completion_time = None  # Tiempo de finalización

    # Inicializar variables del simulador
    time = 0  # Reloj del sistema (tiempo actual de simulación)
    gantt = []  # Lista para almacenar el diagrama de Gantt
    ready = []  # Lista de procesos listos para ejecutar
    blocked = []  # Lista de procesos bloqueados: (proceso, unblock_time)
    completed = 0  # Contador de procesos completados
    n = len(processes)  # Total de procesos a procesar
    arrived = set()  # Conjunto de PIDs que ya llegaron al sistema

    # Buffers de encolado para respetar la prioridad
    enq_cpu = []      # procesos que entran a ready por llegada o por terminar CPU
    enq_unblock = []  # procesos que entran a ready por desbloqueo

    def collapse_zeros(proc, t):
        """
        FUNCIÓN AUXILIAR: Saltar ráfagas de duración 0 encadenadas.
        
        Si un proceso tiene ráfagas de duración 0, las salta automáticamente
        hasta encontrar una ráfaga con duración > 0 o hasta que termine el proceso.
        
        Args:
            proc: Proceso a procesar
            t: Tiempo actual
            
        Returns:
            bool: True si el proceso terminó, False si aún tiene ráfagas
        """
        # Saltar todas las ráfagas de duración 0 consecutivas
        while proc.current_burst_index < len(proc.bursts) and proc.bursts[proc.current_burst_index] == 0:
            proc.advance_burst()  # Avanzar a la siguiente ráfaga
        
        # Verificar si el proceso terminó después de saltar ráfagas 0
        if proc.current_burst_index >= len(proc.bursts):
            proc.completion_time = t  # Marcar tiempo de finalización
            return True  # El proceso terminó
        return False  # El proceso aún tiene ráfagas

    def enqueue_arrivals_leq_t(t):
        """
        FUNCIÓN AUXILIAR: Encolar llegadas hasta tiempo t (incluido) con prioridad de llegada.
        
        Busca todos los procesos que han llegado al sistema hasta el tiempo t
        y los procesa según su tipo de primera ráfaga.
        
        Args:
            t: Tiempo hasta el cual buscar llegadas
        """
        nonlocal completed
        for p in processes:
            # Saltar procesos que ya llegaron
            if p.pid in arrived:
                continue
            
            # Verificar si el proceso llegó y no ha terminado
            if p.arrival_time <= t and p.completion_time is None:
                arrived.add(p.pid)  # Marcar como llegado
                
                # Saltar ráfagas 0 si las hay
                if collapse_zeros(p, t):
                    completed += 1
                    continue
                
                # Determinar qué tipo de ráfaga tiene el proceso al llegar
                if p.is_cpu_burst():  # Si la primera ráfaga es de CPU
                    p.ready_since = p.arrival_time  # Marcar tiempo desde que está listo
                    enq_cpu.append(p)  # Agregar al buffer de CPU (alta prioridad)
                else:  # Si la primera ráfaga es de bloqueo
                    dur = p.bursts[p.current_burst_index]  # Duración del bloqueo
                    if dur > 0:  # Si tiene duración
                        gantt.append((p.pid, t, t + dur, "BLOCK"))  # Registrar bloqueo en Gantt
                        blocked.append((p, t + dur))  # Agregar a cola de bloqueados
                    else:  # Si es de duración 0 (bloqueo instantáneo)
                        p.advance_burst()  # Avanzar a la siguiente ráfaga
                        if collapse_zeros(p, t):
                            completed += 1
                        elif p.is_cpu_burst():  # Si la siguiente es CPU
                            p.ready_since = p.arrival_time  # Marcar tiempo desde que está listo
                            enq_cpu.append(p)  # Agregar al buffer de CPU

    # PROCESAR LLEGADAS INICIALES
    enqueue_arrivals_leq_t(time)
    if enq_cpu or enq_unblock:
        ready.extend(enq_cpu)  # Agregar procesos de CPU primero
        ready.extend(enq_unblock)  # Luego los de desbloqueo
        enq_cpu.clear()  # Limpiar buffer de CPU
        enq_unblock.clear()  # Limpiar buffer de desbloqueo

    # BUCLE PRINCIPAL: Simular hasta que todos los procesos terminen
    while completed < n:  # Mientras no se completen todos los procesos
        
        # FASE 1: PROCESAR DESBLOQUEOS
        # Ordenar bloqueados por tiempo de desbloqueo
        if blocked:
            blocked.sort(key=lambda x: x[1])
        
        # Procesar desbloqueos que vencen en este momento
        for (bp, unb) in blocked[:]:  # Iterar sobre una copia de la lista
            if unb <= time:  # Si el bloqueo termina en este momento o antes
                blocked.remove((bp, unb))  # Remover de la cola de bloqueados
                bp.advance_burst()  # Avanzar a la siguiente ráfaga
                
                # Saltar ráfagas 0 si las hay
                if collapse_zeros(bp, time):
                    completed += 1
                    continue
                
                # Determinar qué tipo de ráfaga sigue
                if bp.is_cpu_burst():  # Si la siguiente ráfaga es de CPU
                    bp.ready_since = time  # Marcar tiempo desde que está listo
                    enq_unblock.append(bp)  # Agregar al buffer de desbloqueo (baja prioridad)
                else:  # Si la siguiente ráfaga es de bloqueo
                    dur = bp.bursts[bp.current_burst_index]  # Duración del bloqueo
                    if dur > 0:  # Si tiene duración
                        gantt.append((bp.pid, time, time + dur, "BLOCK"))  # Registrar bloqueo en Gantt
                        blocked.append((bp, time + dur))  # Agregar a cola de bloqueados
                    else:  # Si es de duración 0 (bloqueo instantáneo)
                        bp.advance_burst()  # Avanzar a la siguiente ráfaga
                        if collapse_zeros(bp, time):
                            completed += 1
                        elif bp.is_cpu_burst():  # Si la siguiente es CPU
                            bp.ready_since = time  # Marcar tiempo desde que está listo
                            enq_unblock.append(bp)  # Agregar al buffer de desbloqueo

        # FASE 2: PROCESAR LLEGADAS
        enqueue_arrivals_leq_t(time)

        # FASE 3: VOLCAR BUFFERS A COLA DE LISTOS
        # Volcar buffers a ready respetando prioridades
        if enq_cpu or enq_unblock:
            ready.extend(enq_cpu)  # Agregar procesos de CPU primero
            ready.extend(enq_unblock)  # Luego los de desbloqueo
            enq_cpu.clear()  # Limpiar buffer de CPU
            enq_unblock.clear()  # Limpiar buffer de desbloqueo

        # FASE 4: MANEJAR CPU OCIOSA
        # Si no hay procesos listos, saltar al siguiente evento
        if not ready:
            future_arrivals = [p.arrival_time for p in processes if p.pid not in arrived and p.completion_time is None]
            future_unblocks = [unb for _, unb in blocked]
            if not future_arrivals and not future_unblocks:
                break
            next_event = min(future_arrivals + future_unblocks) if (future_arrivals or future_unblocks) else None
            if next_event is None:
                time += 1
            elif next_event > time:
                gantt.append(("IDLE", time, next_event, "IDLE"))
                time = next_event
            else:
                time += 1
            continue

        # FASE 5: SELECCIÓN DE PROCESO (CRITERIO SJF)
        # Filtrar procesos que aún tienen ráfagas
        ready = [p for p in ready if p.current_burst_index < len(p.bursts)]
        
        # Ordenar por criterio SJF con desempates
        ready.sort(key=lambda x: (
            cpu_total_restante(x),  # SJF: menor tiempo total de CPU restante (prioridad principal)
            (x.ready_since if x.ready_since is not None else x.arrival_time),  # FIFO en empates
            x.pid  # Estabilidad (desempate por PID)
        ))

        # Seleccionar el proceso con menor tiempo total de CPU restante
        current = ready.pop(0)
        
        # Marcar tiempo de inicio si es la primera vez que se ejecuta
        if current.start_time is None:
            current.start_time = time

        # FASE 6: EJECUTAR RÁFAGA COMPLETA (SJF es no expulsivo)
        start = time  # Tiempo de inicio de esta ejecución
        cpu_dur = current.bursts[current.current_burst_index]  # Duración de la ráfaga de CPU
        if cpu_dur <= 0:
            if collapse_zeros(current, time):
                completed += 1
            else:
                if current.is_cpu_burst():
                    current.ready_since = time
                    enq_cpu.append(current)
            continue

        time += cpu_dur
        
        # CRÍTICO: Actualizar tanto remaining_time como el burst actual
        if hasattr(current, "remaining_time") and current.remaining_time is not None:
            current.remaining_time -= cpu_dur
            if current.remaining_time < 0:
                current.remaining_time = 0
        
        # IMPORTANTE: Marcar la ráfaga como completada
        current.bursts[current.current_burst_index] = 0
        
        gantt.append((current.pid, start, time, "CPU"))

        # Avanzar bursts
        current.advance_burst()
        if collapse_zeros(current, time):
            completed += 1
            continue

        if current.is_cpu_burst():
            current.ready_since = time
            enq_cpu.append(current)
        else:
            dur = current.bursts[current.current_burst_index]
            if dur > 0:
                gantt.append((current.pid, time, time + dur, "BLOCK"))
                blocked.append((current, time + dur))
            else:
                current.advance_burst()
                if collapse_zeros(current, time):
                    completed += 1
                elif current.is_cpu_burst():
                    current.ready_since = time
                    enq_cpu.append(current)

        # Volcar buffers
        if enq_cpu or enq_unblock:
            ready.extend(enq_cpu)
            ready.extend(enq_unblock)
            enq_cpu.clear()
            enq_unblock.clear()

    return gantt, processes