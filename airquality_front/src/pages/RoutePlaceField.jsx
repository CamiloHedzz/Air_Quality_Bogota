import { useEffect, useRef, useState } from "react";
import { useLanguage } from "../i18n/useLanguage";
import { routeRequest } from "./routeApi";

export function RoutePlaceField({ name, label, value, onChange }) {
  const { localize, t } = useLanguage();
  const [places, setPlaces] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const controller = useRef(null);
  useEffect(() => () => controller.current?.abort(), []);

  function edit(text) {
    controller.current?.abort();
    setBusy(false); setError(""); setPlaces([]);
    onChange({ text, place: null });
  }
  async function search() {
    controller.current?.abort();
    const current = new AbortController();
    controller.current = current;
    setBusy(true); setPlaces([]); setError("");
    try {
      const result = await routeRequest("places", { q: value.text }, current.signal);
      if (!current.signal.aborted) {
        setPlaces(result.places);
        if (!result.places.length) setError("No encontramos ese lugar en Bogotá. Prueba un parque, una dirección o un barrio cercano.");
      }
    } catch (failure) { if (!current.signal.aborted) setError(failure.message); }
    finally { if (!current.signal.aborted) setBusy(false); }
  }

  return localize(<div className="route-place-field">
    <label htmlFor={`route-${name}`}>{label}</label>
    <div className="route-place-search"><input id={`route-${name}`} autoComplete="off" value={value.text}
      placeholder="Lugar o dirección en Bogotá" onChange={e => edit(e.target.value)}
      onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); if (value.text.trim().length >= 3 && !busy) search(); } }}
      aria-describedby={`route-${name}-status`} />
      <button type="button" onClick={search} disabled={busy || value.text.trim().length < 3}
        aria-label={t(name === "origin" ? "Buscar origen" : "Buscar destino")}>{busy ? "…" : "Buscar"}</button></div>
    <span id={`route-${name}-status`} className="route-field-hint" role="status">{value.place ? "✓ Lugar seleccionado" : "Busca y selecciona un resultado para ubicar el punto."}</span>
    {error && <p className="route-field-error" role="alert">{error}</p>}
    {places.length > 0 && <ul className="route-place-results" aria-label={name === "origin" ? "Resultados para el origen" : "Resultados para el destino"}>
      {places.map((place, index) => <li key={index}><button type="button" onClick={() => { onChange({ text: place.label, place }); setPlaces([]); setError(""); }}>
        <strong>{place.label}</strong><span>{place.detail}</span></button></li>)}
    </ul>}
  </div>);
}

RoutePlaceField.propTypes = { name: () => null, label: () => null, value: () => null, onChange: () => null };
