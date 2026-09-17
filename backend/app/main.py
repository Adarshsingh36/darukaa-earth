from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, dashboard, metrics, projects, sites
from app.core.config import settings

app = FastAPI(
    title="Darukaa.Earth API",
    description="Geospatial data analytics platform for carbon and biodiversity projects.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(sites.router)
app.include_router(metrics.router)
app.include_router(dashboard.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "darukaa-earth-api"}


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "healthy"}
