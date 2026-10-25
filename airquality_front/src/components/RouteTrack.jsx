import { useEffect, useId, useRef, useState } from "react";
import { useLanguage } from "../i18n/useLanguage";
import "../assets/styles/route_track.css";

// An illustrative circuit, deliberately separate from the calculated routes.
const circuit = "M113 427C94 431 78 418 93 404L180 374C201 367 208 349 230 349H252C274 349 281 329 300 324L321 319C340 313 340 297 327 286L311 273C296 260 299 242 316 235C330 228 351 237 364 234L470 172C493 159 517 154 528 171C545 193 515 207 494 210L460 216C440 220 438 233 453 241L473 253C492 265 480 278 460 276L412 267C393 264 378 274 381 291C385 310 404 318 404 335C404 354 386 365 367 372L137 443C127 447 117 438 113 427Z";

export function RouteTrack() {
  const { localize } = useLanguage();
  const unique = "route-circuit-" + useId().replaceAll(":", "");
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [manualPause, setManualPause] = useState(false);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    const svg = svgRef.current;
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    let visible = false;
    let wasReduced = media.matches;
    function sync() {
      const active = visible && !document.hidden && !media.matches && !manualPause;
      if (wasReduced && !media.matches) svg.setCurrentTime(0);
      wasReduced = media.matches;
      if (active) svg.unpauseAnimations();
      else svg.pauseAnimations();
      if (media.matches) svg.setCurrentTime(4.4);
      setRunning(active);
    }
    const observer = new IntersectionObserver(entries => {
      visible = entries.some(entry => entry.isIntersecting);
      sync();
    }, { threshold: .08 });
    observer.observe(containerRef.current);
    media.addEventListener("change", sync);
    document.addEventListener("visibilitychange", sync);
    sync();
    return () => {
      observer.disconnect();
      media.removeEventListener("change", sync);
      document.removeEventListener("visibilitychange", sync);
      svg.pauseAnimations();
    };
  }, [manualPause]);

  return localize(<div ref={containerRef} className="route-track" data-running={running}>
    <svg ref={svgRef} className="route-track-svg" viewBox="0 0 600 600" role="img"
      aria-label="Ilustración animada de una ruta en bicicleta" focusable="false">
      <defs>
        <path id={unique} d={circuit} />
        <pattern id={`${unique}-grid`} width="30" height="30" patternUnits="userSpaceOnUse">
          <path d="M30 0H0V30" fill="none" stroke="currentColor" strokeWidth=".65" />
          <circle cx="0" cy="0" r="1.1" fill="currentColor" />
        </pattern>
        <radialGradient id={`${unique}-halo`}>
          <stop offset="0" stopColor="currentColor" stopOpacity=".16" />
          <stop offset="1" stopColor="currentColor" stopOpacity="0" />
        </radialGradient>
      </defs>

      <g aria-hidden="true">
        <circle className="route-track-halo" cx="315" cy="298" r="275" fill={`url(#${unique}-halo)`} />
        <circle className="route-track-grid" cx="300" cy="296" r="233" fill={`url(#${unique}-grid)`} />
        <g className="route-track-orbits" fill="none">
          <circle cx="300" cy="296" r="251" />
          <circle className="route-track-orbit-dots" cx="300" cy="296" r="236" />
          <path d="M67 201a252 252 0 0 1 166-149M404 524a251 251 0 0 0 142-173" />
        </g>
        <g className="route-track-survey" fill="none">
          <path d="M28 296h25m494 0h25M300 25v25m0 494v25M91 87l13 13m392 392 13 13M91 505l13-13m392-392 13-13" />
          <path d="M86 464h29m-14-14v28M461 111h24m-12-12v24" />
        </g>
        <g className="route-track-ground" fill="none">
          <ellipse cx="300" cy="434" rx="214" ry="66" />
          <ellipse cx="300" cy="434" rx="168" ry="47" />
          <path d="M70 434h460M300 354v159M117 462l365-66M151 392l296 88" />
        </g>

        <g className="route-track-space">
          <use className="route-track-extrusion" href={`#${unique}`} transform="translate(0 15)" />
          <use className="route-track-sidewall" href={`#${unique}`} transform="translate(0 8)" />
          <use className="route-track-edge" href={`#${unique}`} />
          <use className="route-track-road" href={`#${unique}`} />
          <use className="route-track-center" href={`#${unique}`} />
          <path className="route-track-progress" d={circuit} pathLength="1000" />
          <g className="route-track-start" transform="translate(113 427)">
            <circle r="6" />
            <circle r="11" />
          </g>
          <g className="route-track-traveler">
            <path className="route-track-arrow-shadow" d="M13 0-9-8-5 0-9 8Z" transform="translate(0 4)" />
            <path className="route-track-arrow" d="M13 0-9-8-5 0-9 8Z" />
            <animateMotion dur="14s" repeatCount="indefinite" rotate="auto" calcMode="paced">
              <mpath href={`#${unique}`} />
            </animateMotion>
          </g>
        </g>
      </g>
    </svg>
    <button type="button" className="route-track-pause" aria-pressed={manualPause}
      aria-label={manualPause ? "Reanudar animación" : "Pausar animación"}
      onClick={() => setManualPause(current => !current)}>
      <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
        {manualPause ? <path d="m7 4 9 6-9 6Z" /> : <path d="M6 4v12M14 4v12" />}
      </svg>
      <span>{manualPause ? "Reanudar animación" : "Pausar animación"}</span>
    </button>
  </div>);
}
