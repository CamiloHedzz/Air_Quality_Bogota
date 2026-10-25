export const routeErrors = {
  invalid_point: "Selecciona un origen y un destino de la búsqueda.",
  outside_bogota: "Elige dos puntos dentro de la zona urbana de Bogotá.",
  points_too_close: "El origen y el destino deben estar separados al menos 200 metros.",
  trip_too_long: "Prueba un recorrido de menos de 25 km en línea recta.",
  invalid_time: "Revisa la hora, el día y el contaminante.",
  invalid_search: "Escribe al menos tres caracteres para buscar un lugar.",
  search_busy: "Espera un momento antes de buscar otro lugar.",
  router_busy: "Hay una consulta de rutas en curso. Inténtalo en un momento.",
  provider_unavailable: "El servicio de rutas o lugares no está disponible. Intenta de nuevo.",
  invalid_route: "No encontramos una ruta de bicicleta válida entre estos puntos. Prueba lugares cercanos.",
  data_unavailable: "No pudimos cargar los históricos del aire. Intenta de nuevo.",
};

export async function routeRequest(path, params, signal) {
  const response = await fetch(`/api/routes/${path}/?${new URLSearchParams(params)}`, { signal });
  if (!response.headers.get("content-type")?.includes("application/json")) throw new Error("No pudimos conectar con el planificador. Intenta de nuevo.");
  const body = await response.json();
  if (!response.ok) throw new Error(routeErrors[body.error] || "No pudimos completar la consulta. Intenta de nuevo.");
  return body;
}

let plotly;
export function loadRoutePlotly() {
  if (window.Plotly) return Promise.resolve(window.Plotly);
  if (!plotly) plotly = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "/api/routes/plotly.js";
    script.async = true;
    script.onload = () => window.Plotly ? resolve(window.Plotly) : reject(new Error("plotly_unavailable"));
    script.onerror = () => { script.remove(); plotly = null; reject(new Error("plotly_unavailable")); };
    document.head.append(script);
  });
  return plotly;
}
