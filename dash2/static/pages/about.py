from dash import html, dcc

about = html.Nav(
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
                html.Button('Nosotros', className="btn btn-transparent btn-nav", id='btn_nosotros'),
                html.Button('Haz tus predicciones', className="btn btn-transparent btn-nav", id='btn_predicciones')
            ], className="items_list")
        ], className="items_nav"),
    ],
    className="nav"
)