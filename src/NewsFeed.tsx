import React from 'react';
import { motion } from 'framer-motion';
import { Newspaper, ExternalLink, Calendar, ArrowLeft } from 'lucide-react';


interface NewsItem {
    symbol: string;
    title: string;
    publisher: string;
    published_at: string;
    url: string;
    summary: string;
}

interface NewsFeedProps {
    newsItems: NewsItem[];
    onBack: () => void;
    isPrivacyMode: boolean;
}

const NewsFeed: React.FC<NewsFeedProps> = ({ newsItems, onBack }) => {
    return (
        <div className="min-h-screen bg-[#F8F9FA] text-[#1D1D1F] p-4 sm:p-8 font-sans transition-colors duration-300">
            <div className="max-w-4xl mx-auto">
                <header className="flex items-center justify-between mb-8 sm:mb-12">
                    <button
                        onClick={onBack}
                        className="flex items-center gap-2 text-sm font-medium text-[#1D1D1F] hover:text-[#0066CC] transition-colors"
                    >
                        <ArrowLeft size={16} /> Asset Dashboard
                    </button>
                    <div className="flex items-center gap-2 text-[#00D084] text-xs font-semibold tracking-wider uppercase">
                        <span className="w-2 h-2 rounded-full bg-[#00D084] animate-pulse" />
                        Live Feed
                    </div>
                </header>

                <section className="mb-12">
                    <div className="flex items-center gap-3 mb-4 text-[#86868B] text-xs font-semibold tracking-widest uppercase">
                        <Newspaper size={14} />
                        <span>Enterprise News Intelligence</span>
                    </div>
                    <h1 className="text-4xl sm:text-5xl font-serif text-[#1D1D1F] tracking-tight leading-tight mb-4">
                        Global Market Pulse
                    </h1>
                    <p className="text-lg text-[#86868B] max-w-2xl leading-relaxed">
                        Real-time macroeconomic developments and market-moving events shaping the global financial landscape.
                    </p>
                </section>

                <div className="space-y-6">
                    {newsItems.length > 0 ? (
                        newsItems.map((item, index) => (
                            <motion.a
                                href={item.url || '#'}
                                target="_blank"
                                rel="noopener noreferrer"
                                key={index}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.4, delay: index * 0.05 }}
                                className="block group"
                            >
                                <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm hover:shadow-md transition-all duration-300 border border-[#E5E5EA]">
                                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-3">
                                        <h2 className="text-xl sm:text-2xl font-serif font-medium text-[#1D1D1F] group-hover:text-[#0066CC] transition-colors leading-snug">
                                            {item.title}
                                        </h2>
                                        <ExternalLink size={18} className="text-[#86868B] group-hover:text-[#0066CC] opacity-0 group-hover:opacity-100 transition-all flex-shrink-0 mt-1" />
                                    </div>

                                    <p className="text-[#515154] leading-relaxed mb-6 line-clamp-2 sm:line-clamp-3">
                                        {item.summary || "No summary available for this headline."}
                                    </p>

                                    <div className="flex items-center gap-4 text-xs font-medium text-[#86868B]">
                                        <span className="flex items-center gap-1.5 uppercase tracking-wider">
                                            {item.publisher}
                                        </span>
                                        <span className="w-1 h-1 rounded-full bg-[#D1D1D6]" />
                                        <span className="flex items-center gap-1.5">
                                            <Calendar size={12} />
                                            {item.published_at.replace(' UTC', '')}
                                        </span>
                                    </div>
                                </div>
                            </motion.a>
                        ))
                    ) : (
                        <div className="bg-white rounded-2xl p-12 text-center border border-[#E5E5EA] shadow-sm">
                            <Newspaper size={48} className="mx-auto text-[#D1D1D6] mb-4" />
                            <h3 className="text-xl font-serif text-[#1D1D1F] mb-2">No News Available</h3>
                            <p className="text-[#86868B]">Market news feed is currently empty. Please check back later or run the data synchronization script.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default NewsFeed;
