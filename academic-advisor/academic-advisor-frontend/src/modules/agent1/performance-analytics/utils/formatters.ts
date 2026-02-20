// modules/agent1/performance-analytics/utils/formatters.ts

/**
 * Format a GPA/SGPA value
 */
export function formatGPA(value: number | undefined | null, decimals: number = 2): string {
  if (value === undefined || value === null || isNaN(value)) return 'N/A';
  return value.toFixed(decimals);
}

/**
 * Format a percentage value
 */
export function formatPercentage(value: number | undefined | null, decimals: number = 1): string {
  if (value === undefined || value === null || isNaN(value)) return 'N/A';
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format a number with commas
 */
export function formatNumber(value: number | undefined | null): string {
  if (value === undefined || value === null || isNaN(value)) return 'N/A';
  return value.toLocaleString();
}

/**
 * Format a date to readable string
 */
export function formatDate(date: Date | string | undefined | null): string {
  if (!date) return 'N/A';
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return 'Invalid Date';
  return d.toLocaleDateString();
}

/**
 * Format credits (e.g., "24/160")
 */
export function formatCredits(earned: number, total: number): string {
  return `${earned}/${total}`;
}

/**
 * Get trend emoji
 */
export function getTrendEmoji(trend: 'improving' | 'declining' | 'stable'): string {
  switch (trend) {
    case 'improving': return '📈';
    case 'declining': return '📉';
    case 'stable': return '➡️';
    default: return '—';
  }
}