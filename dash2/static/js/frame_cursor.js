(function () {
  if (window.parent === window) return;

  function initialize() {
    if (document.getElementById("airquality-frame-cursor")) return;
    const layer = document.createElement("div");
    layer.id = "airquality-frame-cursor";
    layer.setAttribute("aria-hidden", "true");
    layer.dataset.visible = "false";
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    const trail = document.createElementNS("http://www.w3.org/2000/svg", "path");
    svg.appendChild(trail);
    const core = document.createElement("span");
    core.className = "frame-cursor-position";
    const square = document.createElement("span");
    square.className = "frame-cursor-square";
    core.appendChild(square);
    layer.append(svg, core);
    document.body.appendChild(layer);

    const media = window.matchMedia("(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)");
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
      root.classList.remove("aq-frame-cursor-active");
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
          event.target.closest("input, textarea, select, [contenteditable], [data-native-cursor]")) {
        hide();
        return;
      }
      pointer = { x: event.clientX, y: event.clientY, time: performance.now() };
      layer.dataset.visible = "true";
      layer.dataset.interactive = Boolean(event.target.closest("a, button, summary, label, .modebar-btn")).toString();
      root.classList.add("aq-frame-cursor-active");
      if (!frame) frame = requestAnimationFrame(draw);
    }

    // Capture observes movement even when Plotly handles a drag itself.
    // All listeners are passive: chart clicks, panning and zoom remain native.
    document.addEventListener("pointermove", move, { passive: true, capture: true });
    document.addEventListener("pointerover", move, { passive: true, capture: true });
    document.addEventListener("pointerout", event => { if (!event.relatedTarget) hide(); }, { passive: true });
    window.addEventListener("blur", hide);
    window.addEventListener("scroll", hide, { passive: true });
    document.addEventListener("visibilitychange", () => { if (document.hidden) hide(); });
    media.addEventListener("change", hide);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
  else initialize();
})();
