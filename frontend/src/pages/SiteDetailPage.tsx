import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  type ChartOptions,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { metricsApi, sitesApi } from '../api/endpoints';
import { getErrorMessage } from '../api/client';
import type { Metric, Site } from '../api/types';
import { SiteMap } from '../components/SiteMap';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const baseChartOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1c2420',
      borderColor: '#303b34',
      borderWidth: 1,
      titleColor: '#ede9e3',
      bodyColor: '#ede9e3',
      padding: 10,
    },
  },
  scales: {
    x: {
      grid: { color: '#242e28' },
      ticks: { color: '#a3ada4' },
    },
    y: {
      grid: { color: '#242e28' },
      ticks: { color: '#a3ada4' },
      beginAtZero: true,
    },
  },
};

export function SiteDetailPage() {
  const { siteId } = useParams<{ siteId: string }>();
  const [site, setSite] = useState<Site | null>(null);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!siteId) return;
    setLoading(true);
    setError(null);
    Promise.all([sitesApi.get(siteId), metricsApi.list(siteId)])
      .then(([siteRes, metricsRes]) => {
        setSite(siteRes);
        setMetrics(metricsRes);
      })
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [siteId]);

  if (loading) return <div className="page-loading">Loading site…</div>;
  if (error || !site) {
    return (
      <div className="page-error">
        <p className="error-text">{error || 'Site not found.'}</p>
        <Link to="/">← Back to dashboard</Link>
      </div>
    );
  }

  const latest = metrics[metrics.length - 1];
  const labels = metrics.map((m) =>
    new Date(m.recorded_at).toLocaleDateString(undefined, { month: 'short', year: 'numeric' }),
  );

  return (
    <div className="site-page">
      <div className="project-header">
        <div>
          <Link to={`/projects/${site.project_id}`} className="back-link">
            ← Back to project
          </Link>
          <h1>{site.name}</h1>
          {site.description && <p className="project-description">{site.description}</p>}
        </div>
      </div>

      <div className="stat-grid">
        <StatCard label="Area" value={`${site.area_hectares.toLocaleString()} ha`} />
        <StatCard
          label="Carbon stored"
          value={latest ? `${latest.carbon_tonnes.toLocaleString()} t` : '—'}
        />
        <StatCard
          label="Biodiversity index"
          value={latest ? `${latest.biodiversity_index}` : '—'}
        />
        <StatCard label="Tree cover" value={latest ? `${latest.tree_cover_percentage}%` : '—'} />
        <StatCard label="Species count" value={latest ? `${latest.species_count}` : '—'} />
      </div>

      <div className="site-body">
        <div className="site-map card">
          <SiteMap sites={[site]} selectedSiteId={site.id} height="320px" />
        </div>

        {metrics.length === 0 ? (
          <div className="card empty-state">
            <p>No analytics recorded yet for this site.</p>
          </div>
        ) : (
          <div className="charts-grid">
            <ChartCard title="Carbon stored over time (tonnes)">
              <Line
                data={{
                  labels,
                  datasets: [
                    {
                      label: 'Carbon (t)',
                      data: metrics.map((m) => m.carbon_tonnes),
                      borderColor: '#c97b4a',
                      backgroundColor: 'rgba(201, 123, 74, 0.15)',
                      tension: 0.3,
                      fill: true,
                    },
                  ],
                }}
                options={baseChartOptions}
              />
            </ChartCard>

            <ChartCard title="Biodiversity index over time">
              <Line
                data={{
                  labels,
                  datasets: [
                    {
                      label: 'Biodiversity index',
                      data: metrics.map((m) => m.biodiversity_index),
                      borderColor: '#7a9b76',
                      backgroundColor: 'rgba(122, 155, 118, 0.15)',
                      tension: 0.3,
                      fill: true,
                    },
                  ],
                }}
                options={baseChartOptions}
              />
            </ChartCard>

            <ChartCard title="Tree cover over time (%)">
              <Line
                data={{
                  labels,
                  datasets: [
                    {
                      label: 'Tree cover (%)',
                      data: metrics.map((m) => m.tree_cover_percentage),
                      borderColor: '#96b892',
                      backgroundColor: 'rgba(150, 184, 146, 0.15)',
                      tension: 0.3,
                      fill: true,
                    },
                  ],
                }}
                options={{
                  ...baseChartOptions,
                  scales: {
                    ...baseChartOptions.scales,
                    y: { ...baseChartOptions.scales?.y, max: 100 },
                  },
                }}
              />
            </ChartCard>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat-card card">
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card chart-card">
      <h3>{title}</h3>
      <div className="chart-wrap">{children}</div>
    </div>
  );
}
