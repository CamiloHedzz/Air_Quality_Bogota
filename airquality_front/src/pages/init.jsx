import { useEffect , useState } from 'react';
import net_gif from '../assets/images/description.gif'; // Ajusta la ruta según la ubicación real del archivo GIF
import '../assets/styles/init_style.css'; // Importa tu archivo CSS

export function Description() {
    return (
      <div id="aboutinit">
        <div id="leftContentinit" className="content">
          <h1>Visualización y Predicción de la <br></br>Calidad del Aire en Bogotá</h1>
          <h2>Dashboard Interactivo y Modelos Predictivos</h2>
          <p>
            Ofrecemos una solución integral para la gestión de la calidad del aire en Bogotá.
            A través de un dashboard interactivo, proporciona información en tiempo real sobre
            los niveles de contaminantes en diferentes zonas de la ciudad, ayudando a las autoridades
            locales, responsables ambientales y ciudadanos a tomar medidas efectivas para prevenir
            la contaminación y mejorar la calidad del aire. Además, se incluye el desarrollo de un
            modelo predictivo basado en datos recopilados, permitiendo estimar la concentración de
            partículas contaminantes en función de diversos factores.
          </p>
          <button className="discoverButton">Descubre!</button>
        </div>
        <div id="rightContentinit" className="content">
          <img src={net_gif} alt="Ejemplo de GIF" />
        </div>
      </div>
    );
  }