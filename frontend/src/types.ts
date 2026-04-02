export interface FounderSearch {
  id: string;
  name: string;
}

export interface PredictionData {
  founder_id: string;
  name: string;
  prediction_score_percentile: number;
  cohort: string;
  stats: {
    prior_raised: number;
    prior_roles: number;
    pagerank: number;
    degree_centrality: number;
  };
  shap_base_value: number;
  shap_waterfall: { feature: string; value: number; shap: number; type: string }[];
}

export interface GraphData {
  nodes: { id: string; label: string; group: string }[];
  edges: { source: string; target: string; weight: number; hub: string; type: string }[];
  capped?: boolean;
}

export interface TopographyData {
  points: {
    id: string;
    x: number;
    y: number;
    z: number;
    cohort: string;
  }[];
}

export interface MafiaLift {
  id: string;
  count: number;
  success_rate: number;
  multiplier: number;
}

export interface FeatureLift {
  feature: string;
  threshold: number;
  success_rate: number;
  multiplier: number;
}

export interface AdminMetricsData {
  global_rate: number;
  mafia_lifts: MafiaLift[];
  feature_lifts: FeatureLift[];
}

export interface LeaderboardEntry {
  rank: number;
  id: string;
  name: string;
  value: number;
}

export interface LeaderboardData {
  results: LeaderboardEntry[];
}
