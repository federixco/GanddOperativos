from copy import deepcopy
from collections import deque

def round_robin_blocking(process_list, quantum):
    """Round Robin con bloqueos, ejecución por tramos (no tick a tick), con separación estricta de ready y blocked."""

    def collapse_zeros(proc, t):
        """Salta ráfagas 0 encadenadas; si termina, marca completion_time."""
        while proc.current_burst_index < len(proc.bursts) and proc.bursts[proc.current_burst_index] == 0:
            proc.advance_burst()
        if proc.current_burst_index >= len(proc.bursts):
            proc.completion_time = t
            return True
        return False

    # Dos variantes para manejar el post-estado según el origen del evento.
    # - after_cpu_or_arrival: llegada inicial o fin de CPU (prioridad alta)
    # - after_unblock: fin de bloqueo (prioridad detrás de CPU_FINISH/llegada)
    def handle_after_cpu_or_arrival(proc, t, enq_cpu, blocked, gantt):
        """Resolver transición tras llegada o fin de CPU: CPU -> enq_cpu, BLOQ -> blocked."""
        if collapse_zeros(proc, t):
            return True  # terminó
        if proc.is_cpu_burst():
            enq_cpu.append(proc)
        else:
            dur = proc.bursts[proc.current_burst_index]
            if dur > 0:
                gantt.append((proc.pid, t, t + dur, "BLOCK"))
                blocked.append((proc, t + dur))
            else:
                proc.advance_burst()
                return handle_after_cpu_or_arrival(proc, t, enq_cpu, blocked, gantt)
        return False

    def handle_after_unblock(proc, t, enq_unblock, blocked, gantt):
        """Resolver transición tras fin de bloqueo: CPU -> enq_unblock, BLOQ -> (re)blocked."""
        if collapse_zeros(proc, t):
            return True
        if proc.is_cpu_burst():
            enq_unblock.append(proc)
        else:
            dur = proc.bursts[proc.current_burst_index]
            if dur > 0:
                gantt.append((proc.pid, t, t + dur, "BLOCK"))
                blocked.append((proc, t + dur))
            else:
                proc.advance_burst()
                return handle_after_unblock(proc, t, enq_unblock, blocked, gantt)
        return False

    processes = deepcopy(process_list)

    # Init
    for idx, p in enumerate(processes):
        if not hasattr(p, "bursts_original"):
            p.bursts_original = p.bursts[:]
        p._seq = idx
        p.ready_since = None
        p.start_time = None
        p.completion_time = None
        if not p.bursts:
            p.current_burst_index = 0
            p.remaining_time = 0
            p.completion_time = 0
        else:
            # Asegurar remaining_time consistente con la ráfaga actual
            p.remaining_time = p.bursts[p.current_burst_index] if p.current_burst_index < len(p.bursts) else 0

    time = 0
    gantt = []
    ready = deque()
    blocked = []  # [(proc, unblock_time)]
    completed = sum(1 for p in processes if p.completion_time is not None)
    n = len(processes)
    arrived = set()

    # Buffers con prioridad: CPU_FINISH/llegada > UNBLOCK
    enq_cpu = []       # llegada o fin de CPU
    enq_unblock = []   # fin de bloqueo

    def enqueue_arrivals_leq_t(t):
        """Encola llegadas hasta t (incluido) con prioridad de llegada (CPU_FINISH/llegada)."""
        nonlocal completed
        for p in processes:
            if p.pid in arrived:
                continue
            if p.arrival_time <= t and p.completion_time is None:
                arrived.add(p.pid)
                if handle_after_cpu_or_arrival(p, t, enq_cpu, blocked, gantt):
                    completed += 1

    # Llegadas iniciales
    enqueue_arrivals_leq_t(time)
    if enq_cpu or enq_unblock:
        ready.extend(enq_cpu); ready.extend(enq_unblock)
        enq_cpu.clear(); enq_unblock.clear()

    while completed < n:
        # Si no hay listos, saltar al siguiente evento (llegada o fin de bloqueo)
        if not ready:
            future_arrivals = [p.arrival_time for p in processes if p.pid not in arrived and p.completion_time is None]
            future_unblocks = [unb for _, unb in blocked]
            if not future_arrivals and not future_unblocks:
                # Salvaguarda: marcar terminados sin completion_time
                for p in processes:
                    if p.completion_time is None and p.current_burst_index >= len(p.bursts):
                        p.completion_time = time
                        completed += 1
                break
            next_event = min(future_arrivals + future_unblocks) if (future_arrivals or future_unblocks) else time + 1
            if next_event > time:
                gantt.append(("IDLE", time, next_event, "IDLE"))
                time = next_event
            else:
                time += 1

            # Procesar exactamente en 'time'
            # Fin de bloqueos en 'time'
            for (bp, unb) in blocked[:]:
                if unb == time:
                    blocked.remove((bp, unb))
                    bp.advance_burst()
                    if handle_after_unblock(bp, time, enq_unblock, blocked, gantt):
                        completed += 1
            # Llegadas en 'time'
            enqueue_arrivals_leq_t(time)

            # Volcar buffers respetando prioridad
            if enq_cpu or enq_unblock:
                ready.extend(enq_cpu); ready.extend(enq_unblock)
                enq_cpu.clear(); enq_unblock.clear()

            if not ready:
                continue

        # Selección RR
        current = ready.popleft()

        # Sólo CPU debe estar en ready; blindaje por si acaso
        if not current.is_cpu_burst():
            # Si cae acá por desync, resolver como llegada/CPU_FINISH
            if handle_after_cpu_or_arrival(current, time, enq_cpu, blocked, gantt):
                completed += 1
            if enq_cpu or enq_unblock:
                ready.extend(enq_cpu); ready.extend(enq_unblock)
                enq_cpu.clear(); enq_unblock.clear()
            continue

        if current.start_time is None:
            current.start_time = time
        # Sync remaining_time
        if current.remaining_time <= 0:
            current.remaining_time = current.bursts[current.current_burst_index]

        # Definir tramo a ejecutar
        exec_time = min(quantum, current.remaining_time)
        start = time
        end = time + exec_time

        # Registrar eventos que ocurren en (time, end], sin preemptar el tramo actual:
        # - Desbloqueos: se preparan en enq_unblock
        # - Llegadas: se preparan en enq_cpu
        # Se procesan en su instante exacto, pero no se vuelcan a ready hasta el fin del tramo
        # (RR no preempta por llegada/desbloqueo dentro del quantum actual).
        # Desbloqueos
        for (bp, unb) in sorted(blocked[:], key=lambda x: x[1]):
            if time < unb <= end:
                blocked.remove((bp, unb))
                bp.advance_burst()
                if handle_after_unblock(bp, unb, enq_unblock, blocked, gantt):
                    completed += 1
        # Llegadas
        for p in processes:
            if p.pid in arrived:
                continue
            if time < p.arrival_time <= end and p.completion_time is None:
                arrived.add(p.pid)
                if handle_after_cpu_or_arrival(p, p.arrival_time, enq_cpu, blocked, gantt):
                    completed += 1

        # Consumir CPU del actual y avanzar tiempo
        current.remaining_time -= exec_time
        time = end
        gantt.append((current.pid, start, end, "CPU"))

        # ¿Terminó ráfaga o agotó quantum?
        if current.remaining_time == 0:
            # Pasar a siguiente ráfaga
            current.advance_burst()
            if current.current_burst_index >= len(current.bursts):
                # Proceso terminado
                current.completion_time = time
                completed += 1
            else:
                # Resolver siguiente ráfaga: si es BLOQ -> va a blocked; si es CPU -> buffer (enq_cpu)
                if handle_after_cpu_or_arrival(current, time, enq_cpu, blocked, gantt):
                    completed += 1
        else:
            # Ráfaga no terminó → reencolar al final (manteniendo RR)
            current.ready_since = time
            enq_cpu.append(current)

        # Volcar buffers con prioridad (CPU_FINISH/llegada primero, luego UNBLOCK)
        if enq_cpu or enq_unblock:
            ready.extend(enq_cpu); ready.extend(enq_unblock)
            enq_cpu.clear(); enq_unblock.clear()

    # Salvaguarda final
    for p in processes:
        if p.completion_time is None and p.current_burst_index >= len(p.bursts):
            p.completion_time = time

    return gantt, processes
