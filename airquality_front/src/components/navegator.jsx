import { NavLink, useLocation } from "react-router-dom";

const pageTitles = {
  "/About": { title: "About", subtitle: "La historia detrás de Air Quality Bogotá" },
  "/Predictions": { title: "Haz tus predicciones", subtitle: "Predice la calidad del aire" },
};

export function Navegation() {
  const { pathname } = useLocation();
  const { title, subtitle } = pageTitles[pathname] || {
    title: "Air Quality Bogotá",
    subtitle: "Calidad del Aire",
  };

  return (
    <header className="site-header">
      <div className="site-brand">
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      <nav className="site-navigation" aria-label="Navegación principal">
        <ul>
          <li><NavLink to="/" end>Inicio</NavLink></li>
          <li><NavLink to="/About">About</NavLink></li>
          <li><NavLink to="/Predictions">Haz tus predicciones</NavLink></li>
        </ul>
      </nav>
    </header>
  );
}
