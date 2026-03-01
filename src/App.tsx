import { useState } from 'react';
import AssetDashboard from './AssetDashboard';
import AdvisorBriefing from './AdvisorBriefing';
import NewsFeed from './NewsFeed';
import dashboardData from './data.json';

export type ViewState = 'dashboard' | 'advisor' | 'news';

function App() {
  const [currentView, setCurrentView] = useState<ViewState>('dashboard');

  // We hoist privacy mode here so it persists across views
  const [isPrivacyMode, setIsPrivacyMode] = useState<boolean>(false);

  // Extract daily news from JSON payload
  const dailyNews = (dashboardData as any).daily_news || [];

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
