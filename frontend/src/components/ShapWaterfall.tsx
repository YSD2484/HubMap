import { useMemo } from 'react';
import type { PredictionData } from '../types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid } from 'recharts';

export const ShapWaterfall = ({ data }: { data: PredictionData | null }) => {
  const processedData = useMemo(() => {
    if (!data) return [];
    return data.shap_waterfall.map(item => ({
      name: item.feature.replace('emb_', 'Embedding '),
      rawVal: item.value,
      shap: item.shap,
      type: item.type,
      impact: Math.abs(item.shap),
      positive: item.shap > 0
    }));
  }, [data]);

  if (!data) return <div className="h-80 border border-quant-border rounded-xl bg-quant-surface animate-pulse"></div>;

  return (
    <div className="h-80 w-full p-6 border border-quant-border rounded-xl bg-quant-surface relative flex flex-col">
      <h3 className="text-xs uppercase text-[#888] font-mono mb-4 flex justify-between">
        <span>XGBoost Feature Attributions (SHAP)</span>
        <span>Base Value: {data.shap_base_value.toFixed(2)}</span>
      </h3>
      
      <div className="flex-1 min-h-0 w-full relative -ml-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={processedData} layout="vertical" barSize={12} margin={{ left: 140, right: 20 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#222"/>
            <XAxis type="number" hide domain={['dataMin', 'dataMax']} />
            <YAxis 
              type="category" 
              dataKey="name" 
              width={130}
              tick={{ fontSize: 10, fill: '#888', fontFamily: 'monospace' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip 
              cursor={{ fill: '#333' }}
              contentStyle={{ backgroundColor: '#111', borderColor: '#333', fontSize: '12px', fontFamily: 'monospace' }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(_value: any, _name: any, props: any) => [
                `${props.payload.shap > 0 ? '+' : ''}${props.payload.shap.toFixed(4)}`, 
                `Impact (${props.payload.type})`
              ]}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              labelFormatter={(label: any) => `Feature: ${label}`}
            />
            <Bar dataKey="shap" radius={[0, 4, 4, 0]}>
              {processedData.map((entry, index) => (
                 <Cell key={`cell-${index}`} fill={entry.positive ? '#00ffcc' : '#ff3366'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="absolute top-4 right-6 flex gap-4 text-[10px] font-mono uppercase">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded bg-quant-accent"></div> Drives Success
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded bg-quant-red"></div> Drags Success
        </div>
      </div>
    </div>
  );
};
