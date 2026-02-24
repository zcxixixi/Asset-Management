import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AreaChart, Area, ResponsiveContainer, YAxis, XAxis, Tooltip } from 'recharts';
import { Eye, EyeOff, Sparkles, ShieldCheck, LayoutDashboard, ListFilter, Activity, Fingerprint, Database } from 'lucide-react';
import dashboardDataRaw from './data.json';

const dashboardData = dashboardDataRaw as any;

export default function AssetDashboard() {
  const [isPrivacyMode, setIsPrivacyMode] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'holdings' | 'diagnostics'>('overview');
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | 'all'>('30d');

  const filteredChartData = React.useMemo(() => {
    const data = dashboardData.chart_data;
    if (timeRange === '7d') return data.slice(-7);
    if (timeRange === '30d') return data.slice(-30);
    return data;
  }, [timeRange]);

  const p = (val: string | number) => isPrivacyMode ? '••••' : val;

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 font-sans selection:bg-blue-100">
      <div className="max-w-4xl mx-auto p-6 md:p-12 space-y-10">
        
        {/* Header */}
        <header className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-blue-200 shadow-lg">
              <ShieldCheck size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-slate-800 text-sm font-bold tracking-tight uppercase">Asset Guardian</h1>
              <p className="text-[10px] text-slate-400 font-mono uppercase tracking-widest leading-none">Trust Architecture v2.5</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex bg-slate-200/50 p-1 rounded-xl">
               {[
                 { id: 'overview', icon: <LayoutDashboard size={18} /> },
                 { id: 'holdings', icon: <ListFilter size={18} /> },
                 { id: 'diagnostics', icon: <Activity size={18} /> }
               ].map(tab => (
                 <button 
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`p-2 rounded-lg transition-all ${activeTab === tab.id ? 'bg-white shadow-sm text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}
                 >
                   {tab.icon}
                 </button>
               ))}
            </div>
            <button 
              onClick={() => setIsPrivacyMode(!isPrivacyMode)}
              className={`p-2 rounded-xl border transition-all shadow-sm ${isPrivacyMode ? 'bg-blue-600 border-blue-600 text-white' : 'bg-white border-slate-200 text-slate-600'}`}
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
                    {['7d', '30d', 'all'].map((range) => (
                      <button key={range} onClick={() => setTimeRange(range as any)} className={`px-2 py-1 text-[10px] font-bold rounded-md transition-all ${timeRange === range ? 'bg-slate-100 text-slate-900' : 'text-slate-400 hover:text-slate-600'}`}>{range.toUpperCase()}</button>
                    ))}
                  </div>
                </div>
              </section>

              <section className="h-48 md:h-64 w-full -ml-4">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={filteredChartData}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#2563eb" stopOpacity={0.1}/><stop offset="95%" stopColor="#2563eb" stopOpacity={0}/></linearGradient>
                    </defs>
                    <YAxis domain={['dataMin', 'dataMax']} hide={true} /><XAxis dataKey="date" hide={true} />
                    <Area type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={3} fill="url(#colorValue)" animationDuration={1500} />
                  </AreaChart>
                </ResponsiveContainer>
              </section>

              <section className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {dashboardData.assets.map((asset: any) => (
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
                    {dashboardData.holdings.map((h: any, idx: number) => (
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
                    {dashboardData.diagnostics.steps.map((step: any, i: number) => (
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

      </div>
    </div>
  );
}
