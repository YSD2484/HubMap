const API_URL = 'http://localhost:8000/api';

export async function searchFounders(q: string, t_anchor: string) {
  const res = await fetch(`${API_URL}/search?q=${encodeURIComponent(q)}&t_anchor=${t_anchor}`);
  if (!res.ok) throw new Error("Search failed");
  return res.json();
}

export async function getPrediction(founderId: string, tAnchor: string) {
  const res = await fetch(`${API_URL}/predict?founder_id=${founderId}&t_anchor=${tAnchor}`);
  if (!res.ok) throw new Error("Prediction failed");
  return res.json();
}

export async function getEgoGraph(founderId: string, tAnchor: string) {
  const res = await fetch(`${API_URL}/graph?founder_id=${founderId}&t_anchor=${tAnchor}`);
  if (!res.ok) throw new Error("Graph failed");
  return res.json();
}

export async function getTopography(tAnchor: string) {
  const res = await fetch(`${API_URL}/topography?t_anchor=${tAnchor}`);
  if (!res.ok) throw new Error("Topography failed");
  return res.json();
}

export async function getAdminMetrics(tAnchor: string) {
  const res = await fetch(`${API_URL}/admin/metrics?t_anchor=${tAnchor}`);
  if (!res.ok) throw new Error("Admin metrics failed");
  return res.json();
}

export async function getLeaderboard(tAnchor: string, metric: string, limit: number = 20) {
  const res = await fetch(`${API_URL}/leaderboard?t_anchor=${tAnchor}&metric=${metric}&limit=${limit}`);
  if (!res.ok) throw new Error("Leaderboard failed");
  return res.json();
}
