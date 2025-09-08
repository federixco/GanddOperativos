from copy import deepcopy

def sjf_blocking(process_list):
    processes = deepcopy(process_list)

    # Guardar bursts originales y orden de definición
    for idx, p in enumerate(processes):
        p.bursts_original = p.bursts[:]
        p._seq = idx
        p.remaining_time = sum(b for i, b in enumerate(p.bursts) if i % 2 == 0)

    time = 0
    gantt = []
    ready = []
    blocked = []  # (proc, unblock_time)
    completed = 0
    n = len(processes)

    def collapse_zeros(proc, t):
        """Avanza ráfagas de duración 0 encadenadas."""
        while proc.current_burst_index < len(proc.bursts) and proc.bursts[proc.current_burst_index] == 0:
            proc.advance_burst()
        if proc.current_burst_index >= len(proc.bursts):
            proc.completion_time = t
            return True
        return False

    while completed < n:
        # 1) Desbloqueos en este instante
        for (bp, unb) in blocked[:]:
            if unb == time:
                blocked.remove((bp, unb))
                bp.advance_burst()
                if collapse_zeros(bp, time):
                    completed += 1
                    continue
                if bp.is_cpu_burst():
                    ready.append(bp)
                else:
                    dur = bp.bursts[bp.current_burst_index]
                    gantt.append((bp.pid, time, time + dur, "BLOCK"))
                    blocked.append((bp, time + dur))

        # 2) Llegadas en este instante
        for p in processes:
            if p.arrival_time == time and p.completion_time is None:
                if collapse_zeros(p, time):
                    completed += 1
                    continue
                if p.is_cpu_burst():
                    ready.append(p)
                else:
                    dur = p.bursts[p.current_burst_index]
                    gantt.append((p.pid, time, time + dur, "BLOCK"))
                    blocked.append((p, time + dur))

        # 3) Si no hay listos, saltar o avanzar
        if not ready:
            next_event = min(
                [unb for _, unb in blocked] +
                [p.arrival_time for p in processes if p.completion_time is None and p.arrival_time > time],
                default=None
            )
            if next_event is None:
                # No hay más eventos → avanzar 1 para evitar bucle infinito
                time += 1
            elif next_event > time:
                gantt.append(("IDLE", time, next_event, "IDLE"))
                time = next_event
            else:
                # next_event == time pero no hay listos → avanzar 1
                time += 1
            continue

        # 4) Elegir el más corto (FIFO en empates)
        ready.sort(key=lambda x: (x.bursts[x.current_burst_index], x.arrival_time, x._seq))
        current = ready.pop(0)

        # Ejecutar ráfaga completa (no expulsivo)
        start = time
        cpu_dur = current.bursts[current.current_burst_index]
        time += cpu_dur
        current.remaining_time -= cpu_dur
        gantt.append((current.pid, start, time, "CPU"))

        # Avanzar a la siguiente ráfaga
        current.advance_burst()
        if collapse_zeros(current, time):
            completed += 1
            continue
        if current.is_cpu_burst():
            ready.append(current)
        else:
            dur = current.bursts[current.current_burst_index]
            gantt.append((current.pid, time, time + dur, "BLOCK"))
            blocked.append((current, time + dur))

    return gantt, processes
