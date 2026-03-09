import { useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  ArrowRight,
  ChevronLeft,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react';
import { bundledDashboardData, useLiveDashboardData } from './live_data';

export interface AdvisorBriefingProps {
  payload?: AdvisorPayload;
  onBack: () => void;
  isPrivacyMode: boolean;
}

export interface Insight {
  type: 'opportunity' | 'warning' | 'neutral';
  asset: string;
  text: string;
}

interface DashboardAsset {
  label: string;
  value: string | number;
}

interface RawSuggestion {
  asset?: string;
  action?: string;
  rationale?: string;
  thesis?: string;
  catalyst?: string;
  risk?: string;
  horizon?: string;
  confidence?: string;
}

interface RawBriefingNewsItem {
  symbol?: string;
  title?: string;
  headline?: string;
  publisher?: string;
  source?: string;
  published_at?: string;
  timestamp?: string;
  url?: string;
  summary?: string;
  channel?: string;
}

interface RawPortfolioOverlay {
  stance?: string;
  thesis?: string;
  rebalancing_watch?: string;
}

interface RawMacroTheme {
  theme?: string;
  implication?: string;
}

interface AdvisorBriefingData {
  generated_at?: string;
  source?: string;
  headline?: string;
  macro_summary?: string;
  verdict?: string;
  portfolio_overlay?: RawPortfolioOverlay;
  macro_themes?: RawMacroTheme[];
  suggestions?: RawSuggestion[];
  risks?: string[];
  news_context?: RawBriefingNewsItem[];
  global_context?: RawBriefingNewsItem[];
  disclaimer?: string;
}

export interface AdvisorPayload {
  insights?: Insight[];
  assets?: DashboardAsset[];
  advisor_briefing?: AdvisorBriefingData;
}

interface NormalizedNewsItem {
  symbol: string;
  headline: string;
  source: string;
  timestamp: string;
  url: string;
  channel: string;
}

interface NormalizedSuggestion {
  asset: string;
  action: string;
  rationale: string;
  thesis: string;
  catalyst: string;
  risk: string;
  horizon: string;
  confidence: string;
}

interface NormalizedBriefingData {
  generated_at: string;
  source: string;
  headline: string;
  macro_summary: string;
  verdict: string;
  portfolio_overlay: {
    stance: string;
    thesis: string;
    rebalancing_watch: string;
  };
  macro_themes: Array<{
    theme: string;
    implication: string;
  }>;
  suggestions: NormalizedSuggestion[];
  risks: string[];
  news_context: NormalizedNewsItem[];
  global_context: NormalizedNewsItem[];
  disclaimer: string;
}

const FALLBACK_REPORT: NormalizedBriefingData = {
  generated_at: 'N/A',
  source: 'rule-based',
  headline: 'Portfolio Pulse: Balanced but Event-Sensitive',
  macro_summary:
    'No live AI briefing was generated yet. Keep diversified exposure and validate signals against your own risk constraints.',
  verdict: 'NEUTRAL',
  portfolio_overlay: {
    stance: 'BALANCED',
    thesis: 'Maintain a balanced posture until catalysts and macro conditions become more directional.',
    rebalancing_watch: 'Reassess if a single position or sleeve starts dominating risk.',
  },
  macro_themes: [
    {
      theme: 'Risk discipline',
      implication: 'Protect optionality while waiting for clearer, higher-conviction setups.',
    },
  ],
  suggestions: [
    {
      asset: 'Cash USD',
      action: 'HOLD',
      rationale: 'Cash buffer provides optionality when volatility increases.',
      thesis: 'Liquidity matters when conviction is incomplete.',
      catalyst: 'Deploy only when risk/reward improves materially.',
      risk: 'Putting reserve capital to work too early can impair flexibility.',
      horizon: 'SHORT',
      confidence: 'MEDIUM',
    },
    {
      asset: 'US Stocks',
      action: 'HOLD',
      rationale: 'Avoid overreacting to a single headline cycle.',
      thesis: 'Keep the core book intact while validating new information.',
      catalyst: 'Earnings and macro releases will clarify whether trend strength is durable.',
      risk: 'Concentration can turn narrative volatility into real drawdown.',
      horizon: 'MEDIUM',
      confidence: 'MEDIUM',
    },
  ],
  risks: ['Macro uncertainty remains elevated.'],
  news_context: [],
  global_context: [],
  disclaimer: 'Informational only, not financial advice.',
};

const actionToInsightType = (action: string): Insight['type'] => {
  const normalized = action.toLowerCase();
  if (['sell', 'reduce', 'trim', 'rebalance', 'tighten', 'hedge', 'defensive'].some((token) => normalized.includes(token))) {
    return 'warning';
  }
  if (['buy', 'add', 'deploy', 'accumulate', 'hold', 'increase', 'keep', 'maintain'].some((token) => normalized.includes(token))) {
    return 'opportunity';
  }
  return 'neutral';
};

const normalizeNewsItem = (item: RawBriefingNewsItem): NormalizedNewsItem => ({
  symbol: item.symbol || 'MACRO',
  headline: item.headline || item.title || 'Untitled headline',
  source: item.source || item.publisher || 'Unknown',
  timestamp: item.timestamp || item.published_at || '',
  url: item.url || '#',
  channel: item.channel || 'market-news',
});

const normalizeSuggestion = (item: RawSuggestion): NormalizedSuggestion => ({
  asset: item.asset || 'Portfolio',
  action: item.action || 'HOLD',
  rationale: item.rationale || 'No rationale provided.',
  thesis: item.thesis || 'No thesis provided.',
  catalyst: item.catalyst || 'No catalyst provided.',
  risk: item.risk || 'No key risk provided.',
  horizon: item.horizon || 'MEDIUM',
  confidence: item.confidence || 'MEDIUM',
});

const normalizeBriefing = (report?: AdvisorBriefingData): NormalizedBriefingData => ({
  generated_at: report?.generated_at || FALLBACK_REPORT.generated_at,
  source: report?.source || FALLBACK_REPORT.source,
  headline: report?.headline || FALLBACK_REPORT.headline,
  macro_summary: report?.macro_summary || FALLBACK_REPORT.macro_summary,
  verdict: report?.verdict || FALLBACK_REPORT.verdict,
  portfolio_overlay: {
    stance: report?.portfolio_overlay?.stance || FALLBACK_REPORT.portfolio_overlay.stance,
    thesis: report?.portfolio_overlay?.thesis || FALLBACK_REPORT.portfolio_overlay.thesis,
    rebalancing_watch:
      report?.portfolio_overlay?.rebalancing_watch || FALLBACK_REPORT.portfolio_overlay.rebalancing_watch,
  },
  macro_themes:
    report?.macro_themes && report.macro_themes.length > 0
      ? report.macro_themes.map((theme) => ({
          theme: theme.theme || 'Untitled theme',
          implication: theme.implication || 'No implication provided.',
        }))
      : FALLBACK_REPORT.macro_themes,
  suggestions:
    report?.suggestions && report.suggestions.length > 0
      ? report.suggestions.map(normalizeSuggestion)
      : FALLBACK_REPORT.suggestions,
  risks: report?.risks && report.risks.length > 0 ? report.risks : FALLBACK_REPORT.risks,
  news_context: (report?.news_context || []).map(normalizeNewsItem),
  global_context: (report?.global_context || []).map(normalizeNewsItem),
  disclaimer: report?.disclaimer || FALLBACK_REPORT.disclaimer,
});

export default function AdvisorBriefing({ payload: propPayload, onBack, isPrivacyMode }: AdvisorBriefingProps) {
  const typedData = useLiveDashboardData(
    (propPayload ?? bundledDashboardData) as AdvisorPayload,
    { enabled: !propPayload },
  );

  useEffect(() => {
    window.scrollTo(0, 0);
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

  const report = normalizeBriefing(typedData.advisor_briefing);
  const fallbackInsights: Insight[] = report.suggestions.slice(0, 3).map((suggestion) => ({
    type: actionToInsightType(suggestion.action),
    asset: suggestion.asset,
    text: suggestion.rationale,
  }));

  const insights: Insight[] =
    typedData.insights && typedData.insights.length > 0 ? typedData.insights : fallbackInsights;

  const publishAt = report.generated_at;
  const sourceLabel = report.source.toUpperCase();
  const p = (val: string | number) => (isPrivacyMode ? '••••••' : String(val));

  return (
    <div className="min-h-screen bg-slate-50 relative text-slate-900 font-sans selection:bg-blue-100">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#e2e8f0_1px,transparent_1px),linear-gradient(to_bottom,#e2e8f0_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_100%_at_50%_0%,#000_60%,transparent_100%)] opacity-30 pointer-events-none fixed"></div>

      <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4 md:px-12 backdrop-blur-xl bg-white/60 border-b border-slate-200/50">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
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

      <main className="max-w-5xl mx-auto pt-32 pb-24 px-6 relative z-10">
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
          className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-[-0.03em] text-slate-900 leading-[1.05] mb-6"
          style={{ fontFamily: "'Playfair Display', 'Merriweather', serif" }}
        >
          {report.headline}
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-lg md:text-xl text-slate-600 leading-relaxed font-normal mb-12"
        >
          {report.macro_summary}
        </motion.p>

        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="grid gap-6 md:grid-cols-[1.4fr_1fr] mb-12"
        >
          <div className="rounded-[2rem] border border-slate-200/60 bg-white p-8 shadow-sm">
            <div className="flex items-center gap-3 mb-5">
              <Target className="text-blue-600" size={18} />
              <h3 className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500">Portfolio Overlay</h3>
            </div>
            <p className="text-sm uppercase tracking-[0.3em] text-blue-600 font-semibold mb-3">{report.portfolio_overlay.stance}</p>
            <p className="text-xl text-slate-900 leading-relaxed mb-4">{report.portfolio_overlay.thesis}</p>
            <p className="text-sm text-slate-500">Rebalancing watch: {report.portfolio_overlay.rebalancing_watch}</p>
          </div>

          <div className="rounded-[2rem] border border-slate-200/60 bg-slate-900 p-8 shadow-sm text-white">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400 font-bold mb-3">Executive Verdict</p>
            <p className="text-3xl font-semibold tracking-tight mb-3">{report.verdict}</p>
            <p className="text-sm text-slate-300">{report.disclaimer}</p>
          </div>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-6 mb-12"
        >
          <div className="flex items-center space-x-4 mb-8">
            <div className="h-px bg-slate-200 flex-1"></div>
            <h3 className="text-xs uppercase tracking-widest font-bold text-slate-400">Direct Portfolio Impact</h3>
            <div className="h-px bg-slate-200 flex-1"></div>
          </div>

          <div className="grid gap-4">
            {insights.map((impact) => {
              const holding = typedData.assets?.find((asset) => asset.label === impact.asset);
              return (
                <div
                  key={`${impact.asset}-${impact.type}`}
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
                          {holding ? p(holding.value) : '--'}
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

        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="mb-12"
        >
          <div className="flex items-center space-x-4 mb-6">
            <div className="h-px bg-slate-200 flex-1"></div>
            <h3 className="text-xs uppercase tracking-widest font-bold text-slate-400">Macro Themes</h3>
            <div className="h-px bg-slate-200 flex-1"></div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {report.macro_themes.map((theme) => (
              <div key={theme.theme} className="rounded-[2rem] border border-slate-200/60 bg-white p-6 shadow-sm">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400 font-semibold mb-2">{theme.theme}</p>
                <p className="text-slate-700 leading-relaxed">{theme.implication}</p>
              </div>
            ))}
          </div>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-12"
        >
          <div className="flex items-center space-x-4 mb-6">
            <div className="h-px bg-slate-200 flex-1"></div>
            <h3 className="text-xs uppercase tracking-widest font-bold text-slate-400">Per-Holding Suggestions</h3>
            <div className="h-px bg-slate-200 flex-1"></div>
          </div>

          <div className="grid gap-4">
            {report.suggestions.map((suggestion) => (
              <div key={`${suggestion.asset}-${suggestion.action}`} className="rounded-[2rem] border border-slate-200/60 bg-white p-6 md:p-8 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3 mb-5">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400 font-semibold mb-1">{suggestion.action}</p>
                    <h4 className="text-2xl font-semibold tracking-tight text-slate-900">{suggestion.asset}</h4>
                  </div>
                  <div className="flex gap-2 text-xs uppercase tracking-[0.2em]">
                    <span className="rounded-full bg-slate-100 px-3 py-1 font-semibold text-slate-600">{suggestion.horizon}</span>
                    <span className="rounded-full bg-blue-50 px-3 py-1 font-semibold text-blue-700">{suggestion.confidence}</span>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400 font-semibold mb-2">Rationale</p>
                    <p className="text-slate-700 leading-relaxed">{suggestion.rationale}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400 font-semibold mb-2">Thesis</p>
                    <p className="text-slate-700 leading-relaxed">{suggestion.thesis}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400 font-semibold mb-2">Catalyst</p>
                    <p className="text-slate-700 leading-relaxed">{suggestion.catalyst}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400 font-semibold mb-2">Risk</p>
                    <p className="text-slate-700 leading-relaxed">{suggestion.risk}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.section>

        {report.risks.length > 0 && (
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45 }}
            className="mb-12"
          >
            <div className="flex items-center space-x-4 mb-6">
              <div className="h-px bg-slate-200 flex-1"></div>
              <h3 className="text-xs uppercase tracking-widest font-bold text-slate-400">Key Risks</h3>
              <div className="h-px bg-slate-200 flex-1"></div>
            </div>

            <div className="grid gap-3">
              {report.risks.slice(0, 4).map((risk) => (
                <div key={risk} className="rounded-2xl border border-amber-100 bg-amber-50 px-5 py-4 text-amber-900">
                  {risk}
                </div>
              ))}
            </div>
          </motion.section>
        )}

        {((report.global_context && report.global_context.length > 0) || (report.news_context && report.news_context.length > 0)) && (
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="mt-12 space-y-6"
          >
            <div className="flex items-center space-x-4 mb-6">
              <div className="h-px bg-slate-200 flex-1"></div>
              <h3 className="text-xs uppercase tracking-widest font-bold text-slate-400">Evidence Base</h3>
              <div className="h-px bg-slate-200 flex-1"></div>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <div className="bg-white rounded-[2rem] p-6 md:p-8 border border-slate-200/60 shadow-sm space-y-4">
                <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-400">Macro Context</p>
                {(report.global_context || []).slice(0, 3).map((news) => (
                  <a key={`global-${news.url}-${news.headline}`} href={news.url || '#'} target="_blank" rel="noreferrer" className="block group border-l-4 border-blue-500 pl-4 py-1 hover:bg-slate-50 transition-colors">
                    <p className="text-xs text-blue-600 font-bold tracking-widest uppercase mb-1">{news.channel}</p>
                    <h4 className="text-slate-900 font-serif text-lg leading-snug group-hover:text-blue-600 transition-colors">{news.headline}</h4>
                    <p className="text-xs text-slate-400 mt-2">{news.source} · {news.timestamp}</p>
                  </a>
                ))}
              </div>

              <div className="bg-white rounded-[2rem] p-6 md:p-8 border border-slate-200/60 shadow-sm space-y-4">
                <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-400">Portfolio Context</p>
                {(report.news_context || []).slice(0, 3).map((news) => (
                  <a key={`portfolio-${news.url}-${news.headline}`} href={news.url || '#'} target="_blank" rel="noreferrer" className="block group border-l-4 border-emerald-500 pl-4 py-1 hover:bg-slate-50 transition-colors">
                    <p className="text-xs text-emerald-600 font-bold tracking-widest uppercase mb-1">{news.symbol} · {news.channel}</p>
                    <h4 className="text-slate-900 font-serif text-lg leading-snug group-hover:text-emerald-600 transition-colors">{news.headline}</h4>
                    <p className="text-xs text-slate-400 mt-2">{news.source} · {news.timestamp}</p>
                  </a>
                ))}
              </div>
            </div>
          </motion.section>
        )}

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.55 }}
          className="mt-16 bg-slate-900 rounded-[2rem] p-8 md:p-12 text-center text-white relative overflow-hidden shadow-2xl shadow-slate-900/20"
        >
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>
          <span className="text-xs uppercase tracking-[0.25em] font-bold text-slate-400 mb-6 block">Executive Verdict</span>
          <p className="text-xl md:text-2xl font-medium leading-relaxed tracking-wide">{report.portfolio_overlay.stance}: {report.verdict}</p>
          <p className="text-[11px] mt-4 text-slate-400">{report.disclaimer}</p>
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
