import { useState } from "react";
import netGif from "../assets/images/description.gif";
import "../assets/styles/init_style.css";

export function Description() {
  const [animationPaused, setAnimationPaused] = useState(false);

  return (
    <section id="aboutinit" aria-labelledby="intro-heading">
      <div id="leftContentinit" className="intro-copy">
        <p className="intro-eyebrow">BOGOTÁ · AIRE Y TERRITORIO</p>
        <h2 id="intro-heading">Conoce el aire<br />de tu ciudad.</h2>
        <p className="intro-description">
          Explora cómo varían las partículas, la temperatura y la humedad entre los
          barrios de Bogotá. Conecta el territorio con los datos y encuentra preguntas
          para entender mejor tu entorno.
        </p>
        <div className="intro-actions">
          <a className="discoverButton" href="#dashboard">
            Explorar el mapa <span aria-hidden="true">↗</span>
          </a>
          <a className="intro-context-link" href="#why-air-matters">¿Por qué importa?</a>
        </div>
        <ul className="intro-variables" aria-label="Variables que puedes explorar">
          <li>PM2.5</li><li>PM10</li><li>Temperatura</li><li>Humedad</li>
        </ul>
      </div>

      <div id="rightContentinit" className={`intro-visual${animationPaused ? " is-paused" : ""}`}>
        <div className="intro-network" aria-hidden="true">
          <span className="network-orbit network-orbit-one" />
          <span className="network-orbit network-orbit-two" />
          <span className="network-cross network-cross-one">+</span>
          <span className="network-cross network-cross-two">+</span>
          <img className="network-gif" src={netGif} alt="" />
          <svg className="network-still" viewBox="0 0 480 480" fill="none">
            <path d="M84 284 156 148 278 104 366 212 306 350 172 376 84 284M156 148 306 350M278 104 172 376M84 284 366 212" />
            <g><circle cx="84" cy="284" r="7" /><circle cx="156" cy="148" r="7" />
              <circle cx="278" cy="104" r="9" /><circle cx="366" cy="212" r="7" />
              <circle cx="306" cy="350" r="9" /><circle cx="172" cy="376" r="6" /></g>
          </svg>
          <div className="network-label network-label-air"><span />AIRE<span className="network-label-detail">PM2.5 · PM10</span></div>
          <div className="network-label network-label-climate"><span />CLIMA<span className="network-label-detail">Temperatura · Humedad</span></div>
        </div>
        <div className="visual-topline" aria-hidden="true"><span>UNA MIRADA CONECTADA</span><span>BOG / CO</span></div>
        <p className="visual-caption">Una ciudad.<br /><span>Muchas formas de leerla.</span></p>
        <button
          type="button"
          className="animation-toggle"
          aria-pressed={animationPaused}
          aria-label={animationPaused ? "Reanudar animación decorativa" : "Pausar animación decorativa"}
          onClick={() => setAnimationPaused(!animationPaused)}
        >
          <span aria-hidden="true">{animationPaused ? "▷" : "Ⅱ"}</span>
          {animationPaused ? "Reanudar" : "Pausar"}
        </button>
      </div>
    </section>
  );
}

export function WhyAirMatters() {
  return (
    <section id="why-air-matters" className="air-context" aria-labelledby="air-context-heading">
      <div className="air-context-heading">
        <p className="intro-eyebrow">POR QUÉ OBSERVAR EL AIRE</p>
        <h2 id="air-context-heading">Lo que respiramos <br />también cuenta.</h2>
        <a href="https://www.who.int/es/news-room/fact-sheets/detail/ambient-(outdoor)-air-quality-and-health" target="_blank" rel="noopener noreferrer">
          Calidad del aire y salud · OMS <span aria-hidden="true">↗</span>
        </a>
      </div>
      <div className="air-context-reasons">
        <article>
          <span className="context-number" aria-hidden="true">01 / SALUD</span>
          <h3>Más allá de lo visible</h3>
          <p>Las partículas del aire pueden afectar la salud respiratoria y cardiovascular.
            Observarlas ayuda a comprender por qué reducir la contaminación importa en la vida cotidiana.</p>
        </article>
        <article>
          <span className="context-number" aria-hidden="true">02 / TERRITORIO</span>
          <h3>Una mirada cercana</h3>
          <p>Comparar barrios permite explorar diferencias en los registros y formular preguntas
            sobre el entorno. El mapa acerca los datos a los lugares que habitamos.</p>
        </article>
        <article>
          <span className="context-number" aria-hidden="true">03 / TIEMPO</span>
          <h3>El contexto cambia la lectura</h3>
          <p>Revisar fechas, temperatura y humedad amplía el contexto de cada periodo.
            Para comparar, ten en cuenta cuántos registros hay y qué días cubren.</p>
        </article>
      </div>
    </section>
  );
}
