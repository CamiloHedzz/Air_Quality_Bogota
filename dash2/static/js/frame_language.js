(function () {
  "use strict";
  const language = new URLSearchParams(window.location.search).get("lang") === "en" ? "en" : "es";
  document.documentElement.lang = language;
  document.documentElement.dataset.language = language;
  const translated = {
    "Download plot as a PNG": "Descargar gráfica como PNG", "Download plot": "Descargar gráfica",
    "Zoom": "Zoom", "Pan": "Desplazar", "Zoom in": "Acercar", "Zoom out": "Alejar",
    "Autoscale": "Ajustar escala", "Reset axes": "Restablecer ejes", "Reset view": "Restablecer vista",
    "Box Select": "Seleccionar área", "Lasso Select": "Seleccionar con lazo",
    "Show closest data on hover": "Mostrar el dato más cercano", "Compare data on hover": "Comparar datos al pasar el cursor",
    "Toggle Spike Lines": "Mostrar u ocultar líneas de guía", "Produced with Plotly.js": "Creado con Plotly.js",
    "Double-click on legend to isolate one trace": "Haz doble clic en la leyenda para aislar una serie",
    "Double-click to zoom back out": "Haz doble clic para restablecer el zoom",
  };
  const spanish = {
    moduleType: "locale", name: "es", dictionary: translated,
    format: {
      days: ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"],
      shortDays: ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"],
      months: ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
      shortMonths: ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
      date: "%d/%m/%Y", decimal: ",", thousands: "."
    }
  };
  let registered = false;
  function register() {
    if (!registered && window.Plotly) {
      window.Plotly.register(spanish);
      registered = true;
    }
  }
  function initialize() {
    new MutationObserver(register).observe(document.body, { childList: true, subtree: true });
    register();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
  else initialize();
})();
