import { useState } from 'react';
import AssetDashboard from './AssetDashboard';
import AdvisorBriefing from './AdvisorBriefing';
import NewsFeed, { type NewsItem } from './NewsFeed';
import dashboardData from './data.json';

export type ViewState = 'dashboard' | 'advisor' | 'news';

interface DashboardPayload {
  daily_news?: Array<Partial<NewsItem>>;
}

function App() {
  const [currentView, setCurrentView] = useState<ViewState>('dashboard');

  // We hoist privacy mode here so it persists across views
  const [isPrivacyMode, setIsPrivacyMode] = useState<boolean>(false);

  // Extract daily news from JSON payload
  const dailyNewsRaw = (dashboardData as DashboardPayload).daily_news || [];
  const dailyNews: NewsItem[] = dailyNewsRaw.map((item) => ({
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
          onOpenAdvisor={() => setCurrentView('advisor')}
          onOpenNews={() => setCurrentView('news')}
          isPrivacyMode={isPrivacyMode}
          setIsPrivacyMode={setIsPrivacyMode}
        />
      )}

      {currentView === 'advisor' && (
        <AdvisorBriefing
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
    </>
  );
}

export default App;
