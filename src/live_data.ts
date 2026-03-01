import bundledData from './data.json';

export type LiveDashboardPayload = Record<string, unknown>;

export const bundledDashboardData = bundledData as LiveDashboardPayload;

export async function fetchLiveDashboardData(): Promise<LiveDashboardPayload> {
  const liveUrl = `${import.meta.env.BASE_URL}data.json?v=${Date.now()}`;
  const response = await fetch(liveUrl, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Failed to fetch live data: ${response.status}`);
  }

  const parsed = (await response.json()) as unknown;
  if (!parsed || typeof parsed !== 'object') {
    throw new Error('Live data payload is not an object');
  }

  return parsed as LiveDashboardPayload;
}
