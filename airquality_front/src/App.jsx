import { useEffect } from "react";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import { Index } from "./pages/index";
import { About } from "./pages/about";
import { Navegation } from "./components/navegator";
import { Footer } from "./components/foutter";
import { Predictions } from "./pages/predictions";
import "./index.css";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

function AppLayout() {
  const { pathname } = useLocation();
  const isAbout = pathname.toLowerCase() === "/about";

  return (
    <div className={`app-shell${isAbout ? " app-shell--about" : ""}`}>
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
    <BrowserRouter>
      <ScrollToTop />
      <AppLayout />
    </BrowserRouter>
  );
}

export default App;
