import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, Sparkles, TrendingUp, AlertCircle, ArrowRight, ShieldCheck } from 'lucide-react';
import dashboardData from './data.json';

interface AdvisorBriefingProps {
  onBack: () => void;
  isPrivacyMode: boolean;
}

// Mock AI Data for the UI scaffolding (to be replaced by live API later)
const MOCK_AI_REPORT = {
  date: "October 31, 2023",
  headline: "Fed Shifts Tone: Rate Cuts Imminent",
  macroSummary: "The Federal Reserve has signaled a decisive pivot away from its tightening cycle. Markets are currently pricing in a 75% probability of a 25bps rate cut in the upcoming December FOMC meeting, triggering a rotation out of short-term cash equivalents and into long-duration growth assets and defensive hedges.",
  portfolioImpact: [
    {
      asset: "Gold USD",
      trend: "highly-bullish",
      rationale: "As real yields drop on the back of rate cut expectations, non-yielding defensive assets like Gold historically see strong capital inflows. Your current allocation provides an excellent hedge."
    },
    {
      asset: "US Stocks",
      trend: "neutral-bullish",
      rationale: "Broad equities stand to gain from cheaper borrowing costs, but specific tech valuations may experience volatility as investors rotate into beaten-down value sectors. Expect turbulence before a sustained rally."
    },
    {
      asset: "CASH",
      trend: "bearish",
      rationale: "Yields on cash sweeps and money market funds will begin compressing rapidly. The current high-yield environment for idle cash is drawing to a close."
    }
  ],
  verdict: "HOLD Gold & Equities; Consider deploying 15% of CASH into broad market indices on the next 2% dip."
};

// OpenClaw Data Protocol Structure
interface Insight {
  type: 'opportunity' | 'warning' | 'neutral';
  asset: string;
  text: string;
}

interface DashboardAsset {
  label: string;
  value: string | number;
}

interface AdvisorPayload {
  insights?: Insight[];
  assets?: DashboardAsset[];
}

export default function AdvisorBriefing({ onBack, isPrivacyMode }: AdvisorBriefingProps) {
  
  // Scroll to top when this view mounts
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const getImpactIcon = (type: Insight['type']) => {
    switch (type) {
      case 'opportunity': return <TrendingUp className="text-emerald-500" size={20} />;
      case 'warning': return <AlertCircle className="text-amber-500" size={20} />;
      default: return <ShieldCheck className="text-blue-500" size={20} />;
    }
  };

  const getImpactColor = (type: Insight['type']) => {
    switch (type) {
      case 'opportunity': return 'bg-emerald-50 border-emerald-100/50';
      case 'warning': return 'bg-amber-50 border-amber-100/50';
      default: return 'bg-blue-50 border-blue-100/50';
    }
  };

  const typedData = dashboardData as AdvisorPayload;

  // Check if OpenClaw has written the real insights array, otherwise fallback to mock
  const insights: Insight[] = typedData.insights || [
    { type: 'opportunity', asset: 'Gold USD', text: MOCK_AI_REPORT.portfolioImpact[0].rationale },
    { type: 'neutral', asset: 'US Stocks', text: MOCK_AI_REPORT.portfolioImpact[1].rationale },
    { type: 'warning', asset: 'CASH', text: MOCK_AI_REPORT.portfolioImpact[2].rationale }
  ];

  return (
    <div className="min-h-screen bg-slate-50 relative text-slate-900 font-sans selection:bg-blue-100">
      
      {/* Background Mesh (carried over from Dashboard for continuity) */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#e2e8f0_1px,transparent_1px),linear-gradient(to_bottom,#e2e8f0_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_100%_at_50%_0%,#000_60%,transparent_100%)] opacity-30 pointer-events-none fixed"></div>

      {/* Floating Navigation Bar */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4 md:px-12 backdrop-blur-xl bg-white/60 border-b border-slate-200/50">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <button 
            onClick={onBack}
            className="flex items-center space-x-2 text-slate-500 hover:text-slate-900 transition-colors group px-3 py-1.5 -ml-3 rounded-full hover:bg-slate-100"
          >
            <ChevronLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
            <span className="text-sm font-medium tracking-wide border-b border-transparent group-hover:border-slate-900 transition-colors pb-0.5">Asset Dashboard</span>
          </button>
          
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.6)]"></div>
            <span className="text-xs uppercase tracking-widest text-slate-400 font-semibold">Live Feed</span>
          </div>
        </div>
      </nav>

      {/* Main Content Article */}
      <main className="max-w-3xl mx-auto pt-32 pb-24 px-6 relative z-10">
        
        {/* Top Label */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center space-x-3 mb-8"
        >
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100/50 flex items-center justify-center shadow-inner">
            <Sparkles className="text-blue-600" size={18} strokeWidth={2} />
          </div>
          <div>
            <h2 className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500">OpenClaw Intelligence</h2>
            <p className="text-[11px] text-slate-400 font-medium tracking-wider font-mono mt-0.5">PUB: {MOCK_AI_REPORT.date}</p>
          </div>
        </motion.div>

        {/* Headline */}
        <motion.h1 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-[-0.03em] text-slate-900 leading-[1.05] mb-8"
          style={{ fontFamily: "'Playfair Display', 'Merriweather', serif" }} // Editorial Touch
        >
          {MOCK_AI_REPORT.headline}
        </motion.h1>

        {/* Macro Summary (The "Drop Cap" Editorial feel) */}
        <motion.p 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-lg md:text-xl text-slate-600 leading-relaxed font-normal mb-16"
        >
          <span className="float-left text-6xl font-bold leading-none pr-3 pb-2 text-slate-900 mt-1" style={{ fontFamily: "serif" }}>
            {MOCK_AI_REPORT.macroSummary.charAt(0)}
          </span>
          {MOCK_AI_REPORT.macroSummary.slice(1)}
        </motion.p>

        {/* The "Bento" Sub-Grid for Portfolio Impact */}
        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-6"
        >
          <div className="flex items-center space-x-4 mb-8">
            <div className="h-px bg-slate-200 flex-1"></div>
            <h3 className="text-xs uppercase tracking-widest font-bold text-slate-400">Direct Portfolio Impact</h3>
            <div className="h-px bg-slate-200 flex-1"></div>
          </div>

          <div className="grid gap-4">
            {insights.map((impact, idx) => {
              // Find the user's actual holding from data.json to bind reality to the UI
              const holding = typedData.assets?.find((asset) => asset.label === impact.asset);
              
              return (
                <div 
                  key={idx} 
                  className={`relative overflow-hidden group rounded-3xl p-6 md:p-8 transition-colors duration-300 ${getImpactColor(impact.type)}`}
                >
                  {/* Subtle frosted texture over the color tint */}
                  <div className="absolute inset-0 bg-white/40 backdrop-blur-sm"></div>
                  
                  <div className="relative z-10">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        {getImpactIcon(impact.type)}
                        <h4 className="font-semibold text-slate-900 text-lg tracking-tight">{impact.asset}</h4>
                      </div>
                      <div className="text-right">
                        <span className="text-xs uppercase tracking-widest font-bold text-slate-400 block mb-0.5">Current Weight</span>
                        <span className="font-mono text-sm font-medium text-slate-700">
                          {isPrivacyMode && holding ? '••••••' : (holding ? `$${holding.value.toLocaleString()}` : '--')}
                        </span>
                      </div>
                    </div>
                    <p className="text-slate-600 leading-relaxed text-[15px]">
                      {impact.text}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </motion.section>

        {/* Final Verdict Callout */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-16 bg-slate-900 rounded-[2rem] p-8 md:p-12 text-center text-white relative overflow-hidden shadow-2xl shadow-slate-900/20"
        >
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>
          <span className="text-xs uppercase tracking-[0.25em] font-bold text-slate-400 mb-6 block">Executive Verdict</span>
          <p className="text-xl md:text-2xl font-medium leading-relaxed tracking-wide">
            {MOCK_AI_REPORT.verdict}
          </p>
          <button 
            onClick={onBack}
            className="mt-10 px-8 py-3.5 bg-white text-slate-900 font-semibold rounded-full hover:bg-slate-50 transition-colors inline-flex items-center space-x-2 active:scale-95"
          >
            <span>Acknowledge & Return</span>
            <ArrowRight size={16} />
          </button>
        </motion.div>

      </main>
    </div>
  );
}
