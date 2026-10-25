import { useLanguage } from "../i18n/useLanguage";
import { useEffect, useId, useRef, useState } from "react";
import { LanguageToggle } from "./LanguageToggle";
import { SensorSky } from "./SensorSky";
import "../assets/styles/sensor_hero.css";

const parts = [
  { id: "air", name: "Entrada de aire", position: { left: "2%", top: "40%" },
    leader: "M180 262 135 225H92", point: [180, 262],
    description: "El aire y las partículas en suspensión entran por este conducto hacia la zona de medición." },
  { id: "fan", name: "Ventilador", position: { left: "73%", top: "25%" },
    leader: "M405 229 508 150H570", point: [405, 229],
    description: "Un pequeño ventilador mantiene el aire en circulación a través del sensor para que pueda analizarse." },
  { id: "optics", name: "Cámara óptica", position: { left: "1%", top: "72%" },
    leader: "M285 230 223 395H91", point: [285, 230],
    description: "Un láser ilumina las partículas. Un fotodetector recoge la luz que dispersan al atravesar la cámara." },
  { id: "processor", name: "Procesamiento", position: { left: "71%", top: "77%" },
    leader: "M285 308 422 422H558", point: [285, 308],
    description: "La electrónica convierte la señal óptica en estimaciones de concentración de partículas, expresadas en µg/m³." },
];

export function SensorHero() {
  const { localize } = useLanguage();

  const heroRef = useRef(null);
  const [hoveredPart, setHoveredPart] = useState(null);
  const [focusedPart, setFocusedPart] = useState(null);
  const [tappedPart, setTappedPart] = useState(null);
  const closeTimer = useRef(0);
  const activePart = hoveredPart ?? focusedPart ?? tappedPart;
  const gradientId = useId().replaceAll(":", "");

  function enterPart(event, index) {
    if (event.pointerType === "touch") return;
    window.clearTimeout(closeTimer.current);
    setHoveredPart(index);
    setTappedPart(null);
  }
  function leavePart(event) {
    if (event.pointerType === "touch") return;
    window.clearTimeout(closeTimer.current);
    closeTimer.current = window.setTimeout(() => setHoveredPart(null), 120);
  }
  function tapPart(event, index) {
    if (event.nativeEvent.pointerType === "touch" || window.matchMedia("(hover: none), (pointer: coarse)").matches) {
      setHoveredPart(null);
      setFocusedPart(null);
      setTappedPart(current => current === index ? null : index);
    }
  }
  function dismissPart() {
    window.clearTimeout(closeTimer.current);
    setHoveredPart(null);
    setFocusedPart(null);
    setTappedPart(null);
  }
  function partEvents(index) {
    return {
      onPointerEnter: event => enterPart(event, index),
      onPointerLeave: leavePart,
      onClick: event => tapPart(event, index),
    };
  }

  useEffect(() => {
    function outside(event) {
      if (!heroRef.current?.contains(event.target)) setTappedPart(null);
    }
    document.addEventListener("pointerdown", outside, { passive: true });
    return () => {
      window.clearTimeout(closeTimer.current);
      document.removeEventListener("pointerdown", outside);
    };
  }, []);

  useEffect(() => {
    const hero = heroRef.current;
    const media = window.matchMedia("(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)");
    let frame = 0;
    let previous = 0;
    let x = 0;
    let y = 0;
    let targetX = 0;
    let targetY = 0;

    function paint() {
      hero.style.setProperty("--sensor-x", x.toFixed(4));
      hero.style.setProperty("--sensor-y", y.toFixed(4));
    }
    function stop() {
      cancelAnimationFrame(frame);
      frame = 0;
      x = y = targetX = targetY = 0;
      paint();
    }
    function animate(now) {
      frame = 0;
      const easing = 1 - Math.exp(-Math.min(40, now - previous || 16) / 110);
      previous = now;
      x += (targetX - x) * easing;
      y += (targetY - y) * easing;
      const settled = Math.abs(targetX - x) + Math.abs(targetY - y) < 0.001;
      if (settled) { x = targetX; y = targetY; }
      paint();
      if (!settled) frame = requestAnimationFrame(animate);
    }
    function schedule() {
      if (!frame) { previous = performance.now(); frame = requestAnimationFrame(animate); }
    }
    function move(event) {
      if (!media.matches || event.pointerType === "touch") return;
      const bounds = hero.getBoundingClientRect();
      targetX = Math.max(-1, Math.min(1, (event.clientX - bounds.left) / bounds.width * 2 - 1));
      targetY = Math.max(-1, Math.min(1, (event.clientY - bounds.top) / bounds.height * 2 - 1));
      schedule();
    }
    function reset() {
      if (!media.matches || document.hidden) { stop(); return; }
      targetX = targetY = 0;
      schedule();
    }

    hero.addEventListener("pointermove", move, { passive: true });
    hero.addEventListener("pointerleave", reset, { passive: true });
    window.addEventListener("blur", stop);
    document.addEventListener("visibilitychange", reset);
    media.addEventListener("change", reset);
    return () => {
      stop();
      hero.removeEventListener("pointermove", move);
      hero.removeEventListener("pointerleave", reset);
      window.removeEventListener("blur", stop);
      document.removeEventListener("visibilitychange", reset);
      media.removeEventListener("change", reset);
    };
  }, []);

  return (
    localize(<section ref={heroRef} id="aboutinit" className="sensor-hero" aria-labelledby="intro-heading"
      onKeyDown={event => { if (event.key === "Escape") { dismissPart(); event.stopPropagation(); } }}>
      <LanguageToggle className="hero-language-toggle" />
      <div className="sensor-landscape" aria-hidden="true">
        <svg viewBox="0 0 720 620" preserveAspectRatio="none">
          <g className="sensor-terrain-lines">
            {Array.from({ length: 19 }, (_, index) => {
              const base = -400 + index * 85;
              return <path key={index} d={`M${base} 650Q${base * 0.5 + 180} 360 360 170`} />;
            })}
            {Array.from({ length: 12 }, (_, index) => {
              const base = 220 + index * 37;
              return <path key={index} d={`M-100 ${base}Q360 ${base - 100} 820 ${base}`} />;
            })}
          </g>
          <circle cx="390" cy="280" r="203" className="sensor-survey-ring" />
          <path className="sensor-survey-cross" d="M84 92v12m-6-6h12M620 400v12m-6-6h12M570 65v8m-4-4h8" />
        </svg>
        <svg className="sensor-bogota-hills" viewBox="0 0 1440 700" preserveAspectRatio="none">
          <SensorSky />
          <g className="sensor-hill-contours">
            <path className="sensor-hill-ridge" d="M-40 237 79 213 147 221 230 174 300 191 364 158 421 174 495 143 558 169 636 153 701 177 767 151 829 176 892 147 950 156 985 128 992 124H1040L1079 147 1123 154 1190 188 1255 166 1326 201 1395 179 1480 214" />
            <path d="M-40 263Q95 226 172 249T326 223Q419 178 501 185T680 204Q774 175 845 200T984 160Q1023 141 1060 163T1182 221Q1260 191 1343 225T1480 242" />
            <path d="M-40 285Q107 254 204 275T390 242Q476 218 553 230T735 238Q814 219 880 237T1006 198Q1042 176 1090 201T1211 254Q1305 231 1480 275" />
            <path d="M569 174Q600 205 651 228M767 162Q799 202 839 219M990 135Q967 169 941 191M1045 139Q1061 166 1112 194M1187 201Q1173 217 1164 235" />
          </g>
          <g className="sensor-monserrate" transform="translate(992 70)">
            <path d="M0 54H48M2 54V17H14V54M34 54V17H46V54M2 17 8 11 14 17M34 17 40 11 46 17M8 11V3M5 6H11M40 11V3M37 6H43M14 31 24 23 34 31M24 23V17M21 20H27M14 32H34M14 36H34" />
            <path d="M5 28V23Q8 19 11 23V28ZM37 28V23Q40 19 43 23V28ZM19 54V46Q24 38 29 46V54M5 34H11M37 34H43M-5 58H53M-10 62H58" />
          </g>
        </svg>
        <svg className="sensor-city-bus" viewBox="0 0 460 140" fill="none">
          <g className="sensor-bus-wireframe">
            <path className="sensor-bus-body" d="M22 103V48Q22 43 28 43H193M215 43H402L423 64V103H390M366 103H253M229 103H79M55 103H22M193 43V103H215V43" />
            <path d="M22 48 39 31H414L440 54V92L423 103M402 43 414 31M423 64 440 54M423 81 440 71M28 87H193M215 87H422M28 96H55M79 96H193M215 96H229M253 96H366M390 96H422" />
            <path d="M193 46 197 50V97L201 101V47L205 51V98L209 101V47L213 51M196 43H215M196 103H215" />
            <path d="M32 52H65V76H32ZM70 52H101V76H70ZM106 52H137V76H106ZM142 52H180V76H142ZM224 52H251V76H224ZM256 52H285V76H256ZM290 52H320V76H290ZM325 52H355V76H325ZM360 52H394L412 69V77H360Z" />
            <path d="M104 52V96M120 52V96M280 52V96M296 52V96M395 77V99M403 79V99M424 89 437 82M31 82H45M408 84H418" />
            <circle cx="67" cy="103" r="12" /><circle cx="67" cy="103" r="6" />
            <circle cx="241" cy="103" r="12" /><circle cx="241" cy="103" r="6" />
            <circle cx="378" cy="103" r="12" /><circle cx="378" cy="103" r="6" />
            <path className="sensor-bus-road" d="M0 117H447M-12 129H90M123 129H225M258 129H360M393 129H470" />
          </g>
        </svg>
      </div>
      <div id="leftContentinit" className="intro-copy sensor-copy">
        <h2 id="intro-heading" className="hero-city-title" aria-label="Conoce el aire de tu ciudad.">
          <span className="hero-title-variant hero-title-opening" aria-hidden="true">
            <span className="headline-line"><span>Conoce el <em className="headline-accent">aire</em></span></span>
            <span className="headline-line"><span>de Bogotá</span></span>
          </span>
          <span className="hero-title-variant hero-title-final" aria-hidden="true">
            <span className="headline-line"><span>Conoce el <em className="headline-accent">aire</em></span></span>
            <span className="headline-line"><span>de tu ciudad.</span></span>
          </span>
          <span className="hero-title-wipe" aria-hidden="true" />
        </h2>
        <p className="intro-description">
          Lo que no vemos también cuenta. Explora las partículas, la temperatura y la
          humedad, y encuentra otra forma de leer el territorio de Bogotá.
        </p>
        <div className="intro-actions">
          <a className="discoverButton" href="#dashboard">Explorar el mapa <span aria-hidden="true">↗</span></a>
        </div>
      </div>

      <div id="rightContentinit" className="sensor-stage">

        <div id="sensor-parts" className="sensor-scene" tabIndex={-1} role="group" aria-label="Partes de un sensor óptico de PM2.5 y PM10">
          <div className="sensor-model-space">
            <svg className="sensor-model" viewBox="0 0 720 520" fill="none" aria-hidden="true">
              <defs>
                <linearGradient id={`${gradientId}-shell`} x1="230" y1="100" x2="450" y2="405" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#a2ba84" stopOpacity=".12" /><stop offset="1" stopColor="#122e25" stopOpacity=".78" />
                </linearGradient>
                <linearGradient id={`${gradientId}-board`} x1="170" y1="240" x2="430" y2="370" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#385d45" /><stop offset="1" stopColor="#173b2d" />
                </linearGradient>
                <radialGradient id={`${gradientId}-glow`}><stop stopColor="#d8d02a" stopOpacity=".15" /><stop offset="1" stopColor="#d8d02a" stopOpacity="0" /></radialGradient>
              </defs>
              <ellipse cx="340" cy="416" rx="190" ry="45" fill={`url(#${gradientId}-glow)`} />
              <g className="sensor-base-grid">
                <ellipse cx="340" cy="416" rx="188" ry="44" /><ellipse cx="340" cy="416" rx="152" ry="33" />
                <path d="M119 416h442M340 363v105M202 387l276 58M212 449l257-65" />
              </g>
              <g className="sensor-case">
                <path d="m253 105 255 64-86 164-255-64z" fill={`url(#${gradientId}-shell)`} />
                <path d="m167 269 255 64v72l-255-64z" fill="#244535" fillOpacity=".65" />
                <path d="m422 333 86-164v72l-86 164z" fill="#142e25" fillOpacity=".8" />
                <path d="m253 105 255 64-86 164-255-64zm0 0v72m255-8v72l-86 164-255-64v-72m255 64v72" />
                <path d="m188 298 212 54m-212-40 212 54m-212-26 212 54M446 309l42-79m-41 98 42-80" className="sensor-case-vents" />
              </g>
              <g className="sensor-board">
                <path d="m248 163 239 61-75 145-239-61z" fill={`url(#${gradientId}-board)`} />
                <path d="m248 163 239 61-75 145-239-61zM218 299l27-52 80 21 16-31m-142 78 40 11 31-59m39 84 22-42 81 20m-32-20 27-52m-126-55 32 8 14-25" />
                <g className="sensor-solder-points"><circle cx="248" cy="178" r="3" /><circle cx="470" cy="230" r="3" /><circle cx="404" cy="353" r="3" /><circle cx="190" cy="302" r="3" /></g>
              </g>
              <g className="sensor-component sensor-air" data-active={activePart === 0} {...partEvents(0)}>
                <path className="sensor-hit-area" d="M166 191 239 209 219 270 211 291 144 276 144 234Z" />
                {/* The inlet follows the enclosure's width, depth and vertical axes. */}
                <path d="M174 201 228 214.5 207 254.5 153 241Z" fill="#3d6250" />
                <path d="M228 214.5 207 254.5 207 282.5 228 242.5Z" fill="#244635" />
                <path d="M153 241 207 254.5 207 282.5 153 269Z" fill="#193a2c" />
                <path d="M174 201 228 214.5 207 254.5 153 241ZM228 214.5V242.5L207 282.5 153 269V241M207 254.5V282.5" />
                <path d="M160 249 200 259 200 275 160 265Z" fill="#0c241b" />
                <path d="M170 251.5V267.5M180 254V270M190 256.5V272.5" />
                <path d="M151 283 163 260M165 288 177 265M179 291 191 268" className="sensor-air-flow" />
                <circle cx="146" cy="291" r="2" /><circle cx="160" cy="300" r="2.5" /><circle cx="180" cy="300" r="2" />
              </g>
              <g className="sensor-component sensor-optics" data-active={activePart === 2} {...partEvents(2)}>
                <path className="sensor-hit-area" d="M257 176 357 201 327 291 221 269 221 235Z" />
                <path d="m259 182 90 23-30 57-90-23z" fill="#1b392c" /><path d="m229 239 90 23v22l-90-23z" fill="#142d23" />
                <path d="m259 182 90 23-30 57-90-23zm-30 57v22l90 23v-22m0 22 30-57v-22" />
                <path d="m250 214 15 4-6 13-15-4z" fill="#d8d02a" fillOpacity=".3" />
                <path className="sensor-laser" d="m260 224 60 15m-29-7 20 26m-20-26 32-9" />
                <circle cx="291" cy="232" r="4" className="sensor-particle" />
                <path d="m307 253 13 3-5 10-13-3z" fill="#d8d02a" fillOpacity=".5" />
              </g>
              <g className="sensor-component sensor-fan" data-active={activePart === 1} transform="rotate(14 405 229)" {...partEvents(1)}>
                <ellipse className="sensor-hit-area" cx="405" cy="229" rx="61" ry="42" />
                <ellipse cx="405" cy="237" rx="55" ry="34" fill="#122f24" /><ellipse cx="405" cy="229" rx="55" ry="34" fill="#274d38" />
                <ellipse cx="405" cy="229" rx="55" ry="34" /><ellipse cx="405" cy="229" rx="45" ry="27" />
                <path d="M350 229v8m110-8v8M405 229c-7-17 10-25 25-19 4 8-13 17-25 19Zm0 0c21 2 31 12 20 20-16 0-23-12-20-20Zm0 0c-11 16-31 12-33 2 9-10 25-8 33-2Z" fill="currentColor" fillOpacity=".12" />
                <ellipse cx="405" cy="229" rx="8" ry="5" fill="currentColor" fillOpacity=".4" />
              </g>
              <g className="sensor-component sensor-processor" data-active={activePart === 3} {...partEvents(3)}>
                <path className="sensor-hit-area" d="M258 272 333 292 314 339 236 318Z" />
                <path d="m262 281 61 16-16 32-61-16z" fill="#173126" /><path d="m262 281 61 16-16 32-61-16z" />
                <path d="m269 291 39 10-8 17-39-10z" /><path d="m281 299 11 3-3 6-11-3z" fill="currentColor" fillOpacity=".35" />
                {Array.from({ length: 6 }, (_, index) => <path key={index} d={`M${266 + index * 9} ${282 + index * 2.3}l4-8M${249 + index * 9} ${315 + index * 2.3}l-4 8`} />)}
              </g>
              <g className="sensor-cover">
                <path d="m253 58 255 64-86 164-255-64z" fill="#63805c" fillOpacity=".06" />
                <path d="m253 58 255 64-86 164-255-64zm0 0v14l255 64v-14M167 222v14l255 64v-14m0 14 86-164" />
                <path d="m265 82 210 53M259 95l210 53M253 108l210 53" className="sensor-cover-lines" />
                <path d="M253 88v17M508 151v18M167 252v17M422 316v17" className="sensor-assembly-lines" />
                <text x="292" y="179" transform="rotate(14 292 179)">PM2.5 / PM10</text>
              </g>
              {parts.map((part, index) => <g key={part.id} className="sensor-leader" data-active={activePart === index}>
                <path d={part.leader} /><circle cx={part.point[0]} cy={part.point[1]} r="4" />
                <circle className="sensor-leader-ring" cx={part.point[0]} cy={part.point[1]} r="11" />
              </g>)}
            </svg>
            {parts.map((part, index) => <div key={part.id}
              className={`sensor-annotation sensor-annotation-${part.id}${index === 1 || index === 3 ? " is-right" : ""}`}
              style={part.position} onPointerEnter={event => enterPart(event, index)} onPointerLeave={leavePart}>
              <button id={`sensor-part-${part.id}`} className="sensor-hotspot" type="button"
                aria-expanded={activePart === index} aria-label={`${index + 1}. ${part.name}`}
                aria-describedby={activePart === index ? `sensor-tip-${part.id}` : undefined}
                aria-controls={`sensor-tip-${part.id}`} onClick={event => tapPart(event, index)}
                onFocus={event => { if (event.currentTarget.matches(":focus-visible")) setFocusedPart(index); }}
                onBlur={() => setFocusedPart(null)}
                onKeyDown={event => { if (event.key === "Enter" || event.key === " ") setFocusedPart(index); }}>
                <span className="sensor-hotspot-number">0{index + 1}</span><span className="sensor-hotspot-label">{part.name}</span>
              </button>
              <div id={`sensor-tip-${part.id}`} className="sensor-callout" role="tooltip" hidden={activePart !== index}>
                <h3>{part.name}</h3><p>{part.description}</p>
              </div>
            </div>)}
          </div>
        </div>

        <div className="sensor-stage-footer"><span>Sensor óptico · esquema ilustrativo</span>
          <a href="https://sensirion.com/products/product-insights/specialist-articles/particulate-matter-sensing-for-air-quality-measurements" target="_blank" rel="noopener noreferrer">Principio de medición <span aria-hidden="true">↗</span></a>
        </div>
      </div>
    </section>)
  );
}
