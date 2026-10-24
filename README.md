# Air Quality Bogotá

En este proyecto, nos hemos propuesto abordar los desafíos relacionados con la polución y la contaminación del aire en la ciudad, identificando las zonas con mayor contaminación y desarrollando un modelo para estimar la concentración de partículas contaminantes.

## Descripción del Proyecto

La polución y contaminación atmosférica representan desafíos significativos en las grandes ciudades, y Bogotá no es una excepción. El objetivo principal de este proyecto de investigación es identificar las zonas con mayor contaminación en la ciudad y desarrollar un modelo que estime la concentración de partículas contaminantes en función de la hora y la ubicación. Además, se busca determinar el impacto en la salud asociado con la exposición prolongada a estas zonas.

![Pagina principal](https://raw.githubusercontent.com/CamiloHedzz/Air_Quality_Bogota/master/airquality_front/src/assets/images/front1.png)

![Recopilacion de datos](https://raw.githubusercontent.com/CamiloHedzz/Air_Quality_Bogota/master/airquality_front/src/assets/images/Datos2.png)

## Tecnologías Utilizadas

Este proyecto se desarrolló utilizando las siguientes tecnologías:

- Django
- React
- Dash

## Instalación y ejecución local en Windows (Git Bash)

El entorno local utiliza Python 3.11, Node.js y npm. Django sirve la API y el
dashboard Dash en el puerto 8000; React/Vite sirve la web en el puerto 5173.

### Preparación inicial

```bash
git clone https://github.com/CamiloHedzz/Air_Quality_Bogota.git
cd Air_Quality_Bogota
py -3.11 -m venv .venv
source .venv/Scripts/activate
export PYTHONUTF8=1
export PYTHONDONTWRITEBYTECODE=1
python -m pip install --upgrade pip
python -m pip install -r requirements-local.txt
npm --prefix airquality_front ci
```

Si ya tienes el repositorio y el entorno, empieza por activar `.venv`.
Las versiones de las dependencias mantienen la compatibilidad con el código
original de Dash.

### Terminal 1: Django y Dash

Desde la raíz del repositorio:

```bash
source .venv/Scripts/activate
export PYTHONUTF8=1
export PYTHONDONTWRITEBYTECODE=1
python -B manage.py migrate --settings=airquality_api.settings_local
python -B manage.py runserver 127.0.0.1:8000 --settings=airquality_api.settings_local
```

La configuración local crea `.local/db.sqlite3`, una base SQLite independiente
que no requiere contraseña. La API comienza sin registros; el dashboard obtiene
las mediciones por barrios de `dash2/datasets/` y la muestra de estaciones
de `data/samples/`.

El archivo `db.sqlite3` incluido en el repositorio tiene un esquema antiguo.
La configuración local utiliza su propia base y las migraciones actuales.

### Terminal 2: React

Desde la raíz del repositorio:

```bash
cd airquality_front
npm run dev -- --port 5173 --strictPort
```

Abre <http://localhost:5173>. Puedes comprobar el dashboard directamente en
<http://127.0.0.1:8000/dashv1/>. Detén cada servidor con `Ctrl+C` en su terminal.

### Históricos RMCAB en el dashboard

En Inicio, la pestaña **Históricos RMCAB · estaciones** muestra datos reales
de la muestra local, con filtros de variable, año, mes del reporte, estaciones,
frecuencia y estadística. Incluye series, comparación, disponibilidad y descarga
CSV con las cuatro variables, unidades, tratamiento y procedencia.
Los contadores distinguen días consultados y datos presentes; el piloto no
representa once años completos. La pestaña **Mapa por barrios** conserva el
conjunto de trabajo anterior y sus filtros independientes.

Dash lee `data/samples/rmcab_pilot_2015_2025.csv` y comprueba su manifiesto
`.sources.json` al iniciar el proceso. No ejecuta el notebook, descarga históricos
ni entrena modelos al abrir la web. Para el contrato y la actualización del lote,
consulta [`data/README.md`](data/README.md).

```bash
python -B -m unittest dash2.test_rmcab dash2.test_dashboard_filters dash2.test_dashboard_overview -v
```

### Mapa de fondo

El dashboard usa el estilo claro Positron de [OpenFreeMap](https://openfreemap.org/)
para mostrar calles, ríos y localidades alrededor de Bogotá. La capa tiene cobertura
mundial y no requiere una clave de API. Las mediciones coloreadas corresponden
únicamente a los barrios del conjunto de datos de Bogotá. Se necesita conexión a
Internet para cargar el fondo; sus créditos permanecen visibles en el mapa.

### PostgreSQL

`airquality_api/settings.py` contiene la configuración original de PostgreSQL.
Para utilizarla, configura allí la base `AirQuality_DB` y tus credenciales, y
ejecuta los comandos de Django sin `--settings=airquality_api.settings_local`.

Si aparece `password authentication failed for user "postgres"`, la contraseña
configurada no coincide con la del servidor. El modo local anterior permite
ejecutar el proyecto con SQLite.

## Investigación del dataset histórico (2015–2025)

El trabajo reproducible de datos se encuentra en
[`notebooks/01_dataset_historico.ipynb`](notebooks/01_dataset_historico.ipynb).
Incluye auditoría del CSV existente, fuentes oficiales, una muestra real de
RMCAB de varios años, cobertura por variable, comparación de imputación con
scikit-learn y preparación de observaciones para modelado temporal.
La muestra piloto **no equivale a once años completos** y el CSV del dashboard
se conserva. Los detalles del contrato, fuentes y recolección están en
[`data/README.md`](data/README.md).

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

## Primer experimento HistGradientBoosting

[`notebooks/02_histgradientboosting_pronostico.ipynb`](notebooks/02_histgradientboosting_pronostico.ipynb)
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

## HistGradientBoosting con un trimestre

[`notebooks/03_histgradientboosting_trimestre.ipynb`](notebooks/03_histgradientboosting_trimestre.ipynb)
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
El modelo aún no se exporta ni se conecta al panel de predicciones.

## Autores
Este proyecto fue desarrollado con ❤️ por :

Camilo Hernández 

Juan Arias 

¡Gracias por su interés en nuestro proyecto! Si tiene alguna pregunta o sugerencia, no dude en contactarnos.

¡Feliz exploración! 🌎🍃

