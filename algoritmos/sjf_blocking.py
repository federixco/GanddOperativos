from copy import deepcopy

def sjf_blocking(process_list):
    processes = deepcopy(process_list)

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
    blocked = []      # [(proc, unblock_time)]
    completed = 0
    n = len(processes)
    arrived = set()   # PIDs ya encolados por llegada

    def collapse_zeros(proc, t):
        while proc.current_burst_index < len(proc.bursts) and proc.bursts[proc.current_burst_index] == 0:
            proc.advance_burst()
        if proc.current_burst_index >= len(proc.bursts):
            proc.completion_time = t
            return True
        return False

    def enqueue_arrivals_leq_t(t):
        nonlocal completed
        changed = False
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
                    ready.append(p)
                    changed = True
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
                            ready.append(p)
                            changed = True
        return changed

    # Inicializar con todos los procesos que llegan en tiempo 0 o antes
    enqueue_arrivals_leq_t(time)

    while completed < n:
        # 1) Procesar TODOS los desbloqueos que vencieron hasta t
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
                    ready.append(bp)
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
                            ready.append(bp)

        # 2) Encolar llegadas que hayan llegado hasta este momento
        enqueue_arrivals_leq_t(time)

        # 3) Si no hay listos, saltar al siguiente evento
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

        # 4) Selección SJF: elegir el proceso con la ráfaga de CPU actual más corta
        ready = [p for p in ready if p.current_burst_index < len(p.bursts)]
        ready.sort(key=lambda x: (
            x.bursts[x.current_burst_index],  # SJF: ráfaga actual de CPU más corta
            x.arrival_time,                   # FIFO en empates
            x.pid                            # estabilidad
        ))

        current = ready.pop(0)
        if current.start_time is None:
            current.start_time = time

        # 5) Ejecutar ráfaga completa (no expulsivo)
        start = time
        cpu_dur = current.bursts[current.current_burst_index]
        if cpu_dur <= 0:
            if collapse_zeros(current, time):
                completed += 1
            else:
                if current.is_cpu_burst():
                    current.ready_since = time
                    ready.append(current)
            continue

        time += cpu_dur
        if hasattr(current, "remaining_time") and current.remaining_time is not None:
            current.remaining_time -= cpu_dur
            if current.remaining_time < 0:
                current.remaining_time = 0
        gantt.append((current.pid, start, time, "CPU"))

        # 6) Avanzar bursts y re-encolar según corresponda
        current.advance_burst()
        if collapse_zeros(current, time):
            completed += 1
            continue

        if current.is_cpu_burst():
            # En SJF blocking, los procesos deben volver a la cola ready
            # después de terminar una ráfaga de CPU para competir nuevamente
            current.ready_since = time
            ready.append(current)
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
                    ready.append(current)

    return gantt, processes
