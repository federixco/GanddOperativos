def calcular_metricas(procesos):
    lista_metricas = []
    total_tr = 0
    total_te = 0

    for p in procesos:
        # Asegurarnos de que las métricas estén calculadas
        if p.turnaround_time is None or p.waiting_time is None:
            p.calculate_metrics()

        # Usar bursts_original si existe, si no, usar bursts actual
        bursts_fuente = getattr(p, "bursts_original", p.bursts)

        # Suma de todas las ráfagas de CPU (índices pares)
        total_cpu = sum(bursts_fuente[i] for i in range(0, len(bursts_fuente), 2))

        lista_metricas.append({
            "PID": p.pid,
            "Llegada": p.arrival_time,
            "CPU": total_cpu,
            "Finalización": p.completion_time,
            "TR": p.turnaround_time,
            "TE": p.waiting_time
        })

        total_tr += p.turnaround_time
        total_te += p.waiting_time

    trm = total_tr / len(procesos) if procesos else 0
    tem = total_te / len(procesos) if procesos else 0

    return lista_metricas, trm, tem



def imprimir_tabla_metricas(metricas, trm, tem):
    """
    Imprime la tabla de métricas en consola.
    """
    print(f"{'PID':<6}{'Llegada':<10}{'CPU':<8}{'Finalización':<14}{'TR':<8}{'TE':<8}")
    for m in metricas:
        print(f"{m['PID']:<6}{m['Llegada']:<10}{m['CPU']:<8}{m['Finalización']:<14}{m['TR']:<8}{m['TE']:<8}")
    print("\n📈 Promedios:")
    print(f"TRM (Tiempo de Respuesta Medio): {trm:.2f}")
    print(f"TEM (Tiempo de Espera Medio): {tem:.2f}")
