import geometryUrl from "../assets/illustrations/bogota-particle-map.json?url";

const clamp = value => Math.max(0, Math.min(1, value));
const mix = (a, b, amount) => a + (b - a) * amount;
const ease = (start, end, value) => { const t = clamp((value - start) / (end - start)); return t * t * (3 - 2 * t); };
const random = index => { const value = Math.sin(index * 127.1 + 311.7) * 43758.5453; return value - Math.floor(value); };

// Canvas is decorative. The DOM supplies all copy, links and keyboard controls.
export function mountJourneyParticles(root, canvas, image, onPhase) {
  const context = canvas.getContext("2d", { alpha: true });
  if (!context) return () => {};
  const stage = root.querySelector(".journey-stage");
  const header = document.querySelector(".site-header");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  const mapLayer = document.createElement("canvas");
  const mapContext = mapLayer.getContext("2d");
  const samples = document.createElement("canvas");
  samples.width = 160; samples.height = 90;
  const sampleContext = samples.getContext("2d", { willReadFrequently: true });
  let geometry = { aspect: .71358, paths: [], centers: [] }, destinations = [];
  const controller = new AbortController();
  let width = 1, height = 1, headerHeight = 100, dpr = 1, points = [], frame = 0;
  let progress = 0, target = 0, lastTime = 0, lastPhase = -1, visible = true, destroyed = false;

  function mapBox() {
    const mobile = width <= 760;
    const mapHeight = Math.min(height * (mobile ? .54 : .80), width * (mobile ? 1.05 : .66));
    const mapWidth = mapHeight * geometry.aspect;
    return { x: mobile ? (width - mapWidth) / 2 : width * .73 - mapWidth / 2, y: mobile ? height * .36 : (height - mapHeight) / 2, width: mapWidth, height: mapHeight };
  }

  function prepare() {
    headerHeight = header?.getBoundingClientRect().height || 82;
    root.style.setProperty("--journey-header", `${headerHeight}px`);
    const box = stage.getBoundingClientRect();
    width = Math.max(1, box.width); height = Math.max(1, box.height);
    dpr = Math.min(window.devicePixelRatio || 1, width < 761 ? 1.5 : 2);
    canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
    context.setTransform(dpr, 0, 0, dpr, 0, 0);
    mapLayer.width = canvas.width; mapLayer.height = canvas.height;
    mapContext.setTransform(dpr, 0, 0, dpr, 0, 0);
    const map = mapBox();
    mapContext.lineWidth = .65;
    for (const ring of geometry.paths) {
      mapContext.beginPath();
      ring.forEach(([x, y], index) => mapContext[index ? "lineTo" : "moveTo"](map.x + x * map.width, map.y + y * map.height));
      mapContext.closePath();
      mapContext.fillStyle = "rgba(191,211,150,.075)";
      mapContext.strokeStyle = "rgba(218,229,188,.36)";
      mapContext.fill(); mapContext.stroke();
    }
    let pixels;
    if (image.complete && image.naturalWidth) {
      try { sampleContext.drawImage(image, 0, 0, 160, 90); pixels = sampleContext.getImageData(0, 0, 160, 90).data; }
      catch { /* A static image is still available if pixel sampling is unavailable. */ }
    }
    points = Array.from({ length: width < 761 ? 850 : 2400 }, (_, index) => {
      const u = random(index + 7), v = random(index + 803), seed = random(index + 1601);
      const pixel = (Math.min(89, Math.floor(v * 90)) * 160 + Math.min(159, Math.floor(u * 160))) * 4;
      const destination = destinations.length ? destinations[(index * 97) % destinations.length] : [.5, .5];
      return { x: u * width, y: v * height, tx: map.x + destination[0] * map.width, ty: map.y + destination[1] * map.height,
        bend: (seed - .5) * width * .65, seed, r: pixels?.[pixel] ?? 173, g: pixels?.[pixel + 1] ?? 188, b: pixels?.[pixel + 2] ?? 125 };
    });
    updateTarget();
  }

  function paint(now) {
    const p = progress;
    root.style.setProperty("--journey-progress", p.toFixed(4));
    root.style.setProperty("--journey-city-opacity", (1 - ease(.08, .44, p)).toFixed(4));
    root.style.setProperty("--journey-canvas-opacity", ease(.10, .29, p).toFixed(4));
    root.style.setProperty("--journey-map-opacity", ease(.68, .92, p).toFixed(4));
    root.style.setProperty("--journey-city-scale", (1.02 + p * .18).toFixed(4));
    const alphas = [1 - ease(.16, .31, p), ease(.25, .41, p) * (1 - ease(.59, .74, p)), ease(.69, .86, p)];
    alphas.forEach((alpha, index) => root.style.setProperty(`--journey-copy-${index}`, alpha.toFixed(4)));
    const phase = p < .33 ? 0 : p < .72 ? 1 : 2;
    if (phase !== lastPhase) { lastPhase = phase; onPhase(phase); }
    context.clearRect(0, 0, width, height);
    if (reduced.matches || p < .075) return;
    context.globalAlpha = ease(.52, .92, p);
    context.drawImage(mapLayer, 0, 0, width, height);
    const morph = ease(.12, .91, p), spread = Math.sin(morph * Math.PI);
    context.globalAlpha = mix(.8, .58, morph);
    for (const point of points) {
      const breeze = Math.sin(point.seed * 32 + now * .00035) * spread;
      const x = mix(point.x, point.tx, morph) + point.bend * spread + breeze * 12;
      const y = mix(point.y, point.ty, morph) + Math.cos(point.seed * 30 + morph * 7) * spread * height * .16;
      const tint = ease(.2, .8, morph);
      context.fillStyle = `rgb(${Math.round(mix(point.r, 218, tint))},${Math.round(mix(point.g, 226, tint))},${Math.round(mix(point.b, 162, tint))})`;
      const size = mix(1.2 + point.seed * 1.5, .9 + point.seed * 1.2, morph);
      context.fillRect(x, y, size, size);
    }
    context.globalAlpha = 1;
  }

  function tick(now) {
    frame = 0;
    if (destroyed || document.hidden || !visible) return;
    if (now - lastTime < 30) { frame = requestAnimationFrame(tick); return; }
    lastTime = now;
    progress = reduced.matches ? 0 : mix(progress, target, .22);
    if (Math.abs(progress - target) < .0004) progress = target;
    paint(now);
    if (!reduced.matches && (Math.abs(progress - target) > .0003 || (progress > .11 && progress < .90))) frame = requestAnimationFrame(tick);
  }
  function schedule() { if (!frame && visible && !document.hidden && !destroyed) frame = requestAnimationFrame(tick); }
  function updateTarget() {
    target = reduced.matches ? 0 : clamp((headerHeight - root.getBoundingClientRect().top) / Math.max(1, root.offsetHeight - height));
    schedule();
  }
  function visibility() { if (document.hidden) { cancelAnimationFrame(frame); frame = 0; } else updateTarget(); }
  function motionChanged() { progress = target = 0; prepare(); paint(performance.now()); }
  const resize = new ResizeObserver(prepare);
  resize.observe(stage); if (header) resize.observe(header);
  const intersection = new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting;
    if (visible) updateTarget(); else { cancelAnimationFrame(frame); frame = 0; }
  });
  intersection.observe(root);
  image.addEventListener("load", prepare);
  window.addEventListener("scroll", updateTarget, { passive: true });
  document.addEventListener("visibilitychange", visibility);
  reduced.addEventListener("change", motionChanged);
  prepare(); paint(performance.now());
  fetch(geometryUrl, { signal: controller.signal }).then(response => {
    if (!response.ok) throw new Error("Decorative geometry unavailable");
    return response.json();
  }).then(data => {
    if (destroyed) return;
    geometry = data; destinations = geometry.centers.concat(geometry.paths.flatMap(ring => ring)); prepare();
  }).catch(() => { /* The page remains usable with its static artwork and explorer links. */ });
  return () => {
    destroyed = true; controller.abort(); cancelAnimationFrame(frame); resize.disconnect(); intersection.disconnect();
    image.removeEventListener("load", prepare); window.removeEventListener("scroll", updateTarget);
    document.removeEventListener("visibilitychange", visibility); reduced.removeEventListener("change", motionChanged);
  };
}
