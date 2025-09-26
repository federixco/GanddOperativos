from copy import deepcopy
from collections import deque
import re

def _natural_key(pid: str):
    """Orden natural 'P9' < 'P10'; para A..Z simplemente ordena por letra."""
    m = re.search(r'(\d+)$', pid)
    return (int(m.group(1)) if m else float('inf'), pid)

def round_robin_blocking(process_list, quantum):
    """
    RR expulsivo con bloqueos (port de la lógica del compañero a tu modelo Process):
    - bursts = [CPU, BLOQ, CPU, ...]   (CPU en índices pares, BLOQ en impares)
    - No preempción por arrivals/unblocks durante el tramo.
    - En un mismo t, se respeta el orden: (1) requeue/gestión del que ejecutaba, (2) ARRIBOS, (3) DESBLOQUEOS.
    - Cola ready estrictamente FIFO.
    Retorna: (gantt, processes) con gantt = [(pid, start, end, "CPU"/"BLOCK"/"IDLE"), ...]
    """

    # -------- helpers sobre tu modelo --------
    def is_cpu_burst(p):
        return p.current_burst_index < len(p.bursts) and (p.current_burst_index % 2 == 0)

    def collapse_zeros(p, t):
        while p.current_burst_index < len(p.bursts) and p.bursts[p.current_burst_index] == 0:
            p.advance_burst()
        if p.current_burst_index >= len(p.bursts):
            p.completion_time = t
            return True
        return False

    # -------- copia / init --------
    processes = deepcopy(process_list)
    for idx, p in enumerate(processes):
        if not hasattr(p, "arrival_time"):
            p.arrival_time = getattr(p, "arrival", 0)
        if not hasattr(p, "current_burst_index"):
            p.current_burst_index = 0
        if not hasattr(p, "bursts_original"):
            p.bursts_original = p.bursts[:]
        p._seq = idx
        p.start_time = None
        p.completion_time = None

    # Ordenar “arribos” como hace tu compa: por llegada y clave natural de id
    arrivals = sorted(processes, key=lambda p: (p.arrival_time, _natural_key(p.pid)))
    arr_idx = 0

    # Estado global
    tiempo = 0
    gantt = []
    ready = deque()             # objetos Process
    bloqueados = {}             # pid -> t_desbloqueo
    idmap = {p.pid: p for p in processes}

    # Para CPU actual
    ejecutando = None           # pid
    inicio_tramo = None
    rem_burst = {}              # pid -> restante de la ráfaga CPU actual
    qleft = None                # quantum restante del ejecutando

    completado = {p.pid: False for p in processes}

    # ---- helpers de encolado (idénticos en espíritu a los de tu compa) ----
    def encolar_eventos():
        """Encola ARRIBOS y DESBLOQUEOS con t <= tiempo. ARRIBOS antes que DESBLOQUEOS."""
        nonlocal arr_idx, ready

        # 1) Arribos (<= tiempo)
        while arr_idx < len(arrivals) and arrivals[arr_idx].arrival_time <= tiempo:
            p = arrivals[arr_idx]; arr_idx += 1
            if completado[p.pid]:
                continue
            # Ignorar procesos sin más CPU
            # (en tu modelo: si siguiente ráfaga no es CPU, se maneja como bloqueo al llegar)
            if collapse_zeros(p, tiempo):
                continue
            if is_cpu_burst(p):
                ready.append(p.pid)
            else:
                # llega en BLOQ: agendar I/O
                dur = p.bursts[p.current_burst_index]
                if dur > 0:
                    gantt.append((p.pid, tiempo, tiempo + dur, "BLOCK"))
                    bloqueados[p.pid] = tiempo + dur
                else:
                    p.advance_burst()
                    if is_cpu_burst(p):
                        ready.append(p.pid)

        # 2) Desbloqueos (<= tiempo), orden determinista por (t, id natural)
        if bloqueados:
            desbloq = sorted(
                [(t, pid) for pid, t in bloqueados.items() if t <= tiempo],
                key=lambda x: (x[0], _natural_key(x[1]))
            )
            for _, pid in desbloq:
                bloqueados.pop(pid, None)
                pp = idmap[pid]
                # avanzamos más allá del BLOQ que terminó
                pp.advance_burst()
                if collapse_zeros(pp, tiempo):
                    completado[pid] = True
                    continue
                if is_cpu_burst(pp):
                    ready.append(pid)
                else:
                    # encadenamiento de BLOQ
                    dur = pp.bursts[pp.current_burst_index]
                    if dur > 0:
                        gantt.append((pid, tiempo, tiempo + dur, "BLOCK"))
                        bloqueados[pid] = tiempo + dur
                    else:
                        pp.advance_burst()
                        if pp.current_burst_index >= len(pp.bursts):
                            pp.completion_time = tiempo
                            completado[pid] = True
                        elif is_cpu_burst(pp):
                            ready.append(pid)

    total = len(processes)
    # Bucle principal (idéntico en estructura a tu compa)
    while sum(completado.values()) < total:
        encolar_eventos()

        # Si no hay listos ni ejecutando, saltar al próximo evento
        if ejecutando is None and not ready:
            proximo_arribo = arrivals[arr_idx].arrival_time if arr_idx < len(arrivals) else None
            proximo_desb = min(bloqueados.values()) if bloqueados else None
            candidatos = [t for t in (proximo_arribo, proximo_desb) if t is not None]
            if not candidatos:
                break
            tiempo = max(tiempo, min(candidatos))
            continue

        # Tomar CPU si está libre
        if ejecutando is None and ready:
            pid = ready.popleft()
            p = idmap[pid]
            # Asegurar ráfaga CPU válida
            if not is_cpu_burst(p):
                # si por alguna razón no era CPU, lo encaminamos como BLOQ y seguimos
                if collapse_zeros(p, tiempo):
                    completado[pid] = True
                    continue
                if not is_cpu_burst(p):
                    # agendar bloqueo
                    dur = p.bursts[p.current_burst_index]
                    if dur > 0:
                        gantt.append((pid, tiempo, tiempo + dur, "BLOCK"))
                        bloqueados[pid] = tiempo + dur
                        continue
            if pid not in rem_burst:
                rem_burst[pid] = p.bursts[p.current_burst_index]
            ejecutando = pid
            inicio_tramo = tiempo
            qleft = min(quantum, rem_burst[pid])
            if p.start_time is None:
                p.start_time = tiempo  # primera vez que pisa CPU

        # Ejecutar hasta límite (fin de ráfaga / fin de quantum) o hasta “evento de calendario”
        pid = ejecutando
        p = idmap[pid]
        t_slice_end = tiempo + (qleft if qleft is not None else quantum)
        t_burst_end = tiempo + rem_burst[pid]
        proximo_arribo = arrivals[arr_idx].arrival_time if arr_idx < len(arrivals) else None
        proximo_desb = min(bloqueados.values()) if bloqueados else None

        # Igual que tu compa: miramos eventos de calendario, PERO no preemptamos (sólo para saber si hay que encolar)
        candidatos = [t_slice_end, t_burst_end]
        if proximo_arribo is not None:
            candidatos.append(proximo_arribo)
        if proximo_desb is not None:
            candidatos.append(proximo_desb)
        t_next = min(candidatos)
        delta = max(0, t_next - tiempo)

        if delta > 0:
            rem_burst[pid] -= delta
            if qleft is not None:
                qleft -= delta
            # dibujar CPU consumida
            # (ojo: podemos tener múltiples “continues” antes; cerramos el segmento acá)
            prev = tiempo
            tiempo = t_next
            if inicio_tramo is not None and prev < tiempo:
                # Segmento de CPU continuo en el Gantt
                gantt.append((pid, prev, tiempo, "CPU"))

        # Si ocurrió un arribo o desbloqueo ANTES de agotar quantum o ráfaga: no hay preemp. Encolar y continuar
        if tiempo < min(t_slice_end, t_burst_end):
            encolar_eventos()
            continue

        # Fin de tramo (por quantum o fin de ráfaga). Orden exacto:
        # 1) Primero gestionar al que terminaba
        if rem_burst[pid] == 0:
            # Terminó ráfaga CPU
            p.advance_burst()
            rem_burst.pop(pid, None)
            qleft = None

            if p.current_burst_index >= len(p.bursts):
                p.completion_time = tiempo
                completado[pid] = True
                ejecutando = None
                inicio_tramo = None
            else:
                # ¿viene BLOQ o CPU?
                if not is_cpu_burst(p):
                    # Hay I/O: se agenda BLOQ (no se re-encola ahora)
                    dur = p.bursts[p.current_burst_index]
                    if dur > 0:
                        gantt.append((pid, tiempo, tiempo + dur, "BLOCK"))
                        bloqueados[pid] = tiempo + dur
                    else:
                        # bloqueo 0 → avanzar de nuevo
                        p.advance_burst()
                        if p.current_burst_index >= len(p.bursts):
                            p.completion_time = tiempo
                            completado[pid] = True
                        elif is_cpu_burst(p):
                            ready.append(pid)
                    ejecutando = None
                    inicio_tramo = None
                else:
                    # Siguiente también es CPU → re-encolar al FINAL
                    ready.append(pid)
                    ejecutando = None
                    inicio_tramo = None

            # 2) Luego encolar eventos de este mismo t (quedan detrás)
            encolar_eventos()
            continue

        # No terminó ráfaga => se agotó quantum: re-encolar al FINAL
        if qleft == 0:
            ready.append(pid)
            ejecutando = None
            inicio_tramo = None
            qleft = None
            # y recién después encolar eventos de este mismo t
            encolar_eventos()
            continue

    return gantt, processes
