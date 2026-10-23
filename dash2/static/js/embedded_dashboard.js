(function () {
  if (window.parent === window) return;

  document.documentElement.dataset.airqualityEmbedded = "true";
  let parentOrigin;
  try {
    parentOrigin = new URL(document.referrer).origin;
  } catch {
    return;
  }

  function initialize() {
    const root = document.getElementById("react-entry-point");
    if (!root) return;
    let scheduled = false;
    let previousHeight = 0;

    function scheduleHeight() {
      if (scheduled) return;
      scheduled = true;
      window.requestAnimationFrame(function () {
        scheduled = false;
        const height = Math.ceil(root.getBoundingClientRect().bottom + window.scrollY);
        if (height < 100 || height === previousHeight) return;
        previousHeight = height;
        window.parent.postMessage({ type: "airquality:dashboard-height", height }, parentOrigin);
      });
    }

    new ResizeObserver(scheduleHeight).observe(root);
    window.addEventListener("resize", scheduleHeight);
    window.addEventListener("load", scheduleHeight);
    window.addEventListener("message", function (event) {
      if (event.source === window.parent && event.origin === parentOrigin &&
          event.data?.type === "airquality:request-dashboard-height") {
        previousHeight = 0;
        scheduleHeight();
      }
    });
    if (document.fonts) document.fonts.ready.then(scheduleHeight);
    scheduleHeight();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();
