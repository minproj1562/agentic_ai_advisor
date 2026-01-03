// core/integrations/youtube/youtube.service.ts
import axios, { AxiosInstance } from 'axios';

interface YouTubeSearchOptions {
  q: string;
  maxResults?: number;
  relevanceLanguage?: string;
  regionCode?: string;
  order?: 'relevance' | 'date' | 'rating' | 'title' | 'viewCount';
  safeSearch?: 'none' | 'moderate' | 'strict';
  topicId?: string; // e.g., /m/01k8wb (Educational)
}

interface YouTubeVideo {
  id: string;
  title: string;
  description: string;
  channelTitle: string;
  publishedAt: string;
  thumbnails: Record<string, { url: string; width: number; height: number }>;
}

class YouTubeService {
  private axios: AxiosInstance;
  private apiKey: string;
  private cache: Map<string, { data: any; timestamp: number }>;
  private readonly TTL = 1000 * 60 * 10; // 10 min

  constructor() {
    this.apiKey = import.meta.env.VITE_YOUTUBE_API_KEY || '';
    this.axios = axios.create({
      baseURL: 'https://www.googleapis.com/youtube/v3'
    });
    this.cache = new Map();
  }

  private getCache<T>(key: string): T | null {
    const v = this.cache.get(key);
    if (!v) return null;
    if (Date.now() - v.timestamp > this.TTL) {
      this.cache.delete(key);
      return null;
    }
    return v.data as T;
  }

  private setCache(key: string, data: any): void {
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  async searchVideos(options: YouTubeSearchOptions): Promise<YouTubeVideo[]> {
    if (!this.apiKey) {
      console.warn('YouTube API key not set. Returning empty results.');
      return [];
    }

    const params = {
      key: this.apiKey,
      part: 'snippet',
      type: 'video',
      q: options.q,
      maxResults: options.maxResults || 8,
      relevanceLanguage: options.relevanceLanguage || 'en',
      regionCode: options.regionCode || 'US',
      order: options.order || 'relevance',
      safeSearch: options.safeSearch || 'strict',
      videoCategoryId: '27' // Education
    };

    const cacheKey = `search-${JSON.stringify(params)}`;
    const cached = this.getCache<YouTubeVideo[]>(cacheKey);
    if (cached) return cached;

    try {
      const { data } = await this.axios.get('/search', { params });

      const videos = (data.items || []).map((item: any) => ({
        id: item.id.videoId,
        title: item.snippet.title,
        description: item.snippet.description,
        channelTitle: item.snippet.channelTitle,
        publishedAt: item.snippet.publishedAt,
        thumbnails: item.snippet.thumbnails
      }));

      this.setCache(cacheKey, videos);
      return videos;
    } catch (error) {
      console.error('YouTube search failed:', error);
      return [];
    }
  }

  async getVideoDetails(videoId: string): Promise<any> {
    if (!this.apiKey) return null;

    const cacheKey = `video-${videoId}`;
    const cached = this.getCache<any>(cacheKey);
    if (cached) return cached;

    try {
      const { data } = await this.axios.get('/videos', {
        params: {
          key: this.apiKey,
          part: 'snippet,contentDetails,statistics',
          id: videoId
        }
      });

      const details = data.items?.[0] || null;
      this.setCache(cacheKey, details);
      return details;
    } catch (error) {
      console.error('YouTube video details failed:', error);
      return null;
    }
  }

  async getPlaylistItems(playlistId: string, maxResults: number = 10): Promise<any[]> {
    if (!this.apiKey) return [];

    const cacheKey = `playlist-${playlistId}-${maxResults}`;
    const cached = this.getCache<any[]>(cacheKey);
    if (cached) return cached;

    try {
      const { data } = await this.axios.get('/playlistItems', {
        params: {
          key: this.apiKey,
          part: 'snippet,contentDetails',
          playlistId,
          maxResults
        }
      });

      const items = data.items || [];
      this.setCache(cacheKey, items);
      return items;
    } catch (error) {
      console.error('YouTube playlist items failed:', error);
      return [];
    }
  }
}

export const youtubeService = new YouTubeService();