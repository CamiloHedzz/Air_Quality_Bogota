import dash
from dash import html
import dash_bootstrap_components as dbc


layout = dbc.Container([
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Img(src='/static/images/logo.png', className='logo-img'),
                html.H1(['Visualización y Predicción de la Calidad del Aire en Bogotá'], className='title-text'),
                html.B(['Dashboard Interactivo y Modelos Predictivos'], className='title-text')
            ], width=12, className='row-titles')
        ]),
        dbc.Row([
            dbc.Col([], width=2),
            dbc.Col([
                html.P(['Ofrecemos una solución integral para la gestión de la calidad del aire en Bogotá. A través de un dashboard interactivo, proporciona información en tiempo real sobre los niveles de contaminantes en diferentes zonas de la ciudad, ayudando a las autoridades locales, responsables ambientales y ciudadanos a tomar medidas efectivas para prevenir la contaminación y mejorar la calidad del aire. Además, se incluye el desarrollo de un modelo predictivo basado en datos recopilados, permitiendo estimar la concentración de partículas contaminantes en función de diversos factores.'], className='guide'),
                html.Img(src='/static/images/down.png', className='logo-img-down'),
            ], width=8, className='content-row'),
            dbc.Col([], width=2)
        ], className='content-row')
    ], className="teste")
], fluid=True)
