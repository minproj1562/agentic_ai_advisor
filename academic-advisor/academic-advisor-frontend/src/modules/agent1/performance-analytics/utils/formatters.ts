// modules/agent1/performance-analytics/utils/formatters.ts
import { format, formatDistance, formatRelative, parseISO } from 'date-fns';

/**
 * Format GPA value
 */
export function formatGPA(value: number | undefined | null): string {
  if (value === undefined || value === null) return 'N/A';
  return value.toFixed(2);
}

/**
 * Format percentage value
 */
export function formatPercentage(value: number | undefined | null, decimals: number = 1): string {
  if (value === undefined || value === null) return 'N/A';
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format grade letter
 */
export function formatGradeLetter(score: number): string {
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  return 'F';
}

/**
 * Format date
 */
export function formatDate(date: string | Date, formatString: string = 'MMM dd, yyyy'): string {
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return format(dateObj, formatString);
  } catch {
    return 'Invalid date';
  }
}

/**
 * Format relative time
 */
export function formatRelativeTime(date: string | Date): string {
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return formatDistance(dateObj, new Date(), { addSuffix: true });
  } catch {
    return 'Unknown';
  }
}

/**
 * Format number with commas
 */
export function formatNumber(value: number, decimals: number = 0): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
}

/**
 * Format currency
 */
export function formatCurrency(value: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency
  }).format(value);
}

/**
 * Format file size
 */
export function formatFileSize(bytes: number): string {
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Format duration
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  const parts = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);
  
  return parts.join(' ');
}

/**
 * Format credits
 */
export function formatCredits(credits: number): string {
  return `${credits} ${credits === 1 ? 'credit' : 'credits'}`;
}

/**
 * Format rank
 */
export function formatRank(rank: number, total: number): string {
  return `${rank}${getOrdinalSuffix(rank)} of ${total}`;
}

/**
 * Format improvement
 */
export function formatImprovement(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}

/**
 * Format confidence
 */
export function formatConfidence(value: number): string {
  if (value >= 0.9) return 'Very High';
  if (value >= 0.75) return 'High';
  if (value >= 0.6) return 'Moderate';
  if (value >= 0.4) return 'Low';
  return 'Very Low';
}

/**
 * Format trend
 */
export function formatTrend(trend: 'improving' | 'declining' | 'stable'): string {
  const trends = {
    improving: '📈 Improving',
    declining: '📉 Declining',
    stable: '➡️ Stable'
  };
  return trends[trend] || trend;
}

/**
 * Format subject category
 */
export function formatCategory(category: string): string {
  const categories: Record<string, string> = {
    core: 'Core Subject',
    elective: 'Elective',
    minor: 'Minor',
    major: 'Major',
    general: 'General Education'
  };
  return categories[category.toLowerCase()] || category;
}

/**
 * Format semester
 */
export function formatSemester(semester: string): string {
  // Format: "2024-spring" -> "Spring 2024"
  const parts = semester.split('-');
  if (parts.length === 2) {
    const [year, season] = parts;
    return `${season.charAt(0).toUpperCase() + season.slice(1)} ${year}`;
  }
  return semester;
}

/**
 * Format academic year
 */
export function formatAcademicYear(startYear: number): string {
  return `${startYear}-${(startYear + 1).toString().slice(2)}`;
}

/**
 * Truncate text
 */
export function truncateText(text: string, maxLength: number = 50): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

/**
 * Format list
 */
export function formatList(items: string[], maxItems: number = 3): string {
  if (items.length === 0) return 'None';
  if (items.length <= maxItems) return items.join(', ');
  
  const displayed = items.slice(0, maxItems);
  const remaining = items.length - maxItems;
  return `${displayed.join(', ')} and ${remaining} more`;
}

/**
 * Format score with color
 */
export function formatScoreColor(score: number): string {
  if (score >= 90) return 'text-green-600';
  if (score >= 80) return 'text-blue-600';
  if (score >= 70) return 'text-yellow-600';
  if (score >= 60) return 'text-orange-600';
  return 'text-red-600';
}

/**
 * Format status badge
 */
export function formatStatusBadge(status: string): {
  text: string;
  color: string;
  bgColor: string;
} {
  const statuses: Record<string, any> = {
    excellent: {
      text: 'Excellent',
      color: 'text-green-700',
      bgColor: 'bg-green-100'
    },
    good: {
      text: 'Good',
      color: 'text-blue-700',
      bgColor: 'bg-blue-100'
    },
    average: {
      text: 'Average',
      color: 'text-yellow-700',
      bgColor: 'bg-yellow-100'
    },
    poor: {
      text: 'Needs Improvement',
      color: 'text-red-700',
      bgColor: 'bg-red-100'
    },
    pending: {
      text: 'Pending',
      color: 'text-gray-700',
      bgColor: 'bg-gray-100'
    }
  };
  
  return statuses[status.toLowerCase()] || statuses.pending;
}

/**
 * Format time of day
 */
export function formatTimeOfDay(hour: number): string {
  if (hour < 6) return 'Early Morning';
  if (hour < 12) return 'Morning';
  if (hour < 17) return 'Afternoon';
  if (hour < 21) return 'Evening';
  return 'Night';
}

/**
 * Pluralize word
 */
export function pluralize(count: number, singular: string, plural?: string): string {
  if (count === 1) return `${count} ${singular}`;
  return `${count} ${plural || singular + 's'}`;
}

/**
 * Title case
 */
export function toTitleCase(str: string): string {
  return str.replace(/\w\S*/g, txt => 
    txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()
  );
}

/**
 * Camel case to title
 */
export function camelToTitle(str: string): string {
  return str
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim();
}

/**
 * Get initials
 */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

// Helper functions
function getOrdinalSuffix(num: number): string {
  const j = num % 10;
  const k = num % 100;
  
  if (j === 1 && k !== 11) return 'st';
  if (j === 2 && k !== 12) return 'nd';
  if (j === 3 && k !== 13) return 'rd';
  return 'th';
}