import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { createNatureFlight } from "./natureFlight";
import cartography from "../assets/illustrations/bogota-cartography.svg";
import { BirdSilhouette } from "./BirdSilhouette";

export function NatureAtmosphere() {
  const { pathname } = useLocation();
  const [flights, setFlights] = useState([]);
  const sequence = useRef(0);
  const about = pathname.toLowerCase() === "/about";

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    let timer = 0;
    let mounted = true;
    let previousEntry;

    function schedule(delay) {
      timer = window.setTimeout(() => {
        if (!mounted || reduced.matches || document.hidden) return;
        const flight = { ...createNatureFlight(window.innerWidth, window.innerHeight, previousEntry), id: ++sequence.current };
        previousEntry = flight.entry;
        // Two flocks at most; one on small screens. No per-frame React updates.
        setFlights(current => window.innerWidth < 600 ? [flight] : [...current.slice(-1), flight]);
        schedule(8000 + Math.random() * 5500);
      }, delay);
    }
    function restart() {
      window.clearTimeout(timer);
      setFlights([]);
      if (!reduced.matches && !document.hidden) schedule(1600 + Math.random() * 1400);
    }
    restart();
    reduced.addEventListener("change", restart);
    document.addEventListener("visibilitychange", restart);
    window.addEventListener("resize", restart, { passive: true });
    return () => {
      mounted = false;
      window.clearTimeout(timer);
      reduced.removeEventListener("change", restart);
      document.removeEventListener("visibilitychange", restart);
      window.removeEventListener("resize", restart);
    };
  }, []);

  return <div className="nature-atmosphere" aria-hidden="true">
    {about && <div className="about-cartography"><img src={cartography} alt="" width="1600" height="1000" /></div>}
    {flights.map(flight => <div key={flight.id} className="nature-flight" data-entry={flight.entry} data-count={flight.count}
      style={{ offsetPath: `path("${flight.path}")`, "--flight-duration": `${flight.duration}ms`, "--flock-opacity": flight.opacity }}
      onAnimationEnd={event => { if (event.target === event.currentTarget) setFlights(current => current.filter(item => item.id !== flight.id)); }}>
      {flight.birds.map((bird, index) => <div key={index} className="nature-bird"
        style={{ left: bird.x, top: bird.y, width: bird.size, "--bird-direction": flight.direction, "--bird-tilt": `${bird.tilt}deg`, "--bird-flap": `${bird.flap}ms`, "--bird-delay": `${bird.delay}ms` }}>
        <svg viewBox="0 0 100 64" focusable="false"><BirdSilhouette variant={index % 3} /></svg>
      </div>)}
    </div>)}
  </div>;
}
