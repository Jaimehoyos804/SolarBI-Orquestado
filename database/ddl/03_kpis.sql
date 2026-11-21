-- KPI diario de red por inversor y variable
CREATE OR REPLACE VIEW gold.vw_kpi_red_dia AS
SELECT d.fecha,
       f.inverter_key,
       f.variable_key,
       round(sum(f.coverage_minutes) / 1440.0 * 100, 2)                      AS disponibilidad_pct,
       round(sum(f.positive_power_unit_hours), 2)                            AS importada_unit_h,
       round(sum(f.positive_power_unit_hours) FILTER (WHERE NOT h.es_hora_solar), 2)
                                                                             AS importada_noche_unit_h,
       round(100 * sum(f.positive_power_unit_hours) FILTER (WHERE NOT h.es_hora_solar)
             / NULLIF(sum(f.positive_power_unit_hours), 0), 1)               AS pct_importada_noche
FROM gold.fact_energia_red_hora f
JOIN gold.dim_fecha d USING (fecha_key)
JOIN gold.dim_hora  h USING (hora_key)
GROUP BY d.fecha, f.inverter_key, f.variable_key;

-- Horas sin red por día desde el context
CREATE OR REPLACE VIEW gold.vw_horas_sin_red_dia AS
SELECT d.fecha,
       e.inverter_key,
       count(*)                            AS eventos,
       round(sum(e.duracion_horas), 1)     AS horas_sin_red
FROM gold.fact_evento_operativo e
JOIN gold.dim_fecha d USING (fecha_key)
WHERE e.context_type = 'grid_unavailable_or_islanded'
GROUP BY d.fecha, e.inverter_key;