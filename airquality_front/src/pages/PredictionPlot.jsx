import { useEffect, useRef, useState } from "react";

export function PredictionPlot({ query, showObserved }) {
  const frame = useRef(null);
  const [height, setHeight] = useState(520);
  const [loaded, setLoaded] = useState(false);
  const params = new URLSearchParams({ ...query, show_observed: showObserved ? "1" : "0" });
  const key = params.toString();
  params.set("frameKey", key);
  const source = `/django_plotly_dash/app/PredictionCharts/?${params}`;
  useEffect(() => {
    setLoaded(false);
    setHeight(query.view === "diagnostics" ? 660 : 520);
    function receive(event) {
      if (event.origin !== window.location.origin || event.source !== frame.current?.contentWindow ||
          event.data?.type !== "airquality:prediction-plot-height" || event.data.key !== key) return;
      const next = event.data.height;
      if (typeof next === "number" && Number.isFinite(next) && next >= 100 && next < 5000) setHeight(Math.ceil(next));
    }
    window.addEventListener("message", receive);
    return () => window.removeEventListener("message", receive);
  }, [key, query.view]);
  function requestHeight() {
    setLoaded(true);
    frame.current?.contentWindow?.postMessage({type:"airquality:request-prediction-plot-height"}, window.location.origin);
  }
  return <div className="prediction-plotly-container">
    {!loaded && <p className="prediction-chart-hint" role="status">Cargando gráfico interactivo de Plotly…</p>}
    <iframe ref={frame} src={source} title="Gráfico interactivo de Dash y Plotly" className="prediction-plotly-frame" style={{height}} onLoad={requestHeight} />
  </div>;
}

PredictionPlot.propTypes = {
  query: (props, name) => props[name] && typeof props[name] === "object" && typeof props[name].view === "string"
    ? null : new Error("PredictionPlot requiere una consulta con una vista."),
  showObserved: (props, name) => typeof props[name] === "boolean"
    ? null : new Error("showObserved debe ser booleano."),
};
