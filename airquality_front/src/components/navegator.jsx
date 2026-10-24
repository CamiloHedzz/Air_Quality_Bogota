import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link, NavLink, useLocation } from "react-router-dom";

const destinations = [
  { to: "/", label: "Inicio", detail: "Observa tu ciudad", number: "01" },
  { to: "/About", label: "El proyecto", detail: "Ideas, datos y personas", number: "02" },
  { to: "/Predictions", label: "Predicciones", detail: "Explora otras perspectivas", number: "03" },
];

export function Navegation() {
  const { pathname, hash } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const headerRef = useRef(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const closeRef = useRef(null);
  const current = destinations.find(item => item.to.toLowerCase() === pathname.toLowerCase()) || destinations[0];

  useEffect(() => { setMenuOpen(false); }, [pathname, hash]);

  useEffect(() => {
    let frame = 0;
    function update() {
      frame = 0;
      headerRef.current?.classList.toggle("is-scrolled", window.scrollY > 16);
    }
    function scroll() { if (!frame) frame = requestAnimationFrame(update); }
    update();
    window.addEventListener("scroll", scroll, { passive: true });
    return () => { cancelAnimationFrame(frame); window.removeEventListener("scroll", scroll); };
  }, []);

  useEffect(() => {
    if (!menuOpen) return;
    const shell = document.querySelector(".app-shell");
    const trigger = triggerRef.current;
    const previousInert = shell.inert;
    const previousOverflow = document.body.style.overflow;
    shell.inert = true;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus({ preventScroll: true });

    function keys(event) {
      if (event.key === "Escape") { event.preventDefault(); setMenuOpen(false); }
      if (event.key !== "Tab") return;
      const items = Array.from(menuRef.current.querySelectorAll("a[href], button:not([disabled])"));
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    document.addEventListener("keydown", keys);
    return () => {
      shell.inert = previousInert;
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", keys);
      trigger?.focus({ preventScroll: true });
    };
  }, [menuOpen]);

  return (
    <>
      <header ref={headerRef} className="site-header editorial-header">
        <div className="site-brand">
          <h1><Link to="/" aria-label="Air Quality Bogotá · inicio">
            <span className="brand-mark" aria-hidden="true">
              <svg viewBox="0 0 45.46 46.82" focusable="false">
                <g className="brand-letter-reveal">
                  <text className="brand-monogram-letter" x="10.22" y="34.58">B</text>
                </g>
                <g className="brand-bar-reveal">
                  <rect className="brand-monogram-bar" y="4.14" width="9" height="32.5" />
                </g>
              </svg>
            </span>
            <span>Air Quality<span className="brand-city">Bogotá</span></span>
          </Link></h1>
        </div>
        <p className="header-location"><span className="header-location-dot" />{current.detail}</p>
        <div className="header-actions">
          <nav className="site-navigation" aria-label="Navegación principal"><ul>
            {destinations.map(item => <li key={item.to}><NavLink to={item.to} end={item.to === "/"}>{item.label}</NavLink></li>)}
          </ul></nav>
          <button ref={triggerRef} className="menu-toggle" type="button" aria-expanded={menuOpen}
            aria-controls="global-menu" aria-label="Abrir menú" onClick={() => setMenuOpen(true)}>
            <span>Menú</span><span className="menu-toggle-icon" aria-hidden="true"><i /><i /></span>
          </button>
        </div>
      </header>

      {menuOpen && createPortal(
        <div id="global-menu" ref={menuRef} className="global-menu" role="dialog" aria-modal="true" aria-labelledby="menu-heading" onWheel={event => event.stopPropagation()}>
          <div className="global-menu-top"><p>AIR QUALITY BOGOTÁ<span>Una ciudad que respira.</span></p>
            <button ref={closeRef} type="button" className="menu-close" aria-label="Cerrar menú" onClick={() => setMenuOpen(false)}>
              <span>Cerrar</span><span aria-hidden="true">×</span>
            </button>
          </div>
          <h2 id="menu-heading" className="motion-sr-only">Explora Air Quality Bogotá</h2>
          <div className="global-menu-body">
            <nav aria-label="Explorar el sitio" className="menu-destinations">
              {destinations.map(item => <NavLink key={item.to} to={item.to} end={item.to === "/"}
                className="menu-destination" onClick={() => setMenuOpen(false)}>
                <span className="menu-destination-number">{item.number}</span>
                <span className="menu-destination-name">{item.label}<span aria-hidden="true">↗</span></span>
                <span className="menu-destination-detail">{item.detail}</span>
              </NavLink>)}
            </nav>
            <aside className="menu-aside">
              <div className="menu-art" aria-hidden="true"><span className="menu-art-orbit" /><span className="menu-art-orbit" />
                <span className="menu-art-node" /><span className="menu-art-node" /><span className="menu-art-node" />
                <span className="menu-art-label">AIRE<br />TERRITORIO<br />BOGOTÁ.</span><span className="menu-art-coordinate">04° N / 74° O</span>
              </div>
              <p>Conecta los datos<br />con tu entorno.</p>
              <Link className="menu-map-link" to="/#dashboard" onClick={() => setMenuOpen(false)}>Explorar el dashboard <span aria-hidden="true">↗</span></Link>
            </aside>
          </div>
          <div className="global-menu-bottom"><span>BOGOTÁ, COLOMBIA</span><span>DATOS · TERRITORIO · AIRE</span>
            <a href="mailto:camilohedzz@gmail.com">Hablemos <span aria-hidden="true">↗</span></a></div>
        </div>, document.body,
      )}
    </>
  );
}
