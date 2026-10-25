import { useLanguage } from "../i18n/useLanguage";
import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { MapLoadingScreen } from "../components/MapLoadingScreen";
import { useDashboardLoading } from "./useDashboardLoading";
import { Description, WhyAirMatters } from "./init";

const dashboardUrl = "http://127.0.0.1:8000/django_plotly_dash/app/SimpleExamplee/?embedded=1";
const dashboardOrigin = new URL(dashboardUrl).origin;

export function Index() {
  const { localize, language } = useLanguage();

  const dashboardRef = useRef(null);
  const [dashboardHeight, setDashboardHeight] = useState(720);
  const loading = useDashboardLoading(dashboardRef, dashboardOrigin, language);
  const { hash } = useLocation();

  useEffect(() => {
    if (loading.visible || hash !== "#dashboard") return;
    const frame = requestAnimationFrame(() => document.getElementById("dashboard")?.scrollIntoView({ behavior: "instant" }));
    return () => cancelAnimationFrame(frame);
  }, [loading.visible, hash]);

  useEffect(() => {
    function receiveHeight(event) {
      if (event.origin !== dashboardOrigin || event.source !== dashboardRef.current?.contentWindow ||
          event.data?.type !== "airquality:dashboard-height") return;
      const height = event.data.height;
      if (typeof height !== "number" || !Number.isFinite(height) || height <= 0 || height > 30000) return;
      setDashboardHeight(Math.max(480, Math.ceil(height)));
    }
    window.addEventListener("message", receiveHeight);
    return () => window.removeEventListener("message", receiveHeight);
  }, []);

  function requestHeight() {
    loading.frameLoaded();
    dashboardRef.current?.contentWindow?.postMessage(
      { type: "airquality:request-dashboard-height" }, dashboardOrigin,
    );
  }

  return (
    localize(<main>
      {loading.visible && <MapLoadingScreen progress={loading.progress} stage={loading.stage}
        slow={loading.slow} error={loading.error} finishing={loading.finishing}
        onRetry={loading.retry} onContinue={loading.continueLoading} />}
      {(!loading.visible || loading.finishing) && <Description />}
      <WhyAirMatters />
      <section id="dashboard" className="dashboard-section" aria-label="Dashboard interactivo de calidad del aire" aria-busy={!loading.ready && !loading.error}>
        {!loading.visible && !loading.ready && (loading.slow || loading.error) && <div className="dashboard-loading-note" role="status">
          <p>{language === "en" ? "The map is taking longer to load. You can keep exploring or try again." : "El mapa está tardando en cargar. Puedes seguir explorando el sitio o reintentar."}</p>
          <button type="button" onClick={loading.retry}>{language === "en" ? "Retry loading the map" : "Reintentar carga del mapa"}</button>
        </div>}
        <iframe
          key={`${language}-${loading.attempt}`}
          ref={dashboardRef}
          className="dashboard-frame"
          title="Dashboard de calidad del aire en Bogotá"
          src={dashboardUrl + "&lang=" + language + "&loadingAttempt=" + loading.attempt}
          style={{ height: dashboardHeight }}
          onLoad={requestHeight}
          onError={loading.frameFailed}
          loading="eager"
        />
      </section>
    </main>)
  );
}
