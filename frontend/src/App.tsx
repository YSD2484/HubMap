import { useState, useEffect, useCallback } from 'react';
import { Search, Calendar, RefreshCw, BarChart2 } from 'lucide-react';
import clsx from 'clsx';
import type { FounderSearch, PredictionData, GraphData, TopographyData } from './types';
import { searchFounders, getPrediction, getEgoGraph, getTopography } from './api';
import { AlphaScorecard } from './components/AlphaScorecard';
import { EgoGraph } from './components/EgoGraph';
import { ShapWaterfall } from './components/ShapWaterfall';
import { TopographyMap } from './components/TopographyMap';
import { AdminConsole } from './components/AdminConsole';
import { Leaderboard } from './components/Leaderboard';

function App() {
  const [tAnchor, setTAnchor] = useState('2024-01-01');
  const [activeTab, setActiveTab] = useState<'dashboard' | 'admin'>('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<FounderSearch[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [activeFounder, setActiveFounder] = useState<FounderSearch | null>(null);

  const [topography, setTopography] = useState<TopographyData | null>(null);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [graph, setGraph] = useState<GraphData | null>(null);
  
  const [playbackActive, setPlaybackActive] = useState(false);

  // Load topography when anchor changes
  useEffect(() => {
    getTopography(tAnchor).then(data => {
      setTopography(data);
    }).catch(err => {
      console.error(err);
    });
  }, [tAnchor]);

  // Handle Search Input
  useEffect(() => {
    if (searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }
    const delay = setTimeout(() => {
      setIsSearching(true);
      searchFounders(searchQuery, tAnchor).then(data => {
        setSearchResults(data.results);
        setIsSearching(false);
      }).catch(() => setIsSearching(false));
    }, 300);
    return () => clearTimeout(delay);
  }, [searchQuery, tAnchor]);

  // Handle Founder Selection
  const handleSelectFounder = useCallback((founder: FounderSearch) => {
    setActiveFounder(founder);
    setSearchQuery('');
    setSearchResults([]);
    setPrediction(null);
    setGraph(null);

    Promise.all([
      getPrediction(founder.id, tAnchor).then(setPrediction),
      getEgoGraph(founder.id, tAnchor).then(setGraph)
    ]);
  }, [tAnchor]);

  const availableDates = ['2010-01-01', '2013-01-01', '2016-01-01', '2019-01-01', '2022-01-01', '2024-01-01'];

  // Demo playback animation
  useEffect(() => {
    if (!playbackActive) return;
    let idx = 0;
    const interval = setInterval(() => {
      setTAnchor(availableDates[idx]);
      idx++;
      if (idx >= availableDates.length) {
        clearInterval(interval);
        setPlaybackActive(false);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [playbackActive]);

  return (
    <div className="min-h-screen flex flex-col font-sans">
      {/* Header Pipeline Control */}
      <header className="h-16 border-b border-quant-border bg-[#0d0d0d] flex items-center justify-between px-6 z-50 shadow-md">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-quant-accent font-mono font-bold tracking-tight text-lg drop-shadow-[0_0_8px_rgba(0,255,204,0.4)]">
            <BarChart2 />
            <span>VELA</span>
          </div>
        </div>

        <div className="flex-1 max-w-xl mx-8 relative">
          <div className="relative flex items-center w-full">
            <Search className="absolute left-3 text-[#666]" size={18} />
            <input 
              type="text" 
              placeholder="Search startup ecosystem..." 
              className="w-full bg-[#161616] border border-quant-border rounded-full py-2 pl-10 pr-4 text-sm font-mono focus:outline-none focus:border-quant-accent transition-colors text-quant-fg"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {isSearching && <RefreshCw className="absolute right-3 animate-spin text-quant-accent" size={16} />}
          </div>
          
          {searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-[#1a1a1a] border border-quant-border rounded-lg shadow-2xl overflow-hidden z-50">
              {searchResults.map(res => (
                <div 
                  key={res.id} 
                  className="px-4 py-3 hover:bg-[#252525] cursor-pointer font-mono text-sm border-b border-[#222] last:border-0"
                  onClick={() => handleSelectFounder(res)}
                >
                  {res.name}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-4 border border-[#333] bg-[#111] rounded-full px-4 py-1.5 shadow-inner hidden md:flex">
          {/* New Tab Toggle */}
          <div className="flex bg-[#222] rounded-full p-0.5 mr-2">
            <button 
              className={clsx("px-3 py-1 rounded-full text-xs font-mono uppercase transition-colors", activeTab === 'dashboard' ? "bg-[#444] text-white" : "text-[#888] hover:text-white")}
              onClick={() => setActiveTab('dashboard')}
            >
              Dashboard
            </button>
            <button 
              className={clsx("px-3 py-1 rounded-full text-xs font-mono uppercase transition-colors", activeTab === 'admin' ? "bg-[#444] text-white" : "text-[#888] hover:text-white")}
              onClick={() => setActiveTab('admin')}
            >
              Admin
            </button>
          </div>
          
          <Calendar className="text-[#666]" size={16} />
          <span className="text-xs text-[#888] font-mono mr-2">t_anchor</span>
          <input 
            type="range" 
            min="0" max={availableDates.length - 1} step="1"
            className="w-32 accent-quant-accent"
            value={availableDates.indexOf(tAnchor) === -1 ? availableDates.length - 1 : availableDates.indexOf(tAnchor)}
            onChange={(e) => setTAnchor(availableDates[parseInt(e.target.value)])}
          />
          <span className="text-quant-accent font-mono text-sm w-12 text-center">{tAnchor.substring(0,4)}</span>
          <button 
            className={clsx(
              "ml-2 text-[10px] px-2 py-1 rounded font-mono uppercase bg-[#222] border border-[#333] hover:text-white transition-colors",
              playbackActive && "text-quant-red border-quant-red"
            )}
            onClick={() => setPlaybackActive(!playbackActive)}
          >
            {playbackActive ? 'STOP' : 'PLAY'}
          </button>
        </div>
      </header>

      {/* Main Dashboard Space */}
      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 bg-gradient-to-br from-[#0a0a0a] via-[#101216] to-[#04090c] bg-[length:200%_200%] animate-gradient-slow relative">
        {/* Glow orb overlay */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-quant-accent/5 rounded-full blur-[120px] pointer-events-none"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-quant-blue/5 rounded-full blur-[120px] pointer-events-none"></div>
        
        {activeTab === 'admin' ? (
          <AdminConsole tAnchor={tAnchor} />
        ) : (
          <>
            {/* Left Column: Network & Features */}
            <div className="lg:col-span-8 flex flex-col gap-6 z-10">
          <div className="flex-1 flex flex-col relative w-full rounded-xl overflow-hidden shadow-2xl border border-quant-border min-h-[400px] hover:border-quant-accent/50 transition-all duration-500 hover:shadow-[0_0_30px_rgba(0,255,204,0.1)] group bg-black/40 backdrop-blur-sm">
            <div className="absolute top-0 left-0 w-full h-12 bg-gradient-to-b from-[#111] to-transparent z-10 p-4 font-mono text-xs uppercase tracking-widest text-[#888] group-hover:text-quant-accent transition-colors">
              Chronological Ego-Graph
            </div>
            {activeFounder ? <EgoGraph data={graph} /> : (
              <div className="flex-1 bg-[#0d0d0d] flex items-center justify-center text-[#444] font-mono">
                SELECT A TARGET ENTITY TO RENDER GRAPH
              </div>
            )}
          </div>

          <div className="h-[350px] w-full rounded-xl overflow-hidden shadow-2xl border border-quant-border hover:border-quant-accent/50 transition-all duration-500 hover:shadow-[0_0_30px_rgba(0,255,204,0.1)] bg-black/40 backdrop-blur-sm">
            {activeFounder ? <ShapWaterfall data={prediction} /> : (
              <div className="h-full rounded-xl bg-quant-surface/50 animate-pulse"></div>
            )}
          </div>
        </div>

        {/* Right Column: Scoring & Topo */}
        <div className="lg:col-span-4 flex flex-col gap-6 h-full overflow-hidden">
          {activeFounder ? (
            <div className="shrink-0 rounded-xl overflow-hidden shadow-2xl border border-quant-border hover:border-quant-accent/50 transition-all duration-500 hover:shadow-[0_0_30px_rgba(0,255,204,0.1)] bg-black/40 backdrop-blur-sm relative group">
              <AlphaScorecard data={prediction} />
            </div>
          ) : (
            <div className="shrink-0 p-6 border border-quant-border rounded-xl bg-black/40 backdrop-blur-sm h-64 flex flex-col justify-end relative shadow-2xl hover:border-quant-accent/30 transition-all duration-500">
               <div className="absolute top-0 right-0 w-32 h-32 bg-[#222] opacity-20 blur-3xl rounded-full translate-x-10 -translate-y-10 group-hover:bg-quant-accent/20 transition-colors duration-1000"></div>
               <div className="text-xs font-mono uppercase text-[#666] mb-2">Alpha Predictive Engine</div>
               <div className="text-4xl font-mono text-[#444] mb-4">--.-%</div>
               <div className="h-8 w-24 bg-[#222] animate-pulse rounded"></div>
            </div>
          )}

          <div className="flex-1 min-h-[400px] overflow-hidden">
            <Leaderboard 
              tAnchor={tAnchor} 
              onSelectFounder={handleSelectFounder} 
              activeFounderId={activeFounder?.id || null} 
            />
          </div>

          <div className="shrink-0 h-[300px] rounded-xl overflow-hidden shadow-2xl border border-quant-border hover:border-quant-accent/50 transition-all duration-500 hover:shadow-[0_0_30px_rgba(0,255,204,0.1)] bg-black/40 backdrop-blur-sm relative">
            <TopographyMap data={topography} activeFounderId={activeFounder?.id || null} />
          </div>
        </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
