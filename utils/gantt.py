# utils/gantt.py

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def plot_gantt(gantt_chart, title="Diagrama de Gantt"):
    """
    Genera un diagrama de Gantt con cada proceso en su propia fila.

    :param gantt_chart: lista de tuplas (pid, start, end)
                        Ej: [("P1", 0, 5), ("P2", 5, 8), ("IDLE", 8, 10)]
    :param title: título del gráfico
    """
    # Obtener lista única de procesos (excluyendo IDLE)
    procesos_unicos = [pid for pid, _, _ in gantt_chart if pid != "IDLE"]
    procesos_unicos = list(dict.fromkeys(procesos_unicos))  # Mantener orden

    # Asignar un índice Y a cada proceso
    y_positions = {pid: i for i, pid in enumerate(procesos_unicos)}

    # Colores
    colors = {}
    color_palette = plt.cm.get_cmap("tab20", len(procesos_unicos) + 1)

    fig, ax = plt.subplots(figsize=(10, len(procesos_unicos) * 0.8))

    for i, (pid, start, end) in enumerate(gantt_chart):
        if pid not in colors:
            if pid == "IDLE":
                colors[pid] = "lightgray"
            else:
                colors[pid] = color_palette(len(colors))

        # Si es IDLE, lo ponemos en una fila especial o en la fila del proceso anterior
        y = y_positions.get(pid, -1)  # -1 si es IDLE

        ax.barh(y, end - start, left=start, height=0.5,
                align='center', color=colors[pid], edgecolor='black')

        # Etiqueta centrada
        ax.text((start + end) / 2, y, pid,
                ha='center', va='center', color='black', fontsize=9)

    # Configuración del eje Y
    ax.set_yticks(list(y_positions.values()))
    ax.set_yticklabels(list(y_positions.keys()))

    # Configuración del eje X: mostrar todos los ticks
    max_time = max(end for _, _, end in gantt_chart)
    ax.set_xticks(range(0, max_time + 1))
    ax.set_xlim(0, max_time)

    # Cuadrícula
    ax.grid(True, axis='x', linestyle='--', alpha=0.6)

    # Etiquetas y título
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Procesos")
    ax.set_title(title)

    # Leyenda
    legend_patches = [mpatches.Patch(color=col, label=pid) for pid, col in colors.items()]
    ax.legend(handles=legend_patches, bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    plt.show()
