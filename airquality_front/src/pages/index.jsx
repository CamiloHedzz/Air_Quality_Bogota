import { useEffect, useRef, useState } from "react";
import { Description } from "./init";

const dashboardUrl = "http://127.0.0.1:8000/django_plotly_dash/app/SimpleExamplee/?embedded=1";
const dashboardOrigin = new URL(dashboardUrl).origin;

export function Index() {
  const dashboardRef = useRef(null);
  const [dashboardHeight, setDashboardHeight] = useState(720);

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
    dashboardRef.current?.contentWindow?.postMessage(
      { type: "airquality:request-dashboard-height" }, dashboardOrigin,
    );
  }

  return (
    <main>
      <Description />
      <section id="dashboard" className="dashboard-section" aria-label="Dashboard interactivo de calidad del aire">
        <iframe
          ref={dashboardRef}
          className="dashboard-frame"
          title="Dashboard de calidad del aire en Bogotá"
          src={dashboardUrl}
          style={{ height: dashboardHeight }}
          onLoad={requestHeight}
          loading="lazy"
        />
      </section>
    </main>
  );
}
