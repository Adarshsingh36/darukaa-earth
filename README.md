# Darukaa.Earth

A full-stack geospatial data analytics platform for managing and visualizing carbon and
biodiversity projects. Register, create projects, draw site boundaries directly on a map,
and track carbon, biodiversity, tree cover, and species-count metrics over time.

## Features

- Email/password authentication with JWT, secure password hashing (bcrypt)
- Create and browse projects, each with multiple monitored sites
- Draw site polygons directly on an interactive Mapbox map (Mapbox GL Draw)
- Polygons are stored as real PostGIS geometry (SRID 4326) — not fake markers
- Site area is calculated automatically in hectares using PostGIS's geography-aware
  `ST_Area`, so it accounts for the curvature of the earth rather than a naive planar
  calculation
- Dashboard with portfolio-wide stats (projects, sites, monitored area, carbon, biodiversity)
  and a map of every site across every project
- Site detail view with time-series charts (Chart.js) for carbon, biodiversity index, and
  tree cover
- Input validation on both ends, including a GeoJSON polygon validator (closed ring,
  valid lng/lat bounds) before anything reaches PostGIS
- ESLint + Prettier + Husky + lint-staged on the frontend; Ruff + Pytest on the backend
- GitHub Actions CI running lint/build/tests on every push and pull request

## Architecture

```
React (Vite, TypeScript, Mapbox GL JS, Chart.js)
              │  HTTPS / JSON
              ▼
        FastAPI (Python)
   SQLAlchemy · Pydantic · Alembic
              │
              ▼
     PostgreSQL + PostGIS
```

The frontend never talks to the database directly. Mapbox GL Draw produces GeoJSON,
which is validated and sent to FastAPI; FastAPI converts it into a PostGIS geometry via
GeoAlchemy2/Shapely, stores it, computes its area with `ST_Area(geometry::geography)`,
and returns GeoJSON back to the frontend for rendering.

## Technology stack

**Frontend:** React 19, TypeScript, Vite, Mapbox GL JS, Mapbox GL Draw, Chart.js
(via react-chartjs-2), React Router, Axios

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2, GeoAlchemy2, Pydantic v2, Alembic,
python-jose (JWT), passlib/bcrypt, Shapely

**Database:** PostgreSQL 16 + PostGIS 3.4

**Code quality:** ESLint, Prettier, Husky, lint-staged (frontend) · Ruff, Pytest (backend)

**CI/CD:** GitHub Actions · Vercel (frontend) · Render (backend + PostgreSQL/PostGIS)

## Local setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- A PostgreSQL 16 server with the PostGIS extension available (either installed locally,
  or run via Docker: `docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgis/postgis:16-3.4`)

### 1. Database

```bash
createdb darukaa
psql -d darukaa -c "CREATE EXTENSION postgis;"
```

### 2. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env            # then edit .env — see "Environment variables" below

alembic upgrade head            # creates all tables + the PostGIS geometry column
python -m app.seed              # optional: loads a realistic synthetic demo dataset

uvicorn app.main:app --reload   # http://localhost:8000, docs at /docs
```

### 3. Frontend

```bash
cd frontend
npm install

cp .env.example .env            # then edit .env — see "Environment variables" below

npm run dev                     # http://localhost:5173
```

### Demo login

If you ran the seed script, you can sign in immediately with:

```
email:    demo@darukaa.earth
password: demo12345
```

## Environment variables

### Backend (`backend/.env`, see `backend/.env.example`)

| Variable         | Description                                                                 |
| ---------------- | ---------------------------------------------------------------------------- |
| `DATABASE_URL`   | PostgreSQL connection string, e.g. `postgresql://postgres:postgres@localhost:5432/darukaa` |
| `JWT_SECRET`     | Secret used to sign JWTs. Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `CORS_ORIGINS`   | Comma-separated list of origins allowed to call the API                     |
| `ENVIRONMENT`    | `development` or `production` (informational)                               |

### Frontend (`frontend/.env`, see `frontend/.env.example`)

| Variable             | Description                                                          |
| -------------------- | ---------------------------------------------------------------------- |
| `VITE_API_URL`       | Base URL of the FastAPI backend, no trailing slash                     |
| `VITE_MAPBOX_TOKEN`  | A Mapbox access token — get one free at https://account.mapbox.com/access-tokens/. Without this, the app runs normally but shows a "Mapbox token not configured" placeholder wherever the map would appear. |

**Never commit `.env` files.** Both are already excluded in `.gitignore`; only the
`.env.example` templates are tracked.

## Database setup notes

PostGIS is required, not optional — the `sites.geometry` column is a native PostGIS
`geometry(Polygon, 4326)` column, and area calculations use PostGIS's `ST_Area` on a
geography cast. If you're using a managed Postgres provider, confirm PostGIS is
available/enabled before running migrations (see the Deployment section for Render specifics).

## Running the application

```bash
# Terminal 1
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

Then open http://localhost:5173. API documentation (Swagger UI) is available at
http://localhost:8000/docs.

## Testing

```bash
cd backend
source venv/bin/activate
pytest -v
```

The test suite spins up against a real PostGIS-enabled database (point `DATABASE_URL` at
a disposable database, e.g. `darukaa_test`, with `CREATE EXTENSION postgis;` already run on
it) and covers registration, login, JWT-protected routes, project CRUD, site creation
with real polygon geometry (including area-calculation sanity checks and rejection of
invalid polygons), and metrics/dashboard aggregation.

## Code quality

```bash
# Frontend
cd frontend
npm run lint           # ESLint
npm run format:check   # Prettier (check only)
npm run format          # Prettier (write)
npx tsc --noEmit        # TypeScript

# Backend
cd backend
ruff check .            # lint
ruff check . --fix      # lint, auto-fixing what it can
```

## Git hooks

Husky + lint-staged run ESLint and Prettier on staged frontend files before every commit,
so lint errors never make it into the repository. They're wired up automatically:

```bash
npm install   # from the repo root — installs Husky and registers the git hook
```

The hook lives at `.husky/pre-commit` and runs `lint-staged` (configured in
`frontend/.lintstagedrc.json`) against whatever `frontend/` files are staged.

## CI/CD

`.github/workflows/ci.yml` runs on every push and pull request against `main`, with two
parallel jobs:

- **frontend** — `npm ci`, ESLint, `tsc --noEmit`, `vite build`
- **backend** — spins up a `postgis/postgis:16-3.4` service container, enables the
  PostGIS extension, runs Ruff, applies Alembic migrations from scratch, and runs the
  full Pytest suite

Either job failing fails the workflow.

## Deployment

### Frontend → Vercel

1. Import the repository in Vercel, set the project root to `frontend/`.
2. Vercel auto-detects the Vite framework preset (also declared in `frontend/vercel.json`).
3. Set environment variables in the Vercel project settings: `VITE_API_URL` (your deployed
   backend URL) and `VITE_MAPBOX_TOKEN`.
4. Deploy.

### Backend + database → Render

A `render.yaml` Blueprint is included at the repo root, defining the web service and a
managed PostgreSQL database.

1. In Render, create a new Blueprint from this repository.
2. Render provisions the `darukaa-earth-api` web service and `darukaa-earth-db` database.
3. **PostGIS must be enabled manually once**, since Render's managed Postgres doesn't
   enable it by default: open the database's dashboard, copy the external connection
   string, and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
4. Set the `CORS_ORIGINS` environment variable on the web service to your deployed
   Vercel URL (it's marked `sync: false` in `render.yaml`, so Render will prompt for it).
5. The build command (`pip install -r requirements.txt && alembic upgrade head`) applies
   migrations automatically on every deploy.

### Deployment status

This repository is deployment-ready (`render.yaml` and `frontend/vercel.json` are in
place and the exact commands they run have been verified locally), but no live public
URL has been provisioned as part of this build — doing so requires Render/Vercel
account credentials that weren't available in this environment. The steps above are the
exact remaining actions needed to go live.

## Dataset

> The environmental monitoring data is synthetic and is intended for demonstration of
> the platform's geospatial storage, analytics and visualization capabilities. It does
> not represent verified environmental measurements.

Running `python -m app.seed` from `backend/` (with `DATABASE_URL` pointed at your dev
database) loads 5 projects across geographically plausible regions (Western Ghats,
Amazon Basin, Congo Basin, Borneo, East African Rift), 10–20 sites with real polygon
geometry, and 5 metric records per site showing a realistic upward trend from
January 2025 to January 2026.

## API

FastAPI generates interactive API documentation automatically:

- Swagger UI: `/docs`
- ReDoc: `/redoc`

Key endpoints:

```
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me

GET    /api/projects
POST   /api/projects
GET    /api/projects/{project_id}
DELETE /api/projects/{project_id}

GET    /api/projects/{project_id}/sites
POST   /api/projects/{project_id}/sites
GET    /api/sites/{site_id}
DELETE /api/sites/{site_id}

GET    /api/sites/{site_id}/metrics
POST   /api/sites/{site_id}/metrics

GET    /api/dashboard/summary
```

All routes except `/api/auth/register` and `/api/auth/login` require a valid JWT in the
`Authorization: Bearer <token>` header.

## Known limitations

- No email verification or password recovery (intentionally out of scope for this
  prototype — see the project brief).
- Authorization is workspace-level, not per-user multi-tenancy: any authenticated user
  can see and manage all projects and sites (project deletion additionally checks
  `created_by`, but sites don't carry independent ownership). This matches the brief's
  instruction to avoid overengineering; a real multi-tenant deployment would add
  per-user or per-organization scoping.
- The frontend production bundle is a single ~680 KB gzipped chunk; code-splitting
  (e.g. lazy-loading the Mapbox/Chart.js-heavy pages) would improve initial load time
  for a production launch but was left out to keep the build simple for this scope.
- No live public deployment has been verified (see "Deployment status" above).
