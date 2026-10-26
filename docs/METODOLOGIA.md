# Metodología: mapas, modelos y rutas

[← Volver al README](../README.md) · [Desarrollo local](DESARROLLO.md) · [Contrato de datos](../data/README.md)

La integración vigente corresponde al **notebook 05**. Esta guía explica las fuentes
y el alcance actual de la web y conserva después los experimentos anteriores para
que sus muestras, comandos y métricas sigan siendo trazables.

Los comandos se ejecutan desde la raíz del repositorio. La investigación utiliza
un entorno separado del servidor web; Django usa la configuración local indicada.

## Recorrido de los notebooks

| Notebook | Estado y propósito |
|---|---|
| [05 · Integración histórica](../notebooks/05_integracion_historica_2015_2025.ipynb) | **Vigente.** Observaciones 2015–2025, ERA5, HGB multianual y paquetes para la web. |
| [01 · Dataset histórico](../notebooks/01_dataset_historico.ipynb) | Etapa anterior: auditoría, fuentes y muestra piloto. |
| [02 · Experimento HGB inicial](../notebooks/02_histgradientboosting_pronostico.ipynb) | Etapa anterior: primera comparación temporal con persistencia e imputación. |
| [03 · Trimestre de 2025](../notebooks/03_histgradientboosting_trimestre.ipynb) | Etapa anterior: entrenamiento y prueba del primer trimestre de 2025. |
| [04 · Mapa por sectores](../notebooks/04_mapa_historico_barrios.ipynb) | Base del tratamiento espacial/temporal, ampliada por el notebook 05. |

## Integración vigente · notebook 05

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

## Predicciones históricas que consulta la web

El paquete vigente `hgb_2015_2024_era5_holdout_2025_v1` contiene **57.933 resultados**
precalculados para PM2.5 y PM10 a **24/48/72 horas**, con persistencia y observación
objetivo para comparar. No son inferencias emitidas para hoy ni curvas completas.
Las etiquetas y rezagos de PM son observaciones; los predictores ERA5 se unen en el
origen como reanálisis retrospectivo, sin acreditar disponibilidad operativa histórica.

| Artefacto | Uso |
|---|---|
| `data/history/observations.csv.gz` + manifiesto | Observaciones consolidadas y procedencia por variable. |
| `data/weather/era5_hourly_2015_2025.csv.gz` + manifiesto | Reanálisis meteorológico separado de las mediciones. |
| `data/weather/station_grids.csv` | Referencias de estaciones y celdas ERA5. |
| `data/reports/hgb_2015_2025/` | Desarrollo, prueba, cortes, métricas y configuración. |
| `data/forecasts/hgb_historical.csv.gz` + manifiesto | Backtests que sirve Django; no es un modelo ejecutable. |
| `data/maps/` | Calendario del mapa; no se usa como objetivo HGB. |

El servidor verifica hashes, horizonte, separación temporal y coincidencia de los
objetivos con las fuentes. No carga pickle/joblib ni entrena por consulta. El proceso
web no necesita Jupyter ni scikit-learn. Después de reconstruir, reiniciar Django.
El exportador prioriza `data/reports/hgb_2015_2025/` cuando existe; Q1 queda como
vía de compatibilidad, no como el paquete vigente.

### Dos modos de análisis, con procedencia explícita

**Datos originales** conserva observaciones y ausencias. **Datos con tratamiento**,
predeterminado, completa solo temperatura y humedad ausentes con ERA5, con marca
`weather_reanalysis`. No rellena PM para fabricar objetivos ni activa pronósticos
de temperatura/humedad. Los CSV distinguen la procedencia por variable.

Las cinco vistas permiten consultar HGB, comparar estaciones con horas coincidentes,
examinar relaciones, agrupar por día/hora y evaluar errores. La evaluación utiliza
las cuatro semanas de 2025, la estación y el contaminante seleccionados. Presenta
real frente a estimado, histograma de error firmado, MAE frente a persistencia y
cajas del error; estas cajas no son intervalos de predicción. Las comparaciones
entre horizontes emplean objetivos observados emparejados cuando corresponda.

API GET: `/api/predictions/catalog/`, `/api/predictions/options/`,
`/api/predictions/query/` y `/api/predictions/export/`. Filtros y tabla en React;
figuras Dash/Plotly en `PredictionCharts`, con idioma y tema compartidos.

```bash
python -B manage.py test dash2.test_predictions dash2.test_prediction_figures dash2.test_history_integration --settings=airquality_api.settings_local
```

Las métricas vigentes están en su manifiesto y en `data/reports/hgb_2015_2025/`.
Las tablas del archivo de experimentos que sigue corresponden a muestras anteriores.


## Rutas en bicicleta (experimental)

La pestaña **Rutas** permite buscar dos lugares de Bogotá, elegir día y hora de
salida y comparar hasta tres recorridos reales para bicicleta. La navegación y
el Menú siguen el orden Inicio, Predicciones, Rutas, About. El mapa usa Plotly
Scattermap/MapLibre, con los mismos temas e idiomas del sitio.

El servidor consulta BRouter con el perfil `trekking`; Photon resuelve lugares
solo al pulsar Buscar. Se conservan los créditos de OpenStreetMap. Las respuestas
de lugares y geometrías se cachean un día; se limita la búsqueda a una cada dos
segundos y se serializan las consultas al motor. No se guardan viajes en la base
de datos. Estos servicios públicos dependen de Internet y no garantizan
disponibilidad. Para uso con más usuarios, configurar instancias propias con
`AIRQUALITY_PHOTON_URL` y `AIRQUALITY_BROUTER_URL`, además de un caché Django
compartido para que los límites se apliquen entre procesos.

La exposición es **histórica y exploratoria, no un pronóstico actual ni una
medición por calle**. Se verifica el contrato y manifiesto de
`data/samples/rmcab_2025_q1.csv`, y se calculan medianas por estación, hora y
laboral/fin de semana, con al menos ocho observaciones por perfil. Cada punto
usa hasta tres estaciones dentro de 5 km y requiere dos, ponderadas por inverso
de distancia al cuadrado (piso de 250 m). Las posiciones son las referencias
oficiales actuales; no se han comprobado todas las reubicaciones históricas.

Se integra concentración × minutos a lo largo del recorrido, con muestras como
máximo cada 200 m y 60 s, avanzando la hora y el tipo de día en medianoche. El
indicador se expresa en µg·min/m³; no es dosis inhalada. No se comparan
exposiciones si alguna alternativa tiene cobertura incompleta (tolerancia
numérica 1e-6 en la fracción cubierta). Equilibrio minimiza por partes iguales tiempo relativo al mínimo
y exposición relativa al mínimo entre las alternativas disponibles. Las
diferencias pequeñas no demuestran una mejora real. El motor no optimiza todas
las calles con un campo de contaminación ni considera tráfico en vivo.

Endpoints: `/api/routes/places/`, `/api/routes/compare/` y
`/api/routes/plotly.js`. La biblioteca de Plotly se sirve desde el paquete Python
ya instalado, sin otra dependencia. La zona inicial es el área urbana de Bogotá;
se limita la distancia entre extremos a 25 km y el recorrido a 50 km/4 h.

```bash
python -B manage.py test rutes.test_planner --settings=airquality_api.settings_local
```

Referencias: [BRouter](https://brouter.de/brouter/),
[Photon y uso moderado](https://github.com/komoot/photon#demo-server),
[Plotly](https://plotly.com/python/lines-on-tile-maps/).

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

## Archivo de experimentos y primera publicación · notebooks 01–04

> Las cifras de 100 reportes, 17.481 pronósticos y la prueba del 25–31 de marzo
> describen la etapa piloto/trimestral, **no el paquete vigente**. Sus informes y
> datos se preservan para comparación. Para actualizar la web, seguir el notebook 05.
> El exportador actual prioriza el informe multianual cuando existe: los comandos
> históricos de publicación no seleccionan por sí solos el experimento anterior.

<details>
<summary>Consultar los experimentos piloto y trimestral preservados</summary>

### Notebook 01 · investigación y muestra piloto

El trabajo reproducible de datos se encuentra en
[`notebooks/01_dataset_historico.ipynb`](../notebooks/01_dataset_historico.ipynb).
Incluye auditoría del CSV existente, fuentes oficiales, una muestra real de
RMCAB de varios años, cobertura por variable, comparación de imputación con
scikit-learn y preparación de observaciones para modelado temporal.
La muestra piloto **no equivale a once años completos** y el CSV del dashboard
se conserva. Los detalles del contrato, fuentes y recolección están en
[`data/README.md`](../data/README.md).

Usa un entorno independiente del servidor web, desde la raíz del repositorio:

```bash
py -3.11 -m venv .venv-research
source .venv-research/Scripts/activate
export PYTHONUTF8=1
export PYTHONDONTWRITEBYTECODE=1
python -m pip install -r requirements-research.txt
python -B -m unittest research.test_air_quality -v
python -m jupyterlab notebooks/01_dataset_historico.ipynb
```

En Jupyter, usa el kernel Python del entorno `.venv-research`. El notebook puede
ejecutarse sin red con los datos de `data/samples/`. Para ampliar los históricos,
consulta los comandos de `research.collect_rmcab` en la guía de datos.

### Notebook 02 · primer experimento HGB

[`notebooks/02_histgradientboosting_pronostico.ipynb`](../notebooks/02_histgradientboosting_pronostico.ipynb)
entrena y evalúa PM2.5 y PM10 sobre la semana continua del 3 al 9 de febrero de
2025. Compara persistencia, HGB con NaN nativos y HGB con medianas ajustadas
exclusivamente en entrenamiento. No completa años con valores inventados ni
modifica los datos del dashboard. Usa el mismo entorno `requirements-research.txt`.

```bash
python -B -m unittest research.test_air_quality research.test_forecast_experiment -v
python -m jupyterlab notebooks/02_histgradientboosting_pronostico.ipynb
```

Ejecuta todas las celdas para regenerar los informes de `data/reports/hgb_pilot/`
y el detalle de predicciones en `data/processed/hgb_pilot_predictions.csv`.
El experimento conserva los objetivos observados y purga el entrenamiento para
que sus etiquetas precedan a los orígenes de validación. A 1 y 24 horas se evalúan
tres ventanas diarias; a 48 horas solo una; a 72 horas no hay entrenamiento previo
suficiente y se omiten todas las ventanas. Son horizontes puntuales, no una curva
completa emitida desde un mismo origen.

Resultados exploratorios a 24 h (MAE en µg/m³):

| Variable | Persistencia | HGB con NaN | HGB con mediana |
|---|---:|---:|---:|
| PM2.5 | 8.31 | 6.40 | 6.43 |
| PM10 | 13.27 | 11.62 | 11.56 |

Una semana y estaciones conocidas no prueban generalización anual o espacial.
El experimento presupone disponibilidad de las lecturas publicadas en el origen;
no contamos con un archivo de latencias o revisiones del portal. No se exporta
ni despliega un modelo. Para un pronóstico actual hacen falta lecturas recientes,
históricos continuos más amplios y una evaluación final separada.

### Notebook 03 · experimento trimestral de 2025

[`notebooks/03_histgradientboosting_trimestre.ipynb`](../notebooks/03_histgradientboosting_trimestre.ipynb)
amplía la investigación a **90 reportes diarios**, de enero a marzo de 2025:
41,040 filas de estación/hora y 19 estaciones listadas.
Los reportes pueden tener sensores ausentes; la disponibilidad diaria y por estación
se conserva en los informes. No equivale a un dataset completo de 2015–2025.

Se mantienen los hiperparámetros del experimento inicial. La comparación de
variantes usa tres semanas de desarrollo hasta el 21 de marzo. La evaluación final
usa objetivos de los reportes del **25 al 31 de marzo**, con HGB nativo elegido antes
de ver los resultados finales y persistencia como referencia. Los cortes purgan
etiquetas que alcanzarían los orígenes de validación.

Resultados de la semana final (MAE en µg/m³; menor es mejor):

| Variable | Horizonte | Persistencia MAE | HGB MAE |
|---|---:|---:|---:|
| PM2.5 | 1 h | 4.89 | 4.18 |
| PM2.5 | 24 h | 8.00 | 6.49 |
| PM2.5 | 48 h | 9.41 | 7.38 |
| PM2.5 | 72 h | 9.40 | 7.61 |
| PM10 | 1 h | 8.07 | 7.33 |
| PM10 | 24 h | 15.42 | 12.37 |
| PM10 | 48 h | 19.27 | 13.79 |
| PM10 | 72 h | 20.45 | 14.20 |

Los resultados varían por estación y horizonte; revisar `holdout_per_station.csv`.
No se han ajustado parámetros con la semana final. Tras consultar sus resultados,
los cambios futuros necesitarán un periodo de prueba distinto. Un trimestre sigue
sin acreditar comportamiento anual, por barrios o con datos en tiempo real.

Para reconstruir las descargas secuenciales y reanudables:

```bash
python -B -m research.collect_rmcab_period --start 2025-01-01 --end 2025-03-31 --network --output data/samples/rmcab_2025_q1.csv
python -B -m unittest research.test_air_quality research.test_forecast_experiment research.test_collect_period -v
python -m jupyterlab notebooks/03_histgradientboosting_trimestre.ipynb
```

El recolector admite hasta 92 días por lote. Con caché completa, omitir `--network`.
El notebook funciona sin red con el CSV y su manifiesto. Las métricas y metadatos
están en `data/reports/hgb_2025_q1/`; las predicciones detalladas son regenerables
en `data/processed/`. Se conservan los CSV anteriores y el dataset de la web.
Los resultados históricos evaluados se conectan a la web mediante el paquete descrito en la siguiente sección; no se despliega inferencia en tiempo real.

### Primera integración de predicciones en la web · archivo

La primera integración de **Predicciones** consultaba 17.481 estimaciones históricas reales
de HistGradientBoosting para PM2.5 y PM10 a 24, 48 y 72 horas. El usuario selecciona
estación, fecha y hora entre los orígenes disponibles. Se muestran el histórico,
la estimación puntual, persistencia, la observación posterior opcional y el MAE
histórico por estación. No se dibuja una trayectoria ni un intervalo no calculados.

Las otras vistas calculan comparación emparejada entre estaciones, correlación
y dispersión de variables coincidentes, y agregados por día/hora. Humedad y
temperatura tienen análisis histórico; no tienen un modelo de pronóstico activado.
Los filtros de histórico, agrupación y estadística se aplican a los datos reales.
La tabla y los CSV conservan ausencias, las cuatro variables, unidades y procedencia.

El catálogo de esta etapa unía el piloto y el trimestre sin duplicar observaciones: 100 reportes
distribuidos entre 2015–2025, con fechas aisladas antes de 2025. La cobertura parcial
y el entrenamiento de aquella etapa de enero–marzo de 2025 están visibles en la pantalla.
No equivale a once años completos ni a un pronóstico emitido para hoy.

Flujo reproducible:

`notebook 03 → research.publish_predictions → CSV.gz + manifiesto → API Django + DjangoDash → React`

Después de ejecutar todas las celdas del notebook 03, desde la raíz del repositorio:

```bash
python -B -m research.publish_predictions
python -B manage.py test dash2.test_predictions dash2.test_prediction_figures --settings=airquality_api.settings_local
```

El exportador usa las predicciones del test final en `data/processed/` y verifica
los hashes de entrada y la separación temporal. El paquete pequeño de
`data/forecasts/` se versiona para que un clon pueda consultar resultados sin
Jupyter ni scikit-learn en el servidor web. Es una reproducción de backtests
precalculados, no inferencia nueva ni entrenamiento por petición.
Para actualizarlo hay que repetir el notebook y exportar el paquete junto con sus
metadatos. Reiniciar Django tras reemplazarlo, porque se carga en memoria.

API GET:

- `/api/predictions/catalog/`: estaciones, variables, cobertura y alcance del modelo.
- `/api/predictions/options/`: fechas/horas válidas para la selección.
- `/api/predictions/query/`: series, análisis, métricas y resultado histórico.
- `/api/predictions/export/`: CSV de observaciones o del pronóstico seleccionado.

La página conserva los filtros y la tabla en React. Las figuras se renderizan con
**Dash y Plotly** en la aplicación `PredictionCharts`, integrada mediante un iframe
que ajusta su altura al contenido. Las figuras de la web actual siguen el idioma y el tema del sitio. Se puede usar
zoom, consultar puntos, ocultar series con la leyenda y descargar PNG desde la
barra de Plotly. El pie de página permanece fuera del iframe.

La pestaña **Evaluar el modelo** añade cuatro perspectivas:

- Real frente a estimado: la diagonal indica coincidencia y el rombo la consulta.
- Histograma del error firmado: positivo significa sobreestimación.
- MAE por horizonte: HGB frente a persistencia, con los mismos objetivos observados
  disponibles a 24/48/72 h, para evitar comparar muestras distintas.
- Cajas del error: mediana, cuartiles y valores alejados de errores pasados; no son
  intervalos de predicción.

Estos gráficos usan la estación y el contaminante seleccionados, en la semana de
prueba del 25–31 de marzo de 2025; no cambian su periodo con la ventana del histórico.
Las métricas de MAE y sesgo corresponden al horizonte seleccionado. La descarga
`kind=evaluation` incluye los tres horizontes, objetivos, errores, cortes y fuentes.
El panel «Así aprende el modelo» explica entradas, árboles sucesivos, MAE y la
comparación temporal, con el alcance real del modelo visible.

Vite reenvía `/api/predictions`, `/api/maps`, `/api/routes`, `/django_plotly_dash` y `/static` a
`127.0.0.1:8000` durante desarrollo. En despliegue, servir las rutas de API y Dash
con Django bajo el mismo origen de React y los estáticos recogidos con
`collectstatic`, o configurar el proxy correspondiente.
No usar `vite preview` como sustituto del servidor de API.

</details>
