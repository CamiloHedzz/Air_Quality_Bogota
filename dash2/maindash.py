from hashlib import sha256
from pathlib import Path

from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

def _asset_url(path):
    """Refresh dashboard assets in the browser whenever their content changes."""
    content = (Path(__file__).parent / "static" / path).read_bytes()
    version = sha256(content).hexdigest()[:12]
    return f"/static/{path}?v={version}"


# Crear la aplicación Dash
app = DjangoDash(
    'SimpleExamplee',
    # Page callbacks mount their components inside general-content dynamically.
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        _asset_url('css/frame_cursor.css'),
        _asset_url('css/embedded_dashboard.css'),
        _asset_url('css/dashboard_light.css'),
        _asset_url('css/frame_theme.css'),
    ],
    external_scripts=[_asset_url('js/frame_language.js'), _asset_url('js/frame_theme.js'), _asset_url('js/frame_cursor.js'), _asset_url('js/embedded_dashboard.js'), _asset_url('js/dashboard_readiness.js')],
)

app.css.append_css({ "external_url" : _asset_url("css/dash_app.css") })

app.css.append_css({ "external_url" : _asset_url("css/about_app.css") })

app.css.append_css({ "external_url" : _asset_url("css/prediction_app.css") })
