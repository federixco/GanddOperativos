from copy import deepcopy

def sjf_blocking(process_list):
    processes = deepcopy(process_list)

    def cpu_total_restante(p):
        """Calcula el total de CPU restante desde la posición actual."""
        idx = p.current_burst_index
        if idx >= len(p.bursts):
            return 0
        
        total = 0
        # Si estamos en una ráfaga de CPU (índice par)
        if idx % 2 == 0:
            # El burst actual YA refleja lo que queda (se va descontando)
            total += p.bursts[idx]
            start = idx + 2  # Siguiente CPU
        else:
            # Si estamos en bloqueo, la próxima CPU es idx+1
            start = idx + 1
        
        # Sumar las ráfagas de CPU futuras
        for i in range(start, len(p.bursts), 2):
            total += p.bursts[i]
        
        return total

    # Init por proceso
    for idx, p in enumerate(processes):
        if not hasattr(p, "bursts_original"):
            p.bursts_original = p.bursts[:]
        p._seq = idx
        p.remaining_time = sum(b for i, b in enumerate(p.bursts) if i % 2 == 0)
        p.ready_since = None
        p.start_time = None
        p.completion_time = None

    time = 0
    gantt = []
    ready = []
    blocked = []
    completed = 0
    n = len(processes)
    arrived = set()

    enq_cpu = []
    enq_unblock = []

    def collapse_zeros(proc, t):
        while proc.current_burst_index < len(proc.bursts) and proc.bursts[proc.current_burst_index] == 0:
            proc.advance_burst()
        if proc.current_burst_index >= len(proc.bursts):
            proc.completion_time = t
            return True
        return False

    def enqueue_arrivals_leq_t(t):
        nonlocal completed
        for p in processes:
            if p.pid in arrived:
                continue
            if p.arrival_time <= t and p.completion_time is None:
                arrived.add(p.pid)
                if collapse_zeros(p, t):
                    completed += 1
                    continue
                if p.is_cpu_burst():
                    p.ready_since = p.arrival_time
                    enq_cpu.append(p)
                else:
                    dur = p.bursts[p.current_burst_index]
                    if dur > 0:
                        gantt.append((p.pid, t, t + dur, "BLOCK"))
                        blocked.append((p, t + dur))
                    else:
                        p.advance_burst()
                        if collapse_zeros(p, t):
                            completed += 1
                        elif p.is_cpu_burst():
                            p.ready_since = p.arrival_time
                            enq_cpu.append(p)

    # Inicializar
    enqueue_arrivals_leq_t(time)
    if enq_cpu or enq_unblock:
        ready.extend(enq_cpu)
        ready.extend(enq_unblock)
        enq_cpu.clear()
        enq_unblock.clear()

    while completed < n:
        # Procesar desbloqueos
        if blocked:
            blocked.sort(key=lambda x: x[1])
        for (bp, unb) in blocked[:]:
            if unb <= time:
                blocked.remove((bp, unb))
                bp.advance_burst()
                if collapse_zeros(bp, time):
                    completed += 1
                    continue
                if bp.is_cpu_burst():
                    bp.ready_since = time
                    enq_unblock.append(bp)
                else:
                    dur = bp.bursts[bp.current_burst_index]
                    if dur > 0:
                        gantt.append((bp.pid, time, time + dur, "BLOCK"))
                        blocked.append((bp, time + dur))
                    else:
                        bp.advance_burst()
                        if collapse_zeros(bp, time):
                            completed += 1
                        elif bp.is_cpu_burst():
                            bp.ready_since = time
                            enq_unblock.append(bp)

        # Encolar llegadas
        enqueue_arrivals_leq_t(time)

        # Volcar buffers a ready
        if enq_cpu or enq_unblock:
            ready.extend(enq_cpu)
            ready.extend(enq_unblock)
            enq_cpu.clear()
            enq_unblock.clear()

        # Si no hay listos, saltar al siguiente evento
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

        # Selección SJF por total de CPU restante
        ready = [p for p in ready if p.current_burst_index < len(p.bursts)]
        ready.sort(key=lambda x: (
            cpu_total_restante(x),
            (x.ready_since if x.ready_since is not None else x.arrival_time),
            x.pid
        ))

        current = ready.pop(0)
        if current.start_time is None:
            current.start_time = time

        # Ejecutar ráfaga completa
        start = time
        cpu_dur = current.bursts[current.current_burst_index]
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