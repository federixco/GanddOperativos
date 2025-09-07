# utils/metrics.py

def calcular_metricas(procesos):
    """
    Calcula métricas para cada proceso y devuelve también los promedios.

    :param procesos: lista de objetos Process con completion_time asignado
    :return: (lista_metricas, TRM, TEM)
    """
    lista_metricas = []
    total_tr = 0
    total_te = 0

    for p in procesos:
        # Asegurarnos de que TR y TE estén calculados
        if p.turnaround_time is None or p.waiting_time is None:
            p.calculate_metrics()

        lista_metricas.append({
            "PID": p.pid,
            "Llegada": p.arrival_time,
            "CPU": p.burst_time,
            "Finalización": p.completion_time,
            "TR": p.turnaround_time,
            "TE": p.waiting_time
        })

        total_tr += p.turnaround_time
        total_te += p.waiting_time

    trm = total_tr / len(procesos) if procesos else 0
    tem = total_te / len(procesos) if procesos else 0

    return lista_metricas, trm, tem


def imprimir_tabla_metricas(lista_metricas, trm, tem):
    """
    Imprime una tabla de métricas en consola en español.
    """
    print("\n📊 Métricas por proceso:")
    print(f"{'PID':<6}{'Llegada':<10}{'CPU':<8}{'Finalización':<14}{'TR':<8}{'TE':<8}")
    for m in lista_metricas:
        print(f"{m['PID']:<6}{m['Llegada']:<10}{m['CPU']:<8}{m['Finalización']:<14}{m['TR']:<8}{m['TE']:<8}")

    print("\n📈 Promedios:")
    print(f"TRM (Tiempo de Respuesta Medio): {trm:.2f}")
    print(f"TEM (Tiempo de Espera Medio): {tem:.2f}")
