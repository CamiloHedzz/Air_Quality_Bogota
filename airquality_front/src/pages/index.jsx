import { useEffect , useState } from 'react';
import {getDash} from '../api/dash_get'


export function Index() {
    <div>Este es el index</div>
    
    const [dashLayout, setDashLayout] = useState(null);
    useEffect(() => {
      const fetchData = async () => {
        try {
               console.log("aa")
                const response = await getDash();
                //setDashLayout(response.data);
                console.log(response)
                console.log("dfljdsl")
            } catch (error) {
                console.error('Error fetching Dash layout:', error);
            }
        };

        fetchData();
    }, []);

    return (
      <div>
          <h2>Componente React en Dash</h2>
          {dashLayout && (
              <div dangerouslySetInnerHTML={{ __html: dashLayout }} />
          )}
      </div>
  );
    
    
    /*
    useEffect(() => {
      async function loadDash(){
        const response = await getDash();
        console.log(response)
        //setDashLayout(response.data);
      }
      loadDash();
    },[])*/
}
