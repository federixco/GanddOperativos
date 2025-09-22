from copy import deepcopy

def priority_blocking(process_list):
    """
    ALGORITMO DE PRIORIDADES - NO EXPULSIVO CON BLOQUEOS
    
    FUNCIONAMIENTO:
    - Los procesos se ejecutan en orden de prioridad (mayor número = mayor prioridad)
    - Una vez que un proceso comienza a ejecutarse, no puede ser interrumpido
    - Los procesos pueden tener múltiples ráfagas de CPU y E/S (bloqueos)
    - Cuando un proceso termina una ráfaga de CPU, puede ir a bloqueo o continuar con otra CPU
    - Cuando un proceso termina un bloqueo, regresa a la cola de listos
    - Se respeta la prioridad: procesos que terminan CPU tienen prioridad sobre los que salen de bloqueo
    - En caso de empate de prioridad, se aplica FIFO (orden de llegada)
    
    CARACTERÍSTICAS:
    - No expulsivo: no hay preempción una vez que comienza la ejecución
    - Con bloqueos: maneja operaciones de E/S (Entrada/Salida)
    - Basado en prioridades: mayor número = mayor prioridad
    - Desempate FIFO: en caso de empate de prioridad, el primero en llegar se ejecuta primero
    - Maneja múltiples ráfagas: CPU → E/S → CPU → E/S → ...
    - Puede causar inanición: procesos de baja prioridad pueden esperar indefinidamente
    
    PARÁMETROS:
    - process_list: Lista de objetos Process con bursts=[CPU, E/S, CPU, E/S, ...] y priority asignada
    
    RETORNA:
    - gantt_chart: Lista de tuplas (pid, start, end, tipo) para el diagrama de Gantt
    - processes: Lista de procesos con métricas calculadas
    """
    
    # Crear copia profunda para no modificar la lista original
    processes = deepcopy(process_list)
    
    # Inicializar variables del simulador
    time = 0  # Reloj del sistema (tiempo actual de simulación)
    gantt_chart = []  # Lista para almacenar el diagrama de Gantt
    ready_queue = []  # Cola de procesos listos para ejecutar
    blocked_queue = []  # Cola de procesos bloqueados: (proceso, unblock_time)
    completed = 0  # Contador de procesos completados
    n = len(processes)  # Total de procesos a procesar

    # Variables para controlar la ejecución actual
    current = None  # Proceso actualmente en ejecución
    start_time = None  # Tiempo de inicio del bloque actual en Gantt

    # Buffers de encolado para respetar la prioridad:
    # primero entran los que terminan CPU (CPU_FINISH), luego los que salen de BLOQ (UNBLOCK)
    enq_cpu = []      # procesos que entran a ready por llegada o por terminar CPU
    enq_unblock = []  # procesos que entran a ready por desbloqueo

    # Verificar que los procesos tengan prioridad asignada
    for p in processes:
        if not hasattr(p, 'priority'):
            p.priority = 0

    # BUCLE PRINCIPAL: Simular hasta que todos los procesos terminen
    while completed < n:  # Mientras no se completen todos los procesos
        
        # FASE 1: PROCESAR LLEGADAS
        # Buscar procesos que llegan exactamente en este momento
        for p in processes:
            # Verificar si el proceso cumple todas las condiciones para ser procesado:
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
                # Determinar qué tipo de ráfaga tiene el proceso al llegar
                if p.is_cpu_burst():  # Si la primera ráfaga es de CPU
                    enq_cpu.append(p)  # PRIORIDAD: llegan a ready como CPU_FINISH
                else:  # Si la primera ráfaga es de bloqueo
                    dur = p.bursts[p.current_burst_index]  # Duración del bloqueo
                    if dur > 0:  # Si el bloqueo tiene duración
                        gantt_chart.append((p.pid, time, time + dur, "BLOCK"))  # Registrar bloqueo en Gantt
                        blocked_queue.append((p, time + dur))  # Agregar a cola de bloqueados
                    else:  # Si el bloqueo es de duración 0 (bloqueo instantáneo)
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

        # FASE 2: PROCESAR DESBLOQUEOS
        # Buscar procesos que terminan su bloqueo en este momento
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

        # FASE 3: VOLCAR BUFFERS A COLA DE LISTOS
        # Mezclar en ready con la prioridad requerida: primero enq_cpu, luego enq_unblock
        if enq_cpu or enq_unblock:  # Si hay procesos en los buffers
            ready_queue.extend(enq_cpu)  # Agregar procesos de CPU primero (mayor prioridad)
            ready_queue.extend(enq_unblock)  # Luego los de desbloqueo (menor prioridad)
            enq_cpu.clear()  # Limpiar buffer de CPU
            enq_unblock.clear()  # Limpiar buffer de desbloqueo

        # FASE 4: SELECCIÓN DE PROCESO (CRITERIO DE PRIORIDADES)
        # Elegir proceso para ejecutar si no hay uno ejecutando
        if current is None and ready_queue:  # Si no hay proceso ejecutando y hay listos
            # Ordenar por prioridad (mayor número = mayor prioridad), luego FIFO en empates
            ready_queue.sort(key=lambda p: (
                -p.priority,  # Prioridad descendente (mayor número primero)
                p.arrival_time,  # FIFO en empates (menor tiempo de llegada primero)
                p.pid  # Estabilidad (desempate por PID)
            ))
            
            current = ready_queue.pop(0)  # Tomar el proceso con mayor prioridad
            start_time = time  # Marcar inicio del bloque en Gantt
            
            # Marcar tiempo de inicio si es la primera vez que se ejecuta
            if current.start_time is None:  # Si es la primera vez que se ejecuta
                current.start_time = time  # solo la primera vez que toca CPU

        # FASE 5: EJECUTAR PROCESO O AVANZAR TIEMPO
        if current:  # Si hay un proceso ejecutando
            # Ejecutar 1 tick de CPU
            current.remaining_time -= 1  # Reducir tiempo restante del proceso
            time += 1  # Avanzar el reloj del sistema

            # FASE 6: VERIFICAR SI TERMINÓ LA RÁFAGA DE CPU
            if current.remaining_time == 0:  # Si terminó la ráfaga de CPU
                # Cerrar tramo de CPU en el diagrama de Gantt
                gantt_chart.append((current.pid, start_time, time, "CPU"))

                # Avanzar a la siguiente ráfaga
                current.advance_burst()

                # FASE 7: DETERMINAR QUÉ HACER CON EL PROCESO
                if current.current_burst_index >= len(current.bursts):  # Si terminó el proceso
                    current.completion_time = time
                    completed += 1
                    current = None  # Liberar CPU
                else:
                    # Verificar qué tipo de ráfaga sigue
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
                        else:  # Si es de duración 0 (bloqueo instantáneo)
                            # Bloqueo de 0 → saltar
                            current.advance_burst()
                            if current.current_burst_index >= len(current.bursts):  # Si terminó
                                current.completion_time = time
                                completed += 1
                                current = None
                            elif current.is_cpu_burst():  # Si la siguiente es CPU
                                enq_cpu.append(current)
                                current = None

            # FASE 8: VOLCAR BUFFERS DESPUÉS DE EJECUTAR
            # Tras terminar el tick, antes de próxima selección, volcamos buffers con prioridad
            if enq_cpu or enq_unblock:  # Si hay procesos en los buffers
                ready_queue.extend(enq_cpu)  # Agregar procesos de CPU primero
                ready_queue.extend(enq_unblock)  # Luego los de desbloqueo
                enq_cpu.clear()  # Limpiar buffer de CPU
                enq_unblock.clear()  # Limpiar buffer de desbloqueo
        else:  # No hay proceso ejecutando
            # No hay proceso ejecutando ni listo: avanzar tiempo "vacío" (no pintamos IDLE)
            time += 1

    # Retornar resultados de la simulación
    return gantt_chart, processes

