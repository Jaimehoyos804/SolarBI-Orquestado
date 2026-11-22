CATALOGO = {
    "gridpowerw_a": {
        "expr": "gridpowerw_a",
        "descripcion": "Potencia de red reportada por el inversor",
        "unidad": "desconocida", "estado": "sin_confirmar",
        "notas": "Razón con V×gridcurr_a de 0.66 y 0.29 (no cuadra) y perfil horario casi plano. Descartada como medida de importación.",
    },
    "linepowerw_a": {
        "expr": "linepowerw_a",
        "descripcion": "Potencia activa de línea  del inversor",
        "unidad": "W (consistente con V×I, razón 0.81-0.91)", "estado": "candidata",
        "notas": "Perfil de importación esperado: alta de noche, casi 0 a mediodía (inversor 1). Variable base de la dependencia de la red.",
    },
    "pv1power": {
        "expr": "pv1power",
        "descripcion": "Potencia del arreglo fotovoltaico ",
        "unidad": "W (razón 0.998 con V×I)", "estado": "candidata",
        "notas": "Fuente solar para el balance energético",
    },
    "outw_a": {
        "expr": "outw_a",
        "descripcion": "Potencia activa de salida del inversor ",
        "unidad": "W (razón 0.84 con V×I: factor de potencia)", "estado": "candidata",
        "notas": "Destino de la energía en el balance",
    },
    "battpower_calc": {
        "expr": "battvolt * battcurr",
        "descripcion": "Potencia de batería calculada (voltaje × corriente)",
        "unidad": "W (por construcción)", "estado": "candidata",
        "notas": "Signo confirmado con battchgpower: corriente negativa = carga, positiva = descarga. La corriente positiva casi permanente del inversor 1 (~1.7 A) sugiere consumo propio o desfase de medición.",
    },
}