import { useEffect , useState } from 'react';
import {getDash} from '../api/dash_get'
import '../assets/styles/index_graph.css'

export function Index() {    
  //const iframeSrc = "http://127.0.0.1:8000/dash/";
  const iframeSrc = "http://127.0.0.1:8000/django_plotly_dash/app/SimpleExample/"
  
  return(
     <div>
        <div className="container">
          <div class="graph-container simpleExample_graph">
            Este mapa interactivo te permite explorar los barrios de 
            Bogotá con mayores niveles de contaminación por partículas 
            PM2.5. Puedes hacer zoom, moverte por el mapa e incluso 
            seleccionar un barrio para ver las mediciones detalladas
            y obtener más información.
          </div>
          <div class="graph-container regression-graph">
            Aquí puedes examinar con detalle la información de las 
            zonas seleccionadas en el mapa. Realiza comparaciones y
            obtén información precisa. Las unidades en el eje Y son
            microgramos por metro cúbico, con cada muestra tomada en
            una hora específica del día.
          </div>
      </div>
      <iframe
        width="100%"
        height="600px"
        src={iframeSrc}
        frameBorder="0"
      />
    </div>
        
    );
}

