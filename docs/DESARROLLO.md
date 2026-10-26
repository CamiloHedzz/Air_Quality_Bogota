# Desarrollo local

[← Volver al README](../README.md)

Esta guía describe el entorno de desarrollo de Air Quality Bogotá. Ejecuta los comandos desde la raíz del repositorio, salvo que se indique otra carpeta.

## Requisitos

- **Python 3.11.** El entorno web está validado con Python 3.11.9 y las versiones fijadas en [`requirements-local.txt`](../requirements-local.txt).
- **Node.js y npm.** El lock del frontend fija Vite 5.1.1, que declara compatibilidad con Node `^18.0.0 || >=20.0.0`.
- **Git** para clonar el repositorio.
- Conexión a Internet para instalar dependencias, cargar teselas y usar Photon/BRouter.

Los paquetes locales de mapas y predicciones permiten consultar los resultados incluidos sin Jupyter ni scikit-learn en el servidor web. El entorno de investigación es independiente.

## Windows · PowerShell

### Preparación

```powershell
git clone https://github.com/CamiloHedzz/Air_Quality_Bogota.git
cd Air_Quality_Bogota
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-local.txt
npm --prefix airquality_front ci
```

Se usa directamente el intérprete del entorno, por lo que no es necesario activar un script de PowerShell.

### Terminal 1 · Django y Dash

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONDONTWRITEBYTECODE = "1"
.\.venv\Scripts\python.exe -B manage.py migrate --settings=airquality_api.settings_local
.\.venv\Scripts\python.exe -B manage.py runserver 127.0.0.1:8000 --settings=airquality_api.settings_local
```

### Terminal 2 · React y Vite

```powershell
npm --prefix airquality_front run dev -- --port 5173 --strictPort
```

Abre [http://localhost:5173](http://localhost:5173). Puedes consultar el dashboard directamente en [http://127.0.0.1:8000/dashv1/](http://127.0.0.1:8000/dashv1/).

Para detener los servidores, usa `Ctrl+C` en cada terminal.

## Windows · Git Bash

### Preparación

```bash
git clone https://github.com/CamiloHedzz/Air_Quality_Bogota.git
cd Air_Quality_Bogota
py -3.11 -m venv .venv
source .venv/Scripts/activate
export PYTHONUTF8=1
export PYTHONDONTWRITEBYTECODE=1
python -m pip install -r requirements-local.txt
npm --prefix airquality_front ci
```

### Terminal 1

```bash
source .venv/Scripts/activate
export PYTHONUTF8=1
export PYTHONDONTWRITEBYTECODE=1
python -B manage.py migrate --settings=airquality_api.settings_local
python -B manage.py runserver 127.0.0.1:8000 --settings=airquality_api.settings_local
```

### Terminal 2

```bash
npm --prefix airquality_front run dev -- --port 5173 --strictPort
```

## Configuración y datos incluidos

Usa `--settings=airquality_api.settings_local` en los comandos Django. Esa configuración crea `.local/db.sqlite3`, independiente del `db.sqlite3` antiguo de la raíz, y no necesita credenciales PostgreSQL.

La API comienza sin registros propios en la nueva base. El dashboard y las consultas históricas leen los paquetes locales y sus manifiestos; una base SQLite vacía no significa que falten los datos del explorador.

| Carpeta | Contenido que utiliza el proyecto |
|---|---|
| `data/history/` | Observaciones consolidadas de 2015–2025, cobertura y exportaciones de origen. |
| `data/weather/` | Clima ERA5 horario, manifiesto y relación entre estaciones y celdas. |
| `data/maps/` | Calendario diario, centroides y tratamiento del mapa por sectores. |
| `data/forecasts/` | Backtests HGB precalculados que consulta Predicciones. |
| `data/samples/` | Muestras piloto y trimestral preservadas; Rutas sigue usando el primer trimestre de 2025. |
| `dash2/datasets/` | Geometría de Bogotá y conjuntos de trabajo originales preservados. |

La integración vigente se reproduce con el [notebook 05](../notebooks/05_integracion_historica_2015_2025.ipynb). Incluye observaciones de SDA/RMCAB y SISAIRE, reanálisis ERA5 y HGB entrenado con 2015–2024, evaluado en cuatro semanas de 2025. Los manifiestos verifican que los paquetes publicados correspondan a sus fuentes. Predicciones sigue sirviendo resultados históricos, sin entrenamiento ni inferencia nueva al hacer una consulta.

[`airquality_api/settings.py`](../airquality_api/settings.py) conserva la configuración original del proyecto, incluido PostgreSQL. La guía anterior utiliza el archivo local para ejecutar el sitio sin depender de esa instalación.

El dashboard abre **Mapa por sectores**, con **Datos con tratamiento** y fondo **Automático · tema del sitio**. La pestaña **Históricos RMCAB · estaciones** consulta el histórico observado consolidado. Predicciones distingue Datos originales y Datos con tratamiento: en este último, temperatura y humedad ausentes pueden proceder de ERA5, siempre identificadas. El mapa de Rutas abre en **Liberty**. Ambos exploradores ofrecen sus selectores de fondo.

## Comprobaciones

En PowerShell, con las dependencias web instaladas:

```powershell
.\.venv\Scripts\python.exe -B manage.py check --settings=airquality_api.settings_local
.\.venv\Scripts\python.exe -B manage.py test dash2.test_predictions dash2.test_prediction_figures dash2.test_history_integration rutes.test_planner --settings=airquality_api.settings_local
.\.venv\Scripts\python.exe -B -m unittest dash2.test_rmcab dash2.test_dashboard_filters dash2.test_dashboard_overview dash2.test_neighborhood_data dash2.test_map_scenarios -v
npm --prefix airquality_front run build
```

Para investigar con scikit-learn y Jupyter, usa [`requirements-research.txt`](../requirements-research.txt) en otro entorno. El [notebook 05](../notebooks/05_integracion_historica_2015_2025.ipynb) documenta el flujo vigente y sus verificaciones, incluidas las de `research.test_history_ingestion`. La [metodología](METODOLOGIA.md) separa este flujo de los experimentos históricos 01–04 y conserva sus comandos y métricas.

## API principal

| Ruta | Uso |
|---|---|
| `/api/predictions/catalog/` | Estaciones, variables, cobertura y alcance del modelo. |
| `/api/predictions/options/` | Fechas y horas disponibles para consultar. |
| `/api/predictions/query/` | Series, análisis, métricas y resultado histórico. |
| `/api/predictions/export/` | Descarga de observaciones, pronósticos o evaluación. |
| `/api/maps/geometry/` | Geometría de los sectores. |
| `/api/maps/calendar/` | Calendario por estación. |
| `/api/maps/methodology/` | Notebook del procedimiento del mapa. |
| `/api/maps/manifest/` | Metadatos y procedencia del paquete del mapa. |
| `/api/routes/places/` | Búsqueda de origen y destino. |
| `/api/routes/compare/` | Comparación de recorridos en bicicleta. |
| `/api/routes/plotly.js` | Biblioteca de Plotly utilizada por el mapa de Rutas. |

Los parámetros y contratos de cada servicio se implementan en `dash2/prediction_views.py`, `dash2/neighborhood_views.py` y `rutes/planner_views.py`.

## Servicios externos de Rutas

La configuración predeterminada usa Photon para los lugares y BRouter con el perfil `trekking` para los recorridos. No guarda los viajes en la base de datos. Las respuestas de lugares y geometrías se cachean durante un día, se limita la búsqueda y se serializan las peticiones al motor.

Para configurar proveedores propios se admiten las variables `AIRQUALITY_PHOTON_URL` y `AIRQUALITY_BROUTER_URL`. Con varios procesos, el control compartido de límites requiere un backend de caché Django compartido. Los servicios públicos dependen de Internet y de su disponibilidad.

## Frontend y despliegue

En desarrollo, Vite reenvía `/api/predictions`, `/api/maps`, `/api/routes`, `/django_plotly_dash` y `/static` a `127.0.0.1:8000`. El iframe de Inicio también contiene una URL absoluta a ese servidor local.

`npm --prefix airquality_front run build` genera el frontend en `airquality_front/dist/`. Para un despliegue, hay que configurar la URL del iframe de Inicio, servir la API y Dash con sus rutas, recoger los estáticos de Django y configurar el fallback de React Router. La configuración local y `vite preview` no sustituyen ese despliegue completo.

## Si algo no carga

| Síntoma | Qué revisar |
|---|---|
| El frontend abre, pero faltan mapas o datos. | Mantén Django activo en el puerto 8000 y comprueba sus mensajes. |
| Django intenta conectarse a PostgreSQL. | Añade `--settings=airquality_api.settings_local` al comando. |
| `npm ci` no encuentra el lock correcto. | Ejecuta el comando con `--prefix airquality_front` o dentro de esa carpeta. |
| La página pide otro puerto para Vite. | Libera el 5173; el comando usa `--strictPort` para mantener la dirección prevista. |
| Se ven datos, pero falta el fondo del mapa. | Comprueba la conexión y el proveedor de teselas. |
| Cambiaste un paquete de datos y aún ves la versión anterior. | Reinicia Django: algunos conjuntos se cargan y conservan en memoria. |

Para revisar cobertura y procedencia, consulta [`data/README.md`](../data/README.md).
