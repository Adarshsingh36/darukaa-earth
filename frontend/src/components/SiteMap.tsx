import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import 'mapbox-gl/dist/mapbox-gl.css';
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';
import type { GeoJSONPolygon, Site } from '../api/types';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;

interface SiteMapProps {
  sites: Site[];
  drawMode?: boolean;
  onPolygonDrawn?: (geometry: GeoJSONPolygon) => void;
  onPolygonCleared?: () => void;
  selectedSiteId?: string | null;
  onSelectSite?: (siteId: string) => void;
  height?: string;
}

/** Compute a bounding box that covers every site's polygon, for fit-to-bounds. */
function boundsFromSites(sites: Site[]): mapboxgl.LngLatBounds | null {
  if (sites.length === 0) return null;
  const bounds = new mapboxgl.LngLatBounds();
  let hasPoints = false;
  for (const site of sites) {
    for (const ring of site.geometry.coordinates) {
      for (const [lng, lat] of ring) {
        bounds.extend([lng, lat]);
        hasPoints = true;
      }
    }
  }
  return hasPoints ? bounds : null;
}

export function SiteMap({
  sites,
  drawMode = false,
  onPolygonDrawn,
  onPolygonCleared,
  selectedSiteId,
  onSelectSite,
  height = '100%',
}: SiteMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const drawRef = useRef<MapboxDraw | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [tokenMissing] = useState(!MAPBOX_TOKEN);

  // Initialize the map once.
  useEffect(() => {
    if (!containerRef.current || tokenMissing || mapRef.current) return;

    mapboxgl.accessToken = MAPBOX_TOKEN as string;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [0, 20],
      zoom: 1.5,
    });

    map.addControl(new mapboxgl.NavigationControl(), 'top-right');

    if (drawMode) {
      const draw = new MapboxDraw({
        displayControlsDefault: false,
        controls: { polygon: true, trash: true },
        defaultMode: 'simple_select',
      });
      map.addControl(draw, 'top-left');
      drawRef.current = draw;

      map.on('draw.create', (e: { features: GeoJSON.Feature[] }) => {
        const feature = e.features[0];
        if (feature?.geometry.type === 'Polygon') {
          onPolygonDrawn?.(feature.geometry as GeoJSONPolygon);
        }
      });
      map.on('draw.delete', () => {
        onPolygonCleared?.();
      });
      map.on('draw.update', (e: { features: GeoJSON.Feature[] }) => {
        const feature = e.features[0];
        if (feature?.geometry.type === 'Polygon') {
          onPolygonDrawn?.(feature.geometry as GeoJSONPolygon);
        }
      });
    }

    map.on('load', () => setMapReady(true));
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      drawRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tokenMissing]);

  // Render existing site polygons as a layer (skipped in pure draw-only contexts with 0 sites).
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    const sourceId = 'sites-source';
    const geojson: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: sites.map((site) => ({
        type: 'Feature',
        id: site.id,
        properties: { id: site.id, name: site.name, selected: site.id === selectedSiteId },
        geometry: site.geometry,
      })),
    };

    const existingSource = map.getSource(sourceId) as mapboxgl.GeoJSONSource | undefined;
    if (existingSource) {
      existingSource.setData(geojson);
    } else {
      map.addSource(sourceId, { type: 'geojson', data: geojson });

      map.addLayer({
        id: 'sites-fill',
        type: 'fill',
        source: sourceId,
        paint: {
          'fill-color': ['case', ['get', 'selected'], '#c97b4a', '#7a9b76'],
          'fill-opacity': ['case', ['get', 'selected'], 0.35, 0.22],
        },
      });
      map.addLayer({
        id: 'sites-outline',
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': ['case', ['get', 'selected'], '#e09564', '#96b892'],
          'line-width': ['case', ['get', 'selected'], 3, 1.5],
        },
      });
      map.addLayer({
        id: 'sites-label',
        type: 'symbol',
        source: sourceId,
        layout: {
          'text-field': ['get', 'name'],
          'text-size': 12,
          'text-offset': [0, 0.2],
          'text-anchor': 'top',
        },
        paint: {
          'text-color': '#ede9e3',
          'text-halo-color': '#14181a',
          'text-halo-width': 1.4,
        },
      });

      if (onSelectSite) {
        map.on('click', 'sites-fill', (e) => {
          const feature = e.features?.[0];
          const id = feature?.properties?.id;
          if (id) onSelectSite(id);
        });
        map.on('mouseenter', 'sites-fill', () => {
          map.getCanvas().style.cursor = 'pointer';
        });
        map.on('mouseleave', 'sites-fill', () => {
          map.getCanvas().style.cursor = '';
        });
      }
    }

    // Fit bounds to cover all sites, unless we're actively drawing a new one.
    if (!drawMode) {
      const bounds = boundsFromSites(sites);
      if (bounds) {
        map.fitBounds(bounds, { padding: 60, maxZoom: 15, duration: 500 });
      }
    }
  }, [sites, mapReady, selectedSiteId, onSelectSite, drawMode]);

  // In draw-context project maps, still fit to existing sites once on load.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !drawMode) return;
    const bounds = boundsFromSites(sites);
    if (bounds) {
      map.fitBounds(bounds, { padding: 80, maxZoom: 15, duration: 0 });
    } else {
      map.setCenter([0, 20]);
      map.setZoom(1.5);
    }
    // Only run once when the map becomes ready.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapReady]);

  if (tokenMissing) {
    return (
      <div className="map-token-missing" style={{ height }}>
        <p>
          <strong>Mapbox token not configured.</strong>
        </p>
        <p>
          Set <code>VITE_MAPBOX_TOKEN</code> in your frontend <code>.env</code> file to enable the
          map. See the README for setup instructions.
        </p>
      </div>
    );
  }

  return <div ref={containerRef} style={{ height, width: '100%' }} />;
}
