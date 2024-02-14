import { useEffect , useState } from 'react';
import {getDash} from '../api/dash_get'


export function DashTable() {    
  //const iframeSrc = "http://127.0.0.1:8000/dash_table/";
  const iframeSrc = "http://127.0.0.1:8000/django_plotly_dash/app/dash_table/"
    return(
     <div>
      <iframe
        width="100%"
        height="600px"
        src={iframeSrc}
        frameBorder="0"
      />
    </div>
        
    );
}

