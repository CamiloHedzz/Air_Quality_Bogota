import { useEffect, useId, useState } from "react";
import { createPortal } from "react-dom";
import { useLanguage } from "../i18n/useLanguage";
import "../assets/styles/map_loading.css";

const phrases = {
  es: [
    "Terminando la línea del metro...",
    "Emparejando baldosas de la Autopista Norte...",
    "Empezando segunda línea del Metro...",
    "Llenando el TransMilenio H12...",
    "Inspeccionando billeteras...",
    "Han pasado 3 horas y seguimos en la 30...",
    "Contando cuántas grúas hay cazando carros mal parqueados...",
    "Moviendo el trancón de la NQS cinco metros hacia adelante...",
    "Calibrando estaciones de monitoreo con olor a diésel...",
    "Buscando la capa de ozono detrás de la nube negra de la Boyacá...",
    "Descubriendo nuevos elementos químicos en el aire de Ciudad Bolívar...",
    "Esperando a que escampe en Chapinero para tomar la muestra...",
    "Preguntándole a los vecinos si eso es neblina o el aire de Kennedy...",
  ],
  en: [
    "Finishing the metro line...",
    "Leveling the paving stones on Autopista Norte...",
    "Starting the second Metro line...",
    "Filling up the TransMilenio H12...",
    "Inspecting wallets...",
    "Three hours later, we're still on La 30...",
    "Counting the tow trucks hunting for badly parked cars...",
    "Moving the NQS traffic jam five meters forward...",
    "Calibrating monitoring stations with a hint of diesel...",
    "Looking for the ozone layer behind Boyacá's black cloud...",
    "Discovering new chemical elements in Ciudad Bolívar's air...",
    "Waiting for the rain to stop in Chapinero before taking a sample...",
    "Asking the neighbors if that's fog or Kennedy's air...",
  ],
};

const copy = {
  es: {
    title: "Cargando el mapa",
    ready: "Bogotá está lista",
    stages: { connecting: "Conectando con el mapa", dashboard: "Preparando el explorador", data: "Cargando los datos de Bogotá", map: "Dibujando el mapa", ready: "Mapa listo" },
    slow: "El mapa está tardando un poco más. Puedes seguir explorando mientras termina de cargar.",
    error: "No pudimos terminar de cargar el mapa. Puedes volver a intentarlo o entrar al sitio.",
    retry: "Reintentar",
    enter: "Entrar mientras carga",
  },
  en: {
    title: "Loading the map",
    ready: "Bogotá is ready",
    stages: { connecting: "Connecting to the map", dashboard: "Preparing the explorer", data: "Loading Bogotá's data", map: "Drawing the map", ready: "Map ready" },
    slow: "The map is taking a little longer. You can keep exploring while it finishes loading.",
    error: "We couldn't finish loading the map. You can try again or enter the site.",
    retry: "Try again",
    enter: "Enter while it loads",
  },
};

export function MapLoadingScreen({ progress = 0, stage = "connecting", slow = false, error = false, onRetry, onContinue, finishing = false }) {
  const { language } = useLanguage();
  const locale = language === "en" ? "en" : "es";
  const text = copy[locale];
  const [phrase, setPhrase] = useState(0);
  const labelId = useId();
  const phraseId = useId();
  const hintId = useId();
  const fill = Math.max(0, Math.min(100, Number(progress) || 0)) / 100;

  useEffect(() => {
    if (finishing || error) return;
    const timer = window.setInterval(() => {
      if (!document.hidden) setPhrase(current => (current + 1) % phrases.es.length);
    }, 3200);
    return () => window.clearInterval(timer);
  }, [finishing, error]);

  return createPortal(
    <section id="map-loading-screen" className={`map-loading-screen${finishing ? " map-loading-screen--finishing" : ""}`}
      role="dialog" aria-modal="true" aria-labelledby={labelId} aria-describedby={`${phraseId}${slow || error ? ` ${hintId}` : ""}`}
      tabIndex={-1} data-stage={stage} data-finishing={finishing}>
      <div className="map-loading-content">
        <div className="map-loading-logo" role="progressbar" aria-label={text.title} aria-valuetext={text.stages[stage] || text.stages.connecting}>
          <svg viewBox="0 0 45.46 46.82" focusable="false" aria-hidden="true">
            <text className="map-loading-letter" x="10.22" y="34.58">B</text>
            <rect className="map-loading-bar-track" y="4.14" width="9" height="32.5" />
            <rect className="map-loading-bar-fill" y="4.14" width="9" height="32.5" style={{ transform: `scaleY(${fill})` }} />
          </svg>
        </div>
        <h1 className="map-loading-label" id={labelId}>{finishing ? text.ready : text.title}</h1>
        <div className="map-loading-phrase-region" id={phraseId} aria-live="polite" aria-atomic="true">
          <p key={phrase} className="map-loading-phrase">{phrases[locale][phrase]}</p>
        </div>
        {(slow || error) && !finishing && <div className="map-loading-help">
          <p id={hintId} className="map-loading-hint" role={error ? "alert" : undefined}>{error ? text.error : text.slow}</p>
          <div className="map-loading-actions">
            <button type="button" className="map-loading-retry" onClick={onRetry}>{text.retry}<span aria-hidden="true">↻</span></button>
            <button type="button" className="map-loading-continue" onClick={onContinue}>{text.enter}<span aria-hidden="true">↗</span></button>
          </div>
        </div>}
      </div>
      <p className="map-loading-signature" aria-hidden="true">AIR QUALITY BOGOTÁ</p>
    </section>, document.body,
  );
}

MapLoadingScreen.propTypes = {
  progress: () => null, stage: () => null, slow: () => null, error: () => null,
  onRetry: () => null, onContinue: () => null, finishing: () => null,
};
