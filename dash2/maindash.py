from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

# Crear la aplicación Dash
app = DjangoDash(
    'SimpleExamplee',
    # Page callbacks mount their components inside general-content dynamically.
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        '/static/css/embedded_dashboard.css',
        '/static/css/dashboard_light.css',
    ],
    external_scripts=['/static/js/embedded_dashboard.js'],
)

app.css.append_css({ "external_url" : "/static/css/dash_app.css" })

app.css.append_css({ "external_url" : "/static/css/about_app.css" })

app.css.append_css({ "external_url" : "/static/css/prediction_app.css" })
