import React, { useState } from 'react';
import AssetDashboard from './AssetDashboard';
import AdvisorBriefing from './AdvisorBriefing';

export type ViewState = 'dashboard' | 'advisor';

function App() {
  const [currentView, setCurrentView] = useState<ViewState>('dashboard');
  
  // We hoist privacy mode here so it persists across views
  const [isPrivacyMode, setIsPrivacyMode] = useState<boolean>(false);

  return (
    <>
      {currentView === 'dashboard' ? (
        <AssetDashboard 
          onOpenAdvisor={() => setCurrentView('advisor')} 
          isPrivacyMode={isPrivacyMode}
          setIsPrivacyMode={setIsPrivacyMode}
        />
      ) : (
        <AdvisorBriefing 
          onBack={() => setCurrentView('dashboard')} 
          isPrivacyMode={isPrivacyMode}
        />
      )}
    </>
  );
}

export default App;
