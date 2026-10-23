import git from "../assets/figures/github.png";
import ins from "../assets/figures/instagram.png";
import mail from "../assets/figures/correo.png";

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-content">
        <img className="footer-logo" src="/airQuality.svg" alt="Air Quality Bogotá" width="90" />
        <p>
          Si tienes dudas o quedaste con ganas de más, revisa nuestras redes sociales.
          Recuerda que puedes ponerte en contacto con nosotros y consultar los recursos
          que te hemos dejado para mayor información.
        </p>
        <div className="social-icons">
          <a href="https://github.com/CamiloHedzz/Air_Quality_Bogota" target="_blank" rel="noopener noreferrer" aria-label="Proyecto en GitHub">
            <img src={git} alt="" width="32" height="32" />
          </a>
          <a href="https://www.instagram.com/cher_zi/" target="_blank" rel="noopener noreferrer" aria-label="Instagram">
            <img src={ins} alt="" width="32" height="32" />
          </a>
          <a href="mailto:camilohedzz@gmail.com" aria-label="Contacto por correo electrónico">
            <img src={mail} alt="" width="32" height="32" />
          </a>
        </div>
        <nav className="resources" aria-label="Recursos del proyecto">
          <h2>Recursos</h2>
          <div className="resource-links">
            <a href="https://dash.plotly.com/" target="_blank" rel="noopener noreferrer">Dash</a>
            <a href="https://bogota-laburbano.opendatasoft.com/pages/home/" target="_blank" rel="noopener noreferrer">Bogotá Catastral</a>
            <a href="https://datosabiertos.bogota.gov.co/" target="_blank" rel="noopener noreferrer">Datos Abiertos Bogotá</a>
          </div>
        </nav>
      </div>
    </footer>
  );
}
