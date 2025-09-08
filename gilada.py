
from models.process import Process
from algoritmos.sjf_blocking import sjf_blocking

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
    p = Process(pid, arr, bursts)
    procesos.append(p)

print("Ejecutando SJF blocking...")
gantt, result = sjf_blocking(procesos)

print("Orden de ejecución de CPU:")
orden_cpu = [pid for pid, s, e, tipo in gantt if tipo == "CPU"]
print("Actual:", orden_cpu)
print("Esperado: ['B', 'C', 'G', 'I', 'F', 'D', 'H', 'A', 'E']")

print("\nPrimera ejecución de cada proceso:")
primeras = {}
for pid, s, e, tipo in gantt:
    if tipo == "CPU" and pid not in primeras:
        primeras[pid] = s
for pid in ["B", "C", "G", "I", "F", "D", "H", "A", "E"]:
    if pid in primeras:
        print(f"  {pid}: tiempo {primeras[pid]}")

print("\nTiempos totales de CPU:")
for pid, arr, bursts in datos:
    total_cpu = sum(bursts[i] for i in range(0, len(bursts), 2))
    print(f"  {pid}: {total_cpu} segundos total")

print("\nGantt completo:")
for i, seg in enumerate(gantt):
    print(f"  {i+1:2d}: {seg}")
