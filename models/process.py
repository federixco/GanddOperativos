# GanddOperativos/models/process.py
class Process:
    def __init__(self, pid, arrival_time, bursts, priority=0):
        """
        Representa un proceso con ráfagas de CPU y bloqueos (E/S).

        :param pid: Identificador del proceso (str o int)
        :param arrival_time: Tiempo de llegada inicial al sistema
        :param bursts: Lista de enteros, índices pares = CPU, impares = bloqueo
                       Ej: [3, 2, 5] => CPU 3, Bloqueo 2, CPU 5
        :param priority: Prioridad del proceso (entero, mayor número = mayor prioridad)
        """
        self.pid = pid
        self.arrival_time = arrival_time
        self.bursts = bursts[:]              # copia viva (puede mutar en algoritmos)
        self.bursts_original = bursts[:]     # copia inmutable para métricas
        self.current_burst_index = 0
        self.remaining_time = bursts[0] if bursts else 0
        self.priority = priority             # Prioridad del proceso (mayor número = mayor prioridad)

        # Métricas
        self.start_time = None
        self.completion_time = None
        self.turnaround_time = None  # TR
        self.waiting_time = None     # TE

        # Estado de planificación
        self.ready_since = None      # cuándo quedó en ready por última vez

    # ---------- Utilidades de estado ----------
    def is_cpu_burst(self):
        """True si la ráfaga actual es de CPU (índice par)."""
        return self.current_burst_index % 2 == 0

    def is_finished(self):
        """True si el proceso ha terminado todas sus ráfagas."""
        return self.current_burst_index >= len(self.bursts)

    def advance_burst(self):
        """Avanza a la siguiente ráfaga."""
        self.current_burst_index += 1
        if self.current_burst_index < len(self.bursts):
            self.remaining_time = self.bursts[self.current_burst_index]
        else:
            self.remaining_time = 0

    def get_remaining_bursts(self):
        """Retorna las ráfagas restantes del proceso (desde el índice actual)."""
        return self.bursts[self.current_burst_index:] if self.current_burst_index < len(self.bursts) else []

    def get_burst_sequence_description(self):
        """Retorna una descripción legible de la secuencia de ráfagas."""
        if not self.bursts:
            return "Sin ráfagas"
        sequence = []
        for i, duration in enumerate(self.bursts):
            burst_type = "CPU" if i % 2 == 0 else "Bloqueo"
            sequence.append(f"{burst_type}({duration})")
        return " → ".join(sequence)

    # ---------- Cálculos de prioridad / apoyo a algoritmos ----------
    def get_total_cpu_remaining(self):
        """
        Retorna el total de CPU restante desde la posición actual.
        Si está en bloqueo (índice impar), comienza desde la próxima CPU.
        Considera la lista 'bursts' viva (por si un algoritmo preemptivo descuenta).
        """
        idx = self.current_burst_index
        if idx >= len(self.bursts):
            return 0
        start = idx if idx % 2 == 0 else idx + 1
        total = 0
        for i in range(start, len(self.bursts), 2):  # sólo índices de CPU
            dur = self.bursts[i]
            if dur < 0:
                dur = 0
            total += dur
        return total

    # ---------- Métricas (siempre contra los datos originales) ----------
    def calculate_metrics(self):
        """
        Calcula TR (turnaround time) y TE (waiting time).
        TR = completion_time - arrival_time
        TE = TR - tiempo total de CPU - tiempo total de bloqueos
        Se usa 'bursts_original' para evitar sesgos si un algoritmo mutó 'bursts'.
        """
        if self.completion_time is None:
            raise ValueError(f"No se puede calcular métricas: {self.pid} no tiene completion_time asignado.")

        source = self.bursts_original if hasattr(self, "bursts_original") and self.bursts_original else self.bursts

        # Tiempo total en el sistema
        self.turnaround_time = self.completion_time - self.arrival_time

        # Suma de todas las ráfagas de CPU (índices pares)
        total_cpu = sum(source[i] for i in range(0, len(source), 2))

        # Suma de todas las ráfagas de bloqueo/E/S (índices impares)
        total_bloq = sum(source[i] for i in range(1, len(source), 2))

        # Tiempo de espera real en cola de listos
        self.waiting_time = self.turnaround_time - total_cpu - total_bloq

    # ---------- Agregados informativos ----------
    def get_total_cpu_time(self):
        """Retorna el tiempo total de CPU del proceso (sobre datos originales si están disponibles)."""
        source = self.bursts_original if hasattr(self, "bursts_original") and self.bursts_original else self.bursts
        return sum(source[i] for i in range(0, len(source), 2))

    def get_total_blocking_time(self):
        """Retorna el tiempo total de bloqueo del proceso (sobre datos originales si están disponibles)."""
        source = self.bursts_original if hasattr(self, "bursts_original") and self.bursts_original else self.bursts
        return sum(source[i] for i in range(1, len(source), 2))

    def get_burst_count(self):
        """Retorna el número total de ráfagas (CPU + bloqueos)."""
        return len(self.bursts)

    def get_cpu_burst_count(self):
        """Retorna el número de ráfagas de CPU."""
        return len([i for i in range(0, len(self.bursts), 2)])

    def get_blocking_burst_count(self):
        """Retorna el número de ráfagas de bloqueo."""
        return len([i for i in range(1, len(self.bursts), 2)])

    def __repr__(self):
        return (f"Process(pid={self.pid}, arrival={self.arrival_time}, bursts={self.bursts}, "
                f"priority={self.priority}, idx={self.current_burst_index}, start={self.start_time}, "
                f"completion={self.completion_time}, TR={self.turnaround_time}, TE={self.waiting_time})")
