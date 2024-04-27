from .maindash import app
from .static.components.navegator import navbar
import dash_bootstrap_components as dbc

app.layout = dbc.Container(
    [  
        navbar,
        dbc.Row(id="general-content", children=[]) 
    ],
    fluid=True,
)

if __name__ == '__main__':
    app.run_server(debug=True)
