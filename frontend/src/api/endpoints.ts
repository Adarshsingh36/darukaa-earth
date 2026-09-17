import { api } from './client';
import type {
  AuthResponse,
  DashboardSummary,
  GeoJSONPolygon,
  Metric,
  Project,
  Site,
  User,
} from './types';

export const authApi = {
  register: (name: string, email: string, password: string) =>
    api.post<AuthResponse>('/api/auth/register', { name, email, password }).then((r) => r.data),
  login: (email: string, password: string) =>
    api.post<AuthResponse>('/api/auth/login', { email, password }).then((r) => r.data),
  me: () => api.get<User>('/api/auth/me').then((r) => r.data),
};

export const projectsApi = {
  list: () => api.get<Project[]>('/api/projects').then((r) => r.data),
  get: (id: string) => api.get<Project>(`/api/projects/${id}`).then((r) => r.data),
  create: (payload: {
    name: string;
    description?: string;
    location?: string;
    start_date?: string;
  }) => api.post<Project>('/api/projects', payload).then((r) => r.data),
  remove: (id: string) => api.delete(`/api/projects/${id}`),
};

export const sitesApi = {
  listForProject: (projectId: string) =>
    api.get<Site[]>(`/api/projects/${projectId}/sites`).then((r) => r.data),
  create: (
    projectId: string,
    payload: { name: string; description?: string; geometry: GeoJSONPolygon },
  ) => api.post<Site>(`/api/projects/${projectId}/sites`, payload).then((r) => r.data),
  get: (siteId: string) => api.get<Site>(`/api/sites/${siteId}`).then((r) => r.data),
  remove: (siteId: string) => api.delete(`/api/sites/${siteId}`),
};

export const metricsApi = {
  list: (siteId: string) => api.get<Metric[]>(`/api/sites/${siteId}/metrics`).then((r) => r.data),
  create: (
    siteId: string,
    payload: {
      recorded_at: string;
      carbon_tonnes: number;
      biodiversity_index: number;
      tree_cover_percentage: number;
      species_count: number;
    },
  ) => api.post<Metric>(`/api/sites/${siteId}/metrics`, payload).then((r) => r.data),
};

export const dashboardApi = {
  summary: () => api.get<DashboardSummary>('/api/dashboard/summary').then((r) => r.data),
};
