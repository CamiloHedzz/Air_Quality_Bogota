import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useLanguage } from "../i18n/useLanguage";
import { LanguageToggle } from "./LanguageToggle";
import { mountJourneyParticles } from "./journeyParticles";
import bogotaDawn from "../assets/images/bogota-dawn-journey.webp";
import "../assets/styles/bogota_journey.css";

const copy = {
  es: {
    chapters: ["La ciudad", "Lo invisible", "El territorio"],
    labels: ["", "02 / LO QUE NO VEMOS", "03 / DEL AIRE AL TERRITORIO"],
    titles: [["Bogotá,", "en el aire."], ["Lo invisible", "deja huella."], ["Cada lugar,", "otra historia."]],
    descriptions: ["Entre los cerros y la ciudad, el aire cuenta una historia. Vamos a descubrirla.", "Partículas, temperatura y humedad. Pequeñas señales que nos ayudan a entender nuestro entorno.", "Explora el mapa, compara sectores y descubre cómo cambian los registros a través del tiempo."],
    explore: "Explorar el mapa", predictions: "Ver predicciones", journey: "Recorrido visual: de Bogotá a sus datos",
    illustration: "Bogotá · interpretación artística", geometry: "Vista urbana · geometría simplificada", history: "HISTÓRICOS", variables: "PARTÍCULAS", territory: "SECTORES DEL PROYECTO", progress: "Avance del recorrido", north: "N",
  },
  en: {
    chapters: ["The city", "The invisible", "The territory"],
    labels: ["", "02 / WHAT WE CANNOT SEE", "03 / FROM AIR TO TERRITORY"],
    titles: [["Bogotá,", "in the air."], ["The invisible", "leaves a trace."], ["Every place,", "another story."]],
    descriptions: ["Between the hills and the city, the air tells a story. Let's discover it.", "Particles, temperature and humidity. Small signals that help us understand our surroundings.", "Explore the map, compare sectors and discover how the records change over time."],
    explore: "Explore the map", predictions: "View predictions", journey: "A visual journey from Bogotá to its data",
    illustration: "Bogotá · artistic interpretation", geometry: "Urban view · generalized geometry", history: "HISTORICAL RECORDS", variables: "PARTICLES", territory: "PROJECT SECTORS", progress: "Journey progress", north: "N",
  },
};

export function BogotaJourney() {
  const { language } = useLanguage();
  const text = copy[language === "en" ? "en" : "es"];
  const root = useRef(null), canvas = useRef(null), image = useRef(null);
  const [phase, setPhase] = useState(0);
  useEffect(() => mountJourneyParticles(root.current, canvas.current, image.current, setPhase), []);

  function chapter(index) {
    const node = root.current, stage = node.querySelector(".journey-stage");
    const header = document.querySelector(".site-header")?.getBoundingClientRect().height || 82;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced && index) { document.getElementById(index === 1 ? "why-air-matters" : "dashboard")?.scrollIntoView({ behavior: "instant" }); return; }
    const start = window.scrollY + node.getBoundingClientRect().top - header;
    window.scrollTo({ top: start + Math.max(0, node.offsetHeight - stage.offsetHeight) * [0, .5, 1][index], behavior: reduced ? "instant" : "smooth" });
  }

  return <section className="bogota-journey" ref={root} data-phase={phase} aria-label={text.journey}>
    <div className="journey-stage">
      <div className="journey-art" aria-hidden="true"><img ref={image} src={bogotaDawn} width="1672" height="941" alt="" loading="eager" decoding="async" /><div className="journey-art-shade" /></div>
      <div className="journey-atlas-grid" aria-hidden="true" />
      <canvas ref={canvas} className="journey-particles" aria-hidden="true" />
      <div className="journey-topline"><div className="journey-locale"><span className="journey-location">BOGOTÁ, COLOMBIA</span><LanguageToggle className="journey-language-toggle" /></div></div>
      <div className="journey-stories">
        {text.titles.map((title, index) => <div key={index} className={`journey-copy journey-copy--${index}`} aria-hidden={phase !== index} inert={phase !== index ? "" : undefined}>
          {text.labels[index] && <p className="journey-eyebrow">{text.labels[index]}</p>}
          <h2 id={index === 0 ? "journey-heading" : undefined}>{title[0]}<br /><em>{title[1]}</em></h2>
          <p className="journey-description">{text.descriptions[index]}</p>
          {index === 2 && <div className="journey-actions"><a className="journey-enter" href="#dashboard">{text.explore}<span aria-hidden="true">↗</span></a><Link to="/Predictions">{text.predictions} <span aria-hidden="true">↗</span></Link></div>}
        </div>)}
      </div>
      <div className="journey-map-notes" aria-hidden="true"><div className="journey-north">{text.north}<span>↑</span></div><span className="journey-map-place">BOGOTÁ D.C.<small>4°39′ N · 74°05′ O</small></span><span className="journey-map-caption">{text.geometry}</span></div>
      <div className="journey-floating-labels" aria-hidden="true"><span>PM2.5</span><span>PM10</span><span>°C</span><span>% HR</span></div>
      <div className="journey-bottomline">
        <nav className="journey-chapters" aria-label={text.progress}>{text.chapters.map((label, index) => <button type="button" key={label} aria-current={phase === index ? "step" : undefined} onClick={() => chapter(index)}><span>0{index + 1}</span><span>{label}</span></button>)}</nav>
        <p className="journey-credit">{text.illustration}</p>
      </div>
      <div className="journey-progress" aria-hidden="true"><span /></div>
    </div>
    <div className="journey-data-strip">
      <p><span>{text.history}</span><strong>2015—2025</strong></p><p><span>{text.variables}</span><strong>PM2.5 <i>↔</i> PM10</strong></p><p><span>{text.territory}</span><strong>1.160</strong></p><p className="journey-strip-invitation">{text.explore}<a href="#dashboard" aria-label={text.explore}>↗</a></p>
    </div>
  </section>;
}
