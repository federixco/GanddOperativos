class Proceso:
    def __init__(self, pid, arrival_time, bursts):
        self.pid = pid
        self.arrival_time = arrival_time
        self.bursts = bursts[:]  # [CPU, IO, CPU, IO...]
        self.bursts_original = bursts[:]
        self.current_burst_index = 0
        self.completion_time = None
        self.start_time = None
        self._seq = 0
        self.remaining_time = sum(b for i, b in enumerate(bursts) if i % 2 == 0)

    def is_cpu_burst(self):
        return self.current_burst_index % 2 == 0

    def advance_burst(self):
        self.current_burst_index += 1

def sjf_blocking(processes):
    time = 0
    gantt = []
    ready = []
    blocked = []
    completed = 0
    n = len(processes)

    def collapse_zeros(p, t):
        while p.current_burst_index < len(p.bursts) and p.bursts[p.current_burst_index] == 0:
            p.advance_burst()
        if p.current_burst_index >= len(p.bursts):
            p.completion_time = t
            return True
        return False

    while completed < n:
        # desbloqueos
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
                    blocked.append((bp, time+dur))

        # llegadas
        for p in processes:
            if p.arrival_time == time and p.completion_time is None and p not in ready and all(bp is not p for bp, _ in blocked):
                if collapse_zeros(p, time):
                    completed += 1
                    continue
                if p.is_cpu_burst():
                    ready.append(p)
                else:
                    dur = p.bursts[p.current_burst_index]
                    blocked.append((p, time+dur))

        # si no hay listos
        if not ready:
            next_event = min(
                [unb for _, unb in blocked] +
                [p.arrival_time for p in processes if p.completion_time is None and p.arrival_time > time],
                default=None
            )
            if next_event is None:
                time += 1
            elif next_event > time:
                time = next_event
            else:
                time += 1
            continue

        # elegir más corto (FIFO en empates)
        ready.sort(key=lambda x: (x.bursts[x.current_burst_index], x.arrival_time, x._seq))
        current = ready.pop(0)
        if current.start_time is None:
            current.start_time = time

        # ejecutar ráfaga completa
        start = time
        cpu_dur = current.bursts[current.current_burst_index]
        time += cpu_dur
        current.remaining_time -= cpu_dur
        gantt.append((current.pid, start, time, "CPU"))

        # avanzar
        current.advance_burst()
        if collapse_zeros(current, time):
            completed += 1
            continue
        if current.is_cpu_burst():
            ready.append(current)
        else:
            dur = current.bursts[current.current_burst_index]
            blocked.append((current, time+dur))

    return gantt

# Datos del ejercicio
datos = [
    ("A", 0, [6, 2, 3]),
    ("B", 0, [3, 3, 3]),
    ("C", 1, [1, 2, 1]),
    ("D", 1, [4, 3, 3]),
    ("E", 3, [5, 1, 4]),
    ("F", 3, [3, 2, 2]),
    ("G", 4, [2, 1, 2]),
    ("H", 5, [4, 4, 3]),
    ("I", 6, [3])
]

procesos = []
for idx, (pid, arr, bursts) in enumerate(datos):
    p = Proceso(pid, arr, bursts)
    p._seq = idx
    procesos.append(p)

gantt = sjf_blocking(procesos)

# Mostrar solo el orden de CPU
orden_cpu = [pid for pid, s, e, tipo in gantt if tipo == "CPU"]
print("Orden de ejecución de CPU:", orden_cpu)
