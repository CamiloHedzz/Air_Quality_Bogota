import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { useLocation } from "react-router-dom";

const revealSelector = [
  "#aboutinit .intro-eyebrow", "#intro-heading", "#aboutinit .intro-description",
  "#aboutinit .intro-actions", "#aboutinit .intro-variables", ".air-context-heading",
  ".air-context-reasons article", ".about-profile section", ".about-details .about-panel > h2",
  ".about-details .about-panel > p", ".predictions-intro", ".prediction-coverage > summary",
  ".prediction-panel-heading", ".footer-content > p",
].join(",");

export function EditorialScroll() {
  const { pathname } = useLocation();

  useEffect(() => {
    // About already manages its own independent text column.
    if (pathname.toLowerCase() === "/about") return;
    const enabled = window.matchMedia("(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)");
    let frame = 0;
    let target = window.scrollY;
    let previousTime = 0;

    function stop() {
      cancelAnimationFrame(frame);
      frame = 0;
      target = window.scrollY;
    }

    function animate(now) {
      const current = window.scrollY;
      const difference = target - current;
      const elapsed = Math.min(32, now - previousTime || 16);
      previousTime = now;
      if (Math.abs(difference) < 0.8) {
        window.scrollTo({ top: target, behavior: "instant" });
        frame = 0;
        return;
      }
      window.scrollTo({ top: current + difference * (1 - Math.exp(-elapsed / 65)), behavior: "instant" });
      frame = requestAnimationFrame(animate);
    }

    function wheel(event) {
      if (!enabled.matches || event.defaultPrevented || event.ctrlKey || event.metaKey || event.shiftKey ||
          Math.abs(event.deltaX) > Math.abs(event.deltaY) || !(event.target instanceof Element) ||
          event.target.closest("iframe, input, textarea, select, [contenteditable], [role=dialog], [data-native-scroll]") ||
          !event.target.closest("#aboutinit, #why-air-matters, .editorial-header, .site-footer, .predictions-intro")) {
        stop();
        return;
      }
      const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? window.innerHeight : 1;
      const maximum = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
      const next = Math.max(0, Math.min(maximum, (frame ? target : window.scrollY) + event.deltaY * unit));
      if (Math.abs(next - window.scrollY) < 0.8) return;
      event.preventDefault();
      target = next;
      if (!frame) { previousTime = performance.now(); frame = requestAnimationFrame(animate); }
    }

    function key(event) { if (["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End", " ", "Tab"].includes(event.key)) stop(); }
    window.addEventListener("wheel", wheel, { passive: false });
    window.addEventListener("pointerdown", stop, { passive: true });
    window.addEventListener("keydown", key);
    enabled.addEventListener("change", stop);
    return () => {
      stop();
      window.removeEventListener("wheel", wheel);
      window.removeEventListener("pointerdown", stop);
      window.removeEventListener("keydown", key);
      enabled.removeEventListener("change", stop);
    };
  }, [pathname]);

  return null;
}

export function ContentMotion() {
  const { pathname } = useLocation();

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    const marked = new Set();
    let intersection;
    let mutations;

    function show(element) {
      element.dataset.reveal = "visible";
      intersection?.unobserve(element);
    }

    function register(element) {
      if (marked.has(element)) return;
      marked.add(element);
      element.dataset.reveal = "pending";
      // Short local staggering keeps long pages from accumulating delays.
      const siblings = Array.from(element.parentElement.children).filter(node => node.matches(revealSelector));
      element.style.setProperty("--reveal-delay", `${Math.min(siblings.indexOf(element), 3) * 65}ms`);
      intersection.observe(element);
    }

    function scan(node) {
      if (!(node instanceof Element) || node.closest("svg, canvas, iframe, .js-plotly-plot, .prediction-chart-scroll")) return;
      if (node.matches(revealSelector)) register(node);
      node.querySelectorAll(revealSelector).forEach(register);
    }

    function clear() {
      intersection?.disconnect();
      mutations?.disconnect();
      marked.forEach(element => {
        delete element.dataset.reveal;
        element.style.removeProperty("--reveal-delay");
      });
      marked.clear();
    }

    function setup() {
      clear();
      if (reduced.matches || !window.IntersectionObserver) return;
      intersection = new IntersectionObserver(entries => {
        entries.forEach(entry => { if (entry.isIntersecting) show(entry.target); });
      }, { threshold: 0.12, rootMargin: "0px 0px -24px 0px" });
      scan(document.querySelector(".app-shell"));
      mutations = new MutationObserver(records => {
        records.forEach(record => record.addedNodes.forEach(scan));
      });
      mutations.observe(document.querySelector(".app-shell"), { childList: true, subtree: true });
    }

    function revealFocused(event) {
      const parent = event.target.closest('[data-reveal="pending"]');
      if (parent) show(parent);
    }

    setup();
    reduced.addEventListener("change", setup);
    document.addEventListener("focusin", revealFocused);
    return () => {
      clear();
      reduced.removeEventListener("change", setup);
      document.removeEventListener("focusin", revealFocused);
    };
  }, [pathname]);

  return null;
}

export function SquareCursor() {
  const layerRef = useRef(null);
  const coreRef = useRef(null);
  const trailRef = useRef(null);

  useEffect(() => {
    const media = window.matchMedia("(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)");
    const layer = layerRef.current;
    const core = coreRef.current;
    const trail = trailRef.current;
    const root = document.documentElement;
    let frame = 0;
    let points = [];
    let pointer = null;

    function hide() {
      cancelAnimationFrame(frame);
      frame = 0;
      points = [];
      pointer = null;
      layer.dataset.visible = "false";
      root.classList.remove("aq-cursor-active");
      trail.removeAttribute("d");
    }

    function draw(now) {
      frame = 0;
      if (!pointer) return;
      points = points.filter(point => now - point.time < 135);
      const previous = points[points.length - 1];
      if (now - pointer.time < 135 && (!previous || Math.hypot(pointer.x - previous.x, pointer.y - previous.y) > 0.3)) {
        points.push({ ...pointer });
      }

      // Limit the trail to 56 px even after fast movements or wide jumps.
      const short = [];
      let length = 0;
      for (let index = points.length - 1; index >= 0; index -= 1) {
        const point = points[index];
        const next = short[short.length - 1];
        if (next) {
          const distance = Math.hypot(point.x - next.x, point.y - next.y);
          if (length + distance > 56) {
            const ratio = (56 - length) / distance;
            short.push({ x: next.x + (point.x - next.x) * ratio, y: next.y + (point.y - next.y) * ratio });
            break;
          }
          length += distance;
        }
        short.push(point);
      }
      trail.setAttribute("d", short.map((point, index) => `${index ? "L" : "M"}${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(" "));
      core.style.transform = `translate3d(${pointer.x}px, ${pointer.y}px, 0)`;
      if (points.length || now - pointer.time < 150) frame = requestAnimationFrame(draw);
    }

    function move(event) {
      if (!media.matches || event.pointerType === "touch" || !(event.target instanceof Element) ||
          event.target.closest("iframe, input, textarea, select, [contenteditable], [data-native-cursor]")) {
        hide();
        return;
      }
      pointer = { x: event.clientX, y: event.clientY, time: performance.now() };
      layer.dataset.visible = "true";
      layer.dataset.interactive = Boolean(event.target.closest("a, button, summary, label")).toString();
      root.classList.add("aq-cursor-active");
      if (!frame) frame = requestAnimationFrame(draw);
    }

    function leave(event) { if (!event.relatedTarget) hide(); }
    function visibility() { if (document.hidden) hide(); }

    window.addEventListener("pointermove", move, { passive: true, capture: true });
    window.addEventListener("pointerover", move, { passive: true, capture: true });
    window.addEventListener("pointerout", leave, { passive: true });
    window.addEventListener("blur", hide);
    window.addEventListener("scroll", hide, { passive: true });
    document.addEventListener("visibilitychange", visibility);
    media.addEventListener("change", hide);
    return () => {
      hide();
      window.removeEventListener("pointermove", move, true);
      window.removeEventListener("pointerover", move, true);
      window.removeEventListener("pointerout", leave);
      window.removeEventListener("blur", hide);
      window.removeEventListener("scroll", hide);
      document.removeEventListener("visibilitychange", visibility);
      media.removeEventListener("change", hide);
    };
  }, []);

  return createPortal(
    <div ref={layerRef} className="square-cursor" aria-hidden="true" data-visible="false">
      <svg className="cursor-trail"><path ref={trailRef} /></svg>
      <span ref={coreRef} className="cursor-position"><span className="cursor-square" /></span>
    </div>, document.body,
  );
}
