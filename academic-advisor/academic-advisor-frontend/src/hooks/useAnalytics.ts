// src/hooks/useAnalytics.ts
import { useCallback } from 'react';

export const useAnalytics = () => {
  const trackEvent = useCallback((eventName: string, data?: any) => {
    if (import.meta.env.MODE === 'development') {
      console.log('📊 Analytics Event:', eventName, data);
    }

    // Send to analytics service
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', eventName, data);
    }

    // Store in local storage
    const events = JSON.parse(localStorage.getItem('analytics_events') || '[]');
    events.push({
      event: eventName,
      data,
      timestamp: new Date().toISOString(),
    });
    
    if (events.length > 100) {
      events.shift();
    }
    
    localStorage.setItem('analytics_events', JSON.stringify(events));
  }, []);

  const trackPageView = useCallback((path: string) => {
    trackEvent('page_view', { path });
  }, [trackEvent]);

  return { trackEvent, trackPageView };
};