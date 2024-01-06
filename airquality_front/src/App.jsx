import React from "react";
import "./index.css"
import {Index} from "./pages/index"
import {Navegation} from "./components/navegator"
import "./assets/fonts/ELEPHNT.TTF"
import {BrowserRouter, Route, Routes} from "react-router-dom"

function App() {
  return (
    <BrowserRouter>
      <Navegation />
      <Routes>
      <Route path = '' element= {<Index/>}/>
      </Routes>
    </BrowserRouter>
  );
}

export default App;