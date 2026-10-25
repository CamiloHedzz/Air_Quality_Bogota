import { useContext, useEffect, useRef, useState } from "react";
import { ThemeContext } from "../components/ThemeContext";
import { useLanguage } from "../i18n/useLanguage";
import { loadRoutePlotly } from "./routeApi";

export function RouteMap({ result, selectedId, origin, destination }) {
  const { theme } = useContext(ThemeContext);
  const { localize, t, language } = useLanguage();
  const map = useRef(null);
  const renderQueue = useRef(Promise.resolve());
  const renderedStyle = useRef(null);
  const [basemap, setBasemap] = useState("liberty");
  const mapStyle = basemap === "auto" ? (theme === "dark" ? "dark" : "liberty") : basemap;
  const [error, setError] = useState(false);
  const [ready, setReady] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [size, setSize] = useState({ width: 0, height: 0 });
  useEffect(() => {
    const node = map.current;
    let disposed = false;
    const dark = theme === "dark";
    setError(false); setReady(false);
    const ink = dark ? "#e8eddf" : "#263d30";
    const surface = dark ? "#192720" : "#fafbf6";
    // MapLibre style changes and resize renders must finish in order.
    renderQueue.current = renderQueue.current.catch(() => {}).then(async () => {
      const Plotly = await loadRoutePlotly();
      if (disposed) return;
      const routes = result?.routes || [];
      const traces = [...routes].sort((a, b) => Number(a.id === selectedId) - Number(b.id === selectedId)).map(route => ({
        type: "scattermap", mode: "lines", name: `${t("Ruta")} ${route.id.split("-")[1]}`,
        lon: route.coordinates.map(p => p[0]), lat: route.coordinates.map(p => p[1]),
        line: { color: route.id === selectedId ? (dark ? "#e2d936" : "#827b10") : (dark ? "#6c8a8b" : "#799a9c"), width: route.id === selectedId ? 5 : 3 },
        opacity: route.id === selectedId ? 1 : .65, hovertemplate: `${t("Ruta")} ${route.id.split("-")[1]}<extra></extra>`,
      }));
      const ends = result ? [result.query.origin, result.query.destination] : [origin, destination].filter(Boolean);
      if (ends.length) traces.push({ type: "scattermap", mode: "markers", name: t("Tu recorrido"),
        lon: ends.map(p => p[0]), lat: ends.map(p => p[1]), text: ends.length === 2 ? ["A", "B"] : [origin ? "A" : "B"],
        marker: { symbol: "circle", size: 14, color: ends.map((_, i) => i === 0 ? "#4d7c89" : "#ce7753") }, hoverinfo: "text" });
      const points = routes.flatMap(r => r.coordinates).concat(ends);
      const lons = points.map(p => p[0]), lats = points.map(p => p[1]);
      const lonSpan = points.length ? Math.max(.006, Math.max(...lons) - Math.min(...lons)) : .13;
      const latSpan = points.length ? Math.max(.006, Math.max(...lats) - Math.min(...lats)) : .13;
      const zoom = Math.min(Math.log2((node.clientWidth || 600) * 360 / (512 * lonSpan * 1.5)), Math.log2((node.clientHeight || 430) * 360 / (512 * latSpan * 1.7)));
      const center = points.length ? { lon: (Math.min(...lons) + Math.max(...lons)) / 2, lat: (Math.min(...lats) + Math.max(...lats)) / 2 } : { lon: -74.085, lat: 4.655 };
      const layout = { width: node.clientWidth, height: node.clientHeight, margin: { l: 0, r: 0, t: 0, b: 0 }, showlegend: false,
        paper_bgcolor: surface, font: { family: "system-ui, sans-serif", color: ink },
        hoverlabel: { bgcolor: surface, font: { color: ink } },
        uirevision: `${result ? JSON.stringify(result.query) : "route-start"}:${size.width}:${size.height}`, dragmode: "pan",
        map: { center, zoom: Math.max(10, Math.min(14.5, zoom)),
          style: `https://tiles.openfreemap.org/styles/${mapStyle}` },
      };
      // Switching the background keeps the same trip and the current map view.
      if (node.layout?.uirevision === layout.uirevision && node.layout.map) {
        ["center", "zoom", "bearing", "pitch"].forEach(key => {
          if (node.layout.map[key] != null) layout.map[key] = node.layout.map[key];
        });
      }
      const config = { responsive: false, displaylogo: false, scrollZoom: false, displayModeBar: false };
      if (renderedStyle.current !== mapStyle) {
        Plotly.purge(node);
        await Plotly.newPlot(node, traces, layout, config);
        renderedStyle.current = mapStyle;
      } else await Plotly.react(node, traces, layout, config);
      if (!disposed) setReady(true);
    }).catch(() => { renderedStyle.current = null; if (!disposed) setError(true); });
    return () => { disposed = true; };
  }, [result, selectedId, origin, destination, theme, mapStyle, language, t, attempt, size.width, size.height]);
  useEffect(() => {
    const node = map.current;
    const resize = new ResizeObserver(() => {
      const width = Math.round(node.clientWidth), height = Math.round(node.clientHeight);
      setSize(current => current.width === width && current.height === height ? current : { width, height });
    });
    resize.observe(node);
    return () => {
      resize.disconnect();
      renderQueue.current = renderQueue.current.catch(() => {}).then(() => { if (window.Plotly && node) window.Plotly.purge(node); renderedStyle.current = null; });
    };
  }, []);
  return localize(<div className="route-map-view">
    <div className="route-map-toolbar"><div className="route-map-theme">
      <label htmlFor="route-basemap">Tema</label>
      <select id="route-basemap" value={basemap} onChange={event => setBasemap(event.target.value)}>
        <option value="liberty">Liberty</option>
        <option value="positron">Positron</option>
        <option value="dark">Dark</option>
        <option value="auto">Automático · tema del sitio</option>
      </select>
    </div></div>
    <div className="route-map-shell">
    <div ref={map} className="route-map" role="img" aria-busy={!ready && !error} aria-label="Mapa interactivo de las alternativas en bicicleta por Bogotá" />
    <div className="route-map-zoom"><button type="button" disabled={!ready} aria-label="Acercar mapa" onClick={() => { const node = map.current; if (node?.layout?.map) window.Plotly.relayout(node, { "map.zoom": Math.min(18, node.layout.map.zoom + .7) }); }}>+</button>
      <button type="button" disabled={!ready} aria-label="Alejar mapa" onClick={() => { const node = map.current; if (node?.layout?.map) window.Plotly.relayout(node, { "map.zoom": Math.max(9, node.layout.map.zoom - .7) }); }}>−</button></div>
    {error && <div className="route-map-error" role="alert"><p>No pudimos cargar el mapa. Puedes seguir consultando las alternativas.</p><button type="button" onClick={() => setAttempt(v => v + 1)}>Reintentar mapa</button></div>}
    <div className="route-map-key"><span>A · Origen</span><span>B · Destino</span><span><i />Ruta seleccionada</span></div>
    <p className="route-map-credits"><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap</a> · <a href="https://openfreemap.org/" target="_blank" rel="noreferrer">OpenFreeMap</a> · <a href="https://brouter.de/brouter/" target="_blank" rel="noreferrer">BRouter</a></p>
    </div>
  </div>);
}

RouteMap.propTypes = { result: () => null, selectedId: () => null, origin: () => null, destination: () => null };
