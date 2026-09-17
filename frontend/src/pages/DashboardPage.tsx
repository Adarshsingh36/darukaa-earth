import { useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { dashboardApi, projectsApi, sitesApi } from '../api/endpoints';
import { getErrorMessage } from '../api/client';
import type { DashboardSummary, Project, Site } from '../api/types';
import { SiteMap } from '../components/SiteMap';

export function DashboardPage() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [allSites, setAllSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewProject, setShowNewProject] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, projectsRes] = await Promise.all([
        dashboardApi.summary(),
        projectsApi.list(),
      ]);
      setSummary(summaryRes);
      setProjects(projectsRes);

      const siteLists = await Promise.all(
        projectsRes.map((p) => sitesApi.listForProject(p.id).catch(() => [])),
      );
      setAllSites(siteLists.flat());
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return <div className="page-loading">Loading dashboard…</div>;
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <div>
          <h1>Dashboard</h1>
          <p className="dashboard-subtitle">
            An overview of your carbon and biodiversity monitoring projects.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowNewProject(true)}>
          + New project
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}

      {summary && (
        <div className="stat-grid">
          <StatCard label="Projects" value={summary.total_projects.toLocaleString()} />
          <StatCard label="Sites" value={summary.total_sites.toLocaleString()} />
          <StatCard
            label="Monitored area"
            value={`${summary.total_area_hectares.toLocaleString()} ha`}
          />
          <StatCard
            label="Carbon stored"
            value={`${summary.total_carbon_tonnes.toLocaleString()} t`}
          />
          <StatCard
            label="Avg. biodiversity index"
            value={summary.average_biodiversity_index.toLocaleString()}
          />
        </div>
      )}

      <div className="dashboard-body">
        <div className="dashboard-map card">
          <SiteMap sites={allSites} height="440px" />
        </div>

        <div className="dashboard-projects card">
          <h2>Projects</h2>
          {projects.length === 0 ? (
            <div className="empty-state">
              <p>No projects yet.</p>
              <button className="btn btn-primary" onClick={() => setShowNewProject(true)}>
                Create your first project
              </button>
            </div>
          ) : (
            <ul className="project-list">
              {projects.map((project) => (
                <li key={project.id}>
                  <Link to={`/projects/${project.id}`} className="project-list-item">
                    <div>
                      <span className="project-name">{project.name}</span>
                      <span className="project-meta">
                        {project.location || 'No location set'} · {project.site_count} site
                        {project.site_count === 1 ? '' : 's'}
                      </span>
                    </div>
                    <span className="project-arrow" aria-hidden="true">
                      →
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {showNewProject && (
        <NewProjectModal
          onClose={() => setShowNewProject(false)}
          onCreated={(project) => {
            setShowNewProject(false);
            navigate(`/projects/${project.id}`);
          }}
        />
      )}
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

function NewProjectModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (project: Project) => void;
}) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [startDate, setStartDate] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const project = await projectsApi.create({
        name,
        description: description || undefined,
        location: location || undefined,
        start_date: startDate || undefined,
      });
      onCreated(project);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal card" onClick={(e) => e.stopPropagation()}>
        <h2>New project</h2>
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="field">
            <label htmlFor="project-name">Name</label>
            <input
              id="project-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="e.g. Western Ghats Restoration"
            />
          </div>
          <div className="field">
            <label htmlFor="project-description">Description</label>
            <textarea
              id="project-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="What is this project about?"
            />
          </div>
          <div className="field">
            <label htmlFor="project-location">Location</label>
            <input
              id="project-location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Karnataka, India"
            />
          </div>
          <div className="field">
            <label htmlFor="project-start-date">Start date</label>
            <input
              id="project-start-date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>

          {error && <p className="error-text">{error}</p>}

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Creating…' : 'Create project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
