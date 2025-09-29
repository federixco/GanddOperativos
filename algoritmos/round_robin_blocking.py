from copy import deepcopy
from collections import deque
import re

def _natural_key(pid: str):
    """Orden natural 'P9' < 'P10'; para A..Z simplemente ordena por letra."""
    m = re.search(r'(\d+)$', pid)
    return (int(m.group(1)) if m else float('inf'), pid)

def round_robin_blocking(process_list, quantum):
    """
    Round Robin con BLOQUEOS + 'saldo de quantum':
    - Si una ráfaga termina o el proceso se bloquea ANTES de agotar el quantum, el
      sobrante (crédito) se CONSERVA para su próxima entrada a CPU.
    - Si el proceso agota el quantum, el próximo despacho vuelve con quantum COMPLETO (sin crédito).
    - No hay preempción por llegadas/desbloqueos *durante* el tramo: sólo se encolan.
    - Prioridad temporal en el mismo t: (1) gestionar al que estaba ejecutando, (2) encolar llegadas, (3) encolar desbloqueos.
    - Cola de ready FIFO.
    Retorna: (gantt, processes) con tuplas (pid, start, end, "CPU"/"BLOCK"/"IDLE").
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

    # Ordenar arribos por llegada y clave natural
    arrivals = sorted(processes, key=lambda p: (p.arrival_time, _natural_key(p.pid)))
    arr_idx = 0

    # Estado global
    tiempo = 0
    gantt = []
    ready = deque()             # cola FIFO de pids
    bloqueados = {}             # pid -> t_desbloqueo
    idmap = {p.pid: p for p in processes}

    # CPU actual
    ejecutando = None           # pid
    rem_burst = {}              # pid -> restante de la ráfaga actual
    qcredit = {}                # pid -> crédito de quantum (saldo)
    qleft = None                # quantum restante del *tramo actual*

    completado = {p.pid: False for p in processes}

    # ---- helpers de encolado ----
    def encolar_eventos():
        """Encola ARRIBOS y DESBLOQUEOS con t <= tiempo. ARRIBOS antes que DESBLOQUEOS."""
        nonlocal arr_idx

        # 1) Arribos (<= tiempo)
        while arr_idx < len(arrivals) and arrivals[arr_idx].arrival_time <= tiempo:
            p = arrivals[arr_idx]; arr_idx += 1
            if completado[p.pid]:
                continue
            if collapse_zeros(p, tiempo):
                continue
            if is_cpu_burst(p):
                ready.append(p.pid)
            else:
                # llega en BLOQ
                dur = p.bursts[p.current_burst_index]
                if dur > 0:
                    gantt.append((p.pid, tiempo, tiempo + dur, "BLOCK"))
                    bloqueados[p.pid] = tiempo + dur
                else:
                    p.advance_burst()
                    if is_cpu_burst(p):
                        ready.append(p.pid)

        # 2) Desbloqueos (<= tiempo), orden determinista
        if bloqueados:
            desbloq = sorted(
                [(t, pid) for pid, t in bloqueados.items() if t <= tiempo],
                key=lambda x: (x[0], _natural_key(x[1]))
            )
            for _, pid in desbloq:
                bloqueados.pop(pid, None)
                pp = idmap[pid]
                pp.advance_burst()  # salir del BLOQ
                if collapse_zeros(pp, tiempo):
                    completado[pid] = True
                    qcredit.pop(pid, None)
                    rem_burst.pop(pid, None)
                    continue
                if is_cpu_burst(pp):
                    ready.append(pid)
                else:
                    # otra cadena de BLOQ
                    dur = pp.bursts[pp.current_burst_index]
                    if dur > 0:
                        gantt.append((pid, tiempo, tiempo + dur, "BLOCK"))
                        bloqueados[pid] = tiempo + dur
                    else:
                        pp.advance_burst()
                        if pp.current_burst_index >= len(pp.bursts):
                            pp.completion_time = tiempo
                            completado[pid] = True
                            qcredit.pop(pid, None)
                            rem_burst.pop(pid, None)
                        elif is_cpu_burst(pp):
                            ready.append(pid)

    total = len(processes)

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

            if collapse_zeros(p, tiempo):
                completado[pid] = True
                qcredit.pop(pid, None)
                rem_burst.pop(pid, None)
                continue

            if not is_cpu_burst(p):
                # si no es CPU, encaminar a BLOQ
                dur = p.bursts[p.current_burst_index]
                if dur > 0:
                    gantt.append((pid, tiempo, tiempo + dur, "BLOCK"))
                    bloqueados[pid] = tiempo + dur
                    continue
                else:
                    p.advance_burst()
                    if collapse_zeros(p, tiempo):
                        completado[pid] = True
                        qcredit.pop(pid, None)
                        rem_burst.pop(pid, None)
                        continue
                    if not is_cpu_burst(p):
                        # cadena de bloqueos
                        dur = p.bursts[p.current_burst_index]
                        if dur > 0:
                            gantt.append((pid, tiempo, tiempo + dur, "BLOCK"))
                            bloqueados[pid] = tiempo + dur
                            continue

            if pid not in rem_burst:
                rem_burst[pid] = p.bursts[p.current_burst_index]

            # *** SALDO DE QUANTUM ***
            # Si hay crédito pendiente, usarlo; si no, quantum completo
            qleft = qcredit.get(pid, quantum)

            ejecutando = pid
            if p.start_time is None:
                p.start_time = tiempo  # primera vez en CPU

        # Ejecutar hasta el menor de: fin ráfaga / fin crédito / (arribo o desbloqueo)
        pid = ejecutando
        p = idmap[pid]

        t_slice_end = tiempo + qleft
        t_burst_end = tiempo + rem_burst[pid]
        proximo_arribo = arrivals[arr_idx].arrival_time if arr_idx < len(arrivals) else None
        proximo_desb = min(bloqueados.values()) if bloqueados else None

        candidatos = [t_slice_end, t_burst_end]
        if proximo_arribo is not None:
            candidatos.append(proximo_arribo)
        if proximo_desb is not None:
            candidatos.append(proximo_desb)
        t_next = min(candidatos)
        delta = max(0, t_next - tiempo)

        if delta > 0:
            rem_burst[pid] -= delta
            qleft -= delta
            start = tiempo
            tiempo = t_next
            gantt.append((pid, start, tiempo, "CPU"))

        # Si ocurrió un arribo o desbloqueo ANTES de agotar crédito o ráfaga: no preemp, sólo encolar
        if tiempo < min(t_slice_end, t_burst_end):
            encolar_eventos()
            continue

        # --- Fin de tramo ---
        # 1) Gestionar al que estaba ejecutando
        if rem_burst[pid] == 0:
            # Terminó ráfaga de CPU: conservar el saldo de quantum para la próxima CPU
            # (qleft puede ser > 0)
            p.advance_burst()
            rem_burst.pop(pid, None)

            if p.current_burst_index >= len(p.bursts):
                p.completion_time = tiempo
                completado[pid] = True
                # ya no usará más crédito
                qcredit.pop(pid, None)
                ejecutando = None
            else:
                if is_cpu_burst(p):
                    # CPU-CPU: reencolar con MISMO crédito pend.
                    qcredit[pid] = qleft if qleft > 0 else quantum
                    ready.append(pid)
                    ejecutando = None
                else:
                    # Se bloquea: conservar el saldo para la próxima vez que vuelva a CPU
                    qcredit[pid] = qleft if qleft > 0 else quantum
                    dur = p.bursts[p.current_burst_index]
                    if dur > 0:
                        gantt.append((pid, tiempo, tiempo + dur, "BLOCK"))
                        bloqueados[pid] = tiempo + dur
                    else:
                        p.advance_burst()
                        if p.current_burst_index >= len(p.bursts):
                            p.completion_time = tiempo
                            completado[pid] = True
                            qcredit.pop(pid, None)
                        elif is_cpu_burst(p):
                            ready.append(pid)
                    ejecutando = None

            # 2) Luego encolar eventos de este mismo t
            encolar_eventos()
            continue

        # Si no terminó ráfaga, entonces se agotó el crédito (saldo/quantum)
        if qleft == 0:
            # Al agotar crédito, el próximo despacho vuelve con quantum completo
            qcredit.pop(pid, None)  # sin saldo pendiente
            ready.append(pid)
            ejecutando = None
            encolar_eventos()
            continue

    return gantt, processes
