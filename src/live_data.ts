import bundledData from './data.json';

export type LiveDashboardPayload = Record<string, unknown>;

export const bundledDashboardData = bundledData as LiveDashboardPayload;

// Cache key for storing ETag and last modified time
const DATA_CACHE_KEY = 'dashboard_data_cache';

interface DataCache {
  etag?: string;
  lastModified?: string;
  data?: LiveDashboardPayload;
  timestamp: number;
}

// Get cache data with 5 minute validity
function getCachedData(): DataCache | null {
  try {
    const cached = localStorage.getItem(DATA_CACHE_KEY);
    if (!cached) return null;
    const parsed = JSON.parse(cached) as DataCache;
    // Cache valid for 5 minutes
    if (Date.now() - parsed.timestamp < 5 * 60 * 1000) {
      return parsed;
    }
  } catch {
    // Cache corrupted, ignore
  }
  return null;
}

// Store cache data
function setCacheData(cache: DataCache): void {
  try {
    localStorage.setItem(DATA_CACHE_KEY, JSON.stringify(cache));
  } catch {
    // localStorage unavailable, ignore
  }
}

export async function fetchLiveDashboardData(): Promise<LiveDashboardPayload> {
  const liveUrl = `${import.meta.env.BASE_URL}data.json`;

  // Build headers for conditional request
  const cached = getCachedData();
  const headers: Record<string, string> = {};

  if (cached?.etag) {
    headers['If-None-Match'] = cached.etag;
  }
  if (cached?.lastModified) {
    headers['If-Modified-Since'] = cached.lastModified;
  }

  const response = await fetch(liveUrl, {
    cache: 'no-cache',
    headers,
  });

  // Handle 304 Not Modified
  if (response.status === 304 && cached?.data) {
    console.log('[LiveData] Using cached data (304 Not Modified)');
    return cached.data;
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch live data: ${response.status}`);
  }

  const parsed = (await response.json()) as unknown;
  if (!parsed || typeof parsed !== 'object') {
    throw new Error('Live data payload is not an object');
  }

  // Update cache with new ETag/Last-Modified
  const newCache: DataCache = {
    etag: response.headers.get('etag') || undefined,
    lastModified: response.headers.get('last-modified') || undefined,
    data: parsed as LiveDashboardPayload,
    timestamp: Date.now(),
  };
  setCacheData(newCache);

  return parsed as LiveDashboardPayload;
}
