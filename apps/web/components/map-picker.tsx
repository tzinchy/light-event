"use client";

import { useEffect, useRef } from "react";
import maplibregl, { Map as MapLibreMap, Marker } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export type MapPoint = { lat: number; lon: number };

// MapLibre + OSM-тайлы: без ключей и биллинга (PLAN §1.1)
const OSM_STYLE = {
  version: 8 as const,
  sources: {
    osm: {
      type: "raster" as const,
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© участники OpenStreetMap",
    },
  },
  layers: [{ id: "osm", type: "raster" as const, source: "osm" }],
};

const MOSCOW: MapPoint = { lat: 55.7558, lon: 37.6173 };

export function MapPicker({
  value,
  onChange,
  className,
}: {
  value: MapPoint | null;
  onChange: (point: MapPoint) => void;
  className?: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markerRef = useRef<Marker | null>(null);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const center = value ?? MOSCOW;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: OSM_STYLE,
      center: [center.lon, center.lat],
      zoom: value ? 14 : 9,
      attributionControl: { compact: true },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }));
    map.on("click", (e) => {
      onChangeRef.current({ lat: +e.lngLat.lat.toFixed(6), lon: +e.lngLat.lng.toFixed(6) });
    });
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
    // карта создаётся один раз; value дальше двигает только маркер
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (!value) {
      markerRef.current?.remove();
      markerRef.current = null;
      return;
    }
    if (!markerRef.current) {
      markerRef.current = new maplibregl.Marker({ color: "#16a34a" })
        .setLngLat([value.lon, value.lat])
        .addTo(map);
    } else {
      markerRef.current.setLngLat([value.lon, value.lat]);
    }
  }, [value]);

  return (
    <div className={className}>
      <div ref={containerRef} className="h-full w-full rounded-xl border" />
    </div>
  );
}
