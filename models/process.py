class Process:
    def __init__(self, pid, arrival_time, bursts):
        """
        Representa un proceso con ráfagas de CPU y bloqueos (E/S).

        :param pid: Identificador del proceso (str o int)
        :param arrival_time: Tiempo de llegada inicial al sistema
        :param bursts: Lista de enteros, índices pares = CPU, impares = bloqueo
                       Ej: [3, 2, 5] => CPU 3, Bloqueo 2, CPU 5
        """
        self.pid = pid
        self.arrival_time = arrival_time
        self.bursts = bursts[:]  # copia para no modificar la original
        self.current_burst_index = 0
        self.remaining_time = bursts[0] if bursts else 0

        # Métricas
        self.start_time = None
        self.completion_time = None
        self.turnaround_time = None  # TR
        self.waiting_time = None     # TE

    def is_cpu_burst(self):
        """True si la ráfaga actual es de CPU."""
        return self.current_burst_index % 2 == 0

    def advance_burst(self):
        """Avanza a la siguiente ráfaga."""
        self.current_burst_index += 1
        if self.current_burst_index < len(self.bursts):
            self.remaining_time = self.bursts[self.current_burst_index]
        else:
            self.remaining_time = 0

    def calculate_metrics(self):
        """
        Calcula TR (turnaround time) y TE (waiting time).
        TR = completion_time - arrival_time
        TE = TR - tiempo total de CPU - tiempo total de bloqueos
        """
        if self.completion_time is None:
            raise ValueError(f"No se puede calcular métricas: {self.pid} no tiene completion_time asignado.")

        # Tiempo total en el sistema
        self.turnaround_time = self.completion_time - self.arrival_time

        # Suma de todas las ráfagas de CPU (índices pares)
        total_cpu = sum(self.bursts[i] for i in range(0, len(self.bursts), 2))

        # Suma de todas las ráfagas de bloqueo/E/S (índices impares)
        total_bloq = sum(self.bursts[i] for i in range(1, len(self.bursts), 2))

        # Tiempo de espera real en cola de listos
        self.waiting_time = self.turnaround_time - total_cpu - total_bloq

    def __repr__(self):
        return (f"Process(pid={self.pid}, arrival={self.arrival_time}, bursts={self.bursts}, "
                f"start={self.start_time}, completion={self.completion_time}, "
                f"TR={self.turnaround_time}, TE={self.waiting_time})")
