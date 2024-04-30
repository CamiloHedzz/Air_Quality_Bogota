import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output

from ...maindash import app

from ..pages.dashboard import dashboard
from ..pages.about import about
from ..pages.predictions import predictions

navbar = html.Nav(
    [
        html.Div([
            html.Img(src='/static/images/image.png', className="logo_img"),
            html.Div([
                html.H1("Bogota en cifras", className="title_h1"),
                html.H2("Calidad del Aire", className="title_h2")
            ], className="title_container")
        ],
            className="title_nav"),
        html.Div([
            html.Ul([
                html.Button('Inicio', className="btn btn-transparent btn-nav", id='btn_inicio'),
                html.Button('Haz tus predicciones', className="btn btn-transparent btn-nav", id='btn_predicciones'),
                html.Button('Nosotros', className="btn btn-transparent btn-nav", id='btn_nosotros')
            ], className="items_list")
        ], className="items_nav"),
    ],
    className="nav"
)

@app.callback(
    Output("general-content", "children"),
    [Input('btn_inicio', 'n_clicks'),
    Input('btn_nosotros', 'n_clicks'),
    Input('btn_predicciones', 'n_clicks')]
) 
def update_navegation(btn_inicio, btn_nosotros, btn_predicciones):
    button_id = ""
    
    if len(dash.callback_context.triggered) > 0:
        button_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "btn_nosotros":    
        return about
    elif button_id == "btn_predicciones": 
        return predictions

    return dashboard