import React from "react";
import {Index} from "./pages/index"
import {Data} from "./pages/data"
import {About} from "./pages/about"
import {Navegation} from "./components/navegator"
import { Predictions } from "./pages/predictions";
import {BrowserRouter, Route, Routes} from "react-router-dom"

function App() {
  return (
    <BrowserRouter>
      <Navegation />
      <Routes>
      <Route path = '' element= {<Index/>}/>
      <Route path = '/About' element= {<About/>}/>
      <Route path = '/Data' element= {<Data/>}/>
      <Route path = '/Predictions' element= {<Predictions/>}/>
      </Routes>
    </BrowserRouter>
  );
}

export default App;