from copy import deepcopy

def sjf_blocking(process_list):
    processes = deepcopy(process_list)
    time = 0
    gantt_chart = []
    ready_queue = []
    blocked_queue = []  # (proceso, unblock_time)
    completed = 0
    n = len(processes)

    current = None
    start_time = None

    while completed < n:
        # 1) Llegadas
        for p in processes:
            if (
                p.arrival_time == time
                and p.completion_time is None
                and p not in ready_queue
                and all(bp is not p for bp, _ in blocked_queue)
                and p is not current
            ):
                if p.is_cpu_burst():
                    ready_queue.append(p)
                else:
                    dur = p.bursts[p.current_burst_index]
                    if dur > 0:
                        gantt_chart.append((p.pid, time, time + dur, "BLOCK"))
                        blocked_queue.append((p, time + dur))
                    else:
                        p.advance_burst()
                        if p.current_burst_index < len(p.bursts) and p.is_cpu_burst():
                            ready_queue.append(p)

        # 2) Desbloqueos
        for (bp, unblock_time) in blocked_queue[:]:
            if unblock_time == time:
                blocked_queue.remove((bp, unblock_time))
                bp.advance_burst()
                if bp.current_burst_index >= len(bp.bursts):
                    bp.completion_time = time
                    completed += 1
                else:
                    if bp.is_cpu_burst():
                        ready_queue.append(bp)
                    else:
                        dur2 = bp.bursts[bp.current_burst_index]
                        if dur2 > 0:
                            gantt_chart.append((bp.pid, time, time + dur2, "BLOCK"))
                            blocked_queue.append((bp, time + dur2))
                        else:
                            bp.advance_burst()
                            if bp.current_burst_index < len(bp.bursts) and bp.is_cpu_burst():
                                ready_queue.append(bp)

        # 3) Selección SJF (no expulsivo)
        if current is None and ready_queue:
            ready_queue.sort(key=lambda x: x.remaining_time)
            current = ready_queue.pop(0)
            start_time = time
            if current.start_time is None:
                current.start_time = time

        # 4) Ejecutar
        if current:
            current.remaining_time -= 1
            time += 1
            if current.remaining_time == 0:
                gantt_chart.append((current.pid, start_time, time, "CPU"))
                current.advance_burst()
                if current.current_burst_index >= len(current.bursts):
                    current.completion_time = time
                    completed += 1
                    current = None
                else:
                    if current.is_cpu_burst():
                        ready_queue.append(current)
                        current = None
                    else:
                        dur = current.bursts[current.current_burst_index]
                        if dur > 0:
                            gantt_chart.append((current.pid, time, time + dur, "BLOCK"))
                            blocked_queue.append((current, time + dur))
                            current = None
                        else:
                            current.advance_burst()
                            if current.current_burst_index >= len(current.bursts):
                                current.completion_time = time
                                completed += 1
                                current = None
                            elif current.is_cpu_burst():
                                ready_queue.append(current)
                                current = None
        else:
            # Si no hay listos pero sí bloqueados, saltar directo al próximo desbloqueo
            if blocked_queue:
                next_unblock = min(unblock_time for _, unblock_time in blocked_queue)
                time = max(time, next_unblock)
            else:
                time += 1

    return gantt_chart, processes
