from copy import deepcopy

def srtf_blocking(process_list):
    """
    ALGORITMO SRTF (Shortest Remaining Time First) - EXPULSIVO CON BLOQUEOS
    
    FUNCIONAMIENTO:
    - Los procesos se ejecutan en orden de tiempo total de CPU restante (el más corto primero)
    - En cada unidad de tiempo, se selecciona el proceso con menor tiempo total restante
    - Los procesos pueden ser interrumpidos si llega uno con menor tiempo total restante
    - Los procesos pueden tener múltiples ráfagas de CPU y E/S (bloqueos)
    - Cuando un proceso termina una ráfaga de CPU, puede ir a bloqueo o continuar con otra CPU
    - Cuando un proceso termina un bloqueo, regresa a la cola de listos
    - Se respeta la prioridad: procesos que terminan CPU tienen prioridad sobre los que salen de bloqueo
    
    CARACTERÍSTICAS:
    - Expulsivo: los procesos pueden ser preemptados en cualquier momento
    - Con bloqueos: maneja operaciones de E/S (Entrada/Salida)
    - Optimiza tiempo de respuesta: los trabajos cortos tienen prioridad
    - Puede causar inanición: trabajos largos pueden ser postergados indefinidamente
    - Muy responsivo: responde inmediatamente a trabajos más cortos
    - Maneja múltiples ráfagas: CPU → E/S → CPU → E/S → ...
    
    PARÁMETROS:
    - process_list: Lista de objetos Process con bursts=[CPU, E/S, CPU, E/S, ...]
    
    RETORNA:
    - gantt: Lista de tuplas (pid, start, end, tipo) para el diagrama de Gantt
    - processes: Lista de procesos con métricas calculadas
    """

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

    def handle_post(proc, t, destino_cpu, destino_unblock, destino_blocked, gantt):
        """
        FUNCIÓN AUXILIAR: Resolver transición tras fin de ráfaga.
        
        Determina qué hacer con un proceso después de que termina una ráfaga.
        Puede ir a CPU, bloqueo, o terminar.
        
        Args:
            proc: Proceso a procesar
            t: Tiempo actual
            destino_cpu: Buffer de procesos que van a CPU
            destino_unblock: Buffer de procesos que salen de bloqueo
            destino_blocked: Lista de procesos bloqueados
            gantt: Lista del diagrama de Gantt
            
        Returns:
            bool: True si el proceso terminó, False si continúa
        """
        # Primero saltar ráfagas 0 si las hay
        if collapse_zeros(proc, t):
            return True  # El proceso terminó
        
        # Determinar qué tipo de ráfaga sigue
        if proc.is_cpu_burst():  # Si la siguiente ráfaga es de CPU
            destino_cpu.append(proc)  # Agregar al buffer correspondiente
        else:  # Si la siguiente ráfaga es de bloqueo
            dur = proc.bursts[proc.current_burst_index]  # Duración del bloqueo
            if dur > 0:  # Si tiene duración
                gantt.append((proc.pid, t, t + dur, "BLOCK"))  # Registrar bloqueo en Gantt
                destino_blocked.append((proc, t + dur))  # Agregar a cola de bloqueados
            else:  # Si es de duración 0 (bloqueo instantáneo)
                proc.advance_burst()  # Avanzar a la siguiente ráfaga
                # Llamar recursivamente para procesar la siguiente ráfaga
                return handle_post(proc, t, destino_cpu, destino_unblock, destino_blocked, gantt)
        return False  # El proceso continúa

    # Crear copia profunda para no modificar la lista original
    processes = deepcopy(process_list)
    
    # FASE DE INICIALIZACIÓN
    # Configurar atributos necesarios para cada proceso
    for idx, p in enumerate(processes):
        # Guardar copia original de bursts para referencia
        if not hasattr(p, "bursts_original"):
            p.bursts_original = p.bursts[:]
        
        # Asignar secuencia para desempates
        p._seq = idx
        
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
                # Procesar llegada usando la función auxiliar
                if handle_post(p, t, enq_cpu, enq_unblock, blocked, gantt):
                    completed += 1

    def process_unblocks_leq_t(t):
        """
        FUNCIÓN AUXILIAR: Procesar desbloqueos hasta tiempo t (incluido).
        
        Busca todos los procesos que terminan su bloqueo hasta el tiempo t
        y los procesa según su tipo de siguiente ráfaga.
        
        Args:
            t: Tiempo hasta el cual buscar desbloqueos
        """
        nonlocal completed
        for (bp, unb) in blocked[:]:  # Iterar sobre una copia de la lista
            if unb <= t:  # Si el bloqueo termina en este momento o antes
                blocked.remove((bp, unb))  # Remover de la cola de bloqueados
                bp.advance_burst()  # Avanzar a la siguiente ráfaga
                # Procesar desbloqueo usando la función auxiliar
                if handle_post(bp, t, enq_unblock, enq_unblock, blocked, gantt):
                    completed += 1

    # PROCESAR LLEGADAS INICIALES
    enqueue_arrivals_leq_t(time)
    if enq_cpu or enq_unblock:
        ready.extend(enq_cpu)  # Agregar procesos de CPU primero
        ready.extend(enq_unblock)  # Luego los de desbloqueo
        enq_cpu.clear()  # Limpiar buffer de CPU
        enq_unblock.clear()  # Limpiar buffer de desbloqueo

    # Variables para controlar la ejecución actual
    current = None  # Proceso actualmente en ejecución
    seg_start = None  # Tiempo de inicio del segmento actual en Gantt

    # BUCLE PRINCIPAL: Simular hasta que todos los procesos terminen
    while completed < n:  # Mientras no se completen todos los procesos
        
        # FASE 1: PROCESAR EVENTOS
        # Procesar desbloqueos que vencen en este momento
        process_unblocks_leq_t(time)
        
        # Procesar llegadas en este momento
        enqueue_arrivals_leq_t(time)

        # FASE 2: VOLCAR BUFFERS A COLA DE LISTOS
        # Volcar buffers a ready respetando prioridades
        if enq_cpu or enq_unblock:
            ready.extend(enq_cpu)  # Agregar procesos de CPU primero
            ready.extend(enq_unblock)  # Luego los de desbloqueo
            enq_cpu.clear()  # Limpiar buffer de CPU
            enq_unblock.clear()  # Limpiar buffer de desbloqueo

        # FASE 3: IDENTIFICAR PROCESOS ELEGIBLES
        # Filtrar procesos que están en ráfaga de CPU y no han terminado
        eligibles = [p for p in ready if p.is_cpu_burst() and not p.is_finished()]
        
        # FASE 4: MANEJAR CPU OCIOSA
        if not eligibles:  # Si no hay procesos elegibles
            # Buscar próximos eventos (llegadas y desbloqueos)
            future_arrivals = [p.arrival_time for p in processes if p.pid not in arrived and p.completion_time is None]
            future_unblocks = [unb for _, unb in blocked]
            
            # Verificar si no hay más eventos futuros
            if not future_arrivals and not future_unblocks:
                break  # Terminar simulación
            
            # Calcular el próximo evento
            next_event = min(future_arrivals + future_unblocks) if (future_arrivals or future_unblocks) else None
            
            # Avanzar tiempo hasta el próximo evento
            if next_event is None:
                time += 1
            elif next_event > time:
                gantt.append(("IDLE", time, next_event, "IDLE"))  # Registrar período IDLE
                time = next_event
            else:
                time += 1
            
            # Limpiar proceso actual
            current = None
            seg_start = None
            continue

        # FASE 5: SELECCIÓN DE PROCESO (CRITERIO SRTF)
        # Ordenar por criterio SRTF con desempates
        eligibles.sort(key=lambda x: (x.get_total_cpu_remaining(), x.arrival_time, x._seq, x.pid))
        candidate = eligibles[0]  # Seleccionar el proceso con menor tiempo total restante

        # FASE 6: CONTROL DE CAMBIOS DE PROCESO EN GANTT
        if current is not candidate:  # Si cambió el proceso
            # Cerrar segmento anterior si existe
            if current is not None and seg_start is not None and time > seg_start:
                gantt.append((current.pid, seg_start, time, "CPU"))
            
            # Cambiar al nuevo proceso
            current = candidate
            seg_start = time  # Marcar inicio del nuevo segmento
            
            # Marcar tiempo de inicio si es la primera vez que se ejecuta
            if current.start_time is None:
                current.start_time = time

        # FASE 7: EJECUTAR PROCESO POR 1 UNIDAD DE TIEMPO
        # Ejecutar 1 tick de CPU (SRTF es expulsivo por unidades)
        current.bursts[current.current_burst_index] -= 1  # Reducir ráfaga actual
        current.remaining_time = current.get_total_cpu_remaining()  # Actualizar tiempo restante
        time += 1  # Avanzar el reloj del sistema

        # FASE 8: VERIFICAR SI TERMINÓ LA RÁFAGA
        if current.bursts[current.current_burst_index] == 0:  # Si terminó la ráfaga de CPU
            # Cerrar segmento de CPU en el diagrama de Gantt
            gantt.append((current.pid, seg_start, time, "CPU"))
            current.advance_burst()  # Avanzar a la siguiente ráfaga
            
            if current.is_finished():  # Si terminó el proceso
                current.completion_time = time
                completed += 1
                current = None  # Liberar CPU
                seg_start = None
            else:  # Si aún tiene ráfagas
                if handle_post(current, time, enq_cpu, enq_unblock, blocked, gantt):
                    completed += 1
                current = None  # Liberar CPU
                seg_start = None
            
            # Volcar buffers después de terminar ráfaga
            if enq_cpu or enq_unblock:
                ready.extend(enq_cpu)  # Agregar procesos de CPU primero
                ready.extend(enq_unblock)  # Luego los de desbloqueo
                enq_cpu.clear()  # Limpiar buffer de CPU
                enq_unblock.clear()  # Limpiar buffer de desbloqueo
            continue  # Volver al inicio del bucle

        # FASE 9: VERIFICAR PREEMPCIÓN
        # Procesar eventos que pueden causar preempción
        process_unblocks_leq_t(time)  # Procesar desbloqueos
        enqueue_arrivals_leq_t(time)  # Procesar llegadas
        
        # Volcar buffers después de procesar eventos
        if enq_cpu or enq_unblock:
            ready.extend(enq_cpu)  # Agregar procesos de CPU primero
            ready.extend(enq_unblock)  # Luego los de desbloqueo
            enq_cpu.clear()  # Limpiar buffer de CPU
            enq_unblock.clear()  # Limpiar buffer de desbloqueo

        # FASE 10: VERIFICAR PREEMPCIÓN POR PROCESO MÁS CORTO
        # Re-evaluar si hay un proceso más corto que puede preemptar
        eligibles = [p for p in ready if p.is_cpu_burst() and not p.is_finished()]
        if eligibles:  # Si hay procesos elegibles
            # Ordenar por criterio SRTF
            eligibles.sort(key=lambda x: (x.get_total_cpu_remaining(), x.arrival_time, x._seq, x.pid))
            best = eligibles[0]  # El mejor proceso candidato
            
            # Verificar si debe preemptar al proceso actual
            if best is not current and best.get_total_cpu_remaining() < current.get_total_cpu_remaining():
                # Preemptar: cerrar segmento actual y cambiar proceso
                gantt.append((current.pid, seg_start, time, "CPU"))  # Cerrar segmento actual
                current.ready_since = time  # Marcar tiempo desde que está listo
                enq_cpu.append(current)  # Agregar proceso actual al buffer
                current = None  # Liberar CPU
                seg_start = None
                
                # Volcar buffers inmediatamente
                ready.extend(enq_cpu)  # Agregar procesos de CPU primero
                ready.extend(enq_unblock)  # Luego los de desbloqueo
                enq_cpu.clear()  # Limpiar buffer de CPU
                enq_unblock.clear()  # Limpiar buffer de desbloqueo

    # FASE FINAL: CERRAR ÚLTIMO SEGMENTO
    # Cerrar el último segmento del diagrama de Gantt si existe
    if current is not None and seg_start is not None and time > seg_start:
        gantt.append((current.pid, seg_start, time, "CPU"))

    # Retornar resultados de la simulación
    return gantt, processes
