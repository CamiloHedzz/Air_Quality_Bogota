import { useLanguage } from "../i18n/useLanguage";
import { useEffect, useState } from "react";
import { queryString, usePredictionData } from "./usePredictionData";
import { PredictionPlot } from "./PredictionPlot";
import "../assets/styles/predictions.css";

const views = [{ value: "evolution", label: "Pronóstico HGB" }, { value: "comparison", label: "Comparar estaciones" },
  { value: "relationship", label: "Relación entre variables" }, { value: "hourly", label: "Por día y hora" }, { value: "diagnostics", label: "Evaluar el modelo" }];
const statistics = { mean: "Promedio", median: "Mediana", max: "Máximo" };
const formatValue = (value, locale) => value == null ? "Sin dato" : new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(value);
const formatDate = (value, locale) => new Intl.DateTimeFormat(locale, { timeZone: "America/Bogota", day: "numeric", month: "short", year: "numeric" }).format(new Date(`${value}T12:00:00-05:00`));
const formatInstant = (value, locale) => new Intl.DateTimeFormat(locale, { timeZone: "America/Bogota", dateStyle: "medium", timeStyle: "short", hour12: false }).format(new Date(value));

export function Predictions() {
  const { localize, locale } = useLanguage();
  const fmt = value => formatValue(value, locale);
  const dateLabel = value => formatDate(value, locale);
  const instantLabel = value => formatInstant(value, locale);

  const [view, setView] = useState("evolution");
  const [showObserved, setShowObserved] = useState(true);
  const [page, setPage] = useState(0);
  const { catalog, settings, available, result, applied, busy, error, update, apply, retry } = usePredictionData(view);
  useEffect(() => { setPage(0); }, [result]);
  if (!catalog || !settings) return localize(<main className="predictions-page"><section className="prediction-panel" aria-live="polite">
    <h2>Conectando con los datos del aire</h2>{error ? <><p role="alert">{error}</p><button className="prediction-retry" onClick={retry}>Reintentar conexión</button></> : <p>Cargando estaciones y resultados históricos de HistGradientBoosting…</p>}
  </section></main>);

  const variable = catalog.variables.find(v => v.value === settings.variable);
  const context = applied ? {
    ...applied, label: catalog.variables.find(v => v.value === applied.variable).label,
    unit: catalog.variables.find(v => v.value === applied.variable).unit,
    stationLabel: catalog.stations.find(s => s.value === applied.station)?.label,
    comparisonLabel: catalog.stations.find(s => s.value === applied.comparison)?.label,
    relatedLabel: catalog.variables.find(v => v.value === applied.related)?.label,
    relatedUnit: catalog.variables.find(v => v.value === applied.related)?.unit,
    statisticLabel: statistics[applied.statistic],
  } : null;
  const predicting = ["evolution", "diagnostics"].includes(view) && variable.forecast;
  const changed = applied && Object.keys(settings).some(key => settings[key] !== applied[key]);
  const years = [...new Set(available?.dates.map(d => d.slice(0, 4)) || [])];
  const ready = Boolean(available?.hours[settings.date]?.includes(settings.hour));
  const title = view === "diagnostics" ? "¿Qué tan cerca estuvo el modelo?" : view === "comparison" ? "La misma variable, dos estaciones" : view === "relationship" ? "Explora las relaciones" : view === "hourly" ? "Encuentra patrones en el histórico" : predicting ? "Recrea un pronóstico de calidad del aire" : "Explora las mediciones meteorológicas";
  const fc = result?.forecast;
  let metrics = [];
  if (result && context) {
    if (result.diagnostics) metrics = [
      { label: "Error absoluto medio · MAE", value: result.diagnostics.mae, unit: context.unit, detail: `Persistencia: ${fmt(result.diagnostics.baseline_mae)} ${context.unit}` },
      { label: "Sesgo medio", value: result.diagnostics.bias, unit: context.unit, detail: "Positivo: sobreestima · negativo: subestima" },
      { label: "Pronósticos evaluados", value: result.diagnostics.n, unit: "", detail: `Esta estación · +${applied.horizon} h · 25–31 mar. 2025` },
    ];
    else if (fc) metrics = [
      { label: `Estimación a +${applied.horizon} h`, value: fc.value, unit: context.unit, detail: "HistGradientBoosting" },
      { label: "Medición posterior", value: fc.observed_after, unit: context.unit, detail: `Error de este punto: ${fmt(fc.absolute_error)} ${context.unit}` },
      { label: "MAE histórico · esta estación", value: fc.station_score?.mae, unit: context.unit, detail: `${fc.station_score?.n || 0} pronósticos en la semana evaluada` },
    ];
    else if (view === "relationship") metrics = [
      { label: "Correlación de Pearson", value: result.metrics.correlation, unit: "", detail: "Sin cálculo si no hay pares o variación" },
      { label: "Mediciones emparejadas", value: result.metrics.paired_values, unit: "", detail: "Misma estación, fecha y hora" },
      { label: "Cobertura de la variable", value: result.metrics.coverage_pct, unit: "%", detail: `${result.metrics.observed} de ${result.metrics.expected_hours} horas` },
    ];
    else metrics = [
      { label: `${context.statisticLabel} histórico`, value: result.metrics.statistic, unit: context.unit, detail: `${result.metrics.observed} mediciones presentes` },
      { label: view === "comparison" ? "Diferencia emparejada A − B" : "Máximo histórico", value: view === "comparison" ? result.metrics.comparison_difference : result.metrics.max, unit: context.unit,
        detail: view === "comparison" ? `${result.metrics.comparison_pairs} horas coincidentes` : "Ventana anterior al origen" },
      { label: "Cobertura de la variable", value: result.metrics.coverage_pct, unit: "%", detail: `${result.metrics.observed} de ${result.metrics.expected_hours} horas` },
    ];
  }

  function change(event) {
    if (event.target.name === "variable" && view === "diagnostics" && !catalog.variables.find(item => item.value === event.target.value).forecast) setView("evolution");
    update(event.target.name, event.target.value);
  }
  function submit(event) { event.preventDefault(); apply(); }

  return localize(<main className="predictions-page">
    <div className="predictions-intro"><div><p className="predictions-eyebrow">De los datos a una estimación</p><h2>Explora y predice el aire de Bogotá</h2><p>Mediciones reales, pronósticos históricos y más perspectivas para tu análisis.</p></div>
      <span className="predictions-preview-badge"><span aria-hidden="true" />HGB · experimental</span></div>

    <details className="prediction-coverage">
      <summary>Histórico 2015–2025 · cobertura parcial · {catalog.coverage.report_days} reportes diarios</summary>
      <p><strong>Modelo actual:</strong> entrenado y evaluado con datos de enero–marzo de 2025. La colección completa de 2015–2025 sigue pendiente; los demás años tienen fechas aisladas.</p>
      <p>Las consultas recrean pronósticos del pasado. La calidad final de las mediciones publicadas no se ha verificado aquí.</p>
      <div className="prediction-data-scroll"><table><caption className="prediction-sr-only">Cobertura real por año del conjunto disponible</caption><thead><tr><th>Año</th><th>Reportes diarios</th><th>PM2.5 presentes</th><th>PM10 presentes</th></tr></thead><tbody>{catalog.coverage.years.map(year => <tr key={year.year}><td>{year.year}</td><td>{year.report_days}</td><td>{year.pm_25}</td><td>{year.pm_10}</td></tr>)}</tbody></table></div>
    </details>

    <div className="prediction-view-picker prediction-main-tabs" role="group" aria-label="Tipo de análisis">{views.map(item => <button key={item.value} type="button" aria-pressed={view === item.value} disabled={item.value === "diagnostics" && !variable.forecast} onClick={() => setView(item.value)}>{item.label}</button>)}</div>
    <div className="predictions-layout">
      <section className="prediction-panel prediction-controls" aria-labelledby="prediction-controls-heading">
        <div className="prediction-panel-heading"><span className="prediction-step" aria-hidden="true">01</span><div><h2 id="prediction-controls-heading">Tu consulta</h2><p>Elige una estación y un momento disponible. En «Evaluar el modelo», los gráficos resumen la semana de prueba y el origen destaca un punto.</p></div></div>
        <form className="prediction-form" onSubmit={submit}>
          <div className="prediction-field"><label htmlFor="prediction-station">Estación de monitoreo</label><select id="prediction-station" name="station" value={settings.station} onChange={change}>{catalog.stations.map(station => <option key={station.value} value={station.value}>{station.label}{predicting && !station.forecast ? " · solo histórico" : ""}</option>)}</select><span className="prediction-field-hint">Mediciones de estación; no son promedios por barrio.</span></div>
          <fieldset className="prediction-variables"><legend>Variable de análisis</legend><div className="prediction-variable-options">{catalog.variables.map(item => <label className="prediction-variable" key={item.value}>
            <input type="radio" name="variable" value={item.value} checked={settings.variable === item.value} onChange={change} /><span className="prediction-variable-content"><strong>{item.label}</strong><span>{item.forecast ? "Pronóstico e histórico" : "Histórico meteorológico"}</span><small>{item.unit}</small></span></label>)}</div></fieldset>
          <div className="prediction-field"><label htmlFor="prediction-date">{predicting ? "Fecha de origen del pronóstico" : "Fecha final del histórico"}</label><select id="prediction-date" name="date" value={ready ? settings.date : ""} onChange={change} disabled={busy || !available?.dates.length} required>
            {!available?.dates.length && <option value="">Sin fechas disponibles</option>}{years.map(year => <optgroup label={year} key={year}>{available.dates.filter(date => date.startsWith(year)).map(date => <option key={date} value={date}>{dateLabel(date)}</option>)}</optgroup>)}</select></div>
          <div className="prediction-field"><label htmlFor="prediction-hour">Hora de Bogotá (UTC−5)</label><select id="prediction-hour" name="hour" value={ready ? settings.hour : ""} onChange={change} disabled={busy || !ready} required>{!ready && <option value="">Sin horas disponibles</option>}{(available?.hours[settings.date] || []).map(hour => <option key={hour} value={hour}>{hour}</option>)}</select></div>
          {predicting && <div className="prediction-field"><label htmlFor="prediction-horizon">Antelación de la estimación</label><select id="prediction-horizon" name="horizon" value={settings.horizon} onChange={change}>{[24, 48, 72].map(hour => <option key={hour} value={hour}>{hour} horas</option>)}</select><span className="prediction-field-hint">Estimación del valor a +{settings.horizon} h desde el origen.</span></div>}
          <details className="prediction-advanced"><summary>Afina el análisis</summary><div className="prediction-advanced-fields">
            <div className="prediction-field"><label htmlFor="prediction-history">Histórico anterior {view === "diagnostics" ? "(tabla de mediciones)" : ""}</label><select id="prediction-history" name="history" value={settings.history} onChange={change}>{[7, 14, 30, 90].map(days => <option key={days} value={days}>Últimos {days} días</option>)}</select></div>
            <div className="prediction-field"><label htmlFor="prediction-aggregation">Agrupar histórico</label><select id="prediction-aggregation" name="aggregation" value={settings.aggregation} onChange={change} disabled={["relationship", "hourly", "diagnostics"].includes(view)}><option value="hour">Por hora</option><option value="day">Por día</option></select></div>
            <div className="prediction-field"><label htmlFor="prediction-statistic">Estadística</label><select id="prediction-statistic" name="statistic" value={settings.statistic} onChange={change} disabled={["relationship", "diagnostics"].includes(view)}>{Object.entries(statistics).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
          </div></details>
          {view === "comparison" && <div className="prediction-field"><label htmlFor="prediction-comparison">Comparar con</label><select id="prediction-comparison" name="comparison" value={settings.comparison} onChange={change}>{catalog.stations.filter(station => station.value !== settings.station).map(station => <option key={station.value} value={station.value}>{station.label}</option>)}</select></div>}
          {view === "relationship" && <div className="prediction-field"><label htmlFor="prediction-related">Relacionar con</label><select id="prediction-related" name="related" value={settings.related} onChange={change}>{catalog.variables.filter(item => item.value !== settings.variable).map(item => <option key={item.value} value={item.value}>{item.label} ({item.unit})</option>)}</select><span className="prediction-field-hint">Se usan lecturas horarias coincidentes, sin agregación.</span></div>}
          <div className="prediction-form-actions"><button className="prediction-submit" type="submit" disabled={busy || !ready}>{busy ? "Consultando…" : view === "diagnostics" ? "Aplicar evaluación" : predicting ? "Recrear pronóstico" : "Aplicar análisis"}<span aria-hidden="true">↗</span></button><button type="button" className="prediction-reset" disabled={busy} onClick={() => { setView("evolution"); retry(); }}>Restablecer</button></div>
          <p className="prediction-form-status" role="status">{changed ? "Tienes cambios por aplicar. Los resultados visibles corresponden a la consulta anterior." : available && !available.dates.length ? "No hay resultados disponibles para esta combinación. Prueba otra estación o explora el histórico." : "Solo se ofrecen fechas y horas con datos disponibles."}</p>
        </form>
      </section>

      <div className="prediction-results" aria-busy={busy}>
        <section className="prediction-panel prediction-result-panel" aria-labelledby="prediction-results-heading">
          <div className="prediction-result-heading"><div><p className="predictions-eyebrow">Mediciones y resultados calculados</p><h2 id="prediction-results-heading">{title}</h2></div><span className="prediction-variable-badge">{variable.label} · {variable.unit}</span></div>
          {error && <div className="prediction-error" role="alert"><p>{error}</p><button className="prediction-retry" type="button" onClick={apply}>Reintentar consulta</button></div>}
          {busy && <p className="prediction-loading" role="status">Cargando mediciones y resultados…</p>}
          {!busy && !error && !result && <p className="prediction-empty">No hay resultados para esta combinación. Explora el histórico o elige otra estación.</p>}
          {result && context && <>
            <dl className="prediction-summary"><div><dt>Estación</dt><dd>{context.stationLabel}</dd></div><div><dt>Origen</dt><dd>{instantLabel(result.origin)}</dd></div><div><dt>{fc ? "Momento estimado" : "Histórico"}</dt><dd>{fc ? instantLabel(fc.time) : `${applied.history} días anteriores`}</dd></div></dl>
            <div className="prediction-filter-tags"><span>{context.label} · {context.unit}</span><span>{view === "diagnostics" ? "Evaluación: 25–31 mar. 2025" : `Cobertura: ${fmt(result.metrics.coverage_pct)} %`}</span><span>{view === "diagnostics" ? `Esta estación · +${applied.horizon} h` : view === "hourly" ? `${context.statisticLabel} por bloque de 3 h` : view === "relationship" ? "Pares horarios reales" : `${context.statisticLabel} ${applied.aggregation === "hour" ? "por hora" : "por día"}`}</span></div>
            {fc && view === "evolution" && <label className="prediction-toggle"><input type="checkbox" checked={showObserved} onChange={event => setShowObserved(event.target.checked)} />Mostrar la observación posterior en la gráfica</label>}
            <p className="prediction-axis-description">{context.label} · {context.unit}</p>
            <PredictionPlot query={applied} showObserved={showObserved} />
            {fc ? <div className="prediction-model-note"><strong>Pronóstico histórico · {catalog.model.name}</strong><p>El modelo se ajustó con etiquetas anteriores al {instantLabel(fc.training_end)}. La observación posterior se muestra para comparar; no se utilizó como entrada.</p><p>MAE global a {applied.horizon} h: {fmt(fc.global_score.mae)} {context.unit}, sobre {fc.global_score.n} pronósticos de la semana del 25–31 de marzo de 2025. El resultado varía por estación y fecha.</p><a href={fc.source_url} target="_blank" rel="noreferrer">Ver reporte oficial de la observación ↗</a></div> : <p className="prediction-demo-note">Mediciones publicadas por RMCAB. Los valores ausentes permanecen sin dato. {view === "comparison" ? "La diferencia usa únicamente horas presentes en ambas estaciones." : view === "evolution" ? "Humedad y temperatura se analizan como histórico; sus modelos de pronóstico aún no están entrenados." : "Los cálculos utilizan las observaciones presentes en el periodo seleccionado."}</p>}
          </>}
        </section>

        {result && context && <>
          <section className="prediction-metrics" aria-label="Indicadores calculados con datos reales">{metrics.map(metric => <div className="prediction-panel prediction-metric" key={metric.label}><h3>{metric.label}</h3><p>{fmt(metric.value)} <span className="prediction-metric-unit">{metric.unit}</span></p><span className="prediction-metric-status">{metric.detail}</span></div>)}</section>
          <section className="prediction-panel prediction-model-explainer" aria-labelledby="prediction-model-heading">
            <p className="predictions-eyebrow">Entiende lo que estás viendo</p><h2 id="prediction-model-heading">Así aprende el modelo</h2>
            <p>Usamos <strong>HistGradientBoostingRegressor</strong> de scikit-learn. Combina pequeños árboles de decisión: cada uno corrige parte de los errores de los anteriores. Agrupa los valores en intervalos para hacer más eficiente el aprendizaje.</p>
            <ol className="prediction-model-steps">
              <li><span>01 · Lee el contexto</span><p>Estación, PM2.5, PM10, temperatura y humedad disponibles en el origen; además, lecturas previas del contaminante a 1 y 24 horas y señales del calendario.</p></li>
              <li><span>02 · Encuentra patrones</span><p>{catalog.model.iterations} etapas de árboles aprenden de ejemplos históricos. El modelo puede tratar entradas ausentes; los huecos no se convierten en mediciones inventadas.</p></li>
              <li><span>03 · Estima un valor</span><p>Devuelve una concentración de PM2.5 o PM10 a 24, 48 o 72 horas. Es un punto para ese momento; cada horizonte tiene su propio modelo.</p></li>
            </ol>
            <details><summary>Cómo leer sus resultados</summary><p><strong>MAE:</strong> es el promedio de la distancia entre estimación y medición, en µg/m³. Menor es mejor. Un MAE de 6 significa un error absoluto promedio de 6 µg/m³ en los ejemplos evaluados; no garantiza ese margen en cada predicción.</p><p><strong>Persistencia:</strong> repite la concentración del origen. Compararla con HGB permite ver si el modelo mejora esa referencia sencilla.</p><p><strong>Evaluación temporal:</strong> se entrena con etiquetas anteriores al origen y después se compara con lo observado. Las mediciones futuras no se usan como entradas. Los gráficos de error corresponden a los reportes del 25–31 de marzo de 2025.</p></details>
            <p className="prediction-model-references"><a href="https://scikit-learn.org/1.7/modules/ensemble.html#histogram-based-gradient-boosting" target="_blank" rel="noreferrer">Conoce HGB en scikit-learn ↗</a><a href="https://plotly.com/python/ml-regression/" target="_blank" rel="noreferrer">Evaluación de modelos con Plotly ↗</a></p>
            <p className="prediction-model-scope">Modelo actual: enero–marzo de 2025, en estaciones de monitoreo. Esta pantalla reproduce resultados históricos ya calculados. El histórico 2015–2025 aún tiene cobertura parcial; ampliar la colección y evaluar otra época del año sigue pendiente.</p>
          </section>
          <section className="prediction-panel prediction-data-panel" aria-labelledby="prediction-data-heading">
            <div className="prediction-result-heading"><div><p className="predictions-eyebrow">El detalle también cuenta</p><h2 id="prediction-data-heading">Detrás de cada punto</h2></div><span className="prediction-record-count">{result.record_count} registros en el periodo</span></div>
            <p className="prediction-view-description">Mediciones de {context.stationLabel} anteriores al origen. Los campos vacíos se muestran como «Sin dato».</p>
            <div className="prediction-downloads"><a href={`/api/predictions/export/?${queryString(applied, view)}&kind=observations`} download>Mediciones CSV ↓</a>{fc && <a href={`/api/predictions/export/?${queryString(applied, view)}&kind=forecast`} download>Pronóstico CSV ↓</a>}{view === "diagnostics" && <a href={`/api/predictions/export/?${queryString(applied, view)}&kind=evaluation`} download>Evaluación 24/48/72 h CSV ↓</a>}</div>
            <div className="prediction-data-scroll" tabIndex="0" role="region" aria-label="Mediciones reales, desplazable horizontalmente"><table><thead><tr><th scope="col">Fecha y hora</th>{catalog.variables.map(item => <th scope="col" key={item.value}>{item.label}<span>{item.unit}</span></th>)}<th scope="col">Fuente</th></tr></thead><tbody>{result.rows.slice(page * 10, page * 10 + 10).map(row => <tr key={row.time}><td>{instantLabel(row.time)}</td>{catalog.variables.map(item => <td key={item.value}>{fmt(row[item.value])}</td>)}<td><a href={row.source_url} target="_blank" rel="noreferrer">RMCAB ↗</a></td></tr>)}{!result.rows.length && <tr><td colSpan="6">No hay registros en esta ventana.</td></tr>}</tbody></table></div>
            <div className="prediction-pagination"><button type="button" disabled={!page} onClick={() => setPage(n => n - 1)}>Anterior</button><span>{result.rows.length ? page * 10 + 1 : 0}–{Math.min((page + 1) * 10, result.rows.length)} de los últimos {result.rows.length} registros</span><button type="button" disabled={(page + 1) * 10 >= result.rows.length} onClick={() => setPage(n => n + 1)}>Siguiente</button></div>
            <p className="prediction-chart-hint">El CSV incluye el periodo completo de la consulta, las cuatro variables y su procedencia.</p>
          </section>
        </>}
      </div>
    </div>
  </main>);
}
