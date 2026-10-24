# Datos para investigación: objetivo 2015–2025

## Fuentes

| Fuente | Uso | Soporte y resolución | Enlace |
|---|---|---|---|
| RMCAB / Secretaría Distrital de Ambiente | PM2.5, PM10, temperatura ambiental y HR | Estación; reporte horario | https://rmcab.ambientebogota.gov.co/Report/HourlyReports |
| Guía RMCAB | Descarga oficial por estación, variable y periodo | Guía de consulta/exportación | https://rmcab.ambientebogota.gov.co/home/text/1516 |
| Catálogo oficial de estaciones | Identidad, coordenadas y posterior cruce geográfico | Fotografía del catálogo, no historial de reubicaciones | https://datosabiertos.bogota.gov.co/dataset/estaciones-calidad-del-aire-bogota-d-c |
| Open-Meteo / ERA5 | Opción para completar covariables meteorológicas | Reanálisis en rejilla, no sensor de barrio | https://open-meteo.com/en/docs/historical-weather-api |

Las capas de promedio anual son útiles para contexto espacial y contraste; no
permiten reconstruir variaciones horarias ni son etiquetas de pronóstico horario.
No mezclar observaciones y reanálisis sin identificar su origen por variable.
La API pública de Open-Meteo limita su uso gratuito a actividades no comerciales;
consultar su atribución y condiciones antes de integrarla en un servicio comercial.

## Carpetas

- `samples/`: muestra pequeña, publicada y trazable para ejecutar el notebook sin red.
- `processed/`: salidas regenerables y lotes mensuales; no se versionan automáticamente.
- `reports/`: informes y gráficos pequeños que documentan la investigación.
- Los HTML originales comprimidos y sus manifiestos se guardan en
  `.local/research/rmcab/`, fuera del control de versiones.

**La muestra piloto no contiene once años completos.** Consultar
`samples/rmcab_pilot_2015_2025.coverage.csv`: distingue días consultados, horas de
estación publicadas y valores presentes para cada variable. Un día por año no
representa su estacionalidad. La semana adicional de 2025 sirve para comprobar
uniones temporales, no para afirmar que el modelo generaliza a otros años.

## Contrato de datos

- `datetime`: fecha con zona `America/Bogota` (UTC−05:00); hora final del intervalo
  publicado. La hora 24 del reporte se guarda como 00:00 del día siguiente.
- `station_id`, `station_name`: identificación del portal RMCAB. Es una observación
  en una estación; no equivale a una ruta ni al promedio de un barrio.
- `pm_25`, `pm_10`: µg/m³; `temperature`: °C; `humidity`: %.
  Mantienen los nombres de variables usados por el dashboard.
- `*_channel`: canal original. Se seleccionan `PM2.5`, `PM10`, `Temperatura` y `HR`.
  Se excluyen `Humedad Inter`, `Tempe Inter`, otras alturas de temperatura y `HR_2m`.
  Esto evita combinar instrumentos distintos sin calibración; pierde datos de esos
  canales y debe revisarse al construir una serie homogénea por estación.
- `*_raw`: valor publicado antes del filtro de rangos; `*_origin`: `observed`,
  `missing` o `range_review`. Un valor cero se conserva como cero.
- `source_url`, `source_sha256`, `report_date`: procedencia; los manifiestos añaden
  la fecha de descarga. Se conservan los valores mostrados por el reporte, con su
  precisión publicada, no la precisión adicional de sus gráficas internas.
- `validation_status=published_quality_not_verified`: publicado en un sitio oficial
  no implica que se haya comprobado la validación final de cada medición. Los
  filtros del proyecto no reemplazan el control de calidad de la RMCAB.
- `pm25_above_pm10_review`: alerta de consistencia; no se elimina automáticamente.

El dataset existente tiene escala y procedencia insuficientemente documentadas;
se audita, pero no se concatena con datos físicos nuevos ni se sustituye sin más.
Sus 25.000 filas no permiten inferir cobertura fuera de febrero/marzo de 2024.

## Recolección reanudable

Desde la raíz del repositorio y con el entorno de investigación activado:

```bash
python -B -m research.collect_rmcab --pilot --network --output data/processed/pilot_rebuilt.csv
python -B -m research.collect_rmcab --start 2024-01-01 --end 2024-01-31 --network --output data/processed/rmcab_2024_01.csv
```

El notebook genera un plan de **132 lotes mensuales para 2015–2025**. El segundo
comando se repite para cada lote disponible. El recolector usa una petición por
fecha, sin paralelismo, y espera dos segundos después de una descarga. Si falla
el portal, los días descargados permanecen en caché para reanudar. Sin `--network`
solo se permite leer la caché; no se crean observaciones para suplir errores HTTP.
Para once años completos conviene priorizar las exportaciones masivas del portal
oficial frente a miles de reportes HTML. Validar primero su formato y sus códigos
de calidad; este adaptador fue comprobado con el reporte horario visible.

No usar los `id` de esta tabla como códigos espaciales del catálogo: son sistemas
de identificación diferentes. Antes de obtener estimaciones por barrio, verificar
las ubicaciones históricas de cada estación y evaluar interpolación con estaciones
retenidas para validación espacial. No replicar un valor de estación como si fuera
una medición independiente en cada barrio.

## Tratamiento y modelado

El notebook compara imputadores de **predictores** mediante un experimento con
bloques de humedad conocidos que se ocultan en validación. Escalador e imputador
se ajustan solo con entrenamiento. El resultado no se aplica a ciegas al dataset:
requiere analizar error, estación, época y duración de huecos. Los objetivos PM
de entrenamiento y evaluación nunca se rellenan con predicciones del propio modelo.

La tabla supervisada une `X(t)` con observaciones reales en `y(t+h)` por estación
y fecha exacta. Los rezagos son horas reales y no posiciones en un CSV con huecos.
Los cortes temporales purgan objetivos que alcanzarían el periodo de validación.
Retener además estaciones completas al evaluar generalización espacial.
Para pronosticar a 24/48/72 horas no usar meteorología observada en el futuro como
si ya estuviera disponible: se necesitan covariables disponibles en el origen o
archivos históricos de pronósticos emitidos antes del instante de predicción.

Referencias metodológicas: [imputación en scikit-learn](https://scikit-learn.org/stable/modules/impute.html),
[prevención de fuga de información](https://scikit-learn.org/stable/common_pitfalls.html),
[rezagos y evaluación temporal](https://scikit-learn.org/stable/auto_examples/applications/plot_time_series_lagged_features.html).


## Consumo desde Dash

La pestaña RMCAB es la vista inicial del dashboard y consume la muestra tratada,
sin depender del entorno Jupyter ni de scikit-learn en el servidor web:

`reportes RMCAB → recolección/caché → notebook y contrato → CSV + manifiesto → Dash`

El adaptador `dash2/rmcab_data.py` valida columnas, estación/hora única, fecha del
reporte, origen observado de los valores y correspondencia con el manifiesto.
Los filtros de año/mes usan `report_date`; el eje temporal utiliza la hora local
real, de modo que la hora 24 del reporte puede verse al inicio del día siguiente.
Los cálculos excluyen ausencias y no sustituyen valores por cero.

El CSV descargado desde la web contiene registros del periodo y estaciones
seleccionados, conserva las cuatro variables y sus metadatos e incluye unidades.
Las gráficas y la tabla comparan una variable por vez; no mezclan porcentajes,
temperatura y concentraciones en el mismo eje.

Para actualizar el piloto, regenerar el CSV y su manifiesto juntos con el
recolector, revisar los resultados y ejecutar las pruebas de `dash2.test_rmcab`.
Después reiniciar Django para cargar el nuevo lote; el navegador no ejecuta la
recolección. Si se usa otro archivo tratado, configurar `DATA_PATH` en
`dash2/rmcab_data.py` y mantener su `.sources.json` con el mismo nombre base.
Una historia completa de gran tamaño requiere particionar o consultar por periodo
en la base de datos; el adaptador actual está destinado a la muestra local.

Los datos de estación no alimentan los polígonos del mapa anterior. Ese paso
requiere georreferenciación histórica e interpolación validadas, documentadas en
el notebook. Tampoco se presentan las observaciones como pronósticos.

## Experimento HGB del piloto

El notebook `02_histgradientboosting_pronostico.ipynb` registra un primer
entrenamiento histórico con parámetros fijos en `research/forecast_experiment.py`.
Sus informes son `data/reports/hgb_pilot/scores.csv`, `scores_by_station.csv`,
`temporal_folds.csv`, `historical_24h_evaluation.png` y `experiment.json`.
La tabla detallada de predicciones es regenerable y se guarda en
`data/processed/hgb_pilot_predictions.csv`, fuera del seguimiento de Git.
Conserva la URL y el hash del reporte de cada etiqueta real. Todos los métodos
se evalúan sobre exactamente las mismas filas de cada ventana.

La cohorte usa únicamente los siete reportes consecutivos de febrero de 2025.
El modelo recibe lecturas actuales, rezagos exactos a 1/24 h y calendario; el mes
no varía en esta muestra. Las mediciones actuales y futuras del objetivo deben
estar observadas. Se excluyen estaciones no vistas en el entrenamiento del corte.
Las fechas aisladas de los otros años no se convierten en una secuencia continua.
No se usa `train_test_split` aleatorio ni parada temprana con validación aleatoria.

En el comparador con mediana, el imputador vive dentro del pipeline y se ajusta
solo en entrenamiento. Esta transformación no se aplica al CSV publicado.
HGB también se prueba con sus entradas NaN nativas. No se fabrican objetivos,
no se agregan registros sintéticos y no se rellena el periodo 2015–2025.

`experiment.json` identifica el CSV y manifiesto con SHA256, versiones,
configuración, ventanas omitidas y estado `deployment_ready=false`.
El archivo previo `run_manifest.json` describe la ejecución de recolección y
preparación del notebook 01; el estado de este entrenamiento se registra por
separado en `hgb_pilot/experiment.json`.

El mínimo operativo de 48 horas de origen y 200 filas no acredita suficiencia
estadística. A 48 h solo queda una ventana válida; a 72 h no queda ninguna.
La validación es retrospectiva por estación conocida y presupone que el dato
publicado estaba disponible al emitir cada pronóstico. No se ha verificado
latencia, revisión histórica del portal ni calidad final de las observaciones.
Antes de elegir y desplegar un modelo, ampliar meses/temporadas, volver a evaluar
y reservar un periodo final independiente de selección y ajuste.

## Lote continuo enero–marzo de 2025

`data/samples/rmcab_2025_q1.csv` contiene los 90 reportes diarios del trimestre,
con el mismo contrato por variable. Su `.sources.json` conserva las 90 URLs, horas
de descarga UTC y hashes originales; su `.coverage.csv` resume valores presentes.
Hay 41,040 filas de estación/hora y 19 estaciones listadas.
Los días válidos sin ninguna medición PM son:
2025-01-27, 2025-01-28.
Estas ausencias no se convierten en ceros, no se rellenan y no invalidan por sí
solas un reporte cuyo formato y fecha se verificaron correctamente.

El módulo `research.collect_rmcab_period` recolecta de 1 a 92 días por ejecución,
sin paralelismo, con caché y reintento acotado. Si una fecha/formato/unidad falla,
conserva las descargas correctas e impide publicar el periodo como completo.
Por defecto no usa red; `--network` autoriza solo las descargas que falten.

El notebook 03 registra 24 ventanas de desarrollo (tres por variable/horizonte)
y 8 ventanas finales (una por variable/horizonte). La mediana se compara únicamente
en desarrollo; el test final compara HGB con NaN nativos y persistencia. Los métodos
se fijan antes de puntuar, sin búsqueda de hiperparámetros. La tabla de modelado
requiere observaciones en el origen y objetivo del contaminante; los predictores
restantes pueden conservar NaN. Todas las etiquetas de entrenamiento preceden al
primer origen de validación. Se excluyen estaciones no vistas en ese entrenamiento.

Los informes de `data/reports/hgb_2025_q1/` separan `development_*` y `holdout_*`.
Incluyen métricas por estación y por ventana, cobertura por día/mes/estación,
gráfica y `experiment.json` con hashes, periodos, versiones y parámetros.
Los CSV `data/processed/hgb_2025_q1_*_predictions.csv` conservan la URL/hash de cada
observación objetivo y se regeneran al ejecutar todas las celdas.

La evaluación final contiene objetivos de los reportes del 25–31 de marzo de 2025;
las horas de origen y el corte de entrenamiento dependen del horizonte. No son
curvas completas emitidas desde una sola hora. Se presupone que las observaciones
publicadas estaban disponibles en cada origen; no hay archivo de latencias o
revisiones. La calidad final de los datos RMCAB no se certifica aquí. El trimestre
no cubre la variación anual, no valida estimación por barrios y no habilita un
pronóstico para hoy sin nuevas entradas. No hay artefacto desplegado.

El dataset original de barrios y el piloto 2015–2025 permanecen intactos. Dash
continúa usando su dataset piloto; este nuevo lote alimenta la investigación y
requiere una integración posterior si se decide incorporarlo a la aplicación.
