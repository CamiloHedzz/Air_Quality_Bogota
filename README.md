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
las mediciones de los CSV incluidos en `dash2/datasets/`.

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

## Autores
Este proyecto fue desarrollado con ❤️ por :

Camilo Hernández 

Juan Arias 

¡Gracias por su interés en nuestro proyecto! Si tiene alguna pregunta o sugerencia, no dude en contactarnos.

¡Feliz exploración! 🌎🍃

