from .maindash import app
from .static.pages.dashboard import dashboard
from .static.pages.home import layout
from .static.components.navegator import navbar
import dash_bootstrap_components as dbc

app.layout = dbc.Container(
    [
        navbar,
        dbc.Row(layout),
        dbc.Row(dashboard) 
    ],
    fluid=True,
)

if __name__ == '__main__':
    app.run_server(debug=True)
