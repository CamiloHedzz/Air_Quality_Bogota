import netGif from "../assets/images/description.gif";
import "../assets/styles/init_style.css";

export function Description() {
  return (
    <section id="aboutinit" aria-labelledby="intro-heading">
      <div id="leftContentinit" className="content">
        <h2 id="intro-heading">Visualización y predicción de la calidad del aire en Bogotá</h2>
        <h3>Dashboard interactivo y modelos predictivos</h3>
        <p>
          Ofrecemos una solución integral para la gestión de la calidad del aire en Bogotá.
          A través de un dashboard interactivo, proporciona información en tiempo real sobre
          los niveles de contaminantes en diferentes zonas de la ciudad, ayudando a las autoridades
          locales, responsables ambientales y ciudadanos a tomar medidas efectivas para prevenir
          la contaminación y mejorar la calidad del aire. Además, se incluye el desarrollo de un
          modelo predictivo basado en datos recopilados, permitiendo estimar la concentración de
          partículas contaminantes en función de diversos factores.
        </p>
        <a className="discoverButton" href="#dashboard">¡Descubre!</a>
      </div>
      <div id="rightContentinit" className="content">
        <img src={netGif} alt="Visualización de una red de datos" />
      </div>
    </section>
  );
}
