"""Seed the database with a realistic synthetic dataset for demonstration purposes.

Run with:  python -m app.seed
(from the backend/ directory, with the venv activated and DATABASE_URL set)

This data is entirely synthetic. It exists to demonstrate the platform's
geospatial storage, analytics and visualization capabilities -- it is NOT
real environmental monitoring data.
"""
import random
from datetime import date

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.metric import Metric
from app.models.project import Project
from app.models.site import Site
from app.models.user import User
from app.services.geo import calculate_area_hectares, geojson_to_ewkt_element

random.seed(42)

# Rough anchor points for geographically plausible project regions.
REGIONS = [
    {"name": "Western Ghats, India", "lat": 12.9716, "lng": 77.5946},
    {"name": "Amazon Basin, Brazil", "lat": -3.4653, "lng": -62.2159},
    {"name": "Congo Basin, DRC", "lat": -0.2280, "lng": 24.2543},
    {"name": "Borneo, Indonesia", "lat": -0.7893, "lng": 113.9213},
    {"name": "East African Rift, Kenya", "lat": -1.2921, "lng": 36.8219},
]

PROJECT_NAMES = [
    "Western Ghats Restoration",
    "Amazon Basin Conservation Corridor",
    "Congo Basin REDD+ Initiative",
    "Borneo Rainforest Recovery",
    "Rift Valley Agroforestry Program",
]

PROJECT_DESCRIPTIONS = [
    "Community-led reforestation and biodiversity monitoring across degraded ridge forest.",
    "Protecting primary and secondary rainforest to preserve carbon stocks and habitat corridors.",
    "Avoided-deforestation and forest-carbon monitoring across community forest concessions.",
    "Peatland and lowland rainforest restoration to reduce emissions and protect endemic species.",
    "Mixed agroforestry and native tree planting to restore degraded rangeland.",
]


def make_square_polygon(lat: float, lng: float, size_deg: float) -> dict:
    """Build a small square GeoJSON polygon roughly `size_deg` degrees on a side,
    anchored at (lat, lng), with a little jitter so sites don't overlap exactly."""
    jitter_lat = random.uniform(-0.05, 0.05)
    jitter_lng = random.uniform(-0.05, 0.05)
    lat0, lng0 = lat + jitter_lat, lng + jitter_lng
    return {
        "type": "Polygon",
        "coordinates": [[
            [lng0, lat0],
            [lng0 + size_deg, lat0],
            [lng0 + size_deg, lat0 + size_deg],
            [lng0, lat0 + size_deg],
            [lng0, lat0],
        ]],
    }


def make_metric_series(base_carbon, base_bio, base_tree, base_species):
    """Generate a 5-point time series (quarterly-ish, Jan 2025 -> Jan 2026) that
    trends upward, mirroring the example progression in the project brief."""
    dates = [date(2025, 1, 1), date(2025, 4, 1), date(2025, 7, 1), date(2025, 10, 1), date(2026, 1, 1)]
    series = []
    for i, d in enumerate(dates):
        growth = i / (len(dates) - 1)
        noise = random.uniform(-0.03, 0.03)
        series.append({
            "recorded_at": d,
            "carbon_tonnes": round(base_carbon * (1 + 0.55 * growth + noise), 1),
            "biodiversity_index": round(min(100, base_bio * (1 + 0.45 * growth + noise)), 1),
            "tree_cover_percentage": round(min(100, base_tree * (1 + 0.3 * growth + noise)), 1),
            "species_count": max(1, round(base_species * (1 + 0.35 * growth + noise))),
        })
    return series


def seed():
    Base.metadata.create_all(bind=engine)  # no-op if Alembic already applied migrations
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Database already has data -- skipping seed. Truncate tables first if you want to reseed.")
            return

        demo_user = User(
            name="Demo Admin",
            email="demo@darukaa.earth",
            password_hash=hash_password("demo12345"),
        )
        db.add(demo_user)
        db.flush()
        print("Created demo user: demo@darukaa.earth / demo12345")

        site_names = [
            "North Ridge Plot", "River Valley Block", "Highland Corridor", "Lowland Buffer Zone",
        ]

        total_sites = 0
        for idx, region in enumerate(REGIONS):
            project = Project(
                name=PROJECT_NAMES[idx],
                description=PROJECT_DESCRIPTIONS[idx],
                location=region["name"],
                start_date=date(2024, random.randint(1, 6), random.randint(1, 28)),
                created_by=demo_user.id,
            )
            db.add(project)
            db.flush()

            num_sites = random.randint(2, 4)  # ~10-20 sites across 5 projects
            for s in range(num_sites):
                geojson = make_square_polygon(region["lat"], region["lng"], size_deg=round(random.uniform(0.02, 0.08), 4))
                geom_element = geojson_to_ewkt_element(geojson)

                site = Site(
                    project_id=project.id,
                    name=f"{site_names[s % len(site_names)]} {s + 1}",
                    description=f"Monitored plot within {project.name}.",
                    geometry=geom_element,
                )
                db.add(site)
                db.flush()
                site.area_hectares = calculate_area_hectares(db, site.geometry)
                total_sites += 1

                base_carbon = random.uniform(400, 2000)
                base_bio = random.uniform(30, 55)
                base_tree = random.uniform(35, 60)
                base_species = random.randint(15, 60)

                for m in make_metric_series(base_carbon, base_bio, base_tree, base_species):
                    db.add(Metric(site_id=site.id, **m))

            db.commit()
            print(f"  + {project.name}: {num_sites} sites")

        print(f"Seed complete: {len(REGIONS)} projects, {total_sites} sites, "
              f"~{total_sites * 5} metric records.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
