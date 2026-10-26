# Datos y procedencia · 2015–2025

## Histórico integrado 2015–2025

El notebook vigente es [`05_integracion_historica_2015_2025.ipynb`](../notebooks/05_integracion_historica_2015_2025.ipynb).
La colección consolidada contiene **1.323.391 filas de estación/hora y 4.013 fechas**,
entre el 1 de enero de 2015 y el 31 de diciembre de 2025. Cinco fechas de 2020
no tienen mediciones utilizables; los sensores también conservan ausencias horarias.
Los registros de PM proceden de 22 exportaciones públicas SISAIRE/SDA, con sus
CSV originales comprimidos y metadatos en `data/history/source_exports/`.
Las lecturas válidas de las muestras RMCAB previas se conservan en los solapamientos.

Open-Meteo/ERA5 aporta 385.728 registros horarios de cuatro celdas de 0,25°
para los 4.018 días calendario. Es reanálisis meteorológico, sin ajuste de elevación,
no medición de barrio. Se conserva separado en `data/weather/` y se identifica al
completar temperatura y humedad; lluvia y viento sirven como predictores adicionales.

El mapa conserva 1.160 sectores y las opciones **Datos originales** / **Datos con tratamiento**.
Predicciones ofrece las mismas opciones para el contexto meteorológico. El relleno
no modifica los objetivos de PM ni las lecturas válidas y ERA5 no recibe ruido sintético.

HGB usa desarrollo con entrenamiento 2015–2023 y cuatro semanas de 2024;
el ajuste final usa 2015–2024 y se prueba en las semanas 15–21 de enero,
abril, julio y octubre de 2025, a 24/48/72 h, sobre estaciones conocidas.
Los parámetros se fijan antes de puntuar. Las etiquetas y los rezagos de PM
siempre están observados. El mapa/KNN no participa en el entrenamiento.
ERA5 en el origen es contexto retrospectivo: sus demoras y revisiones no acreditan
un pronóstico operativo en tiempo real. Se compara con persistencia y se publican
MAE/RMSE, sin intervalos de incertidumbre calibrados.

Para reproducir, usar el entorno de `requirements-research.txt` desde la raíz:

```bash
python -B -m research.collect_sisaire --network
python -B -m research.weather_history --network
python -B -m research.build_observed_history
python -B -m research.train_history
python -B -m research.publish_predictions
python -B -m research.neighborhood_history
```

El recolector es secuencial y reanudable. Sin `--network` no descarga.
La consolidación también puede leer los originales versionados de
`data/history/source_exports/` si no existe caché local. Se verifican SHA256,
unidades, fechas y origen por variable. Los intervalos desalineados y duplicados
contradictorios se excluyen, sin inventar valores; los duplicados idénticos se
conservan una sola vez. Estaciones sin correspondencia segura se excluyen del
paquete espacial, pero sus filas permanecen en las exportaciones originales.
Las posiciones son referencias fijas: no se han validado reubicaciones históricas.
La condición de publicado no certifica aquí la validación final de cada sensor.
Reiniciar Django después de reconstruir los paquetes.

Fuentes: [SISAIRE](https://sisaire.ideam.gov.co/ideam-sisaire-web/consultas.xhtml),
[RMCAB/SDA](https://www.ambientebogota.gov.co/es/red-de-monitoreo-de-calidad-del-aire-de-bogota-rmcab),
[Open-Meteo/ERA5](https://open-meteo.com/en/docs/historical-weather-api).

Los notebooks 01–04 y sus secciones de investigación describen las muestras y
experimentos anteriores. El notebook 05 y los manifiestos de `data/history/`,
`data/weather/`, `data/maps/` y `data/forecasts/` describen esta integración.


## Fuentes

| Fuente | Uso | Soporte y resolución | Enlace |
|---|---|---|---|
| RMCAB / Secretaría Distrital de Ambiente | PM2.5, PM10, temperatura ambiental y HR | Estación; reporte horario | https://rmcab.ambientebogota.gov.co/Report/HourlyReports |
| Guía RMCAB | Descarga oficial por estación, variable y periodo | Guía de consulta/exportación | https://rmcab.ambientebogota.gov.co/home/text/1516 |
| Catálogo oficial de estaciones | Identidad, coordenadas y posterior cruce geográfico | Fotografía del catálogo, no historial de reubicaciones | https://datosabiertos.bogota.gov.co/dataset/estaciones-calidad-del-aire-bogota-d-c |
| Open-Meteo / ERA5 | Contexto meteorológico retrospectivo de la integración vigente | Reanálisis en rejilla, no sensor de barrio | https://open-meteo.com/en/docs/historical-weather-api |

Las capas de promedio anual son útiles para contexto espacial y contraste; no
permiten reconstruir variaciones horarias ni son etiquetas de pronóstico horario.
No mezclar observaciones y reanálisis sin identificar su origen por variable.
La API pública de Open-Meteo limita su uso gratuito a actividades no comerciales;
consultar su atribución y condiciones antes de integrarla en un servicio comercial.

## Carpetas

- `history/`: histórico observado consolidado, cobertura y exportaciones originales.
- `weather/`: reanálisis ERA5 y correspondencia entre estaciones y celdas.
- `maps/`: calendario diario y fuentes del tratamiento del mapa.
- `forecasts/`: paquete de backtests históricos publicado para la web.
- `samples/`: muestras piloto y trimestral anteriores, preservadas y trazables.
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


## Consumo desde Dash y Predicciones

El dashboard abre **Mapa por sectores**. La pestaña **Históricos RMCAB · estaciones**
consulta el histórico consolidado mediante `dash2/history_data.py`; no ejecuta
Jupyter ni entrena modelos al abrir la web.

`exportaciones SISAIRE/SDA + muestras RMCAB → contrato y consolidación → CSV.gz + manifiesto → Dash / API`

El adaptador verifica el hash de `data/history/observations.csv.gz`, las claves de
estación/hora y la procedencia por variable. Si el manifiesto integrado no existe,
conserva una vía de compatibilidad que une las dos muestras anteriores; ese caso
no tiene la cobertura del paquete vigente.

Los filtros de año/mes usan `report_date`; el eje temporal usa la hora local real.
El CSV conserva las cuatro variables, ausencias, unidades y procedencia. Una
medición ausente no se convierte en cero y cada variable conserva su propio eje.

En Predicciones, Datos originales conserva observaciones y ausencias. Datos con
tratamiento completa solo temperatura y humedad ausentes con ERA5, con marca
`weather_reanalysis`. No completa objetivos de PM ni modifica lecturas válidas.
Las estimaciones del mapa son otro producto y no se usan como objetivos HGB.

Para actualizar, reconstruir CSV y manifiestos juntos con el notebook 05, revisar
las comprobaciones y reiniciar Django para renovar los datos cargados en memoria.
Las secciones del piloto y el trimestre que siguen documentan las etapas anteriores.

## Experimento HGB del piloto · etapa anterior

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

## Lote continuo enero–marzo de 2025 · etapa anterior

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
continúa usando su dataset piloto. El panel React de predicciones consulta la unión
del piloto y el trimestre para análisis y el paquete evaluado para pronósticos históricos.


## Primer paquete de resultados · etapa anterior

> Esta sección conserva la publicación del notebook 03. El paquete vigente es el del notebook 05, con entrenamiento 2015–2024 y cuatro semanas de prueba en 2025. `research.publish_predictions` selecciona el informe multianual cuando está presente.

`data/forecasts/hgb_historical.csv.gz` conserva las estimaciones HGB y la referencia
de persistencia de la semana final del notebook 03 a 24/48/72 h. No se generan
nuevos valores de observación. `hgb_historical.json` contiene hash del paquete,
hashes de entrada, versión del experimento, parámetros y errores por estación/horizonte.
Ambos archivos deben actualizarse juntos con `python -B -m research.publish_predictions`.

El servidor valida integridad, separación temporal y coincidencia de cada objetivo
con las mediciones publicadas antes de exponer los resultados. No usa pickle,
joblib ni scikit-learn al atender una consulta, ni entrena al hacer clic.
Las fechas ofrecidas corresponden a resultados ya calculados. La observación
posterior se etiqueta explícitamente y no es una entrada del pronóstico.

La cobertura histórica de la ventana une ambos CSV de muestras, comprueba los
duplicados y conserva una observación por estación/hora. Los análisis muestran
datos ausentes como tales; no interpolan años ni estiman valores por barrio.
Los CSV de observaciones solo contienen horas anteriores o iguales al origen.
El CSV de pronóstico diferencia estimación, persistencia y observación posterior,
e identifica corte de entrenamiento, versión y fuente.


## Mapa por sectores · datos originales y datos con tratamiento

> El mecanismo del notebook 04 se conserva. El notebook 05 amplió las fuentes a 4.013 fechas e incorporó ERA5 para clima; la muestra de 100 fechas descrita en los experimentos anteriores no es la cobertura actual del mapa.

El selector tiene dos opciones y abre por defecto en **Datos con tratamiento**:

- **Datos originales**: utiliza únicamente las fechas con mediciones consolidadas SDA/RMCAB y SISAIRE,
  sin rellenar huecos temporales. Si solo hay un mes disponible, la gráfica
  mensual muestra un punto por sector.
- **Datos con tratamiento**: conserva esas mediciones y completa el calendario
  2015–2025. Primero interpola linealmente huecos internos de hasta tres días;
  el resto usa una base KNN de cinco vecinos, ubicación, año y ciclo anual,
  sin atributos de día de la semana. Los rellenos largos incluyen variación
  sintética suave, reproducible y distinta por sector (amplitud fija 10 % del
  rango P95–P5 observado). Temperatura y humedad pueden completarse con ERA5, con procedencia diferenciada
y sin aplicar ruido sintético al reanálisis. No hay que activar otro modo para ver las curvas completas.

El tratamiento conserva la prioridad de las mediciones. Sus valores añadidos son
estimaciones exploratorias; no son nuevas observaciones ni promedios anuales
oficiales. Las fuentes vigentes abarcan 4.013 fechas de 2015–2025; cinco fechas de 2020
carecen de mediciones utilizables y persisten huecos por sensor. Completar el calendario
no demuestra cómo fue la variación real durante los periodos ausentes.

La variación interna usa PCG64 con semilla 20251024 y SHA256 por sector/variable.
Combina un componente común (peso 0,5) y uno local (sqrt(0,75)), con filtro AR(1)
aproximado (coeficiente 0,65, ventana 21 días). No representa precisión ni
incertidumbre calibrada, y no valida relaciones físicas entre variables ni la
estacionalidad anual. PM se limita a valores no negativos y humedad a 0–100 %.
No se aplica ruido a mediciones ni huecos cortos. El calendario absoluto conserva
los resultados al cambiar mes, año, orden o selección de sectores.

Se conservan los 1.160 polígonos y cada sector vuelve a tener una sola curva por
variable. El hover identifica mediciones, rellenos cortos y rellenos con variación
sintética; las agregaciones mensuales o semanales pueden mezclar orígenes. Mapa,
barras, series y CSV comparten filtros y valores. Los CSV indican el modo,
fuentes, días añadidos, semilla y variación, sin presentar los añadidos como medidos.

IDW combina las cuatro estaciones disponibles más cercanas al centroide
(haversine, potencia 2, piso 0,1 km). Ambos modos muestran estimaciones espaciales,
no mediciones directas del barrio ni promedios de toda su área. Los límites
permanecen en gris si no hay valor. Las ubicaciones provienen de la SDA; los
traslados históricos de estaciones no están verificados.

El paquete compacto está en `data/maps/`. Su calendario por estación conserva
`*_hours`, `*_origin`, `*_neighbor_gap_days` y `*_short_gap`. La etiqueta interna
`knn_scenario_baseline` identifica la base determinista de relleno; la variación
por sector se genera al consultar y no modifica el archivo. El manifiesto
documenta hashes, cobertura, las dos opciones y su opción inicial.

El tratamiento es retrospectivo y puede usar fuentes posteriores a una fecha.
No alimenta el HGB de pronósticos. Sus fuentes y artefactos, y los recorridos
originales de 2024, permanecen conservados. La comprobación temporal limitada
de KNN (25–31 de marzo de 2025) no valida meses/años ausentes ni precisión espacial.

El notebook 04 documenta la base del procedimiento y sus comprobaciones; el
notebook 05 reproduce la integración vigente y amplía las fuentes del mapa.
La siguiente orden reconstruye el paquete del mapa con las fuentes locales
disponibles en el entorno de investigación:

```bash
python -B -m research.neighborhood_history
python -B -m unittest dash2.test_neighborhood_data dash2.test_map_scenarios -v
```

La primera referencia de estaciones se obtiene con `--network`; después funciona
sin red. Reiniciar Django tras reconstruir. Descargas GET:
`/api/maps/calendar/`, `/api/maps/methodology/` y `/api/maps/manifest/`.
