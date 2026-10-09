// src/hooks/useApplyPreferences.js
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { usePreferencesStore } from "../state/usePreferencesStore";

/**
 * Synchronizes persisted preferences with the DOM root and external services.
 * Mount this hook at the top level of the application (e.g., App.jsx).
 */
export function useApplyPreferences() {
  const { theme, fontSize, reducedMotion, language } = usePreferencesStore();
  const { i18n } = useTranslation();

  // 1. Theme application (Tailwind class-based dark mode & system media queries)
  useEffect(() => {
    const root = document.documentElement;
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const applyTheme = () => {
      const isDark =
        theme === "dark" || (theme === "system" && mediaQuery.matches);
      root.classList.toggle("dark", isDark);
    };

    applyTheme();

    // Listen for OS-level scheme shifts when set to 'system'
    mediaQuery.addEventListener("change", applyTheme);
    return () => mediaQuery.removeEventListener("change", applyTheme);
  }, [theme]);

  // 2. Proportional typography scaling (WCAG 1.4.4 compliance for Cyrillic clarity)
  useEffect(() => {
    const root = document.documentElement;
    const fontScaleMap = {
      sm: "14px",
      base: "16px",
      lg: "18px",
      xl: "20px",
    };
    root.style.fontSize = fontScaleMap[fontSize] || "16px";
  }, [fontSize]);

  // 3. Motion accessibility attribute for Framer Motion / CSS media fallback
  useEffect(() => {
    document.documentElement.setAttribute(
      "data-reduced-motion",
      reducedMotion ? "true" : "false",
    );
  }, [reducedMotion]);

  // 4. i18n Language synchronization
  useEffect(() => {
    if (i18n.language !== language) {
      i18n.changeLanguage(language);
    }
  }, [language, i18n]);
}
