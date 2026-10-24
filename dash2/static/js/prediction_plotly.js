(function () {
  if (window.parent === window) return;
  let parentOrigin;
  try { parentOrigin = new URL(document.referrer).origin; } catch { return; }
  const key = new URLSearchParams(window.location.search).get("frameKey");
  function initialize() {
    const root = document.getElementById("react-entry-point");
    if (!root) return;
    let scheduled = false, previous = 0;
    function schedule() {
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(function () {
        scheduled = false;
        const height = Math.ceil(root.getBoundingClientRect().bottom + window.scrollY);
        if (height < 100 || height === previous) return;
        previous = height;
        window.parent.postMessage({type:"airquality:prediction-plot-height", height, key}, parentOrigin);
      });
    }
    new ResizeObserver(schedule).observe(root);
    window.addEventListener("resize", schedule);
    window.addEventListener("load", schedule);
    window.addEventListener("message", function (event) {
      if (event.source === window.parent && event.origin === parentOrigin && event.data?.type === "airquality:request-prediction-plot-height") { previous = 0; schedule(); }
    });
    if (document.fonts) document.fonts.ready.then(schedule);
    schedule();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, {once:true});
  else initialize();
})();
