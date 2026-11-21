# Hallazgos línea 4 — dependencia de la red

- **Inversor 1:** voltaje de línea ≈ 0 V desde 2026-05-03 02:51 (hora Bogotá) hasta el último dato (2026-07-13).
  Frecuencia y `gridpowerw_a` también en 0. Los eventos `grid_unavailable_or_islanded` cubren solo hasta 2026-06-09.
- **Inversor 2:** mismo corte el 2026-05-03; de W20 a W23 reporta filas con voltaje y potencia NULL; deja de reportar el 2026-06-22.
- **Abril 2026, inversor 2:** `gridpowerw_a` alterna entre ~3 y ~45 de un día a otro con voltaje normal. Sin explicación; no se interpreta como dependencia.
- **Muestreo:** ~12.6 s (abr), ~60 s (W19-W24), ~11 s (W25-W27).
- **Límite:** los eventos de `context` son derivados de las mismas mediciones, no una fuente independiente.
- **Pendiente:** unidad y signo de `gridpowerw_a`; causa del corte.