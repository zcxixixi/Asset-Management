import { useState } from 'react';
import AssetDashboard, { type RawDashboardData } from './AssetDashboard';
import AgentMechanism from './AgentMechanism';
import AdvisorBriefing, { type AdvisorPayload } from './AdvisorBriefing';
import NewsFeed, { type NewsItem } from './NewsFeed';
import { bundledDashboardData, useLiveDashboardData } from './live_data';

export type ViewState = 'dashboard' | 'advisor' | 'news' | 'mechanism';

function App() {
  const [currentView, setCurrentView] = useState<ViewState>('mechanism');
  const dashboardPayload = useLiveDashboardData(bundledDashboardData as RawDashboardData);

  // We hoist privacy mode here so it persists across views
  const [isPrivacyMode, setIsPrivacyMode] = useState<boolean>(false);

  // Extract daily news from JSON payload
  const dailyNewsRaw = dashboardPayload.daily_news || [];
  const dailyNews: NewsItem[] = dailyNewsRaw.map((item: Partial<NewsItem>) => ({
    symbol: item.symbol || 'MACRO',
    title: item.title || 'Untitled headline',
    publisher: item.publisher || 'Unknown',
    published_at: item.published_at || '',
    url: item.url || '#',
    summary: item.summary || '',
  }));

  return (
    <>
      {currentView === 'dashboard' && (
        <AssetDashboard
          rawData={dashboardPayload}
          onOpenAdvisor={() => setCurrentView('advisor')}
          onOpenNews={() => setCurrentView('news')}
          onOpenMechanism={() => setCurrentView('mechanism')}
          isPrivacyMode={isPrivacyMode}
          setIsPrivacyMode={setIsPrivacyMode}
        />
      )}

      {currentView === 'advisor' && (
        <AdvisorBriefing
          payload={dashboardPayload as unknown as AdvisorPayload}
          onBack={() => setCurrentView('dashboard')}
          isPrivacyMode={isPrivacyMode}
        />
      )}

      {currentView === 'news' && (
        <NewsFeed
          newsItems={dailyNews}
          onBack={() => setCurrentView('dashboard')}
          isPrivacyMode={isPrivacyMode}
        />
      )}

      {currentView === 'mechanism' && (
        <AgentMechanism onBack={() => setCurrentView('dashboard')} />
      )}
    </>
  );
}

export default App;
