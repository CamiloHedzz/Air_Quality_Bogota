import { useEffect, useMemo, useState } from "react";
import { ThemeContext } from "./ThemeContext";

const storageKey = "airquality-theme";
const frameSelector = "iframe.dashboard-frame, iframe.prediction-plotly-frame";

function storedTheme() {
  try { return localStorage.getItem(storageKey) === "dark" ? "dark" : "light"; }
  catch { return "light"; }
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(storedTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem(storageKey, theme); } catch { /* The toggle also works without storage. */ }

    function send(frame) {
      if (!(frame instanceof HTMLIFrameElement) || !frame.matches(frameSelector)) return;
      const origin = new URL(frame.src, window.location.href).origin;
      frame.contentWindow?.postMessage({ type: "airquality:theme", theme }, origin);
    }
    function ready(event) {
      if (event.data?.type !== "airquality:theme-ready") return;
      const frame = Array.from(document.querySelectorAll(frameSelector)).find(item => item.contentWindow === event.source);
      if (frame && event.origin === new URL(frame.src, window.location.href).origin) send(frame);
    }
    function load(event) { send(event.target); }
    function storage(event) {
      if (event.key === storageKey && (event.newValue === "light" || event.newValue === "dark")) setTheme(event.newValue);
    }
    document.querySelectorAll(frameSelector).forEach(send);
    window.addEventListener("message", ready);
    document.addEventListener("load", load, true);
    window.addEventListener("storage", storage);
    return () => {
      window.removeEventListener("message", ready);
      document.removeEventListener("load", load, true);
      window.removeEventListener("storage", storage);
    };
  }, [theme]);

  const value = useMemo(() => ({ theme, toggleTheme: () => setTheme(current => current === "dark" ? "light" : "dark") }), [theme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

ThemeProvider.propTypes = { children: () => null };
