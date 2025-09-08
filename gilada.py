from models.process import Process
from algoritmos.roundrobin import round_robin

# Datos del ejercicio
datos = [
    ("P1", 0, [10]),
    ("P2", 0, [7]),
    ("P3", 1, [6]),
    ("P4", 1, [3]),
    ("P5", 3, [5]),
    ("P6", 4, [2]),
    ("P7", 6, [6]),
]

# Crear procesos
processes = []
for pid, arrival, bursts in datos:
    p = Process(pid, arrival, bursts)
    processes.append(p)

print("=== EJECUTANDO ROUND ROBIN CON QUANTUM 3 ===")
print("Datos de entrada:")
for p in processes:
    print(f"{p.pid}: llegada={p.arrival_time}, tiempo={p.remaining_time}")

# Ejecutar Round Robin
gantt_chart, completed_processes = round_robin(processes, 3)

print("\n=== GANTT CHART ===")
for pid, start, end in gantt_chart:
    print(f"{pid}: {start}-{end}")

print("\n=== SECUENCIA DE EJECUCIÓN ===")
secuencia = []
for pid, start, end in gantt_chart:
    if pid != "IDLE":
        secuencia.append(pid)
print("Secuencia obtenida:", ",".join(secuencia))
print("Secuencia esperada: P1,P2,P3,P4,P5,P1,P6,P7,P2,P3,P5,P1,P7,P2,P1")

print(f"\nTiempo total de ejecución: {gantt_chart[-1][2]}")
print("Tiempo esperado: 39")

print("\n=== MÉTRICAS DE PROCESOS ===")
for p in completed_processes:
    print(f"{p.pid}: T_completion={p.completion_time}, T_waiting={p.waiting_time}, T_turnaround={p.turnaround_time}")
