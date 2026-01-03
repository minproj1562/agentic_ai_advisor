// src/contexts/ThemeContext.tsx

import React, { createContext, useState, useEffect, useCallback, useMemo } from 'react';

export type Theme = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

interface ThemeContextValue {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  systemTheme: ResolvedTheme;
}

export const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
  enableSystem?: boolean;
  disableTransitionOnChange?: boolean;
}

/**
 * Theme Provider Component
 * Manages application theme with localStorage persistence and system preference detection
 */
export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultTheme = 'system',
  storageKey = 'app-theme',
  enableSystem = true,
  disableTransitionOnChange = false,
}) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    // Check localStorage first
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(storageKey) as Theme;
      if (stored && ['light', 'dark', 'system'].includes(stored)) {
        return stored;
      }
    }
    return defaultTheme;
  });

  const [systemTheme, setSystemTheme] = useState<ResolvedTheme>(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'light';
  });

  // Resolve the actual theme to apply
  const resolvedTheme = useMemo<ResolvedTheme>(() => {
    if (theme === 'system' && enableSystem) {
      return systemTheme;
    }
    return theme === 'dark' ? 'dark' : 'light';
  }, [theme, systemTheme, enableSystem]);

  // Apply theme to document
  const applyTheme = useCallback((newTheme: ResolvedTheme) => {
    const root = window.document.documentElement;
    
    // Disable transitions temporarily if requested
    if (disableTransitionOnChange) {
      root.classList.add('theme-transition-disabled');
    }

    // Remove old theme class and add new one
    root.classList.remove('light', 'dark');
    root.classList.add(newTheme);

    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute(
        'content',
        newTheme === 'dark' ? '#1f2937' : '#ffffff'
      );
    }

    // Re-enable transitions after a brief delay
    if (disableTransitionOnChange) {
      setTimeout(() => {
        root.classList.remove('theme-transition-disabled');
      }, 50);
    }
  }, [disableTransitionOnChange]);

  // Set theme and persist to localStorage
  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme);
    
    if (typeof window !== 'undefined') {
      localStorage.setItem(storageKey, newTheme);
      
      // Dispatch custom event for other tabs/windows
      window.dispatchEvent(new CustomEvent('theme-change', { 
        detail: { theme: newTheme } 
      }));
    }
  }, [storageKey]);

  // Toggle between light and dark themes
  const toggleTheme = useCallback(() => {
    if (theme === 'system') {
      setTheme(systemTheme === 'dark' ? 'light' : 'dark');
    } else {
      setTheme(theme === 'dark' ? 'light' : 'dark');
    }
  }, [theme, systemTheme, setTheme]);

  // Listen for system theme changes
  useEffect(() => {
    if (!enableSystem || typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent | MediaQueryList) => {
      setSystemTheme(e.matches ? 'dark' : 'light');
    };

    // Check if addEventListener is supported (older browsers)
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } else if (mediaQuery.addListener) {
      // Fallback for older browsers
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, [enableSystem]);

  // Apply theme on mount and when it changes
  useEffect(() => {
    applyTheme(resolvedTheme);
  }, [resolvedTheme, applyTheme]);

  // Listen for theme changes from other tabs/windows
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === storageKey && e.newValue) {
        const newTheme = e.newValue as Theme;
        if (['light', 'dark', 'system'].includes(newTheme)) {
          setThemeState(newTheme);
        }
      }
    };

    const handleCustomEvent = (e: CustomEvent) => {
      const newTheme = e.detail.theme as Theme;
      if (['light', 'dark', 'system'].includes(newTheme)) {
        setThemeState(newTheme);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('theme-change' as any, handleCustomEvent);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('theme-change' as any, handleCustomEvent);
    };
  }, [storageKey]);

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      resolvedTheme,
      setTheme,
      toggleTheme,
      systemTheme,
    }),
    [theme, resolvedTheme, setTheme, toggleTheme, systemTheme]
  );

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};