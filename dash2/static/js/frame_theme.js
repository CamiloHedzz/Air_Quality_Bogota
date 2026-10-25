(function () {
  "use strict";
  const root = document.documentElement;
  const key = "airquality-theme";
  let theme = "light";
  try { if (localStorage.getItem(key) === "dark") theme = "dark"; } catch { /* Storage is optional. */ }
  root.dataset.theme = theme;
  let parentOrigin = null;
  if (window.parent !== window) {
    try { parentOrigin = new URL(document.referrer).origin; } catch { /* Standalone dashboard. */ }
  }
  const records = new WeakMap();
  const colors = { "#314e62": "#9bc8ea", "#827b10": "#e5db37", "#4d7c89": "#7dc6d6", "#85877d": "#b1bbab" };
  let queued = false;

  function get(object, path) {
    return path.replace(/\[(\d+)\]/g, ".$1").split(".").reduce((value, part) => value?.[part], object);
  }
  function schedule() {
    if (queued) return;
    queued = true;
    window.setTimeout(function () {
      queued = false;
      document.querySelectorAll(".js-plotly-plot").forEach(paint);
    }, 60);
  }

  async function paint(graph) {
    if (!window.Plotly || !graph.layout || !graph.data || !graph._fullLayout || !graph.on || !graph.isConnected) return;
    let record = records.get(graph);
    if (!record) {
      record = { original: new Map(), applied: new Map(), traceOriginal: new Map(), traceApplied: new Map(), busy: false };
      records.set(graph, record);
      graph.on("plotly_afterplot", schedule);
    }
    if (record.busy) return;
    const dark = theme === "dark";
    const prediction = Boolean(document.getElementById("prediction-plot-root"));
    const ink = dark ? "#e8eddf" : null;
    const panel = dark ? (prediction ? "#192720" : "#101b17") : null;
    const grid = "#35483c";
    const layout = {};
    function field(path, value) {
      const current = get(graph.layout, path);
      if (dark) {
        if (!record.applied.has(path) || current !== record.applied.get(path)) record.original.set(path, current ?? null);
      } else if (!record.original.has(path)) return;
      const next = dark ? value : record.original.get(path);
      if ((current ?? null) !== next) {
        layout[path] = next;
        record.applied.set(path, next);
      }
    }
    field("paper_bgcolor", panel);
    field("plot_bgcolor", panel);
    field("font.color", ink);
    field("title.font.color", ink);
    field("legend.font.color", ink);
    field("legend.title.font.color", ink);
    field("legend.bgcolor", "rgba(0,0,0,0)");
    field("hoverlabel.bgcolor", "#22332a");
    field("hoverlabel.font.color", ink);
    field("hoverlabel.bordercolor", "#52634a");
    Object.keys(graph._fullLayout).filter(name => /^[xy]axis\d*$/.test(name)).forEach(function (axis) {
      field(axis + ".color", ink);
      field(axis + ".gridcolor", grid);
      field(axis + ".zerolinecolor", "#52634a");
      field(axis + ".linecolor", "#52634a");
      field(axis + ".tickfont.color", ink);
      field(axis + ".title.font.color", ink);
    });
    (graph.layout.annotations || []).forEach(function (annotation, index) {
      field("annotations[" + index + "].font.color", ink);
      if (annotation.bgcolor && annotation.bgcolor !== "rgba(0,0,0,0)") field("annotations[" + index + "].bgcolor", panel);
    });
    (graph.layout.shapes || []).forEach(function (shape, index) {
      const color = shape.line?.color;
      if (typeof color === "string") field("shapes[" + index + "].line.color", colors[color.toLowerCase()] || color);
    });
    // Only the automatic basemap follows the site; explicit choices remain available.
    if (graph.layout.meta?.airqualityAutoBasemap && graph.layout.mapbox) {
      const style = "https://tiles.openfreemap.org/styles/" + (dark ? "dark" : "liberty");
      if (graph.layout.mapbox.style !== style) layout["mapbox.style"] = style;
    }
    const traces = [];
    graph.data.forEach(function (trace, index) {
      const update = {};
      ["line.color", "marker.color", "marker.line.color"].forEach(function (path) {
        const current = get(trace, path);
        if (typeof current !== "string") return;
        const traceKey = index + ":" + path;
        if (dark && colors[current.toLowerCase()]) {
          record.traceOriginal.set(traceKey, current);
          record.traceApplied.set(traceKey, colors[current.toLowerCase()]);
          update[path] = colors[current.toLowerCase()];
        } else if (!dark && record.traceApplied.get(traceKey) === current) {
          update[path] = record.traceOriginal.get(traceKey);
        }
      });
      if (trace.colorbar) {
        ["colorbar.tickfont.color", "colorbar.title.font.color"].forEach(function (path) {
          const traceKey = index + ":" + path;
          const current = get(trace, path);
          if (dark) {
            if (!record.traceApplied.has(traceKey) || current !== record.traceApplied.get(traceKey)) record.traceOriginal.set(traceKey, current ?? null);
            if (current !== ink) { update[path] = ink; record.traceApplied.set(traceKey, ink); }
          } else if (record.traceOriginal.has(traceKey) && (current ?? null) !== record.traceOriginal.get(traceKey)) update[path] = record.traceOriginal.get(traceKey);
        });
      }
      if (Object.keys(update).length) traces.push([index, update]);
    });
    if (!Object.keys(layout).length && !traces.length) return;
    record.busy = true;
    try {
      if (Object.keys(layout).length) await window.Plotly.relayout(graph, layout);
      for (const [index, update] of traces) {
        if (graph.isConnected) await window.Plotly.restyle(graph, update, [index]);
      }
    } catch { /* A Dash callback can replace a graph while its theme is updating. */ }
    finally { record.busy = false; schedule(); }
  }

  function apply(value) {
    if (value !== "light" && value !== "dark") return;
    theme = value;
    root.dataset.theme = value;
    try { localStorage.setItem(key, value); } catch { /* Storage is optional. */ }
    schedule();
  }
  window.addEventListener("message", function (event) {
    if (event.source !== window.parent || !parentOrigin || event.origin !== parentOrigin ||
        event.data?.type !== "airquality:theme") return;
    apply(event.data.theme);
  });
  function ready() {
    if (parentOrigin) window.parent.postMessage({ type: "airquality:theme-ready" }, parentOrigin);
  }
  function initialize() {
    new MutationObserver(schedule).observe(document.body, { childList: true, subtree: true });
    window.addEventListener("load", function () { ready(); schedule(); });
    ready();
    schedule();
  }
  ready();
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
  else initialize();
})();
