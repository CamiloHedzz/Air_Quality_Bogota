from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

# Crear la aplicación Dash
app = DjangoDash('SimpleExamplee', external_stylesheets=[dbc.themes.BOOTSTRAP])

app.css.append_css({ "external_url" : "/static/css/dash_app.css" })

app.css.append_css({ "external_url" : "/static/css/about_app.css" })

app.css.append_css({ "external_url" : "/static/css/prediction_app.css" })
