from copy import deepcopy

def srtf_blocking(process_list):
    """
    SRTF expulsivo con soporte para procesos mixtos (con y sin bloqueos).
    - Criterio: CPU total restante (CPU actual + futuras CPUs).
    - arrival_time nunca se modifica.
    - Bloqueos manejados con unblock_time (sin restar tick a tick).
    - Gantt: (pid, start, end, tipo) con tipo en {"CPU","BLOCK"}.
    """

    def total_cpu_restante(p):
        """Suma CPU restante de la ráfaga actual + CPUs futuras."""
        idx = p.current_burst_index
        if idx >= len(p.bursts):
            return 0
        if idx % 2 == 0:  # CPU
            total = p.remaining_time
            for i in range(idx + 2, len(p.bursts), 2):
                total += p.bursts[i]
            return total
        return float("inf")  # si está en bloqueo, no debería estar en ready

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
                        ready_queue.append(p)

        # 2) Desbloqueos - almacenar para agregar después de los procesos que terminan ejecución
        procesos_desbloqueados = []
        for (bp, unblock_time) in blocked_queue[:]:
            if unblock_time == time:
                blocked_queue.remove((bp, unblock_time))
                bp.advance_burst()
                if bp.current_burst_index >= len(bp.bursts):
                    bp.completion_time = time
                    bp.calculate_metrics()
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
                            procesos_desbloqueados.append(bp)

        # 3) Selección SRTF por CPU total restante, con desempate por FIFO
        eligibles = [p for p in ready_queue if p.is_cpu_burst() and p.completion_time is None]
        if eligibles:
            eligibles.sort(key=lambda x: (
                total_cpu_restante(x),  # SRTF: menor CPU total restante
                x.arrival_time,         # FIFO en empates
                x.pid                  # estabilidad
            ))
            candidate = eligibles[0]
            if current is not candidate:
                if current is not None:
                    gantt_chart.append((current.pid, start_time, time, "CPU"))
                current = candidate
                start_time = time
                if current.start_time is None:
                    current.start_time = time
        else:
            # No hay listos, avanzar tiempo
            time += 1
            continue

        # 4) Ejecutar 1 unidad
        current.remaining_time -= 1
        time += 1

        # 5) ¿Terminó la ráfaga de CPU?
        if current.remaining_time == 0:
            gantt_chart.append((current.pid, start_time, time, "CPU"))
            if current in ready_queue:
                ready_queue.remove(current)
            current.advance_burst()

            if current.current_burst_index >= len(current.bursts):
                current.completion_time = time
                current.calculate_metrics()
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
                    else:
                        current.advance_burst()
                        ready_queue.append(current)
                    current = None

        # 6) Agregar procesos desbloqueados al final de la cola después de procesar la ejecución
        # Esto asegura que los procesos que terminan ejecución van antes que los que se desbloquean
        for p in procesos_desbloqueados:
            ready_queue.append(p)

    # Cierre por seguridad
    if current is not None:
        gantt_chart.append((current.pid, start_time, time, "CPU"))

    return gantt_chart, processes
