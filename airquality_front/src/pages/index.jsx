import { useEffect , useState } from 'react';
import {getDash} from '../api/dash_get'
import '../assets/styles/index_graph.css'

export function Index() {
  //const iframeSrc = "http://127.0.0.1:8000/django_plotly_dash/app/SimpleExample/"
  const iframeSrc = "http://127.0.0.1:8000/dashv1/"
  return(
      <iframe
        width="100%"
        height="2600px"
        src={iframeSrc}
        frameBorder="0"
      />        
    );
}

