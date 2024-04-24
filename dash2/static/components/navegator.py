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
                html.A('Inicio', href='', className="link_nav"),
                html.A('Nosotros', href='us', className="link_nav"),
                html.A('Haz tus predicciones', href='predictions', className="link_nav")
            ], className="items_list")
        ], className="items_nav"),
    ],
    className="nav"
)


