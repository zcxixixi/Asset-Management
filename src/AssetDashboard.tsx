import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AreaChart, Area, ResponsiveContainer, YAxis, XAxis, Tooltip } from 'recharts';
import { Eye, EyeOff, Sparkles, ShieldCheck, LayoutDashboard, ListFilter } from 'lucide-react';
import dashboardDataRaw from './data.json';

const dashboardData = dashboardDataRaw as any;

export default function AssetDashboard() {
  const [isPrivacyMode, setIsPrivacyMode] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'holdings'>('overview');
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | 'all'>('30d');

  const filteredChartData = React.useMemo(() => {
    const data = dashboardData.chart_data;
    if (timeRange === '7d') return data.slice(-7);
    if (timeRange === '30d') return data.slice(-30);
    return data;
  }, [timeRange]);

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
              <p className="text-[10px] text-slate-400 font-mono uppercase tracking-widest leading-none">Verified Security</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex bg-slate-200/50 p-1 rounded-xl">
               <button 
                onClick={() => setActiveTab('overview')}
                className={`p-2 rounded-lg transition-all ${activeTab === 'overview' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}
               >
                 <LayoutDashboard size={18} />
               </button>
               <button 
                onClick={() => setActiveTab('holdings')}
                className={`p-2 rounded-lg transition-all ${activeTab === 'holdings' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}
               >
                 <ListFilter size={18} />
               </button>
            </div>
            <button 
              onClick={() => setIsPrivacyMode(!isPrivacyMode)}
              className="p-2 bg-white hover:bg-slate-50 rounded-xl border border-slate-200 shadow-sm text-slate-600"
            >
              {isPrivacyMode ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </header>

        <AnimatePresence mode="wait">
          {activeTab === 'overview' ? (
            <motion.div 
              key="overview"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-10"
            >
              {/* Balance Card */}
              <section className="space-y-2">
                <div className="flex justify-between items-center">
                  <h2 className="text-slate-400 text-xs font-bold uppercase tracking-[0.2em]">Total Balance</h2>
                  <span className="text-[10px] text-slate-400 font-mono uppercase">{dashboardData.last_updated}</span>
                </div>
                <div className="flex items-baseline space-x-3">
                  <span className="text-4xl font-light text-slate-300">$</span>
                  <span className="text-7xl md:text-8xl font-semibold tracking-tighter text-slate-900">
                    {isPrivacyMode ? '••••••' : dashboardData.total_balance}
                  </span>
                </div>
                
                <div className="flex justify-between items-end pt-4">
                  <div className="flex items-center space-x-3">
                    <div className="px-3 py-1 bg-emerald-50 text-emerald-600 rounded-full text-xs font-bold border border-emerald-100 flex items-center">
                      {dashboardData.performance["1d"]} <span className="ml-1 font-mono opacity-50">LIVE</span>
                    </div>
                    <span className="text-[10px] text-slate-400 font-mono uppercase italic">
                      {dashboardData.performance["summary"]}
                    </span>
                  </div>
                  
                  <div className="flex space-x-1 bg-white p-1 rounded-lg border border-slate-200 shadow-sm">
                    {['7d', '30d', 'all'].map((range) => (
                      <button
                        key={range}
                        onClick={() => setTimeRange(range as any)}
                        className={`px-2 py-1 text-[10px] font-bold rounded-md transition-all ${
                          timeRange === range ? 'bg-slate-100 text-slate-900' : 'text-slate-400 hover:text-slate-600'
                        }`}
                      >
                        {range.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>
              </section>

              {/* Main Chart */}
              <section className="h-48 md:h-64 w-full -ml-4">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={filteredChartData}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2563eb" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <Tooltip 
                      contentStyle={{ borderRadius: '20px', border: 'none', boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)', fontSize: '12px' }}
                      itemStyle={{ color: '#2563eb', fontWeight: 'bold' }}
                    />
                    <YAxis domain={['dataMin', 'dataMax']} hide={true} />
                    <XAxis dataKey="date" hide={true} />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#2563eb" 
                      strokeWidth={3}
                      fill="url(#colorValue)" 
                      animationDuration={1500}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </section>

              {/* Insights */}
              {dashboardData.insights && (
                <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {dashboardData.insights.map((insight: string, idx: number) => (
                    <div key={idx} className="p-5 rounded-3xl bg-blue-600/5 border border-blue-600/10 flex space-x-4">
                      <Sparkles size={16} className="text-blue-600 mt-1 flex-shrink-0" />
                      <p className="text-xs text-blue-900 leading-relaxed font-medium">{insight}</p>
                    </div>
                  ))}
                </section>
              )}

              {/* Asset Cards */}
              <section className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {dashboardData.assets.map((asset: any, index: number) => (
                  <div key={asset.label} className="p-6 rounded-[2rem] bg-white border border-slate-200/60 shadow-sm hover:shadow-md transition-all">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 truncate">{asset.label}</p>
                    <p className="text-2xl font-bold text-slate-800 tracking-tight font-mono">
                      <span className="text-slate-300 mr-1">$</span>
                      {isPrivacyMode ? '••••' : asset.value}
                    </p>
                  </div>
                ))}
              </section>
            </motion.div>
          ) : (
            <motion.div 
              key="holdings"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              <div className="flex justify-between items-center">
                <h2 className="text-slate-800 text-lg font-bold">Current Holdings</h2>
                <div className="text-[10px] text-slate-400 font-mono bg-slate-100 px-2 py-1 rounded-md uppercase tracking-tighter">
                  Real-time Price Engine
                </div>
              </div>
              
              <div className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-slate-50/50">
                    <tr>
                      <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100">Asset</th>
                      <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 text-right">Quantity</th>
                      <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 text-right">Market Price</th>
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
                        <td className="px-6 py-5 border-b border-slate-50 text-right text-xs font-mono font-bold text-slate-600">
                          {isPrivacyMode ? '••' : h.qty}
                        </td>
                        <td className="px-6 py-5 border-b border-slate-50 text-right text-xs font-mono font-medium text-slate-400">
                          ${h.price}
                        </td>
                        <td className="px-6 py-5 border-b border-slate-50 text-right text-sm font-bold text-blue-600 font-mono">
                          ${isPrivacyMode ? '••••' : h.value}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </div>
  );
}
