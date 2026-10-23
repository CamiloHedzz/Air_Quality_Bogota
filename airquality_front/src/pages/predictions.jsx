import { useState } from "react";
import "../assets/styles/predictions.css";

const zones = ["La Merced Norte", "Palo Blanco", "Quirigua II", "Acacias Usaquén"];
const variables = [
  { value: "pm25", label: "PM2.5", description: "Partículas finas", unit: "µg/m³", group: "Partículas" },
  { value: "pm10", label: "PM10", description: "Partículas gruesas", unit: "µg/m³", group: "Partículas" },
  { value: "humidity", label: "Humedad", description: "Humedad relativa", unit: "%", group: "Clima" },
  { value: "temperature", label: "Temperatura", description: "Temperatura del aire", unit: "°C", group: "Clima" },
];
const views = [
  { value: "evolution", label: "Evolución", question: "¿Cómo podría cambiar esta variable en las próximas horas?", description: "Explora el histórico y la proyección, junto con su rango estimado." },
  { value: "comparison", label: "Comparar zonas", question: "¿Cómo se comporta la misma variable en dos barrios?", description: "Compara ambas zonas en el mismo periodo y con la misma unidad." },
  { value: "relationship", label: "Relación entre variables", question: "¿Cómo se relacionan estas dos variables?", description: "Explora cómo se distribuyen dos variables. Una relación no implica que una cause la otra." },
  { value: "hourly", label: "Por día y hora", question: "¿En qué días y horas se concentran los cambios?", description: "Busca patrones semanales a partir de los registros históricos." },
];
const statistics = { mean: "Promedio", median: "Mediana", max: "Máximo" };
const weekdays = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];
const hourBlocks = ["00–03", "03–06", "06–09", "09–12", "12–15", "15–18", "18–21", "21–24"];
const heatPattern = [
  [0, 0, 2, 3, 1, 2, 4, 1], [0, 1, 3, 2, 1, 3, 4, 2], [1, 0, 4, 3, 2, 2, 3, 1],
  [0, 1, 3, 2, 1, 3, 4, 2], [1, 1, 4, 3, 2, 4, 3, 2], [0, 0, 1, 2, 2, 3, 2, 1], [0, 0, 1, 1, 2, 1, 2, 0],
];

function initialSettings() {
  const today = new Date();
  const date = [today.getFullYear(), String(today.getMonth() + 1).padStart(2, "0"), String(today.getDate()).padStart(2, "0")].join("-");
  return { zone: zones[0], variable: "pm25", horizon: "24", date, history: "7", aggregation: "hour", statistic: "mean" };
}

function renderChartGrid() {
  return (
    <g className="prediction-chart-grid">
      {[30, 80, 130, 180, 230].map(y => <line key={`y-${y}`} x1="0" y1={y} x2="760" y2={y} />)}
      {[0, 190, 380, 570, 760].map(x => <line key={`x-${x}`} x1={x} y1="10" x2={x} y2="240" />)}
    </g>
  );
}

function renderTimeline(preview, comparisonZone, showBand) {
  const comparing = Boolean(comparisonZone);
  const hours = Number(preview.horizon);
  return (
    <>
      <svg className="prediction-chart-drawing" viewBox="0 0 760 250" preserveAspectRatio="none" role="img"
        aria-label={comparing ? "Ejemplo visual de dos series de barrios, sin mediciones reales" : "Ejemplo visual del histórico y su proyección, sin predicción real"}>
        {renderChartGrid()}
        {comparing ? (
          <>
            <path className="prediction-chart-primary" d="M0 188 C40 188 55 110 110 140 S210 180 270 125 S360 90 420 115 S540 150 600 85 S710 70 760 92" />
            <path className="prediction-chart-secondary" d="M0 125 C55 70 70 110 130 100 S230 140 290 170 S380 145 440 170 S530 105 610 130 S705 190 760 155" />
          </>
        ) : (
          <>
            {showBand && <path className="prediction-chart-band" d="M190 130 C250 90 270 60 330 75 S430 55 500 68 S620 18 760 40 L760 143 C620 125 580 175 500 155 S395 157 330 160 S250 185 190 130 Z" />}
            <path className="prediction-chart-history" d="M0 188 C28 188 28 145 55 155 S100 211 123 170 S160 105 190 130" />
            <line className="prediction-chart-divider" x1="190" y1="10" x2="190" y2="240" />
            <path className="prediction-chart-projection" d="M190 130 C250 138 275 105 330 116 S435 105 500 111 S620 72 760 92" />
            <circle className="prediction-chart-point" cx="190" cy="130" r="5" />
          </>
        )}
      </svg>
      <div className="prediction-chart-axis" aria-hidden="true">
        {(comparing ? [`−${preview.history} días`, "", "", "", "Inicio"] : [`−${preview.history} días`, "Inicio", `+${hours / 3} h`, `+${hours * 2 / 3} h`, `+${hours} h`]).map((label, index) => <span key={index}>{label}</span>)}
      </div>
      <ul className="prediction-chart-legend" aria-label="Leyenda de la gráfica de ejemplo">
        {comparing ? (
          <>
            <li><span className="prediction-legend-primary" aria-hidden="true" />{preview.zone}</li>
            <li><span className="prediction-legend-secondary" aria-hidden="true" />{comparisonZone}</li>
          </>
        ) : (
          <>
            <li><span className="prediction-legend-history" aria-hidden="true" />Histórico</li>
            <li><span className="prediction-legend-projection" aria-hidden="true" />Proyección</li>
            {showBand && <li><span className="prediction-legend-range" aria-hidden="true" />Rango estimado</li>}
          </>
        )}
      </ul>
    </>
  );
}

function renderRelationship(variable, related) {
  return (
    <div className="prediction-scatter">
      <p className="prediction-axis-description">Eje Y · {variable.label} ({variable.unit})</p>
      <svg className="prediction-chart-drawing" viewBox="0 0 760 250" preserveAspectRatio="none" role="img"
        aria-label={`Dispersión ilustrativa de ${variable.label} frente a ${related.label}, sin datos ni correlación calculada`}>
        {renderChartGrid()}
        {Array.from({ length: 40 }, (_, index) => (
          <circle className="prediction-scatter-point" key={index} cx={25 + ((index * 67) % 710)} cy={35 + ((index * 43 + Math.floor(index / 4) * 29) % 185)} r={4 + index % 3} />
        ))}
      </svg>
      <p className="prediction-axis-description prediction-axis-description--x">Eje X · {related.label} ({related.unit})</p>
      <p className="prediction-chart-hint">Cada punto representará dos mediciones tomadas en el mismo lugar y momento.</p>
    </div>
  );
}

function renderHourlyPattern(variable) {
  return (
    <div className="prediction-heatmap">
      <div className="prediction-heatmap-scroll" tabIndex="0" role="region" aria-label="Ejemplo de patrón semanal, desplazable en pantallas pequeñas">
        <table>
          <caption className="prediction-sr-only">Patrón ilustrativo de {variable.label}. Los colores no representan mediciones reales.</caption>
          <thead><tr><th scope="col">Día / hora</th>{hourBlocks.map(hour => <th scope="col" key={hour}>{hour}</th>)}</tr></thead>
          <tbody>{weekdays.map((day, dayIndex) => (
            <tr key={day}><th scope="row">{day}</th>{heatPattern[dayIndex].map((level, index) => (
              <td key={index}><span className={`prediction-heat-cell prediction-heat-cell--${level}`} title={`${day}, ${hourBlocks[index]} h · color ilustrativo, sin medición`}><span className="prediction-sr-only">Sin medición</span></span></td>
            ))}</tr>
          ))}</tbody>
        </table>
      </div>
      <div className="prediction-heat-legend"><span>Menor</span><span className="prediction-heat-scale" aria-hidden="true" /><span>Mayor</span></div>
      <p className="prediction-chart-hint">Intensidad ilustrativa · bloques de 3 horas · histórico de {variable.label}</p>
    </div>
  );
}

export function Predictions() {
  const [settings, setSettings] = useState(initialSettings);
  const [preview, setPreview] = useState(settings);
  const [notice, setNotice] = useState("");
  const [activeView, setActiveView] = useState("evolution");
  const [comparisonZone, setComparisonZone] = useState(zones[1]);
  const [relatedVariable, setRelatedVariable] = useState("humidity");
  const [showBand, setShowBand] = useState(true);
  const changed = Object.keys(settings).some(key => settings[key] !== preview[key]);
  const variable = variables.find(item => item.value === preview.variable);
  const related = variables.find(item => item.value === relatedVariable && item.value !== preview.variable) || variables.find(item => item.value !== preview.variable);
  const view = views.find(item => item.value === activeView);
  const dateLabel = new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "short", year: "numeric" }).format(new Date(`${preview.date}T12:00:00`));
  const statisticLabel = `${statistics[preview.statistic]} ${preview.aggregation === "hour" ? "por hora" : "por día"}`;
  const metricLabels = activeView === "relationship"
    ? [{ label: "Correlación", unit: "" }, { label: "Mediciones emparejadas", unit: "" }, { label: "Cobertura de datos", unit: "%" }]
    : [{ label: `${statistics[preview.statistic]} de ${variable.label}`, unit: variable.unit }, { label: activeView === "comparison" ? "Diferencia entre zonas" : activeView === "hourly" ? "Máximo histórico" : "Máximo esperado", unit: variable.unit }, { label: "Cobertura de datos", unit: "%" }];

  function updateSettings(event) {
    const { name, value } = event.target;
    setSettings(current => ({ ...current, [name]: value }));
    setNotice("");
  }

  function updatePreview(event) {
    event.preventDefault();
    setPreview({ ...settings });
    if (comparisonZone === settings.zone) setComparisonZone(zones.find(zone => zone !== settings.zone));
    setNotice(`Vista previa actualizada: ${settings.zone}, ${variables.find(item => item.value === settings.variable).label}, ${settings.horizon} horas.`);
  }

  function resetSettings() {
    const defaults = initialSettings();
    setSettings(defaults);
    setPreview(defaults);
    setActiveView("evolution");
    setComparisonZone(zones[1]);
    setRelatedVariable("humidity");
    setShowBand(true);
    setNotice("Consulta restablecida.");
  }

  return (
    <main className="predictions-page">
      <div className="predictions-intro">
        <div>
          <p className="predictions-eyebrow">Más perspectivas, mejores preguntas</p>
          <h2>Explora el aire desde cada ángulo</h2>
          <p>Partículas, clima y patrones de Bogotá en un mismo espacio de análisis.</p>
        </div>
        <span className="predictions-preview-badge"><span aria-hidden="true" />Vista previa</span>
      </div>

      <div className="predictions-layout">
        <section className="prediction-panel prediction-controls" aria-labelledby="prediction-controls-heading">
          <div className="prediction-panel-heading">
            <span className="prediction-step" aria-hidden="true">01</span>
            <div><h2 id="prediction-controls-heading">Tu escenario</h2><p>Elige qué, dónde y cuándo explorar.</p></div>
          </div>
          <form className="prediction-form" onSubmit={updatePreview}>
            <div className="prediction-field">
              <label htmlFor="prediction-zone">Zona de Bogotá</label>
              <select id="prediction-zone" name="zone" value={settings.zone} onChange={updateSettings}>
                {zones.map(zone => <option key={zone} value={zone}>{zone}</option>)}
              </select>
              <span className="prediction-field-hint">Zonas de ejemplo para esta vista previa.</span>
            </div>

            <fieldset className="prediction-variables">
              <legend>Variable de análisis</legend>
              {["Partículas", "Clima"].map(group => (
                <div className="prediction-variable-group" key={group}>
                  <p>{group}</p>
                  <div className="prediction-variable-options">
                    {variables.filter(item => item.group === group).map(item => (
                      <label className="prediction-variable" key={item.value}>
                        <input type="radio" name="variable" value={item.value} checked={settings.variable === item.value} onChange={updateSettings} />
                        <span className="prediction-variable-content"><strong>{item.label}</strong><span>{item.description}</span><small>{item.unit}</small></span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </fieldset>

            <div className="prediction-field">
              <label htmlFor="prediction-date">Inicio de la proyección</label>
              <input id="prediction-date" type="date" name="date" value={settings.date} onChange={updateSettings} required />
            </div>
            <div className="prediction-field">
              <label htmlFor="prediction-horizon">Horizonte de predicción</label>
              <select id="prediction-horizon" name="horizon" value={settings.horizon} onChange={updateSettings}>
                <option value="24">24 horas</option><option value="48">48 horas</option><option value="72">72 horas</option>
              </select>
            </div>
            <details className="prediction-advanced">
              <summary>Afina el análisis <span>3 filtros</span></summary>
              <div className="prediction-advanced-fields">
                <div className="prediction-field">
                  <label htmlFor="prediction-history">Histórico anterior al inicio</label>
                  <select id="prediction-history" name="history" value={settings.history} onChange={updateSettings}>
                    <option value="7">Últimos 7 días</option><option value="14">Últimos 14 días</option><option value="30">Últimos 30 días</option><option value="90">Últimos 90 días</option>
                  </select>
                </div>
                <div className="prediction-field">
                  <label htmlFor="prediction-aggregation">Agrupar mediciones</label>
                  <select id="prediction-aggregation" name="aggregation" value={settings.aggregation} onChange={updateSettings}>
                    <option value="hour">Por hora</option><option value="day">Por día</option>
                  </select>
                </div>
                <div className="prediction-field">
                  <label htmlFor="prediction-statistic">Estadística</label>
                  <select id="prediction-statistic" name="statistic" value={settings.statistic} onChange={updateSettings}>
                    {Object.entries(statistics).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                </div>
              </div>
            </details>
            <div className="prediction-form-actions">
              <button className="prediction-submit" type="submit">Aplicar a la vista previa <span aria-hidden="true">↗</span></button>
              <button className="prediction-reset" type="button" onClick={resetSettings}>Restablecer</button>
            </div>
            <p className="prediction-form-status" role="status">{changed ? "Tienes cambios por aplicar a la vista previa." : notice}</p>
          </form>
        </section>

        <div className="prediction-results">
          <section className="prediction-panel prediction-result-panel" aria-labelledby="prediction-results-heading">
            <div className="prediction-result-heading">
              <div><p className="predictions-eyebrow">De una pregunta a una perspectiva</p><h2 id="prediction-results-heading">Tu espacio de análisis</h2></div>
              <span className="prediction-variable-badge">{variable.label} · {variable.unit}</span>
            </div>
            <dl className="prediction-summary">
              <div><dt>Zona</dt><dd>{preview.zone}</dd></div><div><dt>Inicio</dt><dd>{dateLabel}</dd></div><div><dt>Proyección</dt><dd>{preview.horizon} horas</dd></div>
            </dl>
            <div className="prediction-view-picker" role="group" aria-label="Tipo de análisis">
              {views.map(item => <button key={item.value} type="button" aria-pressed={activeView === item.value} aria-controls="prediction-view" onClick={() => setActiveView(item.value)}>{item.label}</button>)}
            </div>

            <div id="prediction-view" className="prediction-analysis-view" aria-labelledby="prediction-view-heading">
              <h3 id="prediction-view-heading">{view.question}</h3>
              <p className="prediction-view-description">{view.description}</p>
              <div className="prediction-view-toolbar">
                {activeView === "evolution" && <label className="prediction-toggle"><input type="checkbox" checked={showBand} onChange={event => setShowBand(event.target.checked)} />Mostrar rango estimado</label>}
                {activeView === "comparison" && <div className="prediction-field"><label htmlFor="prediction-comparison">Comparar {preview.zone} con</label><select id="prediction-comparison" value={comparisonZone} onChange={event => setComparisonZone(event.target.value)}>{zones.filter(zone => zone !== preview.zone).map(zone => <option key={zone}>{zone}</option>)}</select></div>}
                {activeView === "relationship" && <div className="prediction-field"><label htmlFor="prediction-related">Relacionar {variable.label} con</label><select id="prediction-related" value={related.value} onChange={event => setRelatedVariable(event.target.value)}>{variables.filter(item => item.value !== preview.variable).map(item => <option key={item.value} value={item.value}>{item.label} ({item.unit})</option>)}</select></div>}
                <span className="prediction-example-label">Ejemplo visual</span>
              </div>
              <div className="prediction-filter-tags" aria-label="Configuración de la vista">
                <span>Histórico: {preview.history} días</span>
                <span>{activeView === "hourly" ? `${statistics[preview.statistic]} por bloque de 3 h` : statisticLabel}</span>
                {activeView === "relationship" && <span>Mediciones coincidentes</span>}
              </div>
              <div className="prediction-chart">
                {activeView !== "relationship" && <p className="prediction-axis-description">{variable.label} · {variable.unit}</p>}
                {activeView === "evolution" && renderTimeline(preview, null, showBand)}
                {activeView === "comparison" && renderTimeline(preview, comparisonZone, false)}
                {activeView === "relationship" && renderRelationship(variable, related)}
                {activeView === "hourly" && renderHourlyPattern(variable)}
              </div>
            </div>
            <p className="prediction-demo-note">Gráficas ilustrativas para revisar el diseño. Los filtros configuran la vista previa; todavía no calculan análisis ni predicciones reales.</p>
          </section>

          <section className="prediction-metrics" aria-label="Indicadores pendientes de conectar a datos">
            {metricLabels.map(metric => (
              <div className="prediction-panel prediction-metric" key={metric.label}>
                <h3>{metric.label}</h3><p><span aria-label="Sin calcular">—</span> <span className="prediction-metric-unit">{metric.unit}</span></p><span className="prediction-metric-status">Sin calcular</span>
              </div>
            ))}
          </section>

          <section className="prediction-panel prediction-data-panel" aria-labelledby="prediction-data-heading">
            <div className="prediction-result-heading"><div><p className="predictions-eyebrow">El detalle también cuenta</p><h2 id="prediction-data-heading">Detrás de cada punto</h2></div><span className="prediction-record-count">0 registros conectados</span></div>
            <p className="prediction-view-description">Consulta las mediciones que darán origen al análisis, con las cuatro variables en una misma tabla.</p>
            <div className="prediction-data-scroll" tabIndex="0" role="region" aria-label="Tabla de mediciones, desplazable horizontalmente">
              <table><thead><tr><th scope="col">Fecha y hora</th><th scope="col">Zona</th>{variables.map(item => <th scope="col" key={item.value}>{item.label}<span>{item.unit}</span></th>)}</tr></thead><tbody><tr><td colSpan="6">Los registros aparecerán aquí cuando conectemos los datos.</td></tr></tbody></table>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
