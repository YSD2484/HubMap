import React, { useEffect, useState } from 'react';
import { getAdminMetrics } from '../api';
import type { AdminMetricsData } from '../types';
import { ShieldAlert, TrendingUp, Users } from 'lucide-react';
import clsx from 'clsx';

interface AdminConsoleProps {
  tAnchor: string;
}

export const AdminConsole: React.FC<AdminConsoleProps> = ({ tAnchor }) => {
  const [data, setData] = useState<AdminMetricsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getAdminMetrics(tAnchor)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [tAnchor]);

  if (loading || !data) {
    return (
      <div className="w-full h-full flex items-center justify-center col-span-12">
        <div className="animate-pulse text-quant-accent font-mono">LOADING METRICS ENGINE...</div>
      </div>
    );
  }

  return (
    <div className="col-span-12 flex flex-col gap-8 text-quant-fg z-10 w-full mb-10">
      
      {/* Global Stats Head */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 border border-quant-border rounded-xl bg-black/40 backdrop-blur-sm shadow-2xl">
          <div className="flex items-center gap-3 text-quant-accent mb-4">
            <ShieldAlert size={20} />
            <span className="font-mono text-sm uppercase tracking-wider">Global Base Rate</span>
          </div>
          <div className="text-4xl font-mono text-white">
            {(data.global_rate * 100).toFixed(2)}%
          </div>
          <div className="text-xs text-[#666] mt-2 font-mono">Baseline Outlier Probability at {tAnchor}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Feature Multipliers */}
        <div className="flex flex-col gap-4 p-6 border border-quant-border rounded-xl bg-black/40 backdrop-blur-sm shadow-2xl min-h-[500px]">
           <div className="flex items-center justify-between mb-4 border-b border-[#222] pb-4">
            <div className="flex items-center gap-3 text-quant-blue">
              <TrendingUp size={20} />
              <span className="font-mono text-sm uppercase tracking-wider">Feature Alpha Signal Lift</span>
            </div>
          </div>
          
          <div className="space-y-4">
            {data.feature_lifts.map((f, i) => (
              <div key={i} className="flex flex-col bg-[#111] border border-[#222] p-4 rounded-lg relative overflow-hidden group hover:border-[#333] transition-colors">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-quant-blue/50 group-hover:bg-quant-blue transition-colors"></div>
                <div className="flex justify-between items-start z-10 mb-2">
                  <span className="font-mono text-sm text-[#ddd]">{f.feature}</span>
                  <div className="px-3 py-1 bg-quant-blue/10 border border-quant-blue/30 rounded text-quant-blue font-mono font-bold">
                    {f.multiplier.toFixed(2)}x
                  </div>
                </div>
                <div className="flex justify-between text-xs font-mono text-[#666] z-10">
                  <span>Threshold: {f.threshold > 1000 ? `$${(f.threshold/1000000).toFixed(1)}M` : f.threshold.toFixed(2)}</span>
                  <span>Success Prob: {(f.success_rate * 100).toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Mafia Multipliers */}
        <div className="flex flex-col gap-4 p-6 border border-quant-border rounded-xl bg-black/40 backdrop-blur-sm shadow-2xl min-h-[500px]">
          <div className="flex items-center justify-between mb-4 border-b border-[#222] pb-4">
            <div className="flex items-center gap-3 text-quant-red">
              <Users size={20} />
              <span className="font-mono text-sm uppercase tracking-wider">Top Mafia Hub Signals</span>
            </div>
            <span className="text-xs text-[#666] font-mono">Count &ge; 5</span>
          </div>

          <div className="overflow-y-auto max-h-[600px] pr-2 custom-scrollbar">
            <div className="space-y-2">
              {data.mafia_lifts.slice(0, 15).map((m, i) => (
                <div key={i} className="flex justify-between items-center p-3 border border-[#222] bg-[#111] rounded hover:border-[#444] transition-colors">
                  <div className="flex flex-col gap-1">
                     <span className="font-mono text-sm text-[#eee]">{m.id.replace(/_/g, ' ')}</span>
                     <span className="text-xs text-[#555] font-mono">N={m.count} | {(m.success_rate * 100).toFixed(1)}% hit</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className={clsx(
                      "font-mono font-bold text-sm",
                      m.multiplier >= 3 ? "text-quant-red drop-shadow-[0_0_5px_rgba(255,51,102,0.5)]" : "text-quant-accent"
                    )}>
                      {m.multiplier.toFixed(2)}x
                    </span>
                    <span className="text-[10px] uppercase text-[#666]">Multiplier</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
