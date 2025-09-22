from copy import deepcopy

def srtf_blocking(process_list):
    """SRTF expulsivo con soporte para bloqueos, usando get_total_cpu_remaining()."""

    def collapse_zeros(proc, t):
        while proc.current_burst_index < len(proc.bursts) and proc.bursts[proc.current_burst_index] == 0:
            proc.advance_burst()
        if proc.current_burst_index >= len(proc.bursts):
            proc.completion_time = t
            return True
        return False

    def handle_post(proc, t, destino_cpu, destino_unblock, destino_blocked, gantt):
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
    for idx, p in enumerate(processes):
        if not hasattr(p, "bursts_original"):
            p.bursts_original = p.bursts[:]
        p._seq = idx
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

    def enqueue_arrivals_leq_t(t):
        nonlocal completed
        for p in processes:
            if p.pid in arrived:
                continue
            if p.arrival_time <= t and p.completion_time is None:
                arrived.add(p.pid)
                if handle_post(p, t, enq_cpu, enq_unblock, blocked, gantt):
                    completed += 1

    def process_unblocks_leq_t(t):
        nonlocal completed
        for (bp, unb) in blocked[:]:
            if unb <= t:
                blocked.remove((bp, unb))
                bp.advance_burst()
                if handle_post(bp, t, enq_unblock, enq_unblock, blocked, gantt):
                    completed += 1

    enqueue_arrivals_leq_t(time)
    if enq_cpu or enq_unblock:
        ready.extend(enq_cpu)
        ready.extend(enq_unblock)
        enq_cpu.clear()
        enq_unblock.clear()

    current = None
    seg_start = None

    while completed < n:
        process_unblocks_leq_t(time)
        enqueue_arrivals_leq_t(time)

        if enq_cpu or enq_unblock:
            ready.extend(enq_cpu)
            ready.extend(enq_unblock)
            enq_cpu.clear()
            enq_unblock.clear()

        eligibles = [p for p in ready if p.is_cpu_burst() and not p.is_finished()]
        if not eligibles:
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
            current = None
            seg_start = None
            continue

        eligibles.sort(key=lambda x: (x.get_total_cpu_remaining(), x.arrival_time, x._seq, x.pid))
        candidate = eligibles[0]

        if current is not candidate:
            if current is not None and seg_start is not None and time > seg_start:
                gantt.append((current.pid, seg_start, time, "CPU"))
            current = candidate
            seg_start = time
            if current.start_time is None:
                current.start_time = time

        # Ejecutar 1 tick
        current.bursts[current.current_burst_index] -= 1
        current.remaining_time = current.get_total_cpu_remaining()
        time += 1

        # Fin de ráfaga
        if current.bursts[current.current_burst_index] == 0:
            gantt.append((current.pid, seg_start, time, "CPU"))
            current.advance_burst()
            if current.is_finished():
                current.completion_time = time
                completed += 1
                current = None
                seg_start = None
            else:
                if handle_post(current, time, enq_cpu, enq_unblock, blocked, gantt):
                    completed += 1
                current = None
                seg_start = None
            if enq_cpu or enq_unblock:
                ready.extend(enq_cpu)
                ready.extend(enq_unblock)
                enq_cpu.clear()
                enq_unblock.clear()
            continue

        # Preempción
        process_unblocks_leq_t(time)
        enqueue_arrivals_leq_t(time)
        if enq_cpu or enq_unblock:
            ready.extend(enq_cpu)
            ready.extend(enq_unblock)
            enq_cpu.clear()
            enq_unblock.clear()

        eligibles = [p for p in ready if p.is_cpu_burst() and not p.is_finished()]
        if eligibles:
            eligibles.sort(key=lambda x: (x.get_total_cpu_remaining(), x.arrival_time, x._seq, x.pid))
            best = eligibles[0]
            if best is not current and best.get_total_cpu_remaining() < current.get_total_cpu_remaining():
                gantt.append((current.pid, seg_start, time, "CPU"))
                current.ready_since = time
                enq_cpu.append(current)
                current = None
                seg_start = None
                ready.extend(enq_cpu)
                ready.extend(enq_unblock)
                enq_cpu.clear()
                enq_unblock.clear()

    if current is not None and seg_start is not None and time > seg_start:
        gantt.append((current.pid, seg_start, time, "CPU"))

    return gantt, processes
