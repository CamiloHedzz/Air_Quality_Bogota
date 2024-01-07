import React from "react";
import square from "../assets/figures/square.jpg"
import { NavLink } from 'react-router-dom';
import '../index.css' // mejorar css

export function Navegation() {
    return(
        <div class="nav">
            <div class="title_nav">
                <div><img src={square}/></div>
                <div>
                    <h1>Air Quality Bogotá</h1>
                    <h2>Calidad del Aire</h2>
                </div>
            </div>
            <div class="items_nav">
                <ul>
                    <li><NavLink to="" >Inicio</NavLink></li>
                    <li><NavLink to="/About" >Nosotros</NavLink></li>
                    <li><NavLink to="/Data" >Datos</NavLink></li>
                    <li><NavLink to="/Predictions" >Has tus Predicciones</NavLink></li>
                </ul>
            </div>
        </div>
    );
}