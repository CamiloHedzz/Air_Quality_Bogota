import { useContext, useLayoutEffect, useRef, useState } from "react";
import { ThemeContext } from "./ThemeContext";

export function SensorSky() {
  const { theme } = useContext(ThemeContext);
  const previousTheme = useRef(theme);
  const [transition, setTransition] = useState("idle");

  // An initial dark visit starts with the moon. Only a theme change plays the journey.
  useLayoutEffect(() => {
    if (previousTheme.current === theme) return;
    previousTheme.current = theme;
    setTransition(theme === "dark" ? "sunset" : "sunrise");
  }, [theme]);

  return <g className="sensor-sky" data-sky-theme={theme} data-sky-transition={transition}>
    <g key={`${theme}-${transition}`}>
      <g className="sensor-sun-travel">
        <g className="sensor-sun-altitude">
          <circle className="sensor-sun-halo" r="29" />
          <circle className="sensor-sun-disc" r="12" />
          <path className="sensor-sun-rays" d="M0-21v4M0 17v4M-21 0h4M17 0h4M-15-15l3 3M12 12l3 3M-15 15l3-3M12-12l3-3" />
        </g>
      </g>
      <g className="sensor-moon">
        <circle className="sensor-moon-halo" r="28" />
        <path className="sensor-moon-crescent" transform="translate(-19.2 -19.2) scale(1.6)" d="M20 14.3A8.2 8.2 0 0 1 9.7 4a8.2 8.2 0 1 0 10.3 10.3Z" />
        <path className="sensor-moon-stars" d="M-30-13v5m-2.5-2.5h5M23 12v4m-2-2h4" />
      </g>
    </g>
  </g>;
}
