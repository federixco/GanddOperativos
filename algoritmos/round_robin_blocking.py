from copy import deepcopy
from collections import deque

def round_robin_blocking(process_list, quantum):
    """
    ALGORITMO ROUND ROBIN (RR) - EXPULSIVO CON BLOQUEOS
    
    FUNCIONAMIENTO:
    - Los procesos se ejecutan en turnos de tiempo fijo (quantum)
    - Cuando un proceso termina su quantum, se suspende y va al final de la cola
    - El siguiente proceso en la cola toma el CPU
    - Los procesos pueden tener múltiples ráfagas de CPU y E/S (bloqueos)
    - Cuando un proceso termina una ráfaga de CPU, puede ir a bloqueo o continuar con otra CPU
    - Cuando un proceso termina un bloqueo, regresa a la cola de listos
    - Se respeta la prioridad: procesos que terminan CPU tienen prioridad sobre los que salen de bloqueo
    
    CARACTERÍSTICAS:
    - Expulsivo: los procesos pueden ser interrumpidos por el quantum
    - Con bloqueos: maneja operaciones de E/S (Entrada/Salida)
    - Justo: todos los procesos reciben tiempo de CPU equitativo
    - Responsivo: los procesos no esperan mucho tiempo para ejecutarse
    - Maneja múltiples ráfagas: CPU → E/S → CPU → E/S → ...
    
    PARÁMETROS:
    - process_list: Lista de objetos Process con bursts=[CPU, E/S, CPU, E/S, ...]
    - quantum: Tiempo máximo que un proceso puede ejecutarse continuamente
    
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

    def handle_after_cpu_or_arrival(proc, t, enq_cpu, blocked, gantt):
        """
        FUNCIÓN AUXILIAR: Resolver transición tras llegada o fin de CPU.
        
        Determina qué hacer con un proceso después de que termina una ráfaga de CPU
        o cuando llega al sistema. Puede ir a CPU, bloqueo, o terminar.
        
        Args:
            proc: Proceso a procesar
            t: Tiempo actual
            enq_cpu: Buffer de procesos que van a CPU
            blocked: Lista de procesos bloqueados
            gantt: Lista del diagrama de Gantt
            
        Returns:
            bool: True si el proceso terminó, False si continúa
        """
        # Primero saltar ráfagas 0 si las hay
        if collapse_zeros(proc, t):
            return True  # El proceso terminó
        
        # Determinar qué tipo de ráfaga sigue
        if proc.is_cpu_burst():  # Si la siguiente ráfaga es de CPU
            enq_cpu.append(proc)  # Agregar al buffer de CPU (alta prioridad)
        else:  # Si la siguiente ráfaga es de bloqueo
            dur = proc.bursts[proc.current_burst_index]  # Duración del bloqueo
            if dur > 0:  # Si tiene duración
                gantt.append((proc.pid, t, t + dur, "BLOCK"))  # Registrar bloqueo en Gantt
                blocked.append((proc, t + dur))  # Agregar a cola de bloqueados
            else:  # Si es de duración 0 (bloqueo instantáneo)
                proc.advance_burst()  # Avanzar a la siguiente ráfaga
                # Llamar recursivamente para procesar la siguiente ráfaga
                return handle_after_cpu_or_arrival(proc, t, enq_cpu, blocked, gantt)
        return False  # El proceso continúa

    def handle_after_unblock(proc, t, enq_unblock, blocked, gantt):
        """
        FUNCIÓN AUXILIAR: Resolver transición tras fin de bloqueo.
        
        Determina qué hacer con un proceso después de que termina un bloqueo.
        Puede ir a CPU, otro bloqueo, o terminar.
        
        Args:
            proc: Proceso a procesar
            t: Tiempo actual
            enq_unblock: Buffer de procesos que salen de bloqueo
            blocked: Lista de procesos bloqueados
            gantt: Lista del diagrama de Gantt
            
        Returns:
            bool: True si el proceso terminó, False si continúa
        """
        # Primero saltar ráfagas 0 si las hay
        if collapse_zeros(proc, t):
            return True  # El proceso terminó
        
        # Determinar qué tipo de ráfaga sigue
        if proc.is_cpu_burst():  # Si la siguiente ráfaga es de CPU
            enq_unblock.append(proc)  # Agregar al buffer de desbloqueo (baja prioridad)
        else:  # Si la siguiente ráfaga es de bloqueo
            dur = proc.bursts[proc.current_burst_index]  # Duración del bloqueo
            if dur > 0:  # Si tiene duración
                gantt.append((proc.pid, t, t + dur, "BLOCK"))  # Registrar bloqueo en Gantt
                blocked.append((proc, t + dur))  # Agregar a cola de bloqueados
            else:  # Si es de duración 0 (bloqueo instantáneo)
                proc.advance_burst()  # Avanzar a la siguiente ráfaga
                # Llamar recursivamente para procesar la siguiente ráfaga
                return handle_after_unblock(proc, t, enq_unblock, blocked, gantt)
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
        
        # Manejar procesos sin ráfagas (caso especial)
        if not p.bursts:
            p.current_burst_index = 0
            p.remaining_time = 0
            p.completion_time = 0

    # Inicializar variables del simulador
    time = 0  # Reloj del sistema (tiempo actual de simulación)
    gantt = []  # Lista para almacenar el diagrama de Gantt
    ready = deque()  # Cola de procesos listos (FIFO con deque para eficiencia)
    blocked = []  # Lista de procesos bloqueados: (proceso, unblock_time)
    completed = sum(1 for p in processes if p.completion_time is not None)  # Contador de completados
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
                if handle_after_cpu_or_arrival(p, t, enq_cpu, blocked, gantt):
                    completed += 1

    # PROCESAR LLEGADAS INICIALES
    # Buscar procesos que llegan en tiempo 0
    enqueue_arrivals_leq_t(time)
    
    # Volcar buffers iniciales a la cola de listos
    if enq_cpu or enq_unblock:
        ready.extend(enq_cpu)  # Agregar procesos de CPU primero
        ready.extend(enq_unblock)  # Luego los de desbloqueo
        enq_cpu.clear()  # Limpiar buffer de CPU
        enq_unblock.clear()  # Limpiar buffer de desbloqueo

    # BUCLE PRINCIPAL: Simular hasta que todos los procesos terminen
    while completed < n:  # Mientras no se completen todos los procesos
        
        # FASE 1: MANEJAR CPU OCIOSA
        # Si no hay procesos listos, saltar al siguiente evento
        if not ready:
            # Buscar próximos eventos (llegadas y desbloqueos)
            future_arrivals = [p.arrival_time for p in processes if p.pid not in arrived and p.completion_time is None]
            future_unblocks = [unb for _, unb in blocked]
            
            # Verificar si no hay más eventos futuros
            if not future_arrivals and not future_unblocks:
                # Procesar procesos que terminaron sin completar
                for p in processes:
                    if p.completion_time is None and p.current_burst_index >= len(p.bursts):
                        p.completion_time = time
                        completed += 1
                break  # Terminar simulación
            
            # Calcular el próximo evento
            next_event = min(future_arrivals + future_unblocks) if (future_arrivals or future_unblocks) else time + 1
            
            # Avanzar tiempo hasta el próximo evento
            if next_event > time:
                gantt.append(("IDLE", time, next_event, "IDLE"))  # Registrar período IDLE
                time = next_event
            else:
                time += 1

            # FASE 2: PROCESAR EVENTOS EN EL TIEMPO ACTUAL
            # Procesar desbloqueos que vencen en este momento
            for (bp, unb) in blocked[:]:  # Iterar sobre una copia de la lista
                if unb == time:  # Si el bloqueo termina en este momento
                    blocked.remove((bp, unb))  # Remover de la cola de bloqueados
                    bp.advance_burst()  # Avanzar a la siguiente ráfaga
                    if handle_after_unblock(bp, time, enq_unblock, blocked, gantt):
                        completed += 1

            # Procesar llegadas en este momento
            enqueue_arrivals_leq_t(time)
            
            # Volcar buffers a la cola de listos
            if enq_cpu or enq_unblock:
                ready.extend(enq_cpu)  # Agregar procesos de CPU primero
                ready.extend(enq_unblock)  # Luego los de desbloqueo
                enq_cpu.clear()  # Limpiar buffer de CPU
                enq_unblock.clear()  # Limpiar buffer de desbloqueo
            continue  # Volver al inicio del bucle

        # FASE 3: SELECCIÓN DE PROCESO (CRITERIO ROUND ROBIN)
        # Seleccionar el primer proceso de la cola (FIFO)
        current = ready.popleft()

        # FASE 4: VERIFICAR TIPO DE RÁFAGA
        # Si el proceso no está en una ráfaga de CPU, procesarlo
        if not current.is_cpu_burst():
            if handle_after_cpu_or_arrival(current, time, enq_cpu, blocked, gantt):
                completed += 1
            # Volcar buffers después de procesar
            if enq_cpu or enq_unblock:
                ready.extend(enq_cpu)  # Agregar procesos de CPU primero
                ready.extend(enq_unblock)  # Luego los de desbloqueo
                enq_cpu.clear()  # Limpiar buffer de CPU
                enq_unblock.clear()  # Limpiar buffer de desbloqueo
            continue  # Volver al inicio del bucle

        # FASE 5: MARCAR TIEMPO DE INICIO
        # Marcar tiempo de inicio si es la primera vez que se ejecuta
        if current.start_time is None:
            current.start_time = time

        # FASE 6: SINCRONIZAR TIEMPO RESTANTE
        # IMPORTANTE: Sincronizar remaining_time con el burst actual
        current.remaining_time = current.bursts[current.current_burst_index]

        # FASE 7: CALCULAR TIEMPO DE EJECUCIÓN
        # Definir tramo a ejecutar (quantum o tiempo restante, lo que sea menor)
        exec_time = min(quantum, current.remaining_time)
        start = time  # Tiempo de inicio de esta ejecución
        end = time + exec_time  # Tiempo de fin de esta ejecución

        # FASE 8: PROCESAR EVENTOS DURANTE LA EJECUCIÓN
        # Procesar desbloqueos que ocurren durante la ejecución
        for (bp, unb) in sorted(blocked[:], key=lambda x: x[1]):  # Ordenar por tiempo de desbloqueo
            if time < unb <= end:  # Si el desbloqueo ocurre durante la ejecución
                blocked.remove((bp, unb))  # Remover de la cola de bloqueados
                bp.advance_burst()  # Avanzar a la siguiente ráfaga
                if handle_after_unblock(bp, unb, enq_unblock, blocked, gantt):
                    completed += 1

        # Procesar llegadas que ocurren durante la ejecución
        for p in processes:
            if p.pid in arrived:  # Saltar procesos que ya llegaron
                continue
            if time < p.arrival_time <= end and p.completion_time is None:  # Si llega durante la ejecución
                arrived.add(p.pid)  # Marcar como llegado
                if handle_after_cpu_or_arrival(p, p.arrival_time, enq_cpu, blocked, gantt):
                    completed += 1

        # FASE 9: EJECUTAR PROCESO
        # CRÍTICO: Actualizar AMBOS - remaining_time Y el burst actual
        current.remaining_time -= exec_time  # Reducir tiempo restante
        current.bursts[current.current_burst_index] -= exec_time  # ← ESTA LÍNEA ES CRÍTICA
        time = end  # Avanzar el reloj del sistema
        gantt.append((current.pid, start, end, "CPU"))  # Registrar ejecución en Gantt

        # FASE 10: DETERMINAR QUÉ HACER CON EL PROCESO
        # ¿Terminó la ráfaga o agotó el quantum?
        if current.remaining_time == 0:  # Si terminó la ráfaga de CPU
            current.bursts[current.current_burst_index] = 0  # Asegurar que queda en 0
            current.advance_burst()  # Avanzar a la siguiente ráfaga
            
            if current.current_burst_index >= len(current.bursts):  # Si terminó el proceso
                current.completion_time = time
                completed += 1
            else:  # Si aún tiene ráfagas
                if handle_after_cpu_or_arrival(current, time, enq_cpu, blocked, gantt):
                    completed += 1
        else:  # Si la ráfaga no terminó (agotó quantum)
            # Ráfaga no terminó → reencolar al final (Round Robin)
            current.ready_since = time  # Marcar tiempo desde que está listo
            enq_cpu.append(current)  # Agregar al buffer de CPU

        # FASE 11: VOLCAR BUFFERS CON PRIORIDAD
        # Volcar buffers a la cola de listos respetando prioridades
        if enq_cpu or enq_unblock:
            ready.extend(enq_cpu)  # Agregar procesos de CPU primero
            ready.extend(enq_unblock)  # Luego los de desbloqueo
            enq_cpu.clear()  # Limpiar buffer de CPU
            enq_unblock.clear()  # Limpiar buffer de desbloqueo

    # FASE FINAL: SALVAGUARDA
    # Procesar procesos que terminaron sin completar
    for p in processes:
        if p.completion_time is None and p.current_burst_index >= len(p.bursts):
            p.completion_time = time

    # Retornar resultados de la simulación
    return gantt, processes