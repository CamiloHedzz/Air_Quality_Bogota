import { useLanguage } from "../i18n/useLanguage";
import { useContext } from "react";
import { ThemeContext } from "./ThemeContext";

export function ThemeToggle() {
  const { localize } = useLanguage();

  const { theme, toggleTheme } = useContext(ThemeContext);
  const dark = theme === "dark";
  return localize(<button type="button" className="theme-toggle" onClick={toggleTheme}
    aria-label={dark ? "Activar tema claro" : "Activar tema oscuro"} aria-pressed={dark}
    title={dark ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}>
    <svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      {dark ? <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" /></>
        : <path d="M20 14.3A8.2 8.2 0 0 1 9.7 4a8.2 8.2 0 1 0 10.3 10.3Z" />}
    </svg><span>{dark ? "Claro" : "Oscuro"}</span>
  </button>);
}
