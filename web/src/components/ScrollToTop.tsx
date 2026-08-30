import { useLayoutEffect } from "react";
import { useLocation } from "react-router-dom";
import { scrollPageToTop } from "../lib/scrollToTop";

/** Scroll to top on route changes (browser scroll restoration is disabled in main.tsx). */
export function ScrollToTop() {
  const { pathname } = useLocation();

  useLayoutEffect(() => {
    scrollPageToTop();
    // Run again after paint in case layout or restoration shifts scroll.
    const raf = window.requestAnimationFrame(() => {
      scrollPageToTop();
    });
    return () => window.cancelAnimationFrame(raf);
  }, [pathname]);

  return null;
}
