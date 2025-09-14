# NO TOCAR MAS YA FUNCIONA BIEN 
from copy import deepcopy

def fifo_blocking(process_list):
    # Crear copia profunda para no modificar la lista original
    processes = deepcopy(process_list)
    time = 0  # Reloj del sistema
    gantt_chart = []  # Lista para almacenar el diagrama de Gantt
    ready_queue = []  # Cola de procesos listos para ejecutar
    blocked_queue = []  # Cola de procesos bloqueados: (proceso, unblock_time)
    completed = 0  # Contador de procesos completados
    n = len(processes)  # Total de procesos

    current = None  # Proceso actualmente en ejecución
    start_time = None  # Tiempo de inicio del bloque actual en Gantt

    # Buffers de encolado para respetar la prioridad:
    # primero entran los que terminan CPU (CPU_FINISH), luego los que salen de BLOQ (UNBLOCK)
    enq_cpu = []      # procesos que entran a ready por llegada o por terminar CPU
    enq_unblock = []  # procesos que entran a ready por desbloqueo

    while completed < n:  # Mientras no se completen todos los procesos
        # 1) Llegadas - Procesar procesos que llegan en este momento
        for p in processes:
            # Verificar si el proceso:
            # - Llega exactamente en este momento (arrival_time == time)
            # - No ha terminado (completion_time is None)
            # - No está ya en la cola de listos
            # - No está bloqueado
            # - No es el proceso actual en ejecución
            # - No está ya en los buffers de encolado
            if (
                p.arrival_time == time
                and p.completion_time is None
                and p not in ready_queue
                and all(bp is not p for bp, _ in blocked_queue)
                and p is not current
                and p not in enq_cpu  # evitar duplicado si llega y ya está en buffer
                and p not in enq_unblock
            ):
                if p.is_cpu_burst():  # Si la primera ráfaga es de CPU
                    enq_cpu.append(p)  # PRIORIDAD: llegan a ready como CPU_FINISH
                else:  # Si la primera ráfaga es de bloqueo
                    dur = p.bursts[p.current_burst_index]  # Duración del bloqueo
                    if dur > 0:  # Si el bloqueo tiene duración
                        gantt_chart.append((p.pid, time, time + dur, "BLOCK"))  # Registrar bloqueo
                        blocked_queue.append((p, time + dur))  # Agregar a cola de bloqueados
                    else:  # Si el bloqueo es de duración 0
                        p.advance_burst()  # Avanzar a la siguiente ráfaga
                        if p.current_burst_index >= len(p.bursts):  # Si terminó el proceso
                            p.completion_time = time
                            completed += 1
                        elif p.is_cpu_burst():  # Si la siguiente es CPU
                            enq_cpu.append(p)  # entra por CPU
                        else:  # Si la siguiente es otro bloqueo
                            dur2 = p.bursts[p.current_burst_index]
                            if dur2 > 0:  # Si tiene duración
                                gantt_chart.append((p.pid, time, time + dur2, "BLOCK"))
                                blocked_queue.append((p, time + dur2))
                            else:  # Si es de duración 0
                                p.advance_burst()
                                if p.current_burst_index < len(p.bursts) and p.is_cpu_burst():
                                    enq_cpu.append(p)

        # 2) Desbloqueos que vencen ahora - Procesar procesos que terminan su bloqueo
        for (bp, unblock_time) in blocked_queue[:]:  # Iterar sobre una copia de la lista
            if unblock_time == time:  # Si el bloqueo termina en este momento
                blocked_queue.remove((bp, unblock_time))  # Remover de la cola de bloqueados
                bp.advance_burst()  # Avanzar a la siguiente ráfaga
                if bp.current_burst_index >= len(bp.bursts):  # Si terminó el proceso
                    bp.completion_time = time
                    completed += 1
                else:
                    if bp.is_cpu_burst():  # Si la siguiente ráfaga es de CPU
                        enq_unblock.append(bp)  # SALIDA DE BLOQ va detrás de CPU_FINISH
                    else:  # Si la siguiente ráfaga es de bloqueo
                        dur2 = bp.bursts[bp.current_burst_index]
                        if dur2 > 0:  # Si tiene duración
                            gantt_chart.append((bp.pid, time, time + dur2, "BLOCK"))
                            blocked_queue.append((bp, time + dur2))
                        else:  # Si es de duración 0
                            bp.advance_burst()
                            if bp.current_burst_index >= len(bp.bursts):  # Si terminó
                                bp.completion_time = time
                                completed += 1
                            elif bp.is_cpu_burst():  # Si la siguiente es CPU
                                enq_unblock.append(bp)

        # Mezclar en ready con la prioridad requerida: primero enq_cpu, luego enq_unblock
        if enq_cpu or enq_unblock:  # Si hay procesos en los buffers
            ready_queue.extend(enq_cpu)  # Agregar procesos de CPU primero
            ready_queue.extend(enq_unblock)  # Luego los de desbloqueo
            enq_cpu.clear()  # Limpiar buffer de CPU
            enq_unblock.clear()  # Limpiar buffer de desbloqueo

        # 3) Selección FIFO - Elegir proceso para ejecutar
        if current is None and ready_queue:  # Si no hay proceso ejecutando y hay listos
            current = ready_queue.pop(0)  # Tomar el primero de la cola (FIFO)
            start_time = time  # Marcar inicio del bloque
            if current.start_time is None:  # Si es la primera vez que se ejecuta
                current.start_time = time  # solo la primera vez que toca CPU

        # 4) Ejecutar 1 tick de CPU o avanzar tiempo si no hay listos
        if current:  # Si hay un proceso ejecutando
            current.remaining_time -= 1  # Reducir tiempo restante
            time += 1  # Avanzar el reloj del sistema

            # ¿Terminó esta ráfaga de CPU?
            if current.remaining_time == 0:  # Si terminó la ráfaga de CPU
                # Cerrar tramo de CPU
                gantt_chart.append((current.pid, start_time, time, "CPU"))

                # Avanzar a la siguiente ráfaga
                current.advance_burst()

                # ¿Proceso terminado?
                if current.current_burst_index >= len(current.bursts):  # Si terminó el proceso
                    current.completion_time = time
                    completed += 1
                    current = None  # Liberar CPU
                else:
                    # ¿Siguiente es CPU?
                    if current.is_cpu_burst():  # Si la siguiente ráfaga es de CPU
                        # Entra a ready como "CPU_FINISH" (prioridad sobre UNBLOCK si coincide el instante)
                        enq_cpu.append(current)
                        current = None  # Liberar CPU
                    else:  # Si la siguiente ráfaga es de bloqueo
                        # Siguiente es BLOQUEO
                        dur = current.bursts[current.current_burst_index]
                        if dur > 0:  # Si tiene duración
                            gantt_chart.append((current.pid, time, time + dur, "BLOCK"))
                            blocked_queue.append((current, time + dur))
                            current = None  # Liberar CPU
                        else:  # Si es de duración 0
                            # Bloqueo de 0 → saltar
                            current.advance_burst()
                            if current.current_burst_index >= len(current.bursts):  # Si terminó
                                current.completion_time = time
                                completed += 1
                                current = None
                            elif current.is_cpu_burst():  # Si la siguiente es CPU
                                enq_cpu.append(current)
                                current = None

            # Tras terminar el tick, antes de próxima selección, volcamos buffers con prioridad
            if enq_cpu or enq_unblock:  # Si hay procesos en los buffers
                ready_queue.extend(enq_cpu)  # Agregar procesos de CPU primero
                ready_queue.extend(enq_unblock)  # Luego los de desbloqueo
                enq_cpu.clear()  # Limpiar buffer de CPU
                enq_unblock.clear()  # Limpiar buffer de desbloqueo
        else:  # No hay proceso ejecutando
            # No hay proceso ejecutando ni listo: avanzar tiempo "vacío" (no pintamos IDLE)
            time += 1

    return gantt_chart, processes
