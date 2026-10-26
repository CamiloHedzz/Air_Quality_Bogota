import { useLanguage } from "../i18n/useLanguage";
import { Link } from "react-router-dom";
import { FooterOrchids } from "./FooterOrchids";

function FooterArrow() {
  return <svg viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">
    <path d="M5 19 19 5M5 5h14v14" />
  </svg>;
}

function RibbonStar() {
  return <svg className="footer-ribbon-star" viewBox="0 0 32 32" aria-hidden="true" focusable="false">
    <path d="m16 0 3.2 10.5L28 4l-6.5 8.8L32 16l-10.5 3.2L28 28l-8.8-6.5L16 32l-3.2-10.5L4 28l6.5-8.8L0 16l10.5-3.2L4 4l8.8 6.5Z" />
  </svg>;
}

export function Footer() {
  const { localize } = useLanguage();

  return (
    localize(<footer className="site-footer footer-refresh">
      <FooterOrchids />
      <div className="footer-content">
        <Link className="footer-brand" to="/" aria-label="Air Quality Bogotá · inicio">
          <img className="footer-logo" src="/airQuality.svg" alt="" width="68" height="70" />
          <span>Air Quality<span>Bogotá</span></span>
        </Link>
        <div className="footer-main">
          <div className="footer-invitation">
            <h2>Una idea crece<span>cuando la compartimos.</span></h2>
            <p>¿Tienes una idea, datos o ganas de aportar? Hagamos crecer este proyecto para Bogotá.</p>
            <Link className="footer-email" to="/About#contact">
              Envíame un email <span><FooterArrow /></span>
            </Link>
          </div>
          <div className="footer-link-columns">
            <nav aria-label="Recursos del proyecto">
              <h3>Recursos</h3>
              <a href="https://dash.plotly.com/" target="_blank" rel="noopener noreferrer">Dash <FooterArrow /></a>
              <a href="https://bogota-laburbano.opendatasoft.com/pages/home/" target="_blank" rel="noopener noreferrer">Bogotá Catastral <FooterArrow /></a>
              <a href="https://datosabiertos.bogota.gov.co/" target="_blank" rel="noopener noreferrer">Datos Abiertos Bogotá <FooterArrow /></a>
            </nav>
            <nav aria-label="Redes y contacto">
              <h3>Conectemos</h3>
              <a href="https://github.com/CamiloHedzz/Air_Quality_Bogota" target="_blank" rel="noopener noreferrer">GitHub <FooterArrow /></a>
              <a href="https://www.instagram.com/cher_zi/" target="_blank" rel="noopener noreferrer">Instagram <FooterArrow /></a>
              <Link to="/About#contact">Email <FooterArrow /></Link>
            </nav>
          </div>
        </div>
      </div>
      <div className="footer-ribbon">
        <div className="footer-ribbon-viewport">
          <div className="footer-ribbon-track">
            {[0, 1].map(copy => <div className="footer-ribbon-group" key={copy} aria-hidden={copy === 1}>
              <span>Hagamos algo increíble.</span>
              <RibbonStar />
              <span>Hagamos que esto crezca.</span>
              <RibbonStar />
              <span className="footer-ribbon-love">Hecho con amor para mi Bogotá</span>
              <RibbonStar />
            </div>)}
          </div>
        </div>
      </div>
    </footer>)
  );
}
