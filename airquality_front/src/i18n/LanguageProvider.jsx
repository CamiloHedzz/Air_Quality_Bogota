import { useEffect, useMemo, useState } from "react";
import { LanguageContext } from "./LanguageContext";

const key = "airquality-language";
function initialLanguage() {
  try { return localStorage.getItem(key) === "en" ? "en" : "es"; }
  catch { return "es"; }
}

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(initialLanguage);
  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dataset.language = language;
    try { localStorage.setItem(key, language); } catch { /* The control also works without storage. */ }
    function storage(event) {
      if (event.key === key) setLanguage(event.newValue === "en" ? "en" : "es");
    }
    window.addEventListener("storage", storage);
    return () => window.removeEventListener("storage", storage);
  }, [language]);
  const value = useMemo(() => ({ language, locale: language === "en" ? "en-US" : "es-CO", setLanguage }), [language]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

LanguageProvider.propTypes = { children: () => null };
