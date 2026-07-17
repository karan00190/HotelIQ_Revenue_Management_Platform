"use client";

import { Moon, Sun } from "lucide-react";

// Stateless by design: the current theme lives in the `dark` class on <html>
// (set before paint by the init script in layout.tsx), and the icon swap is
// driven purely by the CSS `dark:` variant - no React state, so there is no
// hydration mismatch and no set-state-in-effect to lint around.
function toggleTheme() {
  const isDark = document.documentElement.classList.toggle("dark");
  try {
    localStorage.setItem("hoteliq-theme", isDark ? "dark" : "light");
  } catch {
    /* localStorage unavailable (private mode) - theme just won't persist */
  }
}

export function ThemeToggle() {
  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label="Toggle light and dark theme"
      title="Toggle theme"
      className="flex size-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-nav-fg transition-all duration-200 hover:bg-white/15 hover:scale-105"
    >
      <Moon className="size-4 dark:hidden" />
      <Sun className="hidden size-4 dark:block" />
    </button>
  );
}
