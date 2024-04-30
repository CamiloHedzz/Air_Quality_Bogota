from dash import html, dcc
from ..components.footer import footer_content

about = html.Div(
    id="about",
    className="about-container",
    children=[
        html.Div(children=[
            html.H2("Detrás de la Cortina 🎓", className="title_about"),
            html.Div(className="container_behind_desc", children=[
                html.P("Este proyecto ha sido posible gracias al apoyo incondicional de nuestras familias. Detrás de esta aplicación, encontramos un equipo comprometido que trabaja arduamente en la toma de muestras: estudiantes y alumnos motivados por la causa ambiental. Nuestro equipo está en constante crecimiento y, al desarrollar esta aplicación web, contamos con la valiosa guía y liderazgo de nuestro director de proyecto, Darwin Martínez. Los desarrolladores de esta aplicacion los encuentras aqui abajo.")
            ]),
            html.Div(className="container_authors", children=[
                html.Div(className="info_author", children=[
                    html.Img(src="/static/images/jap.png", alt="developer"),
                    html.A("Juan Esteban Arias", href="https://github.com/Juanariasp"),
                    html.P("Profesional con formación en Ingeniería en Ciencias de la Computación e Inteligencia Artificial. Mi participación destacada en competiciones de programación a nivel nacional y regional subraya mi habilidad para abordar desafíos complejos.")
                ]),
                html.Div(className="info_author", children=[
                    html.Img(src="/static/images/chi.jpg", alt="developer"),
                    html.A("Juan Camilo Hernandez", href="https://github.com/CamiloHedzz"),
                    html.P("Ingeniero en Ciencias de la Computación e Inteligencia Artificial, interesado en siempre aprender nuevas tecnologías y prácticas para procesamiento de datos y creación de modelos de Machine Learning.")
                ]), 
            ])
        ]), 
        
        html.Div(children = [
            html.H2("Como hacemos que funcione? 🙌", className="title_about"),
            html.Div(className="paragraph_about", children = [
                html.P("Nuestra estrategia para hacer que funcione se basa en un sistema de mapeo de rutas predefinidas, donde desplegamos sensores PM2.5 a lo largo de las calles de Bogotá. Estos sensores recopilan datos cruciales sobre la calidad del aire en tiempo real. Posteriormente, esta información se somete a un riguroso proceso de análisis y procesamiento de datos, empleando herramientas avanzadas como el análisis estadístico y algoritmos de Machine Learning."),
                html.P("Este enfoque nos permite no solo identificar con precisión las áreas con mayores impactos ambientales, sino también prever tendencias y patrones futuros en la calidad del aire. Además, al integrar criterios como el nivel de tráfico y eventos diarios al momento de la toma de muestras, garantizamos predicciones más certeras y contextualizadas."),
                html.P("Los datos procesados son esenciales para diseñar e implementar medidas de mitigación efectivas y políticas públicas orientadas a mejorar la salud pública y reducir los efectos negativos en el medio ambiente. Actualmente, estamos dedicados a mejorar la precisión de nuestro modelo mediante la recopilación de una mayor cantidad de muestras, pruebas exhaustivas y ajustes continuos. Este compromiso nos permite avanzar hacia una gestión ambiental más efectiva y una ciudad más saludable para todos."),
                html.P("Recuerda que puedes encontrar más información sobre este proyecto a través de nuestro repositorio en GitHub!"),                
            ])
        ]),

        html.Div(children = [
            html.H2("Motivados por un Impacto Positivo 🌄", className="title_about"),
            html.Div(className="paragraph_about last-one", children = [
                html.P("La contaminación ambiental representa una amenaza tangible para la salud de quienes habitan en zonas afectadas. Al desarrollar una aplicación web capaz de identificar las áreas más contaminadas de Bogotá, podemos empoderar a los residentes, brindándoles información clara y accesible sobre los niveles de contaminación en diferentes localidades. Esto no solo les permite tomar medidas inmediatas para proteger su salud, sino que también fomenta la conciencia colectiva sobre la necesidad de reducir la contaminación en nuestra ciudad."),
                html.P("Al crear conciencia y promover la acción comunitaria, podemos iniciar un movimiento hacia una Bogotá más saludable y sostenible. En un contexto donde la ciudad y muchas otras enfrentan desafíos como sequías y cambios climáticos, es fundamental que todos contribuyamos activamente a cuidar nuestro entorno. Nuestra responsabilidad como ciudadanos es crucial para garantizar un futuro mejor para nuestras generaciones venideras."),
                html.P("¿Quieres explorar más sobre cómo nuestros servicios pueden beneficiarte? ¿Estás buscando oportunidades de colaboración o deseas brindar soporte a nuestra causa? ¡Nos encantaría saber de ti! Estamos comprometidos a responder con prontitud a tus consultas e intereses, así que no dudes en ponerte en contacto con nosotros. Tu participación es fundamental para impulsar nuestro crecimiento y éxito compartido.")
            ])
        ]),
        
        footer_content
    ]
)
