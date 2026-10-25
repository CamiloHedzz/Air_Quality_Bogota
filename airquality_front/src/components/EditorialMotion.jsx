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
    const paths = Array.from(trailRef.current.querySelectorAll("path"));
    const frameSelector = "iframe.dashboard-frame, iframe.prediction-plotly-frame";
    const connectedFrames = new WeakSet();
    let frame = 0;
    let points = [];
    let pointer = null;
    let follower = null;
    let lastSample = null;
    let lastFrame = 0;

    function hide() {
      cancelAnimationFrame(frame);
      frame = 0;
      points = [];
      pointer = null;
      follower = null;
      lastSample = null;
      lastFrame = 0;
      layer.dataset.visible = "false";
      paths.forEach(path => path.removeAttribute("d"));
    }

    function draw(now) {
      frame = 0;
      if (!pointer || !follower) return;
      const elapsed = Math.min(64, now - lastFrame || 16);
      lastFrame = now;
      const target = { x: pointer.x + 12, y: pointer.y + 12 };
      const easing = 1 - Math.exp(-elapsed / 90);
      follower.x += (target.x - follower.x) * easing;
      follower.y += (target.y - follower.y) * easing;
      const remaining = Math.hypot(target.x - follower.x, target.y - follower.y);
      if (remaining < 0.1) follower = target;
      points = points.filter(point => now - point.time < 600);
      if (!lastSample || Math.hypot(follower.x - lastSample.x, follower.y - lastSample.y) > 0.35) {
        lastSample = { ...follower, time: now };
        points.push(lastSample);
      }

      // Bound distance as well as age, so a fast sweep cannot fill the screen.
      const recent = [];
      let length = 0;
      for (let index = points.length - 1; index >= 0; index -= 1) {
        const point = points[index];
        const next = recent[recent.length - 1];
        if (next) {
          const distance = Math.hypot(point.x - next.x, point.y - next.y);
          if (length + distance > 220) {
            const ratio = (220 - length) / distance;
            recent.push({ x: next.x + (point.x - next.x) * ratio, y: next.y + (point.y - next.y) * ratio, time: point.time });
            break;
          }
          length += distance;
        }
        recent.push(point);
      }
      recent.reverse();
      const count = Math.min(paths.length, Math.max(0, recent.length - 1));
      const sample = index => recent[Math.round(index * (recent.length - 1) / count)];
      paths.forEach((path, index) => {
        if (index >= count) { path.removeAttribute("d"); return; }
        const from = sample(index);
        const to = sample(index + 1);
        const before = sample(Math.max(0, index - 1));
        const after = sample(Math.min(count, index + 2));
        const c1 = { x: from.x + (to.x - before.x) / 6, y: from.y + (to.y - before.y) / 6 };
        const c2 = { x: to.x - (after.x - from.x) / 6, y: to.y - (after.y - from.y) / 6 };
        const positionFade = Math.pow((index + 1) / count, 1.6);
        const ageFade = Math.pow(Math.max(0, 1 - (now - to.time) / 600), 1.3);
        path.setAttribute("opacity", (0.88 * positionFade * ageFade).toFixed(3));
        path.setAttribute("d", `M${from.x.toFixed(1)},${from.y.toFixed(1)} C${c1.x.toFixed(1)},${c1.y.toFixed(1)} ${c2.x.toFixed(1)},${c2.y.toFixed(1)} ${to.x.toFixed(1)},${to.y.toFixed(1)}`);
      });
      core.style.transform = `translate3d(${follower.x}px, ${follower.y}px, 0)`;
      if (remaining >= 0.1 || points.length) frame = requestAnimationFrame(draw);
    }

    function follow(x, y, interactive) {
      if (!media.matches) { hide(); return; }
      pointer = { x, y };
      if (!follower) follower = { x: x + 12, y: y + 12 };
      layer.dataset.visible = "true";
      layer.dataset.interactive = Boolean(interactive).toString();
      if (!frame) { lastFrame = performance.now(); frame = requestAnimationFrame(draw); }
    }

    function move(event) {
      if (!media.matches || event.pointerType === "touch" || !(event.target instanceof Element) ||
          event.target.closest("input, textarea, select, [contenteditable], [data-native-cursor]")) {
        hide();
        return;
      }
      const embedded = event.target.closest("iframe");
      if (embedded) {
        if (!connectedFrames.has(embedded)) hide();
        return;
      }
      follow(event.clientX, event.clientY, event.target.closest("a, button, summary, label"));
    }

    function connect(embedded, enabled = true) {
      try {
        const origin = new URL(embedded.src, window.location.href).origin;
        embedded.contentWindow?.postMessage({ type: "airquality:cursor-bridge", enabled }, origin);
      } catch { /* A frame navigating away can reconnect on its next load. */ }
    }

    function frameLoad(event) {
      if (event.target instanceof Element && event.target.matches(frameSelector)) connect(event.target);
    }

    function receive(event) {
      if (!event.data || typeof event.data.type !== "string" || !event.data.type.startsWith("airquality:cursor-")) return;
      const embedded = Array.from(document.querySelectorAll(frameSelector)).find(item => item.contentWindow === event.source);
      if (!embedded) return;
      let origin;
      try { origin = new URL(embedded.src, window.location.href).origin; } catch { return; }
      if (event.origin !== origin) return;
      const data = event.data;
      if (data.type === "airquality:cursor-ready") { connect(embedded); return; }
      if (data.type === "airquality:cursor-connected") {
        if (data.enabled === true) connectedFrames.add(embedded);
        else connectedFrames.delete(embedded);
        return;
      }
      if (!connectedFrames.has(embedded)) return;
      if (data.type === "airquality:cursor-leave") {
        // Crossing an iframe boundary keeps the same follower and trail alive.
        if (!document.documentElement.matches(":hover")) hide();
        return;
      }
      if (data.type !== "airquality:cursor-move") return;
      if (data.visible !== true) { hide(); return; }
      if (![data.x, data.y, data.width, data.height].every(Number.isFinite) ||
          data.width <= 0 || data.height <= 0 || data.x < 0 || data.y < 0 ||
          data.x > data.width || data.y > data.height) return;
      const rect = embedded.getBoundingClientRect();
      const scaleX = rect.width / embedded.offsetWidth;
      const scaleY = rect.height / embedded.offsetHeight;
      const x = rect.left + (embedded.clientLeft + data.x * embedded.clientWidth / data.width) * scaleX;
      const y = rect.top + (embedded.clientTop + data.y * embedded.clientHeight / data.height) * scaleY;
      if (!Number.isFinite(x) || !Number.isFinite(y)) return;
      follow(x, y, data.interactive === true);
    }

    function leave(event) {
      if (!event.relatedTarget && !document.documentElement.matches(":hover")) hide();
    }
    function visibility() { if (document.hidden) hide(); }

    window.addEventListener("message", receive);
    document.addEventListener("load", frameLoad, true);
    document.querySelectorAll(frameSelector).forEach(embedded => connect(embedded));
    window.addEventListener("pointermove", move, { passive: true, capture: true });
    window.addEventListener("pointerover", move, { passive: true, capture: true });
    window.addEventListener("pointerout", leave, { passive: true });
    window.addEventListener("blur", hide);
    window.addEventListener("scroll", hide, { passive: true });
    document.addEventListener("visibilitychange", visibility);
    media.addEventListener("change", hide);
    return () => {
      hide();
      window.removeEventListener("message", receive);
      document.removeEventListener("load", frameLoad, true);
      document.querySelectorAll(frameSelector).forEach(embedded => connect(embedded, false));
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
      <svg ref={trailRef} className="cursor-trail">
        {Array.from({ length: 32 }, (_, index) => <path key={index} />)}
      </svg>
      <span ref={coreRef} className="cursor-position"><span className="cursor-square" /></span>
    </div>, document.body,
  );
}
