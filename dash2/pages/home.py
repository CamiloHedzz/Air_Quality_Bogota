import dash
from dash import html
import dash_bootstrap_components as dbc

layout = dbc.Container([
    
    
    html.Div([
    html.Div(className="perspective", children=[
        html.Div(className="box", children=[
            html.Div(className="face top"),
            html.Div(className="face back"),
            html.Div(className="face front"),
            html.Div(className="face left"),
            html.Div(className="face right"),
            html.Span(className="shadow")
        ])
    ])
], style={'width': '100%'}),
    
    dbc.Row([
        dbc.Col([
            html.Img(src='/assets/my_image.png', style={'width': '100%'}),
            html.H1(['Visualización y Predicción de la Calidad del Aire en Bogotá']),
            html.B(['Dashboard Interactivo y Modelos Predictivos'])
        ], width=12, className='row-titles')
    ]),
    dbc.Row([
        dbc.Col([], width = 2),
        dbc.Col([
            html.P(['Ofrecemos una solución integral para la gestión de la calidad del aire en Bogotá. A través de un dashboard interactivo, proporciona información en tiempo real sobre los niveles de contaminantes en diferentes zonas de la ciudad, ayudando a las autoridades locales, responsables ambientales y ciudadanos a tomar medidas efectivas para prevenir la contaminación y mejorar la calidad del aire. Además, se incluye el desarrollo de un modelo predictivo basado en datos recopilados, permitiendo estimar la concentración de partículas contaminantes en función de diversos factores.'], className='guide'),
        ], width = 8),
        dbc.Col([], width = 2)
    ])
],fluid=True)