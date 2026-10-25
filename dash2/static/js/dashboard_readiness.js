(function () {
  "use strict";
  if (window.parent === window) return;

  let parentOrigin;
  try {
    parentOrigin = new URL(document.referrer).origin;
    if (!/^https?:$/.test(new URL(parentOrigin).protocol)) return;
  } catch { return; }

  const milestones = { dashboard: 28, data: 58, map: 82 };
  let latest = null;
  let complete = false;
  let disposed = false;
  let timer = 0;
  let observer;
  let watchedGraph;
  let watchedMap;
  let quietMap;
  let quietSince = 0;

  function send(message) {
    window.parent.postMessage(message, parentOrigin);
  }

  function progress(stage) {
    const value = milestones[stage];
    if (latest && latest.progress >= value) return;
    latest = { type: "airquality:dashboard-progress", stage, progress: value };
    send(latest);
  }

  function detachGraph() {
    if (watchedGraph && typeof watchedGraph.removeListener === "function") {
      watchedGraph.removeListener("plotly_afterplot", schedule);
    }
    watchedGraph = null;
  }

  function detachMap() {
    if (watchedMap && typeof watchedMap.off === "function") {
      ["load", "idle", "sourcedata", "styledata"].forEach(name => watchedMap.off(name, schedule));
    }
    watchedMap = null;
    quietMap = null;
    quietSince = 0;
  }

  function stopWatching() {
    window.clearTimeout(timer);
    timer = 0;
    observer?.disconnect();
    detachGraph();
    detachMap();
  }

  function finish() {
    complete = true;
    latest = { type: "airquality:dashboard-ready", stage: "ready", progress: 100 };
    send(latest);
    stopWatching();
  }

  function hasMapData(graph) {
    return Array.isArray(graph?.data) && graph.data.some(trace =>
      (trace.type === "choroplethmapbox" || trace.type === "choroplethmap") &&
      trace.visible !== false && trace.visible !== "legendonly" &&
      trace.locations?.length > 0 &&
      ((typeof trace.geojson === "string" && trace.geojson.length > 0) || trace.geojson?.features?.length > 0));
  }

  function hasRenderedSectors(graph, map) {
    if (typeof map.getSource !== "function" || typeof map.querySourceFeatures !== "function") return false;
    return (graph._fullData || []).some(trace => {
      if ((trace.type !== "choroplethmapbox" && trace.type !== "choroplethmap") ||
          trace.visible === false || trace.visible === "legendonly") return false;
      // Plotly assigns the rendered trace a GeoJSON source after fetching its
      // geometry. Checking this source prevents a failed geometry request from
      // reporting success merely because the basemap tiles have finished.
      const sourceId = trace._glTrace?.sourceId || (trace.uid && "source-" + trace.uid);
      if (!sourceId || !map.getSource(sourceId)) return false;
      return map.querySourceFeatures(sourceId).length > 0;
    });
  }

  function isBusy(container, graph) {
    return container.getAttribute("data-dash-is-loading") === "true" ||
      graph.getAttribute("data-dash-is-loading") === "true" ||
      Boolean(container.querySelector('[data-dash-is-loading="true"]')) ||
      Boolean(graph._promises?.length) || Boolean(graph._redrawPending);
  }

  function check() {
    timer = 0;
    if (disposed || complete) return;

    const root = document.getElementById("react-entry-point");
    if (root?.querySelector("#dashboard-source")) progress("dashboard");
    const container = document.getElementById("bogota_map");
    const graph = container?.matches(".js-plotly-plot") ? container : container?.querySelector(".js-plotly-plot");

    if (graph && graph !== watchedGraph && typeof graph.on === "function") {
      detachGraph();
      watchedGraph = graph;
      graph.on("plotly_afterplot", schedule);
    }

    if (hasMapData(graph) && graph._fullLayout && container) {
      progress("data");
      const subplot = graph._fullLayout.mapbox?._subplot || graph._fullLayout.map?._subplot;
      const map = subplot?.map;
      if (map && map !== watchedMap) {
        detachMap();
        watchedMap = map;
        if (typeof map.on === "function") {
          ["load", "idle", "sourcedata", "styledata"].forEach(name => map.on(name, schedule));
        }
      }
      const canvas = container.querySelector(".mapboxgl-canvas, .maplibregl-canvas");
      if (map && canvas && typeof map.loaded === "function") {
        try {
          const styleReady = typeof map.isStyleLoaded !== "function" || map.isStyleLoaded();
          if (styleReady) progress("map");
          const tilesReady = typeof map.areTilesLoaded !== "function" || map.areTilesLoaded();
          if (styleReady && map.loaded() && tilesReady && hasRenderedSectors(graph, map) && !isBusy(container, graph)) {
            // The initial empty Plotly graph can already have a canvas. Require
            // real sector data and a settled map on two consecutive checks.
            if (quietMap !== map) {
              quietMap = map;
              quietSince = Date.now();
            } else if (Date.now() - quietSince >= 200) {
              finish();
              return;
            }
          } else {
            quietMap = null;
            quietSince = 0;
          }
        } catch {
          // A style swap may briefly invalidate the map. Never treat it as ready.
          quietMap = null;
          quietSince = 0;
        }
      }
    } else {
      quietMap = null;
      quietSince = 0;
    }
    schedule();
  }

  function schedule() {
    if (!disposed && !complete && !timer) timer = window.setTimeout(check, 300);
  }

  function request(event) {
    if (disposed || event.source !== window.parent || event.origin !== parentOrigin ||
        event.data?.type !== "airquality:request-dashboard-state") return;
    if (latest) send(latest);
    if (!complete) schedule();
  }

  function dispose() {
    disposed = true;
    stopWatching();
    window.removeEventListener("message", request);
    window.removeEventListener("pagehide", dispose);
    document.removeEventListener("DOMContentLoaded", initialize);
  }

  function initialize() {
    if (disposed) return;
    const root = document.getElementById("react-entry-point");
    if (root && typeof MutationObserver !== "undefined") {
      observer = new MutationObserver(schedule);
      observer.observe(root, { childList: true, subtree: true, attributes: true, attributeFilter: ["data-dash-is-loading"] });
    }
    check();
  }

  window.addEventListener("message", request);
  window.addEventListener("pagehide", dispose, { once: true });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
  else initialize();
})();
