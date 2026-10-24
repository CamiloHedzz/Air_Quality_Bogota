import { useCallback, useEffect, useRef, useState } from "react";

export function queryString(settings, view) {
  return new URLSearchParams({ ...settings, view }).toString();
}

async function getJSON(path, signal) {
  const response = await fetch(`/api/predictions/${path}`, { signal });
  if (!response.headers.get("content-type")?.includes("application/json")) throw new Error("No se pudo conectar con los datos. Comprueba que el servidor esté disponible.");
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "No se pudo completar la consulta.");
  return body;
}

export function usePredictionData(view) {
  const [catalog, setCatalog] = useState(null);
  const [settings, setSettings] = useState(null);
  const [available, setAvailable] = useState(null);
  const [result, setResult] = useState(null);
  const [applied, setApplied] = useState(null);
  const [busy, setBusy] = useState(false);
  const [optionsBusy, setOptionsBusy] = useState(false);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const sequence = useRef(0);
  const manual = useRef(null);

  const load = useCallback(async (next, activeView, signal) => {
    const id = ++sequence.current;
    setBusy(true); setError(""); setResult(null);
    try {
      const payload = await getJSON(`query/?${queryString(next, activeView)}`, signal);
      if (id === sequence.current) { setResult(payload); setApplied({ ...next, view: activeView }); }
    } catch (failure) {
      if (failure.name !== "AbortError" && id === sequence.current) setError(failure.message);
    } finally { if (id === sequence.current) setBusy(false); }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    getJSON("catalog/", controller.signal).then(payload => {
      setCatalog(payload);
      setSettings({ ...payload.defaults, comparison: "11", related: "humidity", date: "", hour: "" });
    }).catch(failure => { if (failure.name !== "AbortError") setError(failure.message); });
    return () => controller.abort();
  }, [attempt]);

  const station = settings?.station, variable = settings?.variable, horizon = settings?.horizon;
  useEffect(() => {
    if (!catalog || !station) return;
    const controller = new AbortController();
    ++sequence.current;
    setOptionsBusy(true); setResult(null); setAvailable(null); setError(""); setBusy(false);
    getJSON(`options/?${new URLSearchParams({ station, variable, horizon, view })}`, controller.signal).then(payload => {
      if (controller.signal.aborted) return;
      setAvailable({ ...payload, key: `${station}|${variable}|${horizon}|${view}` });
      if (!payload.dates.length) { setOptionsBusy(false); return; }
      setSettings(current => {
        const date = payload.dates.includes(current.date) ? current.date : payload.dates.at(-1);
        const hours = payload.hours[date];
        const hour = hours.includes(current.hour) ? current.hour : hours.at(-1);
        return { ...current, date, hour };
      });
    }).catch(failure => { if (failure.name !== "AbortError") setError(failure.message); }).finally(() => {
      if (!controller.signal.aborted) setOptionsBusy(false);
    });
    return () => { controller.abort(); ++sequence.current; };
  }, [catalog, station, variable, horizon, view]);

  // Cargar al entrar o cambiar de estación/variable/vista; fecha e histórico se aplican con el botón.
  useEffect(() => {
    if (available?.key === `${station}|${variable}|${horizon}|${view}` && settings?.date && available.hours[settings.date]?.includes(settings.hour) && !optionsBusy && !result && !busy && !error) {
      manual.current?.abort();
      manual.current = new AbortController();
      load(settings, view, manual.current.signal);
    }
  }, [available, settings, optionsBusy, result, busy, error, view, load, station, variable, horizon]);

  useEffect(() => () => { sequence.current = -1; manual.current?.abort(); }, []);

  function update(name, value) {
    setSettings(current => {
      const next = { ...current, [name]: value };
      if (name === "date") next.hour = available.hours[value].includes(current.hour) ? current.hour : available.hours[value].at(-1);
      if (name === "variable" && next.related === value) next.related = value === "humidity" ? "pm_25" : "humidity";
      if (name === "station" && next.comparison === value) next.comparison = catalog.stations.find(s => s.value !== value).value;
      return next;
    });
  }

  function apply() {
    manual.current?.abort(); manual.current = new AbortController();
    load(settings, view, manual.current.signal);
  }

  return { catalog, settings, available, result, applied, busy: busy || optionsBusy, error,
    update, apply, retry: () => { setError(""); setCatalog(null); setSettings(null); setAttempt(n => n + 1); } };
}
