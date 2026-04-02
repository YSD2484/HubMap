import type { TopographyData } from '../types';
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ZAxis } from 'recharts';

export const TopographyMap = ({ data, activeFounderId }: { data: TopographyData | null, activeFounderId: string | null }) => {
  if (!data) return <div className="h-80 border border-quant-border rounded-xl bg-quant-surface animate-pulse"></div>;

  return (
    <div className="h-80 w-full p-6 border border-quant-border rounded-xl bg-quant-surface flex flex-col">
      <h3 className="text-xs uppercase text-[#888] font-mono mb-4">Ecosystem Topography (Start Cap vs Connect)</h3>
      <div className="flex-1 w-full relative">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 20 }}>
            <XAxis 
              type="number" 
              dataKey="x" 
              name="PageRank" 
              scale="log" 
              domain={['auto', 'auto']}
              tick={{ fontSize: 10, fill: '#666' }}
              stroke="#333"
              tickFormatter={(v) => v.toExponential()}
            />
            <YAxis 
              type="number" 
              dataKey="y" 
              name="Capital" 
              scale="log" 
              domain={[1000, 'auto']}
              tick={{ fontSize: 10, fill: '#666' }}
              stroke="#333"
              tickFormatter={(v) => `$${(v/1e6).toFixed(0)}M`}
            />
            <ZAxis dataKey="z" range={[15, 60]} />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              contentStyle={{ backgroundColor: '#111', borderColor: '#333', fontSize: '11px', fontFamily: 'monospace' }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(value: any, name: any) => {
                if (name === 'Capital') return [`$${value.toLocaleString()}`, name];
                if (name === 'PageRank') return [value.toExponential(4), name];
                return [value, name];
              }}
            />
            <Scatter name="Ecosystem" data={data.points} fill="#333333" opacity={0.4}>
              {data.points.map((entry, index) => {
                const isActive = entry.id === activeFounderId;
                return (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={isActive ? '#00ffcc' : '#333333'} 
                    style={isActive ? { filter: 'drop-shadow(0px 0px 5px #00ffcc)', zIndex: 100 } : {}}
                  />
                )
              })}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
