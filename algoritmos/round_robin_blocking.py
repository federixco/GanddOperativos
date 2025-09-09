from copy import deepcopy
from collections import deque

def round_robin_blocking(process_list, quantum):
    processes = deepcopy(process_list)
    time = 0
    gantt_chart = []
    ready_queue = deque()
    blocked_queue = []  # (proceso, unblock_time)
    completed = 0
    n = len(processes)

    current = None
    start_time = None
    quantum_counter = 0

    while completed < n:
        # 1) Llegadas
        procesos_que_llegan = []
        for p in processes:
            if (
                p.arrival_time == time
                and p.completion_time is None
                and p not in ready_queue
                and all(bp is not p for bp, _ in blocked_queue)
                and p is not current
            ):
                if p.is_cpu_burst():
                    procesos_que_llegan.append(p)
                else:
                    dur = p.bursts[p.current_burst_index]
                    if dur > 0:
                        gantt_chart.append((p.pid, time, time + dur, "BLOCK"))
                        blocked_queue.append((p, time + dur))
                    else:
                        p.advance_burst()
                        if p.current_burst_index < len(p.bursts) and p.is_cpu_burst():
                            procesos_que_llegan.append(p)
        
        # Ordenar por PID y agregar al final de la cola
        procesos_que_llegan.sort(key=lambda p: p.pid)
        for p in procesos_que_llegan:
            ready_queue.append(p)

        # 2) Desbloqueos
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
                            if bp.current_burst_index < len(bp.bursts) and bp.is_cpu_burst():
                                procesos_desbloqueados.append(bp)

        # 3) Selección RR
        if current is None and ready_queue:
            current = ready_queue.popleft()
            start_time = time
            quantum_counter = 0
            if current.start_time is None:
                current.start_time = time

        # 4) Ejecutar
        if current:
            current.remaining_time -= 1
            quantum_counter += 1
            time += 1

            # Verificar si terminó ráfaga de CPU o se agotó el quantum
            proceso_termina_quantum = False
            proceso_termina_cpu = False
            
            if current.remaining_time == 0:
                proceso_termina_cpu = True
            elif quantum_counter >= quantum:
                proceso_termina_quantum = True

            if proceso_termina_cpu or proceso_termina_quantum:
                gantt_chart.append((current.pid, start_time, time, "CPU"))
                
                if proceso_termina_cpu:
                    current.advance_burst()
                    if current.current_burst_index >= len(current.bursts):
                        current.completion_time = time
                        completed += 1
                        current = None
                    else:
                        if current.is_cpu_burst():
                            # CORRECCIÓN: Agregar al final de la cola después de los desbloqueos
                            ready_queue.append(current)
                            current = None
                        else:
                            dur = current.bursts[current.current_burst_index]
                            if dur > 0:
                                gantt_chart.append((current.pid, time, time + dur, "BLOCK"))
                                blocked_queue.append((current, time + dur))
                            else:
                                current.advance_burst()
                                if current.current_burst_index < len(current.bursts) and current.is_cpu_burst():
                                    ready_queue.append(current)
                            current = None
                else:  # proceso_termina_quantum
                    # CORRECCIÓN: Agregar al final de la cola después de los desbloqueos
                    ready_queue.append(current)
                    current = None

        else:
            # Si no hay listos pero sí bloqueados, saltar al próximo desbloqueo
            if blocked_queue:
                next_unblock = min(unblock_time for _, unblock_time in blocked_queue)
                time = max(time, next_unblock)
            else:
                time += 1

        # 5) CORRECCIÓN: Agregar procesos desbloqueados al final de la cola
        # después de que se haya procesado el cambio de quantum
        # Esto asegura que los procesos que terminan ejecución van antes que los que se desbloquean
        if procesos_desbloqueados:
            procesos_desbloqueados.sort(key=lambda p: p.pid)
            for p in procesos_desbloqueados:
                ready_queue.append(p)

    return gantt_chart, processes
