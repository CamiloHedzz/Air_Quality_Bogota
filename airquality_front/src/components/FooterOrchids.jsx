import { useEffect, useId, useRef, useState } from "react";

function OrchidDrawing() {
  const hatch = "orchid-hatch-" + useId().replaceAll(":", "");
  const bloom = "orchid-bloom-" + useId().replaceAll(":", "");
  return <svg viewBox="0 0 280 500" fill="none" focusable="false">
    <defs>
      <pattern id={hatch} width="4" height="7" patternUnits="userSpaceOnUse"><path d="M1 0V7" stroke="currentColor" strokeWidth="1.1" /></pattern>
      <g id={bloom} fill={`url(#${hatch})`} className="orchid-bloom">
        <path d="M-5 3C-40-43-77-47-84-19C-92 13-52 38-11 20Z" />
        <path d="M5 3C40-43 77-47 84-19C92 13 52 38 11 20Z" />
        <path d="M-9-5C-26-45-14-77 0-84C21-67 28-32 9-5Z" />
        <path d="M-14 13C-42 27-56 55-48 69C-25 70-4 41-4 24Z" />
        <path d="M14 13C42 27 56 55 48 69C25 70 4 41 4 24Z" />
        <path className="orchid-lip" d="M-10 10C-28 19-34 33-27 43L-19 49-15 45-8 53 0 50 8 53 15 45 19 49 27 43C34 33 28 19 10 10L0 22Z" />
        <path className="orchid-veins" d="M-10 8-64-13M10 8 64-13M0-12V-61M-11 23-34 54M11 23 34 54M0 24v17" />
      </g>
    </defs>
    <g className="orchid-stems"><path d="M68 510C94 442 108 380 136 334S186 271 161 205M110 395C88 317 72 239 95 147M146 317C196 270 224 200 217 146" /></g>
    <g fill={`url(#${hatch})`} className="orchid-leaves">
      <path d="M92 420C50 400 20 360 16 310C66 312 109 354 116 393Z" />
      <path d="M108 395C160 389 223 353 240 305C168 303 128 337 108 395Z" />
      <path d="M77 466C27 451 10 420 5 380C57 386 82 422 91 451Z" />
      <path d="M85 467C148 474 204 441 230 402C158 402 111 428 85 467Z" />
    </g>
    <g className="orchid-veins"><path d="M20 316Q60 350 107 402M116 389Q168 348 232 311M12 386Q52 418 84 459M94 463Q148 436 220 409" /></g>
    <use href={`#${bloom}`} transform="translate(160 205) rotate(13) scale(.9)" />
    <use href={`#${bloom}`} transform="translate(95 144) rotate(-21) scale(.67)" />
    <g className="orchid-bud" fill={`url(#${hatch})`}><path d="M216 150C196 146 193 120 207 109C226 115 235 136 216 150Z" /><path d="m216 150-9-41" /></g>
  </svg>;
}

export function FooterOrchids() {
  const layer = useRef(null);
  const revealPoint = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (!window.IntersectionObserver) { setVisible(true); return; }
    const footer = layer.current.closest("footer");
    const point = revealPoint.current;
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.target === footer) {
          // Reset only after leaving the footer, including dashboard layout shifts.
          if (!entry.isIntersecting) setVisible(false);
          else if (point.getBoundingClientRect().top <= (entry.rootBounds?.bottom ?? window.innerHeight)) setVisible(true);
        } else if (entry.isIntersecting) {
          // The artwork must reach the viewport before its entrance starts.
          setVisible(true);
        }
      });
    }, { threshold: 0, rootMargin: "0px 0px -24px 0px" });
    observer.observe(footer);
    observer.observe(point);
    return () => observer.disconnect();
  }, []);
  return <div ref={layer} className="footer-orchids" data-visible={visible} aria-hidden="true">
    <span ref={revealPoint} className="footer-orchid-reveal-point" />
    <div className="footer-orchid footer-orchid-left"><OrchidDrawing /></div>
    <div className="footer-orchid footer-orchid-right"><OrchidDrawing /></div>
  </div>;
}
