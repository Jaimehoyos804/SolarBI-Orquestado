-- Q1. Perfil por franja horaria e inversor (agregación + dimensión propia)
SELECT i.nombre, h.franja,
       round(sum(f.coverage_minutes) / 60, 1)                        AS horas_cubiertas,
       round(sum(f.positive_power_unit_hours), 1)                    AS pos_total,
       round(sum(f.positive_power_unit_hours)
             / NULLIF(sum(f.coverage_minutes) / 60, 0), 2)           AS pos_por_hora_cubierta
FROM gold.fact_energia_red_hora f
JOIN gold.dim_inversor i USING (inverter_key)
JOIN gold.dim_hora h     USING (hora_key)
GROUP BY i.nombre, h.franja
ORDER BY i.nombre, min(h.hora_key);

-- Q2. Comparativo mensual con LAG (ventana + variación contra el mes anterior)
WITH mensual AS (
  SELECT f.inverter_key, d.anio, d.mes,
         sum(f.positive_power_unit_hours) AS pos,
         sum(f.coverage_minutes) / 60     AS horas_cub
  FROM gold.fact_energia_red_hora f
  JOIN gold.dim_fecha d USING (fecha_key)
  GROUP BY 1, 2, 3
), tasa AS (
  SELECT *, pos / NULLIF(horas_cub, 0) AS pos_por_hora
  FROM mensual
)
SELECT inverter_key, anio, mes,
       round(horas_cub, 1)    AS horas_cubiertas,
       round(pos_por_hora, 2) AS pos_por_hora_cubierta,
       round(100 * (pos_por_hora
             / NULLIF(lag(pos_por_hora) OVER (PARTITION BY inverter_key ORDER BY anio, mes), 0)
             - 1), 1)         AS var_pct_vs_mes_anterior
FROM tasa
ORDER BY inverter_key, anio, mes;