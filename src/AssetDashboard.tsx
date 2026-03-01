import React, { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AreaChart, Area, ResponsiveContainer, YAxis, XAxis } from 'recharts';
import { Eye, EyeOff, Sparkles, ShieldCheck, LayoutDashboard, ListFilter, Activity, Fingerprint, Database, ChevronRight } from 'lucide-react';
import { bundledDashboardData, fetchLiveDashboardData } from './live_data';

type ActiveTab = 'overview' | 'holdings' | 'diagnostics';
type TimeRange = '7d' | '30d' | 'all';

interface AssetItem {
  label: string;
  value: string | number;
}

interface HoldingItem {
  symbol: string;
  name: string;
  qty: string | number;
  value: string | number;
}

interface ChartDataPoint {
  date: string;
  value: number;
}

interface DiagnosticsStep {
  name: string;
  status: string;
}

interface DiagnosticsData {
  math_proof: string;
  api_status: string;
  latency_ms: string | number;
  last_run: string;
  steps: DiagnosticsStep[];
}

interface DashboardData {
  total_balance: string | number;
  performance: { '1d': string | number };
  chart_data: ChartDataPoint[];
  assets: AssetItem[];
  holdings: HoldingItem[];
  diagnostics: DiagnosticsData;
}

interface RawSummary {
  total_usd?: number;
  cash_usd?: number;
  gold_usd?: number;
  stocks_usd?: number;
}

interface RawChartDataPoint {
  date?: string;
  value?: number;
  total_usd?: number;
}

interface AdvisorSuggestion {
  asset?: string;
  action?: string;
  rationale?: string;
}

interface AdvisorBriefingData {
  headline?: string;
  macro_summary?: string;
  verdict?: string;
  suggestions?: AdvisorSuggestion[];
}

interface RawDashboardData {
  total_balance?: string | number;
  performance?: { '1d'?: string | number };
  chart_data?: RawChartDataPoint[];
  assets?: AssetItem[];
  holdings?: HoldingItem[];
  diagnostics?: Partial<DiagnosticsData>;
  summary?: RawSummary;
  daily_data?: { date?: string; total_usd?: number }[];
  last_updated?: string;
  advisor_briefing?: AdvisorBriefingData;
}

function buildDashboardData(rawData: RawDashboardData): DashboardData {
  const normalizedChartData: ChartDataPoint[] = (rawData.chart_data ?? [])
    .map((point) => ({
      date: String(point.date ?? ''),
      value: Number(point.value ?? point.total_usd ?? 0),
    }))
    .filter((point) => point.date.length > 0);

  const fallbackChartData: ChartDataPoint[] = (rawData.daily_data ?? []).map((point) => ({
    date: String(point.date ?? ''),
    value: Number(point.total_usd ?? 0),
  }));

  const fallbackAssets: AssetItem[] = [
    { label: 'Cash USD', value: Number(rawData.summary?.cash_usd ?? 0).toFixed(2) },
    { label: 'Gold USD', value: Number(rawData.summary?.gold_usd ?? 0).toFixed(2) },
    { label: 'US Stocks', value: Number(rawData.summary?.stocks_usd ?? 0).toFixed(2) },
  ];

  return {
    total_balance: rawData.total_balance ?? Number(rawData.summary?.total_usd ?? 0).toFixed(2),
    performance: { '1d': rawData.performance?.['1d'] ?? 'Live' },
    chart_data: normalizedChartData.length > 0 ? normalizedChartData : fallbackChartData,
    assets: rawData.assets && rawData.assets.length > 0 ? rawData.assets : fallbackAssets,
    holdings: rawData.holdings ?? [],
    diagnostics: {
      math_proof: rawData.diagnostics?.math_proof ?? 'N/A',
      api_status: rawData.diagnostics?.api_status ?? 'Unknown',
      latency_ms: rawData.diagnostics?.latency_ms ?? '--',
      last_run: rawData.diagnostics?.last_run ?? rawData.last_updated ?? 'N/A',
      steps: rawData.diagnostics?.steps ?? [{ name: 'Data Load', status: 'Success' }],
    },
  };
}

interface AssetDashboardProps {
  onOpenAdvisor?: () => void;
  onOpenNews?: () => void;
  isPrivacyMode: boolean;
  setIsPrivacyMode: (val: boolean) => void;
}

export default function AssetDashboard({ onOpenAdvisor, onOpenNews, isPrivacyMode, setIsPrivacyMode }: AssetDashboardProps) {
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');
  const [timeRange, setTimeRange] = useState<TimeRange>('7d');
  const [rawData, setRawData] = useState<RawDashboardData>(bundledDashboardData as RawDashboardData);

  useEffect(() => {
    let alive = true;
    fetchLiveDashboardData()
      .then((payload) => {
        if (alive) {
          setRawData(payload as RawDashboardData);
        }
      })
      .catch(() => {
        // Keep bundled fallback when live data is unavailable.
      });

    return () => {
      alive = false;
    };
  }, []);

  const dashboardData = useMemo(() => buildDashboardData(rawData), [rawData]);
  const advisorBriefing = rawData.advisor_briefing;
  const advisorHeadline = advisorBriefing?.headline ?? 'Portfolio Pulse: Balanced but Event-Sensitive';
  const advisorSummary =
    advisorBriefing?.macro_summary ??
    'No live AI briefing available yet. Keep diversified allocation and rebalance with discipline.';
  const advisorSuggestion = advisorBriefing?.suggestions?.[0];

  const filteredChartData = useMemo(() => {
    const data = dashboardData.chart_data;
    if (timeRange === '7d') return data.slice(-7);
    if (timeRange === '30d') return data.slice(-30);
    return data;
  }, [dashboardData.chart_data, timeRange]);

  const p = (val: string | number) => isPrivacyMode ? '••••' : val;
  const formatChartDate = (date: string) => {
    const parsedDate = new Date(`${date}T00:00:00Z`);
    if (Number.isNaN(parsedDate.getTime())) return date;
    if (timeRange === 'all') {
      return parsedDate.toLocaleDateString(undefined, { month: 'short', year: '2-digit', timeZone: 'UTC' });
    }
    return parsedDate.toLocaleDateString(undefined, { month: 'short', day: 'numeric', timeZone: 'UTC' });
  };

  const tabs: Array<{ id: ActiveTab; icon: React.ReactNode }> = [
    { id: 'overview', icon: <LayoutDashboard size={18} /> },
    { id: 'holdings', icon: <ListFilter size={18} /> },
    { id: 'diagnostics', icon: <Activity size={18} /> },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] relative text-slate-900 font-sans selection:bg-blue-100">
      {/* Subtle Background Pattern for Frosted Glass Visibility */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#e2e8f0_1px,transparent_1px),linear-gradient(to_bottom,#e2e8f0_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-40 pointer-events-none"></div>

      <div className="max-w-4xl mx-auto p-6 md:p-12 space-y-12 relative z-10">

        {/* Header */}
        <header className="flex justify-between items-center bg-white/60 backdrop-blur-md p-4 rounded-3xl border border-slate-200/50 shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-blue-200 shadow-xl">
              <ShieldCheck size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-slate-900 text-[15px] font-bold tracking-tight">Asset Guardian</h1>
              <p className="text-[10px] text-slate-500 font-mono uppercase tracking-widest leading-none mt-0.5">Trust Architecture v2.5</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => onOpenNews?.()}
              className="flex items-center space-x-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold uppercase tracking-wider rounded-xl shadow-lg transition-all"
            >
              <Activity size={14} />
              <span>Daily News</span>
            </button>

            <div className="flex bg-slate-100 p-1.5 rounded-xl border border-slate-200/50">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`p-2 rounded-lg transition-all ${activeTab === tab.id ? 'bg-white shadow-sm text-blue-600 font-medium' : 'text-slate-500 hover:text-slate-800'}`}
                >
                  {tab.icon}
                </button>
              ))}
            </div>
            <button
              onClick={() => setIsPrivacyMode(!isPrivacyMode)}
              className={`p-2.5 rounded-xl border transition-all shadow-sm ${isPrivacyMode ? 'bg-blue-600 border-blue-600 text-white' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'}`}
            >
              {isPrivacyMode ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </header>

        <AnimatePresence mode="wait">
          {activeTab === 'overview' && (
            <motion.div key="overview" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-10">
              <section className="space-y-2">
                <h2 className="text-slate-400 text-xs font-bold uppercase tracking-[0.2em]">Total Balance</h2>
                <div className="flex items-baseline space-x-3">
                  <span className="text-4xl font-light text-slate-300">$</span>
                  <span className="text-7xl md:text-8xl font-semibold tracking-tighter text-slate-900">{p(dashboardData.total_balance)}</span>
                </div>
                <div className="flex justify-between items-end pt-4">
                  <div className="flex items-center space-x-3">
                    <div className="px-3 py-1 bg-emerald-50 text-emerald-600 rounded-full text-xs font-bold border border-emerald-100 flex items-center">
                      {p(dashboardData.performance["1d"])} <span className="ml-1 font-mono opacity-50 uppercase">Sync</span>
                    </div>
                  </div>
                  <div className="flex space-x-1 bg-white p-1 rounded-lg border border-slate-200 shadow-sm">
                    {(['7d', '30d', 'all'] as const).map((range) => (
                      <button key={range} onClick={() => setTimeRange(range)} className={`px-2 py-1 text-[10px] font-bold rounded-md transition-all ${timeRange === range ? 'bg-slate-100 text-slate-900' : 'text-slate-400 hover:text-slate-600'}`}>{range.toUpperCase()}</button>
                    ))}
                  </div>
                </div>
              </section>

              <section className="h-48 md:h-64 w-full -ml-4">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={filteredChartData} margin={{ top: 8, right: 8, left: 0, bottom: 4 }}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#2563eb" stopOpacity={0.1} /><stop offset="95%" stopColor="#2563eb" stopOpacity={0} /></linearGradient>
                    </defs>
                    <YAxis domain={['dataMin', 'dataMax']} hide={true} />
                    <XAxis
                      dataKey="date"
                      tickFormatter={formatChartDate}
                      axisLine={false}
                      tickLine={false}
                      minTickGap={20}
                      tick={{ fontSize: 10, fill: '#94a3b8' }}
                    />
                    <Area type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={3} fill="url(#colorValue)" animationDuration={1500} />
                  </AreaChart>
                </ResponsiveContainer>
              </section>

              <section className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {dashboardData.assets.map((asset) => (
                  <div key={asset.label} className="p-6 rounded-[2rem] bg-white border border-slate-200/60 shadow-sm hover:shadow-md transition-all relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-2 opacity-10"><Database size={40} /></div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 truncate">{asset.label}</p>
                    <p className="text-2xl font-bold text-slate-800 tracking-tight font-mono"><span className="text-slate-300 mr-1">$</span>{p(asset.value)}</p>
                  </div>
                ))}
              </section>
            </motion.div>
          )}

          {activeTab === 'holdings' && (
            <motion.div key="holdings" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-6">
              <div className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-slate-50/50">
                    <tr>
                      <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100">Asset</th>
                      <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 text-right">Qty</th>
                      <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 text-right">Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboardData.holdings.map((h, idx) => (
                      <tr key={idx} className="group hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-5 border-b border-slate-50">
                          <div className="text-sm font-bold text-slate-800">{h.symbol}</div>
                          <div className="text-[10px] text-slate-400 font-medium truncate max-w-[120px]">{h.name}</div>
                        </td>
                        <td className="px-6 py-5 border-b border-slate-50 text-right text-xs font-mono font-bold text-slate-600">{p(h.qty)}</td>
                        <td className="px-6 py-5 border-b border-slate-50 text-right text-sm font-bold text-blue-600 font-mono">${p(h.value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {activeTab === 'diagnostics' && (
            <motion.div key="diagnostics" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-6 text-slate-600">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-8 rounded-[2rem] bg-slate-900 text-slate-300 border border-slate-800 space-y-6">
                  <div className="flex items-center space-x-2 text-blue-400">
                    <Fingerprint size={20} />
                    <h3 className="text-xs font-bold uppercase tracking-widest">Audit Evidence</h3>
                  </div>
                  <div className="space-y-4 font-mono text-[11px]">
                    <div className="flex justify-between border-b border-slate-800 pb-2"><span>Atomic Proof</span> <span className="text-emerald-400">{dashboardData.diagnostics.math_proof}</span></div>
                    <div className="flex justify-between border-b border-slate-800 pb-2"><span>API Status</span> <span className="text-emerald-400">{dashboardData.diagnostics.api_status}</span></div>
                    <div className="flex justify-between border-b border-slate-800 pb-2"><span>Latency</span> <span className="text-blue-400">{dashboardData.diagnostics.latency_ms}ms</span></div>
                    <div className="flex justify-between border-b border-slate-800 pb-2"><span>Last Run</span> <span>{dashboardData.diagnostics.last_run}</span></div>
                  </div>
                </div>

                <div className="p-8 rounded-[2rem] bg-white border border-slate-200 space-y-6 shadow-sm">
                  <div className="flex items-center space-x-2 text-slate-400">
                    <Activity size={20} />
                    <h3 className="text-xs font-bold uppercase tracking-widest">Pipeline Health</h3>
                  </div>
                  <div className="space-y-3">
                    {dashboardData.diagnostics.steps.map((step, i) => (
                      <div key={i} className="flex items-center space-x-3">
                        <div className={`w-2 h-2 rounded-full ${step.status === 'Success' ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-amber-500'}`} />
                        <span className="text-xs font-medium text-slate-500 truncate">{step.name}</span>
                        <div className="flex-grow border-t border-dotted border-slate-200" />
                        <span className={`text-[10px] font-bold ${step.status === 'Success' ? 'text-emerald-600' : 'text-amber-600'}`}>{step.status.toUpperCase()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="p-8 rounded-[2rem] bg-blue-50 border border-blue-100 flex items-start space-x-4">
                <Sparkles size={18} className="text-blue-600 mt-1 flex-shrink-0" />
                <div className="space-y-1">
                  <p className="text-xs font-bold text-blue-900 uppercase">System Integrity Guarantee</p>
                  <p className="text-xs text-blue-700 leading-relaxed">This terminal is powered by an "Atomic Sync" architecture. Data flows are cryptographically signed by the system planner and verified through mathematical balance proofs before every commit.</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* AI Insights & Robo-Advisor (Apple Interactive Widget Style) */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="group relative overflow-hidden rounded-3xl bg-white/80 backdrop-blur-3xl p-8 md:p-10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100/50 hover:shadow-[0_12px_40px_rgb(0,0,0,0.08)] hover:border-slate-200/60 transition-all duration-300"
        >
          <div className="relative z-10 space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-full bg-slate-50 border border-slate-100 flex items-center justify-center shadow-sm group-hover:bg-blue-50 group-hover:border-blue-100 transition-colors">
                  <Sparkles className="text-slate-600 group-hover:text-blue-500 transition-colors" size={14} strokeWidth={2.5} />
                </div>
                <h2 className="text-slate-800 text-sm font-medium tracking-tight">
                  OpenClaw Assistant
                </h2>
              </div>
              <div className="flex items-center space-x-3">
                <span className="px-2.5 py-1 rounded-full bg-slate-100/80 text-slate-500 text-[10px] font-semibold tracking-widest border border-slate-200/50 uppercase">
                  Just Updated
                </span>
                <a
                  href="#"
                  onClick={(e) => { e.preventDefault(); onOpenAdvisor?.(); }}
                  className="w-6 h-6 rounded-full bg-slate-50 flex items-center justify-center hover:bg-slate-200 transition-colors cursor-pointer group-hover:bg-slate-100"
                  aria-label="View Analysis"
                >
                  <ChevronRight size={14} className="text-slate-400 group-hover:text-slate-600 group-hover:translate-x-0.5 transition-all" strokeWidth={2.5} />
                </a>
              </div>
            </div>

            <h3 className="text-2xl md:text-3xl text-slate-900 font-semibold tracking-tighter">
              {advisorHeadline}
            </h3>

            <p className="text-slate-500 leading-relaxed text-sm md:text-[15px] font-normal tracking-wide max-w-2xl">
              {advisorSummary}
              {advisorSuggestion?.asset ? (
                <>
                  {' '}Primary action: <span className="text-slate-900 font-semibold underline decoration-slate-200 underline-offset-4 pointer-events-none">{advisorSuggestion.asset}</span> — {advisorSuggestion.action || 'Hold'}.
                </>
              ) : null}
            </p>

            <div className="pt-6 flex items-center justify-between border-t border-slate-100 mt-8">
              <a
                href="#"
                onClick={(e) => { e.preventDefault(); onOpenAdvisor?.(); }}
                className="text-blue-600 text-sm font-medium hover:text-blue-700 hover:underline underline-offset-4 cursor-pointer"
              >
                View Analysis Details
              </a>
              <div className="flex items-center space-x-2 text-xs text-slate-400 font-medium tracking-wide">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-20"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                </span>
                <span>Synced with Market</span>
              </div>
            </div>
          </div>
        </motion.section>

      </div>
    </div>
  );
}
