import { useMemo } from 'react';
import { ReactFlow, Controls, Background } from '@xyflow/react';
import type { Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { GraphData } from '../types';

export const EgoGraph = ({ data }: { data: GraphData | null }) => {
  const { animatedNodes, animatedEdges } = useMemo(() => {
    if (!data) return { animatedNodes: [], animatedEdges: [] };
    
    const egoNode = data.nodes.find(n => n.group === 'ego');
    const neighbors = data.nodes.filter(n => n.group !== 'ego');
    
    const radius = 250;
    
    const newNodes: Node[] = [];
    if (egoNode) {
      newNodes.push({
        id: egoNode.id,
        position: { x: 300, y: 250 },
        data: { label: egoNode.label },
        style: {
          background: '#00ffcc',
          color: '#000',
          border: 'none',
          boxShadow: '0 0 15px rgba(0,255,204,0.5)',
          borderRadius: '50%',
          width: 80,
          height: 80,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 'bold',
          textAlign: 'center',
          fontSize: '10px'
        }
      });
    }

    neighbors.forEach((n, i) => {
      const angle = (i / neighbors.length) * 2 * Math.PI;
      const x = 300 + radius * Math.cos(angle);
      const y = 250 + radius * Math.sin(angle);
      
      newNodes.push({
        id: n.id,
        position: { x, y },
        data: { label: n.label },
        style: {
          background: '#161616',
          color: '#dedede',
          border: '1px solid #333',
          borderRadius: '4px',
          padding: '8px',
          fontSize: '10px'
        }
      });
    });

    const newEdges: Edge[] = data.edges.map((e, i) => {
      const isSchool = e.type === 'school';
      return {
        id: `e-${e.source}-${e.target}-${i}`,
        source: e.source,
        target: e.target,
        animated: true,
        style: {
          strokeWidth: Math.max(1, Math.min(6, Math.log1p(e.weight) / 2)),
          stroke: isSchool ? '#0088ff' : '#ff3366',
          opacity: 0.6
        },
        label: e.hub,
        labelStyle: { fill: '#fff', fontSize: 10 },
        labelBgStyle: { fill: '#111', stroke: '#333' }
      };
    });

    return { animatedNodes: newNodes, animatedEdges: newEdges };
  }, [data]);

  if (!data) return <div className="h-96 w-full border border-quant-border rounded-xl bg-quant-surface animate-pulse"></div>;

  return (
    <div className="h-96 w-full border border-quant-border rounded-xl bg-[#080808] relative overflow-hidden flex shadow-inner">
      <div className="absolute top-4 left-4 z-10 font-mono text-xs z-50 bg-black/50 p-2 rounded border border-[#333]">
        <span className="text-quant-blue/80">■ School Hubs</span><br/>
        <span className="text-quant-red/80">■ Corporate Hubs</span><br/>
        <span className="text-[#888]">Thickness = Weight</span>
        {data?.capped && (
          <div className="mt-2 text-quant-orange text-[10px] border-t border-[#333] pt-1">
            ⚠️ Graph capped to top 40 connections
          </div>
        )}
      </div>
      <ReactFlow
        nodes={animatedNodes}
        edges={animatedEdges}
        fitView
        className="w-full h-full"
      >
        <Background gap={20} size={1} color="#222" />
        <Controls showInteractive={false} className="bg-quant-surface fill-quant-fg border-[#333]"/>
      </ReactFlow>
    </div>
  );
};
