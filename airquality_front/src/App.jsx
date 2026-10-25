import { useEffect } from "react";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import { Index } from "./pages/index";
import { About } from "./pages/about";
import { Navegation } from "./components/navegator";
import { Footer } from "./components/foutter";
import { Predictions } from "./pages/predictions";
import { ContentMotion, EditorialScroll, SquareCursor } from "./components/EditorialMotion";
import { ThemeProvider } from "./components/ThemeProvider";
import "./index.css";
import "./assets/styles/editorial_motion.css";
import "./assets/styles/theme.css";

function ScrollToTop() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      let target;
      try { target = hash && document.getElementById(decodeURIComponent(hash.slice(1))); }
      catch { target = null; }
      if (target) target.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth" });
      else window.scrollTo({ top: 0, behavior: "instant" });
    });
    return () => cancelAnimationFrame(frame);
  }, [pathname, hash]);
  return null;
}

function AppLayout() {
  const { pathname } = useLocation();
  const isAbout = pathname.toLowerCase() === "/about";

  return (
    <div className={`app-shell${isAbout ? " app-shell--about" : ""}`}>
      <ContentMotion />
      <EditorialScroll />
      <SquareCursor />
      <Navegation />
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/About" element={<About />} />
        <Route path="/Predictions" element={<Predictions />} />
      </Routes>
      {!isAbout && <Footer />}
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
    <BrowserRouter>
      <ScrollToTop />
      <AppLayout />
    </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
