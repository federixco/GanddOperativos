from copy import deepcopy

def fifo_blocking(process_list):
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
                        if p.current_burst_index >= len(p.bursts):
                            p.completion_time = time
                            completed += 1
                        elif p.is_cpu_burst():
                            ready_queue.append(p)
                        else:
                            dur2 = p.bursts[p.current_burst_index]
                            if dur2 > 0:
                                gantt_chart.append((p.pid, time, time + dur2, "BLOCK"))
                                blocked_queue.append((p, time + dur2))
                            else:
                                p.advance_burst()
                                if p.current_burst_index < len(p.bursts) and p.is_cpu_burst():
                                    ready_queue.append(p)

        # 2) Desbloqueos que vencen ahora - se almacenan para agregar después de los procesos que terminan ejecución
        procesos_desbloqueados = []
        for (bp, unblock_time) in blocked_queue[:]:
            if unblock_time == time:
                blocked_queue.remove((bp, unblock_time))
                bp.advance_burst()
                if bp.current_burst_index >= len(bp.bursts):
                    bp.completion_time = time
                    completed += 1
                else:
                    if bp.is_cpu_burst():
                        procesos_desbloqueados.append(bp)
                    else:
                        dur2 = bp.bursts[bp.current_burst_index]
                        if dur2 > 0:
                            gantt_chart.append((bp.pid, time, time + dur2, "BLOCK"))
                            blocked_queue.append((bp, time + dur2))
                        else:
                            bp.advance_burst()
                            if bp.current_burst_index >= len(bp.bursts):
                                bp.completion_time = time
                                completed += 1
                            elif bp.is_cpu_burst():
                                procesos_desbloqueados.append(bp)

        # 3) Selección FIFO
        if current is None and ready_queue:
            current = ready_queue.pop(0)
            start_time = time
            if current.start_time is None:
                current.start_time = time  # solo la primera vez que toca CPU

        # 4) Ejecutar 1 tick de CPU o avanzar tiempo si no hay listos
        if current:
            current.remaining_time -= 1
            time += 1

            # ¿Terminó esta ráfaga de CPU?
            if current.remaining_time == 0:
                # Cerrar tramo de CPU
                gantt_chart.append((current.pid, start_time, time, "CPU"))

                # Avanzar a la siguiente ráfaga
                current.advance_burst()

                # ¿Proceso terminado?
                if current.current_burst_index >= len(current.bursts):
                    current.completion_time = time
                    completed += 1
                    current = None
                else:
                    # ¿Siguiente es CPU?
                    if current.is_cpu_burst():
                        ready_queue.append(current)
                        current = None
                    else:
                        # Siguiente es BLOQUEO
                        dur = current.bursts[current.current_burst_index]
                        if dur > 0:
                            gantt_chart.append((current.pid, time, time + dur, "BLOCK"))
                            blocked_queue.append((current, time + dur))
                            current = None
                        else:
                            # Bloqueo de 0 → saltar
                            current.advance_burst()
                            if current.current_burst_index >= len(current.bursts):
                                current.completion_time = time
                                completed += 1
                                current = None
                            elif current.is_cpu_burst():
                                ready_queue.append(current)
                                current = None
        else:
            # No hay proceso ejecutando ni listo: avanzar tiempo "vacío" (no pintamos IDLE)
            time += 1

        # 5) Agregar procesos desbloqueados al final de la cola después de procesar la ejecución
        # Esto asegura que los procesos que terminan ejecución van antes que los que se desbloquean
        for p in procesos_desbloqueados:
            ready_queue.append(p)

    return gantt_chart, processes
