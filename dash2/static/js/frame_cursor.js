(function () {
  if (window.parent === window) return;

  function initialize() {
    if (document.getElementById("airquality-frame-cursor")) return;
    const layer = document.createElement("div");
    layer.id = "airquality-frame-cursor";
    layer.setAttribute("aria-hidden", "true");
    layer.dataset.visible = "false";
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    const paths = Array.from({ length: 32 }, () => document.createElementNS("http://www.w3.org/2000/svg", "path"));
    paths.forEach(path => svg.appendChild(path));
    const core = document.createElement("span");
    core.className = "frame-cursor-position";
    const square = document.createElement("span");
    square.className = "frame-cursor-square";
    core.appendChild(square);
    layer.append(svg, core);
    document.body.appendChild(layer);

    const media = window.matchMedia("(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)");
    let frame = 0;
    let points = [];
    let pointer = null;
    let follower = null;
    let lastSample = null;
    let lastFrame = 0;
    let delegated = false;
    let parentOrigin;
    try { parentOrigin = new URL(document.referrer).origin; } catch { /* Keep the local fallback. */ }

    function notify(message) {
      if (parentOrigin) window.parent.postMessage(message, parentOrigin);
    }

    function bridge(event) {
      if (event.source !== window.parent || event.origin !== parentOrigin ||
          event.data?.type !== "airquality:cursor-bridge" || typeof event.data.enabled !== "boolean") return;
      delegated = event.data.enabled;
      document.documentElement.dataset.airqualityCursorBridge = delegated ? "shared" : "local";
      hide();
      notify({ type: "airquality:cursor-connected", enabled: delegated });
    }

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

    function move(event) {
      if (!media.matches || event.pointerType === "touch" || !(event.target instanceof Element) ||
          event.target.closest("input, textarea, select, [contenteditable], [data-native-cursor]")) {
        hide();
        if (delegated) notify({ type: "airquality:cursor-move", visible: false });
        return;
      }
      if (delegated) {
        notify({ type: "airquality:cursor-move", visible: true,
          x: event.clientX, y: event.clientY, width: window.innerWidth, height: window.innerHeight,
          interactive: Boolean(event.target.closest("a, button, summary, label, .modebar-btn")) });
        return;
      }
      pointer = { x: event.clientX, y: event.clientY };
      if (!follower) follower = { x: pointer.x + 12, y: pointer.y + 12 };
      layer.dataset.visible = "true";
      layer.dataset.interactive = Boolean(event.target.closest("a, button, summary, label, .modebar-btn")).toString();
      if (!frame) { lastFrame = performance.now(); frame = requestAnimationFrame(draw); }
    }

    // Capture observes movement even when Plotly handles a drag itself.
    // All listeners are passive: chart clicks, panning and zoom remain native.
    document.addEventListener("pointermove", move, { passive: true, capture: true });
    document.addEventListener("pointerover", move, { passive: true, capture: true });
    document.addEventListener("pointerdown", move, { passive: true, capture: true });
    document.addEventListener("pointerout", event => {
      if (!event.relatedTarget) {
        hide();
        if (delegated) notify({ type: "airquality:cursor-leave" });
      }
    }, { passive: true });
    window.addEventListener("message", bridge);
    notify({ type: "airquality:cursor-ready" });
    window.addEventListener("blur", hide);
    window.addEventListener("scroll", hide, { passive: true });
    document.addEventListener("visibilitychange", () => { if (document.hidden) hide(); });
    media.addEventListener("change", hide);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
  else initialize();
})();
