import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output

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
                html.A('Inicio', href='/inicio', className="link_nav"),
                html.A('Nosotros', href='/pagina1', className="link_nav"),
                html.A('Haz tus predicciones', href='/pagina2', className="link_nav")
            ], className="items_list")
        ], className="items_nav"),
    ],
    className="nav"
)
