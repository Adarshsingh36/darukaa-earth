"""Helpers for converting between GeoJSON (as sent by Mapbox) and PostGIS geometry,
and for computing polygon area in hectares."""
from geoalchemy2 import Geography
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import mapping, shape
from sqlalchemy import cast, func
from sqlalchemy.orm import Session


def geojson_to_ewkt_element(geojson: dict):
    """Convert a GeoJSON Polygon dict into a WKBElement usable with GeoAlchemy2."""
    geom = shape(geojson)
    return from_shape(geom, srid=4326)


def geometry_to_geojson(geom) -> dict:
    """Convert a stored PostGIS geometry (WKBElement) back into a GeoJSON dict."""
    if geom is None:
        return None
    shapely_geom = to_shape(geom)
    return mapping(shapely_geom)


def calculate_area_hectares(db: Session, geom_element) -> float:
    """Use PostGIS geography casting to get an accurate area in square metres,
    then convert to hectares (1 ha = 10,000 m^2). Geography cast accounts for
    the earth's curvature, which is more accurate than a naive planar calc
    on lng/lat degrees."""
    result = db.query(func.ST_Area(cast(geom_element, Geography))).scalar()
    square_metres = float(result or 0)
    return round(square_metres / 10000, 4)
