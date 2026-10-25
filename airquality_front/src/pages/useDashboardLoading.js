import { useCallback, useEffect, useRef, useState } from "react";
import { lockPageForOverlay } from "../components/pageOverlayLock";

const initial = () => ({ progress: 4, stage: "connecting", visible: true, finishing: false, ready: false, slow: false, error: false });
const milestones = { dashboard: 25, data: 58, map: 82 };

export function useDashboardLoading(frameRef, origin, language) {
  const [attempt, setAttempt] = useState(0);
  const [loading, setLoading] = useState(initial);
  const dismissed = useRef(false);
  const progressTimer = useRef(0);
  const loadedFrame = useRef(null);

  useEffect(() => {
    let settled = false;
    let finishTimer = 0;
    dismissed.current = false;
    setLoading(initial());

    // Smooth the bar between observed milestones, without completing on a timer.
    progressTimer.current = window.setInterval(() => {
      if (settled || dismissed.current || document.hidden) return;
      setLoading(current => ({ ...current, progress: Math.min(92, current.progress + Math.max(.16, (92 - current.progress) * .025)) }));
    }, 400);
    const slowTimer = window.setTimeout(() => {
      if (!settled) setLoading(current => ({ ...current, slow: true }));
    }, 30000);

    function receive(event) {
      if (event.origin !== origin || event.source !== frameRef.current?.contentWindow) return;
      const data = event.data;
      if (data?.type === "airquality:dashboard-progress" && Object.hasOwn(milestones, data.stage) && !settled) {
        setLoading(current => ({ ...current,
          stage: milestones[data.stage] >= (milestones[current.stage] || 0) ? data.stage : current.stage,
          progress: Math.max(current.progress, milestones[data.stage]),
        }));
      } else if (data?.type === "airquality:dashboard-ready" && !settled) {
        settled = true;
        window.clearInterval(progressTimer.current);
        window.clearTimeout(slowTimer);
        setLoading(current => ({ ...current, progress: 100, stage: "ready", ready: true, slow: false, error: false, finishing: !dismissed.current }));
        if (!dismissed.current) {
          finishTimer = window.setTimeout(() => setLoading(current => ({ ...current, visible: false, finishing: false })),
            window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 380);
        }
      } else if (data?.type === "airquality:dashboard-error" && !settled) {
        setLoading(current => ({ ...current, error: true, slow: true }));
      }
    }
    window.addEventListener("message", receive);
    // Reconnect if this effect restarts after the frame has already loaded.
    if (loadedFrame.current && loadedFrame.current === frameRef.current?.contentWindow) {
      loadedFrame.current.postMessage({ type: "airquality:request-dashboard-state" }, origin);
    }
    return () => {
      window.removeEventListener("message", receive);
      window.clearInterval(progressTimer.current);
      window.clearTimeout(slowTimer);
      window.clearTimeout(finishTimer);
    };
  }, [attempt, language, frameRef, origin]);

  useEffect(() => {
    if (!loading.visible) return;
    const shell = document.querySelector(".app-shell");
    const screen = document.getElementById("map-loading-screen");
    if (!shell || !screen) return;
    const previousFocus = document.activeElement;
    const unlockPage = lockPageForOverlay(shell, screen);
    screen.focus({ preventScroll: true });
    function keys(event) {
      if (event.key !== "Tab") return;
      const items = [...screen.querySelectorAll("button:not([disabled]), a[href]")];
      if (!items.length) { event.preventDefault(); screen.focus({ preventScroll: true }); return; }
      const first = items[0];
      const last = items.at(-1);
      if (event.shiftKey && (document.activeElement === first || document.activeElement === screen)) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    document.addEventListener("keydown", keys);
    return () => {
      unlockPage();
      document.removeEventListener("keydown", keys);
      if (previousFocus?.isConnected && previousFocus !== document.body) previousFocus.focus({ preventScroll: true });
    };
  }, [loading.visible]);

  const frameLoaded = useCallback(() => {
    loadedFrame.current = frameRef.current?.contentWindow || null;
    loadedFrame.current?.postMessage({ type: "airquality:request-dashboard-state" }, origin);
    setLoading(current => current.ready ? current : { ...current, progress: Math.max(14, current.progress) });
  }, [frameRef, origin]);
  const retry = useCallback(() => { setLoading(initial()); setAttempt(current => current + 1); }, []);
  const continueLoading = useCallback(() => {
    dismissed.current = true;
    window.clearInterval(progressTimer.current);
    setLoading(current => ({ ...current, visible: false, finishing: false }));
  }, []);
  const frameFailed = useCallback(() => setLoading(current => current.ready ? current : { ...current, error: true, slow: true }), []);

  return { ...loading, attempt, frameLoaded, frameFailed, retry, continueLoading };
}
