import { useEffect, useState } from 'react';
import bundledData from './data.json';

export type LiveDashboardPayload = Record<string, unknown>;

export const bundledDashboardData = bundledData as LiveDashboardPayload;
export const LIVE_POLL_INTERVAL_MS = 60_000;

const DATA_CACHE_KEY = 'dashboard_data_cache';

interface DataCache {
  etag?: string;
  lastModified?: string;
  data?: LiveDashboardPayload;
  timestamp: number;
}

function getCachedData(): DataCache | null {
  try {
    const cached = localStorage.getItem(DATA_CACHE_KEY);
    if (!cached) return null;
    return JSON.parse(cached) as DataCache;
  } catch {
    return null;
  }
}

function setCacheData(cache: DataCache): void {
  try {
    localStorage.setItem(DATA_CACHE_KEY, JSON.stringify(cache));
  } catch {
    // Ignore localStorage failures and continue with network fetches.
  }
}

function getPayloadVersion(payload: LiveDashboardPayload): string {
  const lastUpdated = payload.last_updated;
  if (typeof lastUpdated === 'string' && lastUpdated.length > 0) {
    return `last_updated:${lastUpdated}`;
  }

  return JSON.stringify(payload);
}

export function hasLivePayloadChanged(
  current: LiveDashboardPayload,
  next: LiveDashboardPayload,
): boolean {
  return getPayloadVersion(current) !== getPayloadVersion(next);
}

export async function fetchLiveDashboardData(): Promise<LiveDashboardPayload> {
  const liveUrl = `${import.meta.env.BASE_URL}data.json`;

  const cached = getCachedData();
  const headers: Record<string, string> = {};

  if (cached?.etag) {
    headers['If-None-Match'] = cached.etag;
  }
  if (cached?.lastModified) {
    headers['If-Modified-Since'] = cached.lastModified;
  }

  const response = await fetch(liveUrl, {
    cache: 'no-store',
    headers,
  });

  if (response.status === 304 && cached?.data) {
    return cached.data;
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch live data: ${response.status}`);
  }

  const parsed = (await response.json()) as unknown;
  if (!parsed || typeof parsed !== 'object') {
    throw new Error('Live data payload is not an object');
  }

  const newCache: DataCache = {
    etag: response.headers.get('etag') || undefined,
    lastModified: response.headers.get('last-modified') || undefined,
    data: parsed as LiveDashboardPayload,
    timestamp: Date.now(),
  };
  setCacheData(newCache);

  return parsed as LiveDashboardPayload;
}

interface UseLiveDashboardDataOptions {
  enabled?: boolean;
  pollIntervalMs?: number;
}

export function useLiveDashboardData<T extends object>(
  initialData: T,
  options: UseLiveDashboardDataOptions = {},
): T {
  const { enabled = true, pollIntervalMs = LIVE_POLL_INTERVAL_MS } = options;
  const [data, setData] = useState<T>(initialData);

  useEffect(() => {
    setData(initialData);
  }, [initialData]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let alive = true;

    const refresh = async () => {
      if (typeof document !== 'undefined' && document.visibilityState !== 'visible') {
        return;
      }

      try {
        const payload = (await fetchLiveDashboardData()) as T;
        if (!alive) {
          return;
        }

        setData((current) =>
          hasLivePayloadChanged(
            current as LiveDashboardPayload,
            payload as LiveDashboardPayload,
          )
            ? payload
            : current,
        );
      } catch {
        // Keep the current payload when refresh fails.
      }
    };

    void refresh();

    const intervalId = window.setInterval(() => {
      void refresh();
    }, pollIntervalMs);

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        void refresh();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      alive = false;
      window.clearInterval(intervalId);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [enabled, pollIntervalMs]);

  return data;
}
