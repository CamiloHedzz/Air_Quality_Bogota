"""Figuras Plotly de observaciones y evaluación histórica, sin reentrenamiento."""
import pandas as pd
import plotly.graph_objects as go

from .prediction_data import parse_query, query_result, store
from .rmcab_data import VARIABLES

INK, ACCENT, SECONDARY, GRAY = "#314e62", "#827b10", "#4d7c89", "#85877d"
DAYS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def local_time(value):
    return pd.Timestamp(value).tz_convert("America/Bogota").tz_localize(None)


def style(figure, *, x_title="", y_title="", key="", height=430):
    figure.update_layout(
        template="plotly_white", autosize=True, height=height,
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(family="Oswald, sans-serif", size=14, color="#50534d"),
        margin=dict(l=58, r=22, t=30, b=100),
        xaxis=dict(title=x_title, automargin=True, gridcolor="#eeeeE7"),
        yaxis=dict(title=y_title, automargin=True, gridcolor="#eeeeE7", zerolinecolor="#d5d5ca"),
        legend=dict(orientation="h", x=0, y=-0.28, font=dict(size=12)),
        hoverlabel=dict(font=dict(family="Oswald, sans-serif", size=14)), uirevision=key,
    )
    return figure


def empty(message):
    figure = style(go.Figure(), height=300)
    figure.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return figure


def timeline(result, params):
    label, unit = VARIABLES[params["variable"]]
    figure = go.Figure()
    data, _, _ = store()
    names = data.drop_duplicates("station_id", keep="last").set_index("station_id").station_label
    for points, name, color, dash in [
        (result["series"], names[params["station"]], INK, "solid"),
        (result["comparison_series"], names[params["comparison"]], SECONDARY, "dash"),
    ][:2 if params["view"] == "comparison" else 1]:
        figure.add_trace(go.Scatter(x=[local_time(p["time"]) for p in points], y=[p["value"] for p in points],
            mode="lines+markers", name=name, connectgaps=False, marker=dict(size=3), line=dict(color=color, width=2, dash=dash),
            hovertemplate="%{x|%d/%m/%Y %H:%M}<br>%{y:.2f} " + unit + "<extra>%{fullData.name}</extra>"))
    fc = result["forecast"] if params["view"] == "evolution" else None
    if fc:
        x = [local_time(fc["time"])]
        for name, value, color, symbol in [
            (f"HGB a +{params['horizon']} h", fc["value"], ACCENT, "circle"),
            ("Persistencia", fc["baseline"], GRAY, "x"),
            ("Observado después", fc["observed_after"], INK, "square-open"),
        ]:
            visible = "legendonly" if name == "Observado después" and params.get("show_observed") == "0" else True
            figure.add_trace(go.Scatter(x=x, y=[value], mode="markers", name=name, visible=visible,
                marker=dict(color=color, symbol=symbol, size=12),
                hovertemplate="%{x|%d/%m/%Y %H:%M}<br>%{y:.2f} " + unit + "<extra>%{fullData.name}</extra>"))
        figure.add_vline(x=local_time(result["origin"]).timestamp() * 1000, line_dash="dot", line_color="#bebfb1")
    figure = style(figure, x_title="Hora de Bogotá (UTC−5)", y_title=f"{label} ({unit})", key=str(params))
    figure.update_layout(hovermode="closest")
    figure.update_xaxes(tickformat="%d/%m<br>%H:%M")
    return figure, "Acerca con zoom, arrastra para explorar y pulsa una leyenda para ocultar una serie. Las estimaciones son puntos futuros; los huecos del histórico permanecen vacíos."


def relationship(result, params):
    if not result["scatter"]:
        return empty("No hay mediciones coincidentes"), "Selecciona otra estación o un periodo con ambas variables presentes."
    label, unit = VARIABLES[params["variable"]]
    related, related_unit = VARIABLES[params["related"]]
    figure = go.Figure(go.Scattergl(x=[p["x"] for p in result["scatter"]], y=[p["y"] for p in result["scatter"]],
        customdata=[local_time(p["time"]).strftime("%d/%m/%Y %H:%M") for p in result["scatter"]], mode="markers",
        marker=dict(color=ACCENT, opacity=0.6, size=7),
        hovertemplate="%{customdata}<br>" + related + ": %{x:.2f} " + related_unit + "<br>" + label + ": %{y:.2f} " + unit + "<extra></extra>"))
    return style(figure, x_title=f"{related} ({related_unit})", y_title=f"{label} ({unit})", key=str(params)), "Cada punto une valores del mismo lugar y hora. En datos con tratamiento, el clima puede proceder de ERA5; una correlación no demuestra causalidad."


def heatmap(result, params):
    label, unit = VARIABLES[params["variable"]]
    values = [[next(p["value"] for p in result["heatmap"] if p["day"] == day and p["block"] == hour) for hour in range(8)] for day in range(7)]
    counts = [[next(p["n"] for p in result["heatmap"] if p["day"] == day and p["block"] == hour) for hour in range(8)] for day in range(7)]
    figure = go.Figure(go.Heatmap(z=values, x=[f"{h:02d}–{h+3:02d}" for h in range(0, 24, 3)], y=DAYS,
        customdata=counts, hoverongaps=False, colorscale=[[0, "#f3f2dc"], [0.5, "#d4c85c"], [1, "#726613"]],
        colorbar=dict(title=unit, thickness=12, len=0.85),
        hovertemplate="%{y} · %{x} h<br>%{z:.2f} " + unit + "<br>%{customdata} mediciones<extra></extra>"))
    figure = style(figure, x_title="Bloque horario · Bogotá", y_title="Día de la semana", key=str(params))
    figure.update_layout(yaxis_autorange="reversed", margin=dict(l=42, r=65, t=20, b=60))
    return figure, "El color muestra el agregado de valores presentes por bloque de tres horas. En datos con tratamiento, el clima puede proceder de ERA5. Las celdas vacías no representan ceros."


def evaluation(station, variable, horizon):
    _, forecasts, _ = store()
    return forecasts.loc[forecasts.station_id.eq(station) & forecasts.target.eq(variable) & forecasts.horizon_hours.eq(horizon)].copy()


def diagnostic(params, kind):
    part = evaluation(params["station"], params["variable"], int(params["horizon"]))
    if part.empty:
        return empty("No hay pronósticos evaluados para esta selección"), "La evaluación de HGB está disponible para PM2.5 y PM10 en estaciones con resultados."
    unit = VARIABLES[params["variable"]][1]
    error = part.y_pred - part.y_true
    dates = part.target_datetime.dt.tz_localize(None).dt.strftime("%d/%m/%Y %H:%M")
    scope = f"{len(part)} pronósticos · estación seleccionada · {store()[2].get('evaluation_label', 'evaluación histórica')}. "
    if kind == "residual":
        figure = go.Figure(go.Histogram(x=error, nbinsx=20, name="Error firmado", marker_color=ACCENT,
            hovertemplate="Error: %{x:.2f} " + unit + "<br>%{y} pronósticos<extra></extra>"))
        figure.add_vline(x=0, line_dash="dash", line_color=INK)
        return style(figure, x_title=f"Estimado − observado ({unit})", y_title="Número de pronósticos", key=str(params)+kind), scope + "A la derecha de cero el modelo sobreestima; a la izquierda subestima. Se evalúa error histórico, no incertidumbre futura."
    if kind in {"horizon", "box"}:
        groups = {h: evaluation(params["station"], params["variable"], h).set_index("target_datetime") for h in (24, 48, 72)}
        common = groups[24].index.intersection(groups[48].index).intersection(groups[72].index)
        if not len(common):
            return empty("No hay objetivos comunes entre los tres horizontes"), "No se comparan promedios calculados sobre fechas diferentes."
        figure = go.Figure()
        if kind == "horizon":
            for method, color, name in [("y_pred", ACCENT, "HGB"), ("baseline", GRAY, "Persistencia")]:
                values = [float((groups[h].loc[common, method] - groups[h].loc[common, "y_true"]).abs().mean()) for h in (24, 48, 72)]
                figure.add_trace(go.Bar(x=["24 h", "48 h", "72 h"], y=values, name=name, marker_color=color,
                    hovertemplate="%{x}<br>MAE: %{y:.2f} " + unit + "<extra>%{fullData.name}</extra>"))
            figure.update_layout(barmode="group")
            caption = "Menor MAE es mejor. Persistencia repite el valor del origen: sirve como referencia sencilla para HGB."
            ylabel = f"Error absoluto medio ({unit})"
        else:
            for h in (24, 48, 72):
                frame = groups[h].loc[common]
                figure.add_trace(go.Box(y=frame.y_pred - frame.y_true, name=f"{h} h", boxpoints="outliers", marker_color=ACCENT))
            figure.add_hline(y=0, line_dash="dash", line_color=INK)
            caption = "La caja resume cuartiles y mediana del error; los puntos muestran valores alejados. No es un intervalo de predicción."
            ylabel = f"Estimado − observado ({unit})"
        return style(figure, x_title="Antelación", y_title=ylabel, key=str(params)+kind), f"Se comparan los mismos {len(common)} objetivos observados en los tres horizontes. " + caption
    limit = max(1, float(max(part.y_pred.max(), part.y_true.max()))) * 1.08
    figure = go.Figure(go.Scatter(x=part.y_true, y=part.y_pred, mode="markers", customdata=dates,
        marker=dict(color=ACCENT, size=7, opacity=0.65), name="Pronósticos",
        hovertemplate="%{customdata}<br>Observado: %{x:.2f}<br>Estimado: %{y:.2f} " + unit + "<extra></extra>"))
    figure.add_trace(go.Scatter(x=[0, limit], y=[0, limit], mode="lines", name="Coincidencia exacta", line=dict(color=GRAY, dash="dash"), hoverinfo="skip"))
    origin = pd.Timestamp(f"{params['date']}T{params['hour']}", tz="America/Bogota")
    selected = part.loc[part.datetime.eq(origin)]
    figure.add_trace(go.Scatter(x=selected.y_true, y=selected.y_pred, mode="markers", name="Consulta seleccionada", marker=dict(symbol="diamond-open", color=INK, size=14, line=dict(width=2))))
    figure = style(figure, x_title=f"Observado ({unit})", y_title=f"Estimado HGB ({unit})", key=str(params)+kind)
    figure.update_xaxes(range=[0, limit], constrain="domain")
    figure.update_yaxes(range=[0, limit], scaleanchor="x", scaleratio=1)
    return figure, scope + "Cerca de la diagonal, estimación y medición coinciden. Por encima se sobreestima y por debajo se subestima. El rombo identifica tu consulta."


def render(params, kind="parity"):
    parsed = parse_query(params)
    if parsed["view"] == "diagnostics":
        return diagnostic(params, kind)
    result = query_result(params)
    if parsed["view"] == "relationship":
        return relationship(result, params)
    if parsed["view"] == "hourly":
        return heatmap(result, params)
    return timeline(result, params)
