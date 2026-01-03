// src/utils/theme.utils.ts
/**
 * Get theme-aware colors for charts and visualizations
 */
export const getThemeColors = (theme: 'light' | 'dark') => {
  const colors = {
    light: {
      primary: '#3b82f6',
      secondary: '#8b5cf6',
      success: '#10b981',
      warning: '#f59e0b',
      danger: '#ef4444',
      info: '#06b6d4',
      background: '#ffffff',
      surface: '#f3f4f6',
      text: '#111827',
      textSecondary: '#6b7280',
      border: '#e5e7eb',
      chart: {
        grid: '#e5e7eb',
        axis: '#6b7280',
        tooltip: '#1f2937',
      },
    },
    dark: {
      primary: '#60a5fa',
      secondary: '#a78bfa',
      success: '#34d399',
      warning: '#fbbf24',
      danger: '#f87171',
      info: '#22d3ee',
      background: '#1f2937',
      surface: '#111827',
      text: '#f9fafb',
      textSecondary: '#9ca3af',
      border: '#374151',
      chart: {
        grid: '#374151',
        axis: '#9ca3af',
        tooltip: '#374151',
      },
    },
  };

  return colors[theme];
};

/**
 * Generate theme-aware className
 */
export const getThemeClass = (lightClass: string, darkClass: string): string => {
  return `${lightClass} dark:${darkClass}`;
};

/**
 * Check if user prefers reduced motion
 */
export const prefersReducedMotion = (): boolean => {
  if (typeof window === 'undefined') return false;
  
  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  return mediaQuery.matches;
};

/**
 * Get theme transition classes
 */
export const getThemeTransition = (enabled: boolean = true): string => {
  if (!enabled || prefersReducedMotion()) return '';
  
  return 'transition-colors duration-200 ease-in-out';
};