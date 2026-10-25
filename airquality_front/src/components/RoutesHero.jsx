import { useLanguage } from "../i18n/useLanguage";
import { RouteTrack } from "./RouteTrack";
import "../assets/styles/routes_hero.css";

export function RoutesHero() {
  const { localize } = useLanguage();

  return localize(<section className="routes-hero" aria-labelledby="routes-hero-title">
    <div className="routes-hero-copy">
      <p className="routes-hero-kicker">Bogotá, sobre dos ruedas</p>
      <h2 id="routes-hero-title" className="routes-hero-title">Rutas</h2>
      <p className="routes-hero-lead">Planea tus rutas en bici.</p>
      <p className="routes-hero-description">Busca un equilibrio entre menor exposición estimada a la contaminación y un mejor tiempo de recorrido.</p>
      <p className="routes-hero-story">Esta iniciativa nació al montar bicicleta por Bogotá y respirar el humo del tráfico. De esa experiencia surge la idea de comparar caminos pensando en el aire que respiramos y el tiempo que pedaleamos.</p>
      <a href="#route-planner" className="routes-hero-cta">Planear mi ruta<span aria-hidden="true">↗</span></a>
    </div>
    <RouteTrack />
  </section>);
}
