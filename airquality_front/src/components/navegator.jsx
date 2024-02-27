import React, { useState } from "react";
import square from "../assets/figures/square.jpg"
import { NavLink, useLocation } from 'react-router-dom';
import '../index.css' // mejorar css

export function Navegation() {
    const [title, setTitle] = useState("Air Quality Bogotá");
    const [subtitle, setSubtitle] = useState("Calidad del Aire");
    const location = useLocation();

    const updateTitleAndSubtitle = () => {
        switch (location.pathname) {
            case "/About":
                setTitle("Nosotros");
                setSubtitle("Conoce nuestro modus operandi");
                break;
            case "/Predictions":
                setTitle("Haz tus Predicciones");
                setSubtitle("Predice la calidad del aire");
                break;
            default:
                setTitle("Air Quality Bogotá");
                setSubtitle("Calidad del Aire");
                break;
        }
    };

    React.useEffect(() => {
        updateTitleAndSubtitle();
    }, [location]);

    return(
        <div className="nav">
            <div className="title_nav">
                <div><img src={square} alt="logo"/></div>
                <div>
                    <h1>{title}</h1>
                    <h2>{subtitle}</h2>
                </div>
            </div>
            <div className="items_nav">
                <ul>
                    <li><NavLink to="" onClick={updateTitleAndSubtitle}>Inicio</NavLink></li>
                    <li><NavLink to="/About" onClick={updateTitleAndSubtitle}>Nosotros</NavLink></li>
                    <li><NavLink to="/Predictions" onClick={updateTitleAndSubtitle}>Haz tus Predicciones</NavLink></li>
                </ul>
            </div>
        </div>
    );
}
