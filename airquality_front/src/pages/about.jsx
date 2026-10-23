import { useEffect, useRef } from "react";
import { Table } from "../components/simple_table";
import ContactForm from "../components/form";
import { Footer } from "../components/foutter";
import camiloPhoto from "../assets/images/chi.jpg";

export function About() {
  const detailsRef = useRef(null);

  useEffect(() => {
    function scrollDetails(event) {
      const details = detailsRef.current;
      if (!window.matchMedia("(min-width: 961px)").matches || event.ctrlKey ||
          !event.deltaY || details.contains(event.target)) return;
      const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? details.clientHeight : 1;
      event.preventDefault();
      details.scrollTop += event.deltaY * unit;
    }

    window.addEventListener("wheel", scrollDetails, { passive: false });
    return () => window.removeEventListener("wheel", scrollDetails);
  }, []);


  return (
    <main id="about" className="about-layout">
      <aside
        id="leftContent"
        className="about-column about-profile about-panel"
        aria-labelledby="creator-heading"
      >
        <section aria-labelledby="creator-heading">
          <p className="about-eyebrow">Un proyecto personal</p>
          <h2 id="creator-heading" className="section-heading">Detrás del proyecto</h2>
          <article className="author-card">
            <img className="author-photo" src={camiloPhoto} alt="Camilo Hernández" width="100" height="100" />
            <div>
              <h3 className="author-name">
                <a href="https://github.com/CamiloHedzz">Camilo Hernández</a>
              </h3>
              <p className="author-role">Ingeniería · Datos · Inteligencia artificial</p>
            </div>
          </article>
          <p className="author-bio">
            Soy ingeniero en Ciencias de la Computación e Inteligencia Artificial.
            Me interesa aprender nuevas tecnologías, explorar datos y crear modelos de
            Machine Learning para entender mejor nuestro entorno.
          </p>
        </section>
        <section aria-labelledby="purpose-heading">
          <h2 id="purpose-heading" className="section-heading">Una ciudad que respira</h2>
          <p>
            La contaminación del aire afecta la salud y la vida diaria en Bogotá.
            Este proyecto busca hacer visibles los niveles de contaminación por zona
            y acercar los datos a las personas para que puedan tomar decisiones informadas.
          </p>
        </section>
      </aside>
      <div
        id="rightContent"
        ref={detailsRef}
        className="about-column about-details"
        role="region"
        aria-label="Datos y contacto del proyecto"
        tabIndex={0}
      >
        <section className="about-panel" aria-labelledby="data-heading">
          <p className="about-eyebrow">Del recorrido al mapa</p>
          <h2 id="data-heading" className="section-heading">¿Cómo recopilamos los datos?</h2>
          <p>
            Mediante un sistema de rutas ya definido, se circulan las calles de Bogotá con sensores PM2.5
            con el fin de determinar la calidad del aire. Posteriormente, esta información se somete a un
            procesamiento de datos utilizando herramientas y métodos como el análisis estadístico y
            algoritmos de Machine Learning, con el objetivo de obtener mejores predicciones sobre las
            zonas con mayores impactos ambientales.
          </p>
          <div className="table-scroll" role="region" aria-labelledby="data-heading" tabIndex={0}>
            <Table />
          </div>
          <p>
            Estos datos procesados no solo permiten identificar áreas con problemas de calidad del aire,
            sino que también pueden ser utilizados para implementar medidas de mitigación más efectivas
            y políticas públicas orientadas a mejorar la salud pública y reducir los efectos negativos
            en el medio ambiente.
          </p>
          <a className="about-repository" href="https://github.com/CamiloHedzz/Air_Quality_Bogota">
            Explora el proyecto en GitHub <span aria-hidden="true">↗</span>
          </a>
        </section>
        <section className="about-panel" aria-labelledby="contact-heading">
          <p className="about-eyebrow">Sigamos la conversación</p>
          <h2 id="contact-heading" className="section-heading">Hablemos</h2>
          <p>
            ¿Tienes una idea, una pregunta sobre los datos o ganas de colaborar?
            Cuéntame. Este espacio también se construye con nuevas conversaciones.
          </p>
          <ContactForm />
        </section>
        <Footer />
      </div>
    </main>
  );
}
