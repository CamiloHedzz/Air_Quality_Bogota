import { useEffect, useId, useRef, useState } from "react";
import { useLanguage } from "../i18n/useLanguage";
import "../assets/styles/route_track.css";

// An illustrative circuit, deliberately separate from the calculated routes.
const circuit = "M113 427C94 431 78 418 93 404L180 374C201 367 208 349 230 349H252C274 349 281 329 300 324L321 319C340 313 340 297 327 286L311 273C296 260 299 242 316 235C330 228 351 237 364 234L470 172C493 159 517 154 528 171C545 193 515 207 494 210L460 216C440 220 438 233 453 241L473 253C492 265 480 278 460 276L412 267C393 264 378 274 381 291C385 310 404 318 404 335C404 354 386 365 367 372L137 443C127 447 117 438 113 427Z";
const lapDuration = 11;

export function RouteTrack() {
  const { localize } = useLanguage();
  const unique = "route-circuit-" + useId().replaceAll(":", "");
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    const svg = svgRef.current;
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    let visible = false;
    let wasReduced = media.matches;
    function sync() {
      const active = visible && !document.hidden && !media.matches;
      if (wasReduced && !media.matches) svg.setCurrentTime(0);
      wasReduced = media.matches;
      if (active) svg.unpauseAnimations();
      else svg.pauseAnimations();
      if (media.matches) svg.setCurrentTime(lapDuration * .315);
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
  }, []);

  return localize(<div ref={containerRef} className="route-track" data-running={running} style={{ "--track-lap": `${lapDuration}s` }}>
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
        <rect className="route-track-grid" x="60" y="56" width="480" height="480" fill={`url(#${unique}-grid)`} />
        <g className="route-track-ground" fill="none">
          <ellipse cx="300" cy="434" rx="214" ry="66" />
          <ellipse cx="300" cy="434" rx="168" ry="47" />
          <path d="M70 434h460M300 354v159M117 462l365-66M151 392l296 88" />
        </g>

        <g className="route-track-space">
          <g className="route-track-turntable">
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
            <animateMotion dur={`${lapDuration}s`} repeatCount="indefinite" rotate="auto" calcMode="paced">
              <mpath href={`#${unique}`} />
            </animateMotion>
          </g>
          </g>
        </g>
      </g>
    </svg>
  </div>);
}
