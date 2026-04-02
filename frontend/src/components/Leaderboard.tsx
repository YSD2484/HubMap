import React, { useEffect, useState } from 'react';
import { getLeaderboard } from '../api';
import type { LeaderboardData, FounderSearch } from '../types';
import { Trophy, TrendingUp, DollarSign, Share2, Award, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

interface LeaderboardProps {
  tAnchor: string;
  onSelectFounder: (founder: FounderSearch) => void;
  activeFounderId: string | null;
}

type MetricType = 'score' | 'pagerank' | 'capital' | 'degree' | 'neighborhood_success';

interface MetricOption {
  id: MetricType;
  label: string;
  icon: React.ReactNode;
  unit?: string;
  isCurrency?: boolean;
}

const METRICS: MetricOption[] = [
  { id: 'score', label: 'Success Prob', icon: <Award size={14} />, unit: '%' },
  { id: 'pagerank', label: 'Network Power', icon: <Share2 size={14} /> },
  { id: 'capital', label: 'Capital Raised', icon: <DollarSign size={14} />, isCurrency: true },
  { id: 'degree', label: 'Connections', icon: <TrendingUp size={14} /> },
  { id: 'neighborhood_success', label: 'VC Alpha', icon: <Trophy size={14} />, unit: '%' },
];

export const Leaderboard: React.FC<LeaderboardProps> = ({ tAnchor, onSelectFounder, activeFounderId }) => {
  const [data, setData] = useState<LeaderboardData | null>(null);
  const [metric, setMetric] = useState<MetricType>('score');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getLeaderboard(tAnchor, metric, 20)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [tAnchor, metric]);

  const formatValue = (val: number, option: MetricOption) => {
    if (option.isCurrency) {
      if (val >= 1000000000) return `$${(val / 1000000000).toFixed(1)}B`;
      if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`;
      return `$${(val / 1000).toFixed(0)}K`;
    }
    if (option.unit === '%') {
        const displayVal = metric === 'score' || metric === 'neighborhood_success' ? val * 100 : val;
        return `${displayVal.toFixed(1)}%`;
    }
    if (val < 1 && val > 0) return val.toFixed(4);
    return val.toLocaleString();
  };

  const activeMetricOption = METRICS.find(m => m.id === metric)!;

  return (
    <div className="flex flex-col h-full bg-black/40 backdrop-blur-sm border border-quant-border rounded-xl overflow-hidden shadow-2xl relative group">
      <div className="absolute top-0 right-0 w-32 h-32 bg-quant-accent/5 blur-3xl rounded-full -translate-y-16 translate-x-16 group-hover:bg-quant-accent/10 transition-colors duration-700"></div>
      
      <div className="p-4 border-b border-quant-border bg-[#111]/80 flex flex-col gap-3">
        <div className="flex items-center gap-2 text-quant-accent font-mono text-xs uppercase tracking-widest">
          <Trophy size={14} className="drop-shadow-[0_0_5px_rgba(0,255,204,0.5)]" />
          <span>Ecosystem Leaderboard</span>
        </div>
        
        <div className="flex gap-1 overflow-x-auto pb-1 custom-scrollbar no-scrollbar">
          {METRICS.map((m) => (
            <button
              key={m.id}
              onClick={() => setMetric(m.id)}
              className={clsx(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-mono uppercase whitespace-nowrap transition-all border",
                metric === m.id 
                  ? "bg-quant-accent/10 border-quant-accent text-quant-accent shadow-[0_0_10px_rgba(0,255,204,0.2)]" 
                  : "bg-[#1a1a1a] border-[#333] text-[#666] hover:border-[#444] hover:text-[#aaa]"
              )}
            >
              {m.icon}
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar bg-[#080808]/40">
        {loading ? (
          <div className="h-full flex items-center justify-center p-12">
            <div className="animate-pulse flex flex-col items-center gap-2">
              <div className="w-12 h-1 bg-quant-accent/20 rounded-full overflow-hidden">
                <div className="w-1/2 h-full bg-quant-accent animate-loading-bar"></div>
              </div>
              <span className="font-mono text-[10px] text-[#444] uppercase tracking-tighter">Ranking Entities...</span>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-[#1a1a1a]">
            {data?.results.map((entry) => (
              <div
                key={entry.id}
                onClick={() => onSelectFounder({ id: entry.id, name: entry.name })}
                className={clsx(
                  "flex items-center justify-between p-3 cursor-pointer transition-all hover:bg-white/5 group/row",
                  activeFounderId === entry.id ? "bg-quant-accent/5 border-l-2 border-l-quant-accent" : "border-l-2 border-l-transparent"
                )}
              >
                <div className="flex items-center gap-3 overflow-hidden">
                  <span className={clsx(
                    "font-mono text-xs w-6 text-center",
                    entry.rank <= 3 ? "text-quant-accent font-bold" : "text-[#444]"
                  )}>
                    {entry.rank.toString().padStart(2, '0')}
                  </span>
                  <div className="flex flex-col min-w-0">
                    <span className={clsx(
                      "text-sm truncate transition-colors",
                      activeFounderId === entry.id ? "text-white" : "text-[#ccc] group-hover/row:text-white"
                    )}>
                      {entry.name}
                    </span>
                    <span className="text-[10px] text-[#555] font-mono uppercase truncate">
                        ID: {entry.id.substring(0, 8)}...
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 pl-4 shrink-0">
                  <div className="flex flex-col items-end">
                    <span className={clsx(
                      "font-mono text-xs font-bold",
                      activeFounderId === entry.id ? "text-quant-accent" : "text-[#888] group-hover/row:text-quant-accent"
                    )}>
                      {formatValue(entry.value, activeMetricOption)}
                    </span>
                    <span className="text-[8px] text-[#444] uppercase font-mono tracking-tighter">
                      {activeMetricOption.label}
                    </span>
                  </div>
                  <ChevronRight size={14} className={clsx(
                    "transition-all duration-300 transform",
                    activeFounderId === entry.id ? "text-quant-accent translate-x-0 opacity-100" : "text-[#333] -translate-x-2 opacity-0 group-hover/row:translate-x-0 group-hover/row:opacity-100"
                  )} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="p-2 border-t border-quant-border bg-[#0d0d0d]/80 text-center">
        <span className="text-[8px] font-mono text-[#444] uppercase tracking-widest">
            Showing top {data?.results.length || 0} entities by {activeMetricOption.label}
        </span>
      </div>
    </div>
  );
};
