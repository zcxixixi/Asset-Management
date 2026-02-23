import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { AreaChart, Area, ResponsiveContainer, YAxis, XAxis } from 'recharts';
import { Eye, EyeOff } from 'lucide-react';
import dashboardData from './data.json';

export default function AssetDashboard() {
  const [isPrivacyMode, setIsPrivacyMode] = useState(false);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | 'all'>('7d');



  // Filter chart data
  const filteredChartData = React.useMemo(() => {
    const data = dashboardData.chart_data;
    if (timeRange === '7d') return data.slice(-7);
    if (timeRange === '30d') return data.slice(-30);
    return data;
  }, [timeRange]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-6 md:p-12 font-sans selection:bg-blue-100">
      <div className="max-w-4xl mx-auto space-y-12">
        
        {/* Header & Privacy Toggle */}
        <header className="flex justify-between items-center">
          <h1 className="text-slate-500 text-sm font-semibold tracking-widest uppercase">
            Asset Snapshot
          </h1>
          <button 
            onClick={() => setIsPrivacyMode(!isPrivacyMode)}
            className="p-2 bg-white hover:bg-slate-100 rounded-full transition-all border border-slate-200 shadow-sm"
          >
            {isPrivacyMode ? <EyeOff size={18} className="text-slate-400" /> : <Eye size={18} className="text-slate-700" />}
          </button>
        </header>

        {/* Hero Section: Total Net Worth */}
        <section className="space-y-4">
          <h2 className="text-slate-500 text-lg font-medium">Total Balance</h2>
          <div className="flex items-baseline space-x-4">
            <span className="text-3xl font-light text-slate-400">$</span>
            <motion.span 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-6xl md:text-8xl font-semibold tracking-tighter text-slate-800 transition-all duration-500"
            >
              {isPrivacyMode ? '••••••' : dashboardData.total_balance}
            </motion.span>
          </div>
          
          {/* Performance Pills */}
          <div className="flex justify-between items-end">
            <div className="flex space-x-3 text-sm font-medium">
              <div className="px-3 py-1 bg-green-50 text-green-700 rounded-full flex items-center border border-green-200 shadow-sm">
                {dashboardData.performance["7d"]} <span className="text-green-700/50 ml-1">7D</span>
              </div>
              <div className="px-3 py-1 bg-green-50 text-green-700 rounded-full flex items-center border border-green-200 shadow-sm">
                {dashboardData.performance["30d"]} <span className="text-green-700/50 ml-1">30D</span>
              </div>
            </div>
            
            {/* Range Selectors */}
            <div className="flex space-x-2 bg-white p-1 rounded-lg border border-slate-200 shadow-sm">
              {['7d', '30d', 'all'].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range as any)}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                    timeRange === range
                      ? 'bg-slate-100 text-slate-800'
                      : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {range.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Trend Chart */}
        <section className="h-48 md:h-64 w-full -ml-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={filteredChartData}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <YAxis domain={['dataMin', 'dataMax']} hide={true} />
              <XAxis 
                dataKey="date" 
                tick={{fontSize: 10, fill: '#94a3b8'}} 
                axisLine={false} 
                tickLine={false} 
                dy={10}
                minTickGap={30}
              />
              <Area 
                type="linear" 
                dataKey="value" 
                stroke="#2563eb" 
                strokeWidth={3}
                fillOpacity={1} 
                fill="url(#colorValue)" 
                animationDuration={800}
                animationEasing="ease-out"
              />
            </AreaChart>
          </ResponsiveContainer>
        </section>

        {/* Asset Breakdown Cards */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {dashboardData.assets.map((asset: any, index: number) => (
            <motion.div 
              key={asset.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-6 rounded-3xl bg-white border border-slate-200/60 shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] hover:border-slate-300 transition-all duration-300"
            >
              <h3 className="text-slate-500 text-sm font-medium mb-4">{asset.label}</h3>
              <div className="text-2xl font-bold tracking-tight text-slate-800 transition-all duration-500">
                <span className="text-slate-400 font-medium mr-1">$</span>
                {isPrivacyMode ? '••••' : asset.value}
              </div>
            </motion.div>
          ))}
        </section>

      </div>
    </div>
  );
}
