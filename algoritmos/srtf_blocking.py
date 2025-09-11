from copy import deepcopy

def srtf_blocking(process_list):
    """
    SRTF expulsivo con soporte para procesos mixtos (con y sin bloqueos).
    - Criterio: CPU total restante (suma de CPUs restantes).
    - Se descuenta 1 tick en la ráfaga actual (bursts[idx]) y en remaining_time (total CPU) por cada tick.
    - Gantt: (pid, start, end, "CPU"/"BLOCK"), se cierra segmento en fin de ráfaga o preempción.
    """

    def total_cpu_restante(p):
        """Suma CPU restante de la ráfaga actual + CPUs futuras."""
        idx = p.current_burst_index
        if idx >= len(p.bursts):
            return 0
        if idx % 2 == 0:  # CPU
            # remaining_time representa el total de CPU restante (todas las CPUs)
            return p.remaining_time
        return float("inf")  # si está en bloqueo, no compite en ready

    def collapse_zeros(proc, t):
        """Colapsa ráfagas de duración 0."""
        while proc.current_burst_index < len(proc.bursts) and proc.bursts[proc.current_burst_index] == 0:
            proc.advance_burst()
        if proc.current_burst_index >= len(proc.bursts):
            proc.completion_time = t
            return True
        return False

    def handle_post(proc, t, destino_cpu, destino_unblock, destino_blocked, gantt):
        """
        Decide qué hacer con el proceso cuando cambia de ráfaga:
        - Si terminó → True
        - Si siguiente es CPU → encolar en destino_cpu
        - Si siguiente es BLOQ → programar bloqueo (saltando 0s recursivamente)
        """
        if collapse_zeros(proc, t):
            return True
        if proc.is_cpu_burst():
            destino_cpu.append(proc)
        else:
            dur = proc.bursts[proc.current_burst_index]
            if dur > 0:
                gantt.append((proc.pid, t, t + dur, "BLOCK"))
                destino_blocked.append((proc, t + dur))
            else:
                proc.advance_burst()
                return handle_post(proc, t, destino_cpu, destino_unblock, destino_blocked, gantt)
        return False

    processes = deepcopy(process_list)

    # Inicializar procesos
    for idx, p in enumerate(processes):
        if not hasattr(p, "bursts_original"):
            p.bursts_original = p.bursts[:]
        p._seq = idx
        # remaining_time = total de CPU (para la prioridad SRTF)
        p.remaining_time = sum(b for i, b in enumerate(p.bursts) if i % 2 == 0)
        p.ready_since = None
        p.start_time = None
        p.completion_time = None

    time = 0
    gantt = []
    ready = []
    blocked = []      # [(proc, unblock_time)]
    completed = 0
    n = len(processes)
    arrived = set()

    enq_cpu = []      # llegada o fin de CPU
    enq_unblock = []  # fin de bloqueo

    def enqueue_arrivals_leq_t(t):
        nonlocal completed
        for p in processes:
            if p.pid in arrived:
                continue
            if p.arrival_time <= t and p.completion_time is None:
                arrived.add(p.pid)
                if handle_post(p, t, enq_cpu, enq_unblock, blocked, gantt):
                    completed += 1

    # Inicializar llegadas al tiempo 0
    enqueue_arrivals_leq_t(time)
    if enq_cpu or enq_unblock:
        ready.extend(enq_cpu)
        ready.extend(enq_unblock)
        enq_cpu.clear()
        enq_unblock.clear()

    current = None
    seg_start = None  # inicio del segmento actual de CPU

    while completed < n:
        # 1) Desbloqueos vencidos
        if blocked:
            blocked.sort(key=lambda x: x[1])
        for (bp, unb) in blocked[:]:
            if unb <= time:
                blocked.remove((bp, unb))
                bp.advance_burst()
                if handle_post(bp, time, enq_unblock, enq_unblock, blocked, gantt):
                    completed += 1

        # 2) Llegadas hasta este instante
        enqueue_arrivals_leq_t(time)

        # 2.1) Volcar buffers a ready (CPU_FINISH/llegada > UNBLOCK)
        if enq_cpu or enq_unblock:
            ready.extend(enq_cpu)
            ready.extend(enq_unblock)
            enq_cpu.clear()
            enq_unblock.clear()

        # 3) Selección SRTF
        eligibles = [p for p in ready if p.is_cpu_burst() and p.current_burst_index < len(p.bursts)]
        if not eligibles:
            # No hay listos, saltar al próximo evento
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
            # Cerrar segmento si había uno abierto (seguridad)
            current = None
            seg_start = None
            continue

        eligibles.sort(key=lambda x: (total_cpu_restante(x), x.arrival_time, x.pid))
        candidate = eligibles[0]

        # Cambio de proceso en ejecución → cerrar segmento anterior
        if current is not candidate:
            if current is not None and seg_start is not None and time > seg_start:
                gantt.append((current.pid, seg_start, time, "CPU"))
            current = candidate
            seg_start = time
            if current.start_time is None:
                current.start_time = time

        # 4) Ejecutar 1 tick de CPU
        # Descontar 1 del total de CPU y 1 de la ráfaga actual
        current.remaining_time -= 1
        # Aseguramos que haya un índice válido de CPU
        if current.current_burst_index < len(current.bursts) and current.is_cpu_burst():
            current.bursts[current.current_burst_index] -= 1

        time += 1

        # 5) Post-tick: ¿terminó la ráfaga actual?
        finished_cpu_burst = (
            current.current_burst_index < len(current.bursts)
            and not current.is_cpu_burst()  # esto no sirve porque cambia tras advance; usamos valor previo
        )
        # Mejor: mirar el valor de la ráfaga actual ANTES de advance:
        # Si quedó en 0 tras el tick, la ráfaga terminó.
        if current.current_burst_index < len(current.bursts) and current.is_cpu_burst():
            if current.bursts[current.current_burst_index] == 0:
                # Cerrar el segmento de CPU
                if seg_start is not None and time > seg_start:
                    gantt.append((current.pid, seg_start, time, "CPU"))
                # Avanzar a la siguiente ráfaga y decidir
                current.advance_burst()
                if handle_post(current, time, enq_cpu, enq_unblock, blocked, gantt):
                    completed += 1
                # Forzar nueva selección
                current = None
                seg_start = None
                # Volcar buffers tras el cambio
                if enq_cpu or enq_unblock:
                    ready.extend(enq_cpu)
                    ready.extend(enq_unblock)
                    enq_cpu.clear()
                    enq_unblock.clear()
                continue

        # 6) Preempción: ¿apareció alguien con menor total de CPU restante?
        # Procesamos llegadas/desbloqueos exactamente en 'time' antes de comparar
        enqueue_arrivals_leq_t(time)
        for (bp, unb) in blocked[:]:
            if unb <= time:
                blocked.remove((bp, unb))
                bp.advance_burst()
                if handle_post(bp, time, enq_unblock, enq_unblock, blocked, gantt):
                    completed += 1
        if enq_cpu or enq_unblock:
            ready.extend(enq_cpu)
            ready.extend(enq_unblock)
            enq_cpu.clear()
            enq_unblock.clear()

        eligibles = [p for p in ready if p.is_cpu_burst() and p.current_burst_index < len(p.bursts)]
        if eligibles:
            eligibles.sort(key=lambda x: (total_cpu_restante(x), x.arrival_time, x.pid))
            best = eligibles[0]
            if best is not current and total_cpu_restante(best) < total_cpu_restante(current):
                # Cerrar el segmento del actual hasta este instante
                if seg_start is not None and time > seg_start:
                    gantt.append((current.pid, seg_start, time, "CPU"))
                # Re-encolar el actual
                current.ready_since = time
                enq_cpu.append(current)
                current = None
                seg_start = None
                # Volcar buffers tras la expulsión
                ready.extend(enq_cpu)
                ready.extend(enq_unblock)
                enq_cpu.clear()
                enq_unblock.clear()

    # Cierre por seguridad
    if current is not None and seg_start is not None and time > seg_start:
        gantt.append((current.pid, seg_start, time, "CPU"))

    return gantt, processes
