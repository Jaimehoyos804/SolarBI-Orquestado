# Perfilado de la fuente de datos y limitaciones

**Proyecto:** SolarBI Orquestado  
**Fuente:** OpenCEM v1.0.0 (https://zenodo.org/records/21436223) 
**Base de datos original:** SQLite  
**Archivo:** `data/bronze/opencem-v1.0.0.sqlite`  
**Capa:** Bronze
**Estado:** Perfilado inicial 
**Fecha de documentación:** 16 de noviembre de 2026

## 1. Objetivo

Este documento presenta los resultados del análisis exploratorio y perfilado de la fuente de datos OpenCEM v1.0.0, utilizada como origen histórico para la solución de Business Intelligence SolarBI Orquestado.

El propósito es identificar la estructura de los datos, evaluar su calidad, reconocer posibles inconsistencias y establecer las limitaciones que deben considerarse durante el proceso ETL.

El perfilado busca evitar transformaciones que alteren el significado de los datos originales y establecer reglas justificadas para su posterior integración en PostgreSQL.

## 2. Fuente de datos

Se utiliza el conjunto de datos OpenCEM v1.0.0, distribuido en formato SQLite.

Archivo original:

`data/bronze/opencem-v1.0.0.sqlite`

El archivo se conserva en la capa Bronze como fuente histórica original, sin alteraciones.

### 2.1 Integridad del archivo

Se verificó el archivo comprimido original mediante SHA-256.

**Hash SHA-256:**

`8e38f98209029367a3775799ee9a7c0757cc7e8f2742e4df4eccc45dd4b27517`

El hash corresponde al archivo comprimido original descargado, no al archivo SQLite descomprimido.

**Tamaño del SQLite descomprimido:** 4.439.408.640 bytes (aproximadamente 4,14 GiB).

## 3. Inventario de tablas

Durante la inspección del esquema se identificaron las siguientes tablas:

| Tabla | Descripción funcional preliminar |---|---|
| `analog_measurements` | Mediciones eléctricas, batería, paneles fotovoltaicos, red y carga |
| `context` | Eventos y registros contextuales en formato JSON |
| `fault_history` | Historial de fallos y registros asociados |
| `settings` | Configuración de los inversores |
| `specs` | Información de identificación y versiones del equipo |
| `statistics` | Estadísticas de generación, consumo y energía acumulada |
| `status` | Estado operativo, alarmas y modos de funcionamiento |
| `totals` | Valores agregados de potencia y otros indicadores |

También se encontraron `sqlite_stat1` y `sqlite_stat4`, utilizadas por SQLite para estadísticas del optimizador. No se consideran tablas de negocio para el modelo analítico.

## 4. Cobertura temporal y volumen de datos

### 4.1 Mediciones analógicas

| Indicador | Resultado |
|---|---:|
| Total de registros | 2.989.759 |
| Inversores identificados | 2 |
| Primera fecha | 2025-07-12 13:31:35 |
| Última fecha | 2026-07-13 05:13:53 |

### 4.2 Estadísticas

| Inversor | Registros | Primera fecha | Última fecha |
|---|---:|---|---|
| 1 | 1.279.772 | 2025-07-12 13:31:35 | 2026-07-13 05:13:53 |
| 2 | 1.006.132 | 2025-07-14 05:53:32 | 2026-06-22 05:35:24 |

La fuente contiene aproximadamente un año de información sin embargo, la cobertura no es continua y presenta interrupciones temporales.

**Limitación:** no se debe interpretar el rango entre la primera y última fecha como un año completo de mediciones ininterrumpidas.

## 5. Perfilado de calidad de datos

### 5.1 Frecuencia de muestreo variable

Se analizaron los intervalos entre registros consecutivos de `analog_measurements`, utilizando la función `LAG()` para comparar cada marca de tiempo con la anterior dentro de cada inversor.

| Indicador | Inversor 1 | Inversor 2 |
|---|---:|---:|
| Intervalos analizados | 1.610.275 | 1.379.482 |
| Intervalo promedio | 19,62 segundos | 21,48 segundos |
| Intervalos mayores a 10 minutos | 117 | 40 |

El promedio está afectado por interrupciones prolongadas y no representa necesariamente la frecuencia habitual de adquisición.

La mayoría de los intervalos se concentra entre 1 y 60 segundos.

**Limitación:** no se puede asumir una frecuencia de muestreo constante.

**Decisión ETL:**
- Conservar la marca temporal original.
- Calcular intervalos entre mediciones cuando sea necesario.
- Identificar brechas de telemetría.
- Evitar interpolaciones automáticas sin una regla de negocio justificada.

### 5.2 Interrupciones de telemetría

Se identificaron varias interrupciones importantes. La más extensa afecta simultáneamente a los dos inversores.

| Inicio aproximado | Fin aproximado | Duración |
|---|---|---:|
| 2025-08-03 | 2025-08-29 | 627,52 horas |
| 2025-09-22 | 2025-09-25 | 72,61 horas |
| 2025-11-08 | 2025-11-21 | 296,54 horas (inversor 2) |
| 2025-11-15 | 2025-11-21 | 131,66 horas (inversor 1) |
| 2026-05-05 | 2026-05-06 | 7,53 horas |

La tabla `context` contiene eventos `data_gap` que permiten identificar algunas de estas interrupciones.

Se verificó que el evento asociado a la brecha de agosto registra:

- Tipo: `data_gap`.
- Fuente: `derived_context_pipeline`.
- Tabla de origen declarada: `measurement.analog_measurement_fixed`.
- Umbral utilizado: 600 segundos.
- Duración registrada: aproximadamente 2.259.069 segundos.

**Interpretación:** la ausencia de mediciones no demuestra que el inversor estuviera apagado. Puede representar una interrupción de adquisición, comunicación o registro.

**Decisión ETL:**
- Mantener los registros de eventos de brecha.
- Generar indicadores de cobertura temporal.
- No convertir automáticamente las brechas en periodos de equipo apagado.
- No calcular indicadores operativos sobre periodos sin cobertura como si fueran mediciones reales.

### 5.3 Marcas temporales y zona horaria

Las marcas de tiempo de las tablas principales se almacenan como valores Unix.

Al convertirlas mediante:

`datetime(read_ts, 'unixepoch')`

se obtiene una representación UTC sin información explícita de zona horaria.

Se compararon estos resultados con las marcas `previous_sample_local` y `next_sample_local` presentes en algunos eventos de `context`. Estas presentan una diferencia de ocho horas respecto a la representación obtenida desde Unix.

**Decisión ETL:**
- Conservar el timestamp original.
- Registrar explícitamente la interpretación temporal aplicada.
- No asumir que la representación local corresponde a Colombia.
- Evitar conversiones definitivas hasta confirmar la semántica de la zona horaria.

### 5.4 Valores NULL y cero

Se identificaron diferencias importantes entre valores ausentes y valores numéricos iguales a cero.

Ejemplos en `analog_measurements`:

| Campo | NULL | Cero |
|---|---:|---:|
| `battsoc` | 57.931 | 0 |
| `pv1power` | 58.660 | 1.948.399 |
| `outsumw` | 349.992 | 58.153 |
| `gridpowerw_a` | 342.815 | 58.968 |

Un valor NULL representa ausencia de dato registrado, mientras que cero puede representar una medición válida.

**Decisión ETL:**
- No reemplazar NULL por cero de manera general.
- Mantener los ceros válidos.
- Calcular indicadores de completitud por variable.
- Documentar las reglas específicas de imputación, si alguna resulta necesaria.

### 5.5 Registros duplicados

Se verificaron las marcas temporales por inversor en `analog_measurements`.

| Inversor | Registros | Timestamps distintos | Duplicados |
|---|---:|---:|---:|
| 1 | 1.610.276 | 1.610.276 | 0 |
| 2 | 1.379.483 | 1.379.483 | 0 |

No se identificaron timestamps duplicados dentro de cada inversor en esta tabla.

**Limitación:** este resultado no demuestra que no existan duplicados en las demás tablas ni que no haya duplicados semánticos entre diferentes variables.

**Decisión ETL:** utilizar una clave compuesta apropiada, considerando el inversor y la marca temporal, cuando corresponda.

## 6. Perfilado de mediciones y variables físicas

### 6.1 Variables eléctricas

La tabla `analog_measurements` contiene información de:

- Estado de carga de batería.
- Voltaje y corriente de batería.
- Potencia de carga de batería.
- Voltaje, corriente y potencia fotovoltaica.
- Voltaje, corriente, frecuencia y potencia de salida AC.
- Potencia y corriente de red.
- Variables de carga.
- Temperaturas y ventilación.

Se debe conservar la distinción entre potencia instantánea y energía acumulada.

**Limitación:** una medición de potencia en W no equivale directamente a energía en kWh. Para obtener energía a partir de potencia se requiere integrar respecto al tiempo y considerar los intervalos de muestreo y las brechas.

### 6.2 Estado de carga de batería

La variable `battsoc` representa el estado de carga de la batería y no debe sumarse como si fuera energía.

**Decisión ETL:**
- Mantener SOC como porcentaje.
- Utilizar promedio, último valor o evolución temporal según el indicador.
- No sumar porcentajes de SOC para calcular energía.

### 6.3 Ambigüedad en variables de batería

Se analizaron `battcurr` y `battchgpower` para algunos eventos de carga y descarga.

Se encontraron registros en los que la corriente de batería tiene signo negativo mientras `battchgpower` presenta valores positivos elevados.

También existen registros con corriente positiva y potencia de carga igual a cero.

Esto muestra que no es seguro interpretar el sentido físico de ambas variables únicamente por sus nombres.

**Limitación:** no se ha confirmado la semántica del signo de corriente ni el significado exacto de `battchgpower`.

**Decisión ETL:**
- Conservar los valores originales.
- No inferir automáticamente carga o descarga usando únicamente el nombre de la columna.
- No calcular energía cargada o descargada a partir de estas variables hasta confirmar su significado mediante documentación técnica.

### 6.4 Temperaturas y posibles valores centinela

En `context` se encontraron notas de calidad que identifican numerosos registros con valores de temperatura iguales a 120.

Resultados documentados:

| Inversor | Registros identificados como posibles centinelas | Total de referencia | Proporción |
|---|---:|---:|---:|
| 1 | 1.403.695 | 1.424.647 | 98,53 % |
| 2 | 1.086.760 | 1.087.945 | 99,89 % |

Estos valores aparecen señalados en el grupo de variables de temperatura.

**Limitación:** no se ha confirmado mediante documentación del fabricante si 120 corresponde a un valor centinela, error de sensor o temperatura real.

**Decisión ETL:**
- No tratar automáticamente 120 como temperatura válida.
- Marcar estos registros como sospechosos.
- Conservar el valor original.
- Aplicar exclusiones de análisis únicamente mediante reglas documentadas.

## 7. Perfilado de la tabla `context`

La tabla contiene registros contextuales con campos como:

- `id`
- `recorded`
- `start`
- `end`
- `value`

El campo `value` contiene información estructurada en JSON.

Se identificaron diferentes tipos de eventos:

| Tipo de evento | Cantidad |
|---|---:|
| `battery_charging` | 1.058 |
| `battery_discharging` | 659 |
| `pv_generation_active` | 443 |
| `high_ac_load` | 8 |
| `grid_unavailable_or_islanded` | 56 |
| `data_gap` | 141 |
| `data_coverage_summary` | 12 |
| `telemetry_quality_note` | 2 |

Los eventos contextuales no deben considerarse automáticamente mediciones físicas independientes.

Algunos son generados por procesos derivados, como `derived_context_pipeline`.

### 7.1 Identificación del inversor

La tabla `context` no contiene una columna independiente llamada `inverter`.

En los eventos analizados, el identificador del inversor aparece dentro del JSON de `value`, mediante la propiedad `inverter`.

**Decisión ETL:** extraer el identificador desde el JSON cuando exista y validar su disponibilidad antes de relacionar el evento con un inversor.

### 7.2 Cobertura y conteos de contexto

Se encontraron registros `data_coverage_summary` que hacen referencia a tablas procesadas con nombres como `measurement.analog_measurement_fixed`.

Sus conteos no coinciden directamente con los conteos de `analog_measurements` en SQLite.

**Limitación:** los nombres de las tablas y los procesos de generación de estos resúmenes indican que pueden corresponder a datos filtrados o transformados.

**Decisión ETL:** no utilizar los resúmenes contextuales como conteos oficiales de la tabla original sin reconciliar sus reglas de generación.

## 8. Perfilado de `settings`

La tabla `settings` contiene parámetros de configuración de los inversores, entre ellos:

- Tipo de batería.
- Corrientes máximas de carga.
- Corriente de carga desde PV.
- Corriente de carga desde red.
- Capacidad nominal del paquete de baterías.
- Configuración BMS.
- Programación de carga y descarga.
- Umbrales de voltaje.

Se encontraron diferencias en la disponibilidad de los parámetros entre inversores.

Ejemplo:

| Parámetro | Inversor 1 | Inversor 2 |
|---|---:|---:|
| Registros totales | 1.280.052 | 1.004.723 |
| `battype` no nulo | 47.630 | 46.253 |
| `maxchgcurrset` no nulo | 1.278.709 | 947.776 |
| `battpackrateah` no nulo | 1.278.408 | 947.754 |

La variable `battype` presenta una cobertura reducida en ambos inversores.

Además, los valores de configuración pueden cambiar a lo largo del tiempo.

**Decisión ETL:**
- Conservar `read_ts`.
- No tratar la configuración como un conjunto de atributos estáticos sin verificar su evolución.
- No reemplazar configuraciones ausentes por valores predeterminados inventados.
- Permitir análisis históricos de cambios de configuración cuando sea necesario.

## 9. Perfilado de `specs`

La tabla `specs` contiene información de identificación y versiones:

- Fabricante.
- Tipo de producto.
- Número de serie.
- Versiones de hardware.
- Versión de protocolo.
- Versión BMS.
- Versión de librería.

Se observó que los campos de identificación presentan muchos valores NULL y que algunos campos contienen representaciones similares a arreglos de bytes.

Ejemplos encontrados:

- `[65,0]`
- `[68,0]`
- `[0,0,0,0,...]`

También se observó que la información de identificación y versiones deja de aparecer con la misma cobertura después de febrero de 2026, aunque las mediciones analógicas continúan hasta julio de 2026.

**Limitaciones:**
- No se ha confirmado la codificación de los valores.
- No se ha confirmado que los cambios observados correspondan a actualizaciones de firmware.
- No existe cobertura suficiente para construir una dimensión de fabricante o modelo completamente confiable.

**Decisión ETL:**
- Conservar los campos originales.
- No decodificar valores sin documentación.
- Mantener la marca temporal de cada registro.
- No inferir modelos o actualizaciones de firmware a partir de códigos sin validar.

## 10. Perfilado de `statistics`

La tabla `statistics` contiene estadísticas diarias e históricas de energía, generación, consumo y tiempo de funcionamiento.

Se identificaron diferencias importantes en los tipos de datos.

### 10.1 Tipos de almacenamiento

Los campos diarios principales están almacenados como `REAL`, mientras que varios acumulados históricos están almacenados como `TEXT`.

Ejemplos:

| Campo | Tipo SQLite |
|---|---|
| `generatedacpowertoday` | REAL |
| `batchgenergytoday` | REAL |
| `batdischgenergytoday` | REAL |
| `pvgeneratenergytoday` | REAL |
| `usedenergytoday` | REAL |
| `batchgenergytotal` | TEXT |
| `batdischgenergytotal` | TEXT |
| `pvgeneratenergytotal` | TEXT |
| `usedenergytotal` | TEXT |
| `linechgenergytotal` | TEXT |
| `loadconsumlinetotal` | TEXT |

### 10.2 Diferencia de cobertura entre inversores

Los campos diarios presentan una diferencia importante de completitud.

| Indicador | Inversor 1 | Inversor 2 |
|---|---:|---:|
| Registros | 1.279.772 | 1.006.132 |
| Nulos aproximados por campo diario | 0,11 % | 5,65 % |

El inversor 2 presenta aproximadamente 56.800 registros nulos en cada una de las principales métricas diarias.

La investigación por fecha encontró que:

- El 12 de mayo de 2026 presenta una transición durante el mismo día.
- Al inicio del día existen registros con métricas diarias.
- Al final del día esas métricas ya aparecen vacías.
- Desde el 13 de mayo de 2026 hasta el 22 de junio de 2026, las métricas diarias aparecen completamente nulas en los registros analizados.

**Limitación:** la existencia de registros sin métricas diarias no demuestra ausencia de producción o consumo.

**Decisión ETL:**
- Conservar los registros.
- Mantener NULL en las métricas ausentes.
- Generar indicadores de disponibilidad por inversor y fecha.
- No reconstruir métricas diarias utilizando acumulados sin conocer las reglas de cálculo y reinicio.

### 10.3 Estructura JSON de acumulados históricos

Se identificó que varios acumulados almacenados como `TEXT` contienen arreglos JSON.

Ejemplo:

`[927.8,0.0]`

Se verificó que `batchgenergytotal` es JSON válido de tipo `array`, con valores accesibles mediante:

- `$[0]`
- `$[1]`

También se identificaron valores como:

`[null]`

Por esta razón, un simple `COUNT(columna)` en SQLite no permite detectar nulos internos del arreglo.

En una revisión de los siete acumulados para el inversor 2 entre el 12 y el 15 de mayo de 2026 se obtuvieron los siguientes resultados:

| Campo | Arreglos con valores | Arreglos con al menos un NULL |
|---|---:|---:|
| `batchgenergytotal` | 2.952 | 5.123 |
| `batdischgenergytotal` | 2.953 | 5.122 |
| `generatedacpowertotal` | 2.929 | 5.146 |
| `linechgenergytotal` | 2.953 | 5.122 |
| `loadconsumlinetotal` | 2.953 | 5.122 |
| `pvgeneratenergytotal` | 2.953 | 5.122 |
| `usedenergytotal` | 2.953 | 5.122 |

Para `batchgenergytotal` se realizó una validación adicional:

| Estado | Registros |
|---|---:|
| Ambas posiciones con valores | 2.952 |
| Posición 0 nula | 5.123 |
| Posición 1 nula como único NULL | 0 |
| Ambas posiciones nulas | 0 |

**Limitación:** aunque se conoce la estructura JSON, todavía no se ha confirmado qué representa cada posición del arreglo.

**Decisión ETL:**
- Validar JSON antes de extraer sus posiciones.
- Conservar el texto original.
- Extraer los componentes en columnas separadas cuando corresponda.
- Diferenciar NULL SQL, NULL interno y valores numéricos.
- No asignar significado físico a las posiciones sin documentación técnica.
- No convertir directamente el arreglo completo a REAL.

## 11. Matriz consolidada de limitaciones

| Área | Hallazgo | Riesgo analítico | Tratamiento propuesto |
|---|---|---|---|
| Integridad temporal | Interrupciones prolongadas | Indicadores incompletos | Identificar brechas |
| Muestreo | Intervalos variables | Promedios temporales sesgados | Considerar duración real |
| Valores ausentes | NULL y cero coexisten | Falsos consumos o generación | Preservar semántica |
| Batería | Significado de signos no confirmado | Clasificación incorrecta de carga/descarga | Validar documentación |
| Temperatura | Valores 120 sospechosos | Indicadores térmicos incorrectos | Marcar posibles sentinelas |
| Contexto | Eventos derivados | Confundir inferencia con medición | Identificar procedencia |
| Zona horaria | Diferencia de ocho horas observada | Desfase temporal | Confirmar zona |
| Configuración | Parámetros incompletos y variables | Configuración histórica incorrecta | Preservar historial |
| Identificación | Códigos no decodificados | Dimensiones incorrectas | No inferir fabricante/modelo |
| Estadísticas diarias | Pérdida de cobertura del inversor 2 | Comparaciones incompletas | Indicador de calidad |
| Acumulados | Arreglos JSON en TEXT | Conversiones incorrectas | Validación y extracción controlada |

## 12. Arquitectura de tratamiento de datos

Se propone mantener una arquitectura por capas:

### Bronze – Datos originales

Responsabilidad:
- Conservar el SQLite original.
- Mantener integridad y trazabilidad.
- No sobrescribir ni modificar la fuente.
- Registrar información de origen y versión.

### Silver – Datos limpios y tipados

Responsabilidad:
- Transformar timestamps de manera controlada.
- Normalizar tipos de datos.
- Validar estructuras JSON.
- Identificar valores ausentes y sospechosos.
- Conservar indicadores de calidad.
- Identificar brechas de telemetría.
- Mantener trazabilidad hacia los registros originales.

### Gold – Modelo analítico

Responsabilidad:
- Organizar dimensiones y hechos.
- Preparar métricas de generación, consumo y operación.
- Incorporar indicadores de calidad y cobertura.
- Evitar métricas calculadas sobre datos incompletos sin advertencia.

## 13. Reglas generales para el ETL

Las siguientes reglas se consideran obligatorias para la implementación:

1. La fuente Bronze debe permanecer inmutable.
2. Las transformaciones deben ser reproducibles.
3. Los valores NULL no deben convertirse automáticamente en cero.
4. Los valores cero deben conservarse cuando sean mediciones válidas.
5. Los registros de brechas no deben interpretarse como apagados del equipo.
6. Los acumulados JSON deben validarse antes de extraerse.
7. No se deben inventar valores faltantes.
8. Las conversiones de zona horaria deben estar justificadas.
9. Las métricas de batería deben respetar la semántica física confirmada.
10. Las validaciones deben registrar cantidades de registros procesados, rechazados y observados.
11. Los indicadores deben permitir distinguir ausencia de datos de valores físicos iguales a cero.
12. La calidad de los datos debe poder consultarse desde las capas analíticas.

## 14. Conclusión

El perfilado de OpenCEM v1.0.0 permitió identificar una fuente con un volumen significativo de información histórica, dos inversores y diferentes tipos de registros eléctricos, operativos y contextuales.

Sin embargo, la fuente presenta limitaciones importantes relacionadas con interrupciones temporales, frecuencia de muestreo variable, valores ausentes, estructuras JSON, diferencias de cobertura entre inversores y campos cuya semántica física todavía requiere confirmación.

Por lo tanto, el proceso ETL no debe limitarse a copiar datos desde SQLite hacia PostgreSQL. Debe incorporar validaciones, tipificación, trazabilidad y controles de calidad que permitan conservar el significado de los datos.

La arquitectura Bronze → Silver → Gold permitirá mantener los registros originales, producir información estructurada y construir indicadores analíticos confiables, haciendo explícitas las limitaciones de la fuente.

**Principio de diseño:** no transformar un dato cuyo significado no ha sido confirmado como si fuera una medición conocida.