import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, Sparkles, TrendingUp, AlertCircle, ArrowRight, ShieldCheck } from 'lucide-react';
import { bundledDashboardData, fetchLiveDashboardData } from './live_data';

interface AdvisorBriefingProps {
  onBack: () => void;
  isPrivacyMode: boolean;
}

interface Insight {
  type: 'opportunity' | 'warning' | 'neutral';
  asset: string;
  text: string;
}

interface DashboardAsset {
  label: string;
  value: string | number;
}

interface AdvisorSuggestion {
  asset: string;
  action: string;
  rationale: string;
}

interface BriefingNewsItem {
  symbol?: string;
  title?: string;
  published_at?: string;
  url?: string;
}

interface AdvisorBriefingData {
  generated_at?: string;
  source?: string;
  headline?: string;
  macro_summary?: string;
  verdict?: string;
  suggestions?: AdvisorSuggestion[];
  risks?: string[];
  news_context?: BriefingNewsItem[];
  global_context?: BriefingNewsItem[];
  disclaimer?: string;
}

interface AdvisorPayload {
  insights?: Insight[];
  assets?: DashboardAsset[];
  advisor_briefing?: AdvisorBriefingData;
}

const FALLBACK_REPORT: Required<Pick<AdvisorBriefingData, 'generated_at' | 'source' | 'headline' | 'macro_summary' | 'verdict' | 'disclaimer'>> & {
  suggestions: AdvisorSuggestion[];
} = {
  generated_at: 'N/A',
  source: 'rule-based',
  headline: 'Portfolio Pulse: Balanced but Event-Sensitive',
  macro_summary:
    'No live AI briefing was generated yet. Keep diversified exposure and validate signals against your own risk constraints.',
  verdict: 'Maintain diversified core allocation and rebalance gradually.',
  suggestions: [
    {
      asset: 'Cash USD',
      action: 'Maintain reserve',
      rationale: 'Cash buffer provides optionality when volatility increases.',
    },
    {
      asset: 'US Stocks',
      action: 'Hold core exposure',
      rationale: 'Avoid overreacting to a single headline cycle.',
    },
    {
      asset: 'Gold USD',
      action: 'Keep hedge',
      rationale: 'Gold can offset risk-off moves in equities.',
    },
  ],
  disclaimer: 'Informational only, not financial advice.',
};

const actionToInsightType = (action: string): Insight['type'] => {
  const normalized = action.toLowerCase();
  if (['reduce', 'trim', 'rebalance', 'tighten', 'hedge', 'defensive'].some((token) => normalized.includes(token))) {
    return 'warning';
  }
  if (['add', 'deploy', 'accumulate', 'hold', 'increase', 'keep', 'maintain'].some((token) => normalized.includes(token))) {
    return 'opportunity';
  }
  return 'neutral';
};

export default function AdvisorBriefing({ onBack, isPrivacyMode }: AdvisorBriefingProps) {
  const [typedData, setTypedData] = useState<AdvisorPayload>(bundledDashboardData as AdvisorPayload);

  useEffect(() => {
    window.scrollTo(0, 0);

    let alive = true;
    fetchLiveDashboardData()
      .then((payload) => {
        if (alive) {
          setTypedData(payload as AdvisorPayload);
        }
      })
      .catch(() => {
        // Keep bundled fallback when live payload fetch fails.
      });

    return () => {
      alive = false;
    };
  }, []);

  const getImpactIcon = (type: Insight['type']) => {
    switch (type) {
      case 'opportunity':
        return <TrendingUp className="text-emerald-500" size={20} />;
      case 'warning':
        return <AlertCircle className="text-amber-500" size={20} />;
      default:
        return <ShieldCheck className="text-blue-500" size={20} />;
    }
  };

  const getImpactColor = (type: Insight['type']) => {
    switch (type) {
      case 'opportunity':
        return 'bg-emerald-50 border-emerald-100/50';
      case 'warning':
        return 'bg-amber-50 border-amber-100/50';
      default:
        return 'bg-blue-50 border-blue-100/50';
    }
  };

  const report: AdvisorBriefingData = typedData.advisor_briefing ?? FALLBACK_REPORT;
  const macroSummary = (report.macro_summary || FALLBACK_REPORT.macro_summary).trim();

  const fallbackInsights: Insight[] = (report.suggestions && report.suggestions.length > 0
    ? report.suggestions
    : FALLBACK_REPORT.suggestions
  )
    .slice(0, 3)
    .map((suggestion) => ({
      type: actionToInsightType(suggestion.action),
      asset: suggestion.asset,
      text: suggestion.rationale,
    }));

  const insights: Insight[] = typedData.insights && typedData.insights.length > 0 ? typedData.insights : fallbackInsights;

  const publishAt = report.generated_at || FALLBACK_REPORT.generated_at;
  const sourceLabel = (report.source || FALLBACK_REPORT.source).toUpperCase();

  return (
    <div className="min-h-screen bg-slate-50 relative text-slate-900 font-sans selection:bg-blue-100">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#e2e8f0_1px,transparent_1px),linear-gradient(to_bottom,#e2e8f0_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_100%_at_50%_0%,#000_60%,transparent_100%)] opacity-30 pointer-events-none fixed"></div>

      <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4 md:px-12 backdrop-blur-xl bg-white/60 border-b border-slate-200/50">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <button
            onClick={onBack}
            className="flex items-center space-x-2 text-slate-500 hover:text-slate-900 transition-colors group px-3 py-1.5 -ml-3 rounded-full hover:bg-slate-100"
          >
            <ChevronLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
            <span className="text-sm font-medium tracking-wide border-b border-transparent group-hover:border-slate-900 transition-colors pb-0.5">
              Asset Dashboard
            </span>
          </button>

          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.6)]"></div>
            <span className="text-xs uppercase tracking-widest text-slate-400 font-semibold">Live Feed</span>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto pt-32 pb-24 px-6 relative z-10">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center space-x-3 mb-8">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100/50 flex items-center justify-center shadow-inner">
            <Sparkles className="text-blue-600" size={18} strokeWidth={2} />
          </div>
          <div>
            <h2 className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500">OpenClaw Intelligence</h2>
            <p className="text-[11px] text-slate-400 font-medium tracking-wider font-mono mt-0.5">PUB: {publishAt} | SRC: {sourceLabel}</p>
          </div>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-[-0.03em] text-slate-900 leading-[1.05] mb-8"
          style={{ fontFamily: "'Playfair Display', 'Merriweather', serif" }}
        >
          {report.headline || FALLBACK_REPORT.headline}
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-lg md:text-xl text-slate-600 leading-relaxed font-normal mb-16"
        >
          <span className="float-left text-6xl font-bold leading-none pr-3 pb-2 text-slate-900 mt-1" style={{ fontFamily: 'serif' }}>
            {macroSummary.charAt(0) || 'M'}
          </span>
          {macroSummary.slice(1)}
        </motion.p>

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
              const holding = typedData.assets?.find((asset) => asset.label === impact.asset);
              return (
                <div
                  key={idx}
                  className={`relative overflow-hidden group rounded-3xl p-6 md:p-8 transition-colors duration-300 ${getImpactColor(impact.type)}`}
                >
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
                          {isPrivacyMode && holding ? '••••••' : holding ? `$${holding.value.toLocaleString()}` : '--'}
                        </span>
                      </div>
                    </div>
                    <p className="text-slate-600 leading-relaxed text-[15px]">{impact.text}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.section>

        {/* Global & Portfolio News Context */}
        {((report.global_context && report.global_context.length > 0) || (report.news_context && report.news_context.length > 0)) && (
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="mt-12 space-y-6"
          >
            <div className="flex items-center space-x-4 mb-6">
              <div className="h-px bg-slate-200 flex-1"></div>
              <h3 className="text-xs uppercase tracking-widest font-bold text-slate-400">Based on Today's News</h3>
              <div className="h-px bg-slate-200 flex-1"></div>
            </div>

            <div className="bg-white rounded-[2rem] p-6 md:p-8 border border-slate-200/60 shadow-sm space-y-5">
              {(report.global_context || []).slice(0, 2).map((news, idx) => (
                <a key={`global-${idx}`} href={news.url || '#'} target="_blank" rel="noreferrer" className="block group border-l-4 border-blue-500 pl-4 py-1 hover:bg-slate-50 transition-colors">
                  <p className="text-xs text-blue-600 font-bold tracking-widest uppercase mb-1">Macro Market Event</p>
                  <h4 className="text-slate-900 font-serif text-lg leading-snug group-hover:text-blue-600 transition-colors">{news.title}</h4>
                </a>
              ))}
              {(report.news_context || []).slice(0, 2).map((news, idx) => (
                <a key={`portfolio-${idx}`} href={news.url || '#'} target="_blank" rel="noreferrer" className="block group border-l-4 border-emerald-500 pl-4 py-1 hover:bg-slate-50 transition-colors">
                  <p className="text-xs text-emerald-600 font-bold tracking-widest uppercase mb-1">Portfolio Specific: {news.symbol}</p>
                  <h4 className="text-slate-900 font-serif text-lg leading-snug group-hover:text-emerald-600 transition-colors">{news.title}</h4>
                </a>
              ))}
            </div>
          </motion.section>
        )}

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-16 bg-slate-900 rounded-[2rem] p-8 md:p-12 text-center text-white relative overflow-hidden shadow-2xl shadow-slate-900/20"
        >
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>
          <span className="text-xs uppercase tracking-[0.25em] font-bold text-slate-400 mb-6 block">Executive Verdict</span>
          <p className="text-xl md:text-2xl font-medium leading-relaxed tracking-wide">{report.verdict || FALLBACK_REPORT.verdict}</p>
          <p className="text-[11px] mt-4 text-slate-400">{report.disclaimer || FALLBACK_REPORT.disclaimer}</p>
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
