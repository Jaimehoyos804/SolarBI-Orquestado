CATALOGO = {
    "gridpowerw_a": {
        "expr": "gridpowerw_a",
        "descripcion": "Potencia de red reportada por el inversor",
        "unidad": "W (hipótesis)", "estado": "sin_confirmar",
        "notas": "Perfil horario casi plano; no se comporta como importación",
    },
    "linepowerw_a": {
        "expr": "linepowerw_a",
        "descripcion": "Potencia de línea reportada por el inversor",
        "unidad": "W (hipótesis)", "estado": "candidata",
        "notas": "Alta de noche y cercana a 0 a mediodía en el inversor 1",
    },
    "pv1power": {
        "expr": "pv1power",
        "descripcion": "Potencia del arreglo fotovoltaico (entrada PV1)",
        "unidad": "W (hipótesis)", "estado": "candidata",
        "notas": "Fuente solar para el balance energético",
    },
    "outw_a": {
        "expr": "outw_a",
        "descripcion": "Potencia activa de salida del inversor (carga atendida)",
        "unidad": "W (hipótesis)", "estado": "candidata",
        "notas": "Destino de la energía en el balance",
    },
    "battpower_calc": {
        "expr": "battvolt * battcurr",
        "descripcion": "Potencia de batería calculada (voltaje × corriente)",
        "unidad": "W (hipótesis)", "estado": "sin_confirmar",
        "notas": "Positivo = descarga, negativo = carga (convención deducida de los eventos de contexto)",
    },
}