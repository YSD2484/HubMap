import type { PredictionData } from '../types';
import { TrendingUp, Users, DollarSign, Activity } from 'lucide-react';
import clsx from 'clsx';

export const AlphaScorecard = ({ data }: { data: PredictionData | null }) => {
  if (!data) return <div className="p-6 border border-quant-border rounded-xl bg-quant-surface animate-pulse h-64"></div>;

  const formatCurrency = (val: number) => {
    if (val >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
    if (val >= 1e6) return `$${(val / 1e6).toFixed(1)}M`;
    return `$${val.toLocaleString()}`;
  };

  const isHighAlpha = data.prediction_score_percentile >= 85;

  return (
    <div className="p-6 border border-quant-border rounded-xl bg-quant-surface flex flex-col justify-between shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-quant-accent opacity-5 blur-3xl rounded-full translate-x-10 -translate-y-10"></div>
      
      <div className="mb-4">
        <h2 className="text-sm uppercase tracking-widest text-[#888]">Outlier Success Propensity</h2>
        <div className="flex items-end gap-3 mt-2">
          <span className={clsx(
            "text-5xl font-mono font-bold tracking-tighter", 
            isHighAlpha ? "text-quant-accent drop-shadow-[0_0_10px_rgba(0,255,204,0.3)]" : "text-quant-fg"
          )}>
            {data.prediction_score_percentile.toFixed(1)}<span className="text-2xl">%</span>
          </span>
          <span className="text-xs mb-2 px-2 py-1 rounded bg-quant-bg text-[#aaa] border border-quant-border font-mono uppercase">
            Top {Math.max(1, Math.round(100 - data.prediction_score_percentile))} Pct
          </span>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-xs text-[#666] uppercase mb-1 font-mono">Relative Cohort Placement</h3>
        <p className="font-mono text-sm text-quant-blue bg-quant-bg border border-quant-border px-3 py-2 rounded inline-block">
          {data.cohort}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 border-t border-quant-border pt-4">
        <div>
          <div className="text-xs text-[#666] uppercase flex items-center gap-1 mb-1"><DollarSign size={12}/> Prior Capital</div>
          <div className="font-mono text-lg">{formatCurrency(data.stats.prior_raised)}</div>
        </div>
        <div>
          <div className="text-xs text-[#666] uppercase flex items-center gap-1 mb-1"><Activity size={12}/> Prior Roles</div>
          <div className="font-mono text-lg">{data.stats.prior_roles}</div>
        </div>
        <div>
          <div className="text-xs text-[#666] uppercase flex items-center gap-1 mb-1"><TrendingUp size={12}/> PageRank</div>
          <div className="font-mono text-lg truncate" title={data.stats.pagerank.toString()}>{data.stats.pagerank.toExponential(2)}</div>
        </div>
        <div>
          <div className="text-xs text-[#666] uppercase flex items-center gap-1 mb-1"><Users size={12}/> Centrality</div>
          <div className="font-mono text-lg truncate">{data.stats.degree_centrality.toFixed(4)}</div>
        </div>
      </div>
    </div>
  );
};
