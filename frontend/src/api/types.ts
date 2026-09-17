export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  location: string | null;
  start_date: string | null;
  created_at: string;
  created_by: string;
  site_count: number;
}

export interface GeoJSONPolygon {
  type: 'Polygon';
  coordinates: number[][][];
}

export interface Site {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  geometry: GeoJSONPolygon;
  area_hectares: number;
  created_at: string;
}

export interface Metric {
  id: string;
  site_id: string;
  recorded_at: string;
  carbon_tonnes: number;
  biodiversity_index: number;
  tree_cover_percentage: number;
  species_count: number;
  created_at: string;
}

export interface DashboardSummary {
  total_projects: number;
  total_sites: number;
  total_area_hectares: number;
  total_carbon_tonnes: number;
  average_biodiversity_index: number;
}
