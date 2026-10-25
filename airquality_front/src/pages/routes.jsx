import { useEffect, useRef, useState } from "react";
import { useLanguage } from "../i18n/useLanguage";
import { RoutePlaceField } from "./RoutePlaceField";
import { RouteMap } from "./RouteMap";
import { RoutesHero } from "../components/RoutesHero";
import { routeRequest } from "./routeApi";
import "../assets/styles/routes.css";

const exampleOrigin = { text: "Parque Simón Bolívar", place: { label: "Parque Simón Bolívar", coordinates: [-74.0937, 4.6584] } };
const exampleDestination = { text: "Parque Nacional", place: { label: "Parque Nacional", coordinates: [-74.0653, 4.6226] } };
const days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
const priorities = [{ value: "balanced", label: "Equilibrio" }, { value: "exposure", label: "Menor exposición" }, { value: "fastest", label: "Menor tiempo" }];

export function RoutesPage() {
  const { localize, locale } = useLanguage();
  const [origin, setOrigin] = useState(exampleOrigin);
  const [destination, setDestination] = useState(exampleDestination);
  const [time, setTime] = useState("07:00");
  const [day, setDay] = useState("0");
  const [variable, setVariable] = useState("pm_25");
  const [priority, setPriority] = useState("balanced");
  const [result, setResult] = useState(null);
  const [applied, setApplied] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [changed, setChanged] = useState(false);
  const request = useRef(null);
  useEffect(() => () => request.current?.abort(), []);
  const fmt = (v, digits = 0) => v == null ? "—" : new Intl.NumberFormat(locale, { maximumFractionDigits: digits }).format(v);
  const selected = result?.routes.find(route => route.id === selectedId);
  const contaminant = (result?.query.variable || variable) === "pm_25" ? "PM2.5" : "PM10";

  function update(setter, value) { setter(value); setChanged(Boolean(result)); setError(""); }
  function choose(value) {
    setPriority(value);
    if (result) setSelectedId(result.recommendations[value] || result.recommendations.fastest);
  }
  function swap() {
    setOrigin(destination); setDestination(origin); setChanged(Boolean(result)); setError("");
  }
  async function submit(event) {
    event.preventDefault();
    if (!origin.place || !destination.place) return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setBusy(true); setError(""); setResult(null); setSelectedId(null); setChanged(false);
    try {
      const payload = await routeRequest("compare", { origin: origin.place.coordinates.join(","), destination: destination.place.coordinates.join(","), time, day, variable }, controller.signal);
      if (controller.signal.aborted) return;
      setResult(payload); setApplied({ origin: origin.place.label, destination: destination.place.label });
      setSelectedId(payload.recommendations[priority] || payload.recommendations.fastest);
    } catch (failure) { if (!controller.signal.aborted) setError(failure.message); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }

  return localize(<main className="routes-page">
    <RoutesHero />
    <p className="routes-historical"><strong>Comparación experimental · históricos de enero–marzo de 2025.</strong> La hora cambia el perfil histórico del aire. No representa contaminación ni tráfico en tiempo real.</p>

    <div className="routes-layout" id="route-planner" tabIndex={-1} aria-label="Planificador de rutas en bicicleta">
      <section className="route-panel route-controls" aria-labelledby="route-form-heading">
        <h3 id="route-form-heading">Planea tu recorrido</h3>
        <form onSubmit={submit}><fieldset disabled={busy} className="route-form-fields"><legend className="motion-sr-only">Origen, destino y salida</legend>
          <RoutePlaceField name="origin" label="¿De dónde sales?" value={origin} onChange={v => update(setOrigin, v)} />
          <button className="route-swap" type="button" onClick={swap} aria-label="Intercambiar origen y destino">↕ <span>Intercambiar</span></button>
          <RoutePlaceField name="destination" label="¿A dónde vas?" value={destination} onChange={v => update(setDestination, v)} />
          <div className="route-time-fields"><div><label htmlFor="route-day">Día de salida</label><select id="route-day" value={day} onChange={e => update(setDay, e.target.value)}>{days.map((label, i) => <option value={i} key={label}>{label}</option>)}</select></div>
            <div><label htmlFor="route-time">Hora de Bogotá</label><input type="time" id="route-time" value={time} required onChange={e => update(setTime, e.target.value)} /><small>UTC−5</small></div></div>
          <div className="route-field"><label htmlFor="route-pollutant">Contaminante a comparar</label><select id="route-pollutant" value={variable} onChange={e => update(setVariable, e.target.value)}><option value="pm_25">PM2.5</option><option value="pm_10">PM10</option></select></div>
          <button type="submit" className="route-submit" disabled={!origin.place || !destination.place || !time}>{busy ? "Buscando alternativas…" : "Comparar rutas"}<span aria-hidden="true">↗</span></button>
          <button type="button" className="route-example" onClick={() => { update(setOrigin, exampleOrigin); update(setDestination, exampleDestination); }}>Usar ejemplo entre parques</button>
        </fieldset></form>
        <p className="route-service-note">La búsqueda consulta Photon; el cálculo envía los dos puntos a BRouter. <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">Datos de OpenStreetMap.</a></p>
      </section>

      <div className="route-results" aria-busy={busy}>
        <section className="route-panel route-map-panel" aria-labelledby="route-map-heading">
          <div className="route-map-heading"><div><p className="routes-eyebrow">Mira tus opciones</p><h3 id="route-map-heading">{result ? "Un destino, distintos caminos" : "Empieza por dos puntos"}</h3></div><span className="route-unit">{contaminant} · µg/m³</span></div>
          {changed && <p className="route-notice" role="status">Tienes cambios por aplicar. El mapa y los resultados corresponden a la consulta anterior.</p>}
          {error && <p className="route-error" role="alert">{error}</p>}
          {busy && <p className="route-notice" role="status">Consultando recorridos para bicicleta y cruzando los históricos del aire…</p>}
          <RouteMap result={result} selectedId={selectedId} origin={origin.place?.coordinates} destination={destination.place?.coordinates} />
          {!result && !busy && <p className="route-empty">Ya tienes un ejemplo entre parques. Pulsa «Comparar rutas» o busca otros lugares de Bogotá.</p>}
          {result && <p className="route-applied">{applied.origin} → {applied.destination} · {days[result.query.day]} · {result.query.time} · UTC−5</p>}
        </section>

        {result && <section className="route-panel route-alternatives" aria-labelledby="route-alternatives-heading">
          <div className="route-alternatives-heading"><h3 id="route-alternatives-heading">Elige lo que priorizas</h3><span>{result.routes.length} <span>alternativas disponibles</span></span></div>
          <div className="route-priorities" role="group" aria-label="Prioridad del recorrido">{priorities.map(item => <button key={item.value} type="button" aria-pressed={priority === item.value}
            disabled={!result.recommendations[item.value]} onClick={() => choose(item.value)}>{item.label}</button>)}</div>
          {!result.recommendations.exposure && <p className="route-notice">Falta cobertura del aire en alguna alternativa. Mostramos tiempos; no recomendamos una ruta por contaminación.</p>}
          {result.routes.length === 1 && <p className="route-notice">El motor devolvió un solo recorrido distinto. No hay otra alternativa para comparar.</p>}
          <div className="route-cards">{result.routes.map(route => <button key={route.id} type="button" className="route-card" aria-pressed={route.id === selectedId} onClick={() => setSelectedId(route.id)}>
            <div className="route-card-title"><strong>Ruta {route.id.split("-")[1]}</strong><span aria-hidden="true">{route.id === selectedId ? "●" : "○"}</span></div>
            <div className="route-badges">{result.recommendations.fastest === route.id && <span>Menor tiempo</span>}{result.recommendations.exposure === route.id && <span>Menor exposición</span>}{result.recommendations.balanced === route.id && <span>Equilibrio</span>}</div>
            <div className="route-card-metrics"><span><strong>{fmt(route.duration_s / 60)}</strong> min</span><span>{fmt(route.distance_m / 1000, 1)} km</span></div>
            <span className="route-card-air">{contaminant}: {fmt(route.mean_concentration, 1)} µg/m³ <span>estimados</span></span>
            <span className="route-card-coverage">Cobertura: {fmt(route.air_coverage_pct)} %</span>
          </button>)}</div>
          {selected && <div className="route-selected-note"><p><strong>Exposición acumulada estimada:</strong> {fmt(selected.exposure)} µg·min/m³</p><p>Combina concentración y minutos de recorrido. No equivale a dosis inhalada.</p>
            {selected.access_m > 50 && <p>El tiempo corresponde a las vías trazadas. Revisa en el mapa el acceso desde los puntos seleccionados.</p>}</div>}
        </section>}
      </div>
    </div>

    <div className="routes-bottom routes-bottom--method">
      <details className="route-method"><summary>Cómo comparamos las rutas</summary>
        <p>BRouter propone hasta tres recorridos distintos para bicicleta sobre OpenStreetMap. Comparamos esas alternativas; no buscamos todas las rutas posibles de la ciudad. Los tiempos son estimaciones del perfil de bicicleta, sin tráfico en vivo.</p>
        <p>El aire se aproxima con medianas por estación, hora y tipo de día de enero–marzo de 2025. Usamos hasta tres estaciones a un máximo de 5 km, con al menos ocho observaciones por perfil y dos estaciones por punto. La distancia pesa al inverso del cuadrado.</p>
        <p>Integramos la concentración con los minutos de cada tramo y la hora que alcanza la bicicleta durante el trayecto. Solo comparamos exposición cuando todas las alternativas tienen cobertura completa. La opción equilibrada da el mismo peso relativo al tiempo y a la exposición.</p>
        <p>Las estaciones no resuelven el humo de cada calle ni los cambios actuales. Las posiciones de referencia pueden diferir de las históricas y las mediciones publicadas no han sido verificadas aquí. Diferencias pequeñas entre rutas no prueban una mejora real.</p>
        <p><a href="https://www.ambientebogota.gov.co/es/web/sda/estaciones-rmcab" target="_blank" rel="noreferrer">Estaciones y fuente RMCAB ↗</a> · <a href="https://brouter.de/brouter/" target="_blank" rel="noreferrer">Motor de bicicleta ↗</a></p>
      </details></div>
  </main>);
}
