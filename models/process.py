
class Process:
    def __init__(self, pid, arrival_time, burst_time):
        """
        Representa un proceso en el sistema operativo.

        :param pid: Identificador único del proceso (string o int)
        :param arrival_time: Tiempo de llegada al sistema
        :param burst_time: Tiempo total de ejecución requerido
        """
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time

        # Campos para simulación
        self.remaining_time = burst_time  # Para algoritmos expropiativos
        self.start_time = None            # Primer instante en que se ejecuta
        self.completion_time = None       # Momento en que finaliza
        self.turnaround_time = None       # Tiempo de respuesta total
        self.waiting_time = None          # Tiempo total en espera

    def calculate_metrics(self):
        """
        Calcula turnaround_time (tiempo de respuesta total) y waiting_time.
        Debe llamarse después de asignar completion_time.
        """
        if self.completion_time is None:
            raise ValueError(f"No se puede calcular métricas: {self.pid} no tiene completion_time asignado.")

        self.turnaround_time = self.completion_time - self.arrival_time
        self.waiting_time = self.turnaround_time - self.burst_time

    def __repr__(self):
        return (f"Process(pid={self.pid}, arrival={self.arrival_time}, burst={self.burst_time}, "
                f"start={self.start_time}, completion={self.completion_time}, "
                f"TAT={self.turnaround_time}, WT={self.waiting_time})")
