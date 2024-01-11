import { useEffect , useState } from 'react';
import {getDash} from '../api/dash_get'


export function Index() {    
  //const iframeSrc = "http://127.0.0.1:8000/dash/";
  const iframeSrc = "http://127.0.0.1:8000/django_plotly_dash/app/SimpleExample/"
    return(
     <div>
      
      <iframe
        
        width="50%"
        height="600px"
        src={iframeSrc}
        frameBorder="0"
      />
    </div>
        
    );
}

