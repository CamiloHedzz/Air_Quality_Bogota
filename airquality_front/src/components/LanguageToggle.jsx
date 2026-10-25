import { useLanguage } from "../i18n/useLanguage";

export function LanguageToggle({ className = "" }) {
  const { language, setLanguage } = useLanguage();
  return <div className={"language-toggle " + className} role="group" aria-label={language === "en" ? "Site language" : "Idioma del sitio"}>
    <button type="button" lang="es" aria-label="Español" aria-pressed={language === "es"} onClick={() => setLanguage("es")}>ES</button>
    <span aria-hidden="true">/</span>
    <button type="button" lang="en" aria-label="English" aria-pressed={language === "en"} onClick={() => setLanguage("en")}>EN</button>
  </div>;
}

LanguageToggle.propTypes = { className: (props, name) => props[name] === undefined || typeof props[name] === "string" ? null : new Error("className must be a string") };
