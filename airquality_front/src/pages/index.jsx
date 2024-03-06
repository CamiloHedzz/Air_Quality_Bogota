import { useEffect , useState } from 'react';
import {getDash} from '../api/dash_get'
import {Footer} from "../components/foutter"

export function Index() {
  //const iframeSrc = "http://127.0.0.1:8000/django_plotly_dash/app/SimpleExample/"
  const iframeSrc = "http://127.0.0.1:8000/dashv1/"
  return(
    <div>
      <iframe
        width="100%"
        height="2000px"
        src={iframeSrc}
        frameBorder="0"
        style={{backgroundColor: "#F2F2F2"}}
      />   
      <Footer />     
    </div>
  ); 
}

