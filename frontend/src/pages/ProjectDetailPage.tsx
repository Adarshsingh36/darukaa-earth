import { useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { projectsApi, sitesApi } from '../api/endpoints';
import { getErrorMessage } from '../api/client';
import type { GeoJSONPolygon, Project, Site } from '../api/types';
import { SiteMap } from '../components/SiteMap';

/** Shoelace-formula planar approximation, used only as an instant client-side
 * preview while drawing. The authoritative, geography-aware value comes back
 * from the API (calculated in PostGIS) once the site is saved. */
function estimateAreaHectares(geometry: GeoJSONPolygon): number {
  const ring = geometry.coordinates[0];
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const R = 6378137;
  let area = 0;
  for (let i = 0; i < ring.length - 1; i++) {
    const [lng1, lat1] = ring[i];
    const [lng2, lat2] = ring[i + 1];
    area += toRad(lng2 - lng1) * (2 + Math.sin(toRad(lat1)) + Math.sin(toRad(lat2)));
  }
  area = Math.abs((area * R * R) / 2);
  return Math.round((area / 10000) * 100) / 100;
}

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [drawingActive, setDrawingActive] = useState(false);
  const [pendingGeometry, setPendingGeometry] = useState<GeoJSONPolygon | null>(null);
  const [siteName, setSiteName] = useState('');
  const [siteDescription, setSiteDescription] = useState('');
  const [savingSite, setSavingSite] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const load = async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const [projectRes, sitesRes] = await Promise.all([
        projectsApi.get(projectId),
        sitesApi.listForProject(projectId),
      ]);
      setProject(projectRes);
      setSites(sitesRes);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const handleSaveSite = async (e: FormEvent) => {
    e.preventDefault();
    if (!projectId || !pendingGeometry) return;
    setSaveError(null);
    setSavingSite(true);
    try {
      const site = await sitesApi.create(projectId, {
        name: siteName,
        description: siteDescription || undefined,
        geometry: pendingGeometry,
      });
      setSites((prev) => [site, ...prev]);
      setDrawingActive(false);
      setPendingGeometry(null);
      setSiteName('');
      setSiteDescription('');
    } catch (err) {
      setSaveError(getErrorMessage(err));
    } finally {
      setSavingSite(false);
    }
  };

  const cancelDrawing = () => {
    setDrawingActive(false);
    setPendingGeometry(null);
    setSiteName('');
    setSiteDescription('');
    setSaveError(null);
  };

  if (loading) return <div className="page-loading">Loading project…</div>;
  if (error || !project) {
    return (
      <div className="page-error">
        <p className="error-text">{error || 'Project not found.'}</p>
        <Link to="/">← Back to dashboard</Link>
      </div>
    );
  }

  return (
    <div className="project-page">
      <div className="project-header">
        <div>
          <Link to="/" className="back-link">
            ← Dashboard
          </Link>
          <h1>{project.name}</h1>
          <p className="project-header-meta">
            {project.location && <span>{project.location}</span>}
            {project.start_date && <span>Started {project.start_date}</span>}
            <span>
              {sites.length} site{sites.length === 1 ? '' : 's'}
            </span>
          </p>
          {project.description && <p className="project-description">{project.description}</p>}
        </div>
        {!drawingActive && (
          <button className="btn btn-primary" onClick={() => setDrawingActive(true)}>
            + Draw site
          </button>
        )}
      </div>

      <div className="project-body">
        <div className="project-map card">
          {drawingActive && (
            <div className="draw-banner">
              {pendingGeometry
                ? 'Polygon drawn. Fill in site details below, or delete the shape to redraw.'
                : 'Use the polygon tool (top-left) to draw the site boundary on the map.'}
              <button className="btn btn-secondary" onClick={cancelDrawing}>
                Cancel
              </button>
            </div>
          )}
          <SiteMap
            sites={sites}
            drawMode={drawingActive}
            onPolygonDrawn={setPendingGeometry}
            onPolygonCleared={() => setPendingGeometry(null)}
            height={drawingActive ? 'calc(100% - 48px)' : '100%'}
          />
        </div>

        <div className="project-sidebar">
          {drawingActive && pendingGeometry && (
            <div className="card new-site-form">
              <h2>Site details</h2>
              <p className="estimated-area">
                Estimated area: <strong>{estimateAreaHectares(pendingGeometry)} ha</strong>{' '}
                <span className="estimated-area-note">(exact value calculated on save)</span>
              </p>
              <form onSubmit={handleSaveSite}>
                <div className="field">
                  <label htmlFor="site-name">Name</label>
                  <input
                    id="site-name"
                    value={siteName}
                    onChange={(e) => setSiteName(e.target.value)}
                    required
                    placeholder="e.g. North Ridge Plot"
                  />
                </div>
                <div className="field">
                  <label htmlFor="site-description">Description</label>
                  <textarea
                    id="site-description"
                    value={siteDescription}
                    onChange={(e) => setSiteDescription(e.target.value)}
                    rows={2}
                    placeholder="Optional notes about this site"
                  />
                </div>
                {saveError && <p className="error-text">{saveError}</p>}
                <button type="submit" className="btn btn-primary" disabled={savingSite}>
                  {savingSite ? 'Saving…' : 'Save site'}
                </button>
              </form>
            </div>
          )}

          <div className="card site-list-card">
            <h2>Sites</h2>
            {sites.length === 0 ? (
              <div className="empty-state">
                <p>No sites yet. Draw one on the map to get started.</p>
              </div>
            ) : (
              <ul className="site-list">
                {sites.map((site) => (
                  <li key={site.id}>
                    <button
                      className="site-list-item"
                      onClick={() => navigate(`/sites/${site.id}`)}
                    >
                      <span className="site-name">{site.name}</span>
                      <span className="site-area">{site.area_hectares.toLocaleString()} ha</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
