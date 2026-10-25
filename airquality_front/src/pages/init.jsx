import { SensorHero } from "../components/SensorHero";
import "../assets/styles/init_style.css";

export function Description() {
  return <SensorHero />;
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
