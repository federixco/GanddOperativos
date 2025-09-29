from copy import deepcopy

def sjf_blocking(process_list):
    """
    SJF (Shortest Job First) no expulsivo con bloqueos.
    Regla:
      1) Prioridad por MENOR TIEMPO TOTAL DE CPU del proceso (inmutable; suma de todas las CPU del original).
      2) Desempate FIFO por TIEMPO DE LLEGADA del proceso (arrival_time más chico primero).
      3) Desempate final estable por orden de definición (_seq).
    """

    processes = deepcopy(process_list)

    # -------- Init por proceso --------
    for idx, p in enumerate(processes):
        if not hasattr(p, "bursts_original"):
            p.bursts_original = p.bursts[:]

        # Inmutable: suma de TODAS las ráfagas CPU (índices pares) del original
        p.total_cpu = sum(b for i, b in enumerate(p.bursts_original) if i % 2 == 0)

        p._seq = idx
        p.ready_since = None
        if not hasattr(p, "start_time"):
            p.start_time = None
        p.completion_time = None
        if not hasattr(p, "current_burst_index"):
            p.current_burst_index = 0
        if not hasattr(p, "arrival_time"):
            p.arrival_time = getattr(p, "arrival", 0)

    time = 0
    gantt = []
    ready = []
    blocked = []      # [(proc, unblock_time)]
    completed = 0
    n = len(processes)
    arrived = set()

    # buffers: fin de CPU / llegadas (alta prioridad) y desbloqueos (luego)
    enq_cpu = []
    enq_unblock = []

    # -------- Helpers --------
    def collapse_zeros(proc, t):
        """Salta ráfagas 0 encadenadas; True si terminó."""
        while proc.current_burst_index < len(proc.bursts) and proc.bursts[proc.current_burst_index] == 0:
            proc.advance_burst()
        if proc.current_burst_index >= len(proc.bursts):
            proc.completion_time = t
            return True
        return False

    def to_ready_from_arrival_or_cpu(p, t, bucket):
        """Encolar a ready por llegada o tras terminar CPU (marcamos ready_since pero NO se usa para desempate)."""
        p.ready_since = t
        bucket.append(p)

    def to_ready_from_unblock(p, t, bucket):
        """Encolar a ready tras desbloqueo (marcamos ready_since pero NO se usa para desempate)."""
        p.ready_since = t
        bucket.append(p)

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
                    # OJO: el desempate FIFO es por arrival_time, no por ready_since
                    to_ready_from_arrival_or_cpu(p, p.arrival_time, enq_cpu)
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
                            to_ready_from_arrival_or_cpu(p, p.arrival_time, enq_cpu)

    # -------- Llegadas iniciales --------
    enqueue_arrivals_leq_t(time)
    if enq_cpu or enq_unblock:
        ready.extend(enq_cpu)
        ready.extend(enq_unblock)
        enq_cpu.clear()
        enq_unblock.clear()

    # -------- Bucle principal --------
    safe_iters = 0
    while completed < n and safe_iters < 500000:
        safe_iters += 1

        # 1) Desbloqueos <= time
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
                    to_ready_from_unblock(bp, time, enq_unblock)
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
                            to_ready_from_unblock(bp, time, enq_unblock)

        # 2) Llegadas nuevas
        enqueue_arrivals_leq_t(time)

        # 3) Volcar buffers a ready (CPU/llegadas primero, luego desbloqueos)
        if enq_cpu or enq_unblock:
            ready.extend(enq_cpu)
            ready.extend(enq_unblock)
            enq_cpu.clear()
            enq_unblock.clear()

        # 4) Si no hay listos, saltar a próximo evento
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

        # 5) Selección SJF con desempate por ARRIVAL_TIME (FIFO global de llegada)
        #    - total_cpu (menor primero)
        #    - arrival_time (más antiguo primero)
        #    - _seq (estable si todo lo anterior empata)
        ready = [p for p in ready if p.current_burst_index < len(p.bursts)]
        ready.sort(key=lambda x: (x.total_cpu, x.arrival_time, x._seq))
        current = ready.pop(0)

        if current.start_time is None:
            current.start_time = time

        # 6) Ejecutar CPU completa (no expulsivo)
        start = time
        cpu_dur = current.bursts[current.current_burst_index]
        if cpu_dur <= 0:
            if collapse_zeros(current, time):
                completed += 1
            else:
                if current.is_cpu_burst():
                    to_ready_from_arrival_or_cpu(current, time, enq_cpu)
            continue

        time += cpu_dur
        gantt.append((current.pid, start, time, "CPU"))

        # marcar ráfaga como hecha y avanzar
        current.bursts[current.current_burst_index] = 0
        current.advance_burst()

        if collapse_zeros(current, time):
            completed += 1
            continue

        # 7) Próxima ráfaga
        if current.is_cpu_burst():
            to_ready_from_arrival_or_cpu(current, time, enq_cpu)   # vuelve a ready
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
                    to_ready_from_arrival_or_cpu(current, time, enq_cpu)

        # 8) Volcar buffers
        if enq_cpu or enq_unblock:
            ready.extend(enq_cpu)
            ready.extend(enq_unblock)
            enq_cpu.clear()
            enq_unblock.clear()

    if safe_iters >= 500000:
        print("⚠️ SJF: límite de iteraciones alcanzado (posible bucle).")

    return gantt, processes
