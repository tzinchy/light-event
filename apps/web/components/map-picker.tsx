"use client";

/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useRef } from "react";

export type MapPoint = { lat: number; lon: number };

const MOSCOW: MapPoint = { lat: 55.7558, lon: 37.6173 };
const YANDEX_KEY = process.env.NEXT_PUBLIC_YANDEX_MAPS_KEY;

let loader: Promise<any> | null = null;

// Yandex Maps JS API 2.1 подгружается один раз; ключ — NEXT_PUBLIC_YANDEX_MAPS_KEY (referer-ограничен).
function loadYmaps(): Promise<any> {
  if (typeof window === "undefined") return Promise.reject(new Error("no window"));
  if ((window as any).ymaps?.Map) return Promise.resolve((window as any).ymaps);
  if (!loader) {
    loader = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = `https://api-maps.yandex.ru/2.1/?apikey=${YANDEX_KEY ?? ""}&lang=ru_RU`;
      script.async = true;
      script.onload = () => (window as any).ymaps.ready(() => resolve((window as any).ymaps));
      script.onerror = () => reject(new Error("Не удалось загрузить Yandex Maps"));
      document.head.appendChild(script);
    });
  }
  return loader;
}

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
  const mapRef = useRef<any>(null);
  const markerRef = useRef<any>(null);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => {
    let cancelled = false;
    const center = value ?? MOSCOW;
    void loadYmaps().then((ymaps) => {
      if (cancelled || !containerRef.current || mapRef.current) return;
      const map = new ymaps.Map(
        containerRef.current,
        { center: [center.lat, center.lon], zoom: value ? 14 : 9, controls: ["zoomControl"] },
        { suppressMapOpenBlock: true },
      );
      map.events.add("click", (e: any) => {
        const [lat, lon] = e.get("coords");
        onChangeRef.current({ lat: +lat.toFixed(6), lon: +lon.toFixed(6) });
      });
      if (value) {
        markerRef.current = new ymaps.Placemark([value.lat, value.lon]);
        map.geoObjects.add(markerRef.current);
      }
      mapRef.current = map;
    });
    return () => {
      cancelled = true;
      mapRef.current?.destroy();
      mapRef.current = null;
      markerRef.current = null;
    };
    // карта создаётся один раз; value дальше двигает только маркер
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const ymaps = typeof window !== "undefined" ? (window as any).ymaps : null;
    if (!map || !ymaps) return;
    if (!value) {
      if (markerRef.current) {
        map.geoObjects.remove(markerRef.current);
        markerRef.current = null;
      }
      return;
    }
    if (!markerRef.current) {
      markerRef.current = new ymaps.Placemark([value.lat, value.lon]);
      map.geoObjects.add(markerRef.current);
    } else {
      markerRef.current.geometry.setCoordinates([value.lat, value.lon]);
    }
  }, [value]);

  return (
    <div className={className}>
      <div ref={containerRef} data-testid="map-picker" className="h-full w-full rounded-xl border" />
    </div>
  );
}
