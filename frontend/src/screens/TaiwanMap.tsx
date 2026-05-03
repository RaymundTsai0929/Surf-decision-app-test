import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { SPOTS } from '../data/spots'
import type { Spot } from '../data/spots'
import { useCWAData } from '../hooks/useCWAData'

const ESRI_TILE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
const ESRI_ATTR = 'Tiles &copy; Esri'

const REGIONS: Record<string, { label: string; bounds: L.LatLngBoundsExpression; color: string }> = {
  north: { label: '北部', bounds: [[24.4, 120.9], [25.4, 122.1]], color: '#3b82f6' },
  east:  { label: '東部', bounds: [[21.8, 121.3], [25.4, 122.1]], color: '#10b981' },
  south: { label: '南部', bounds: [[21.8, 120.0], [23.2, 121.0]], color: '#f59e0b' },
  west:  { label: '西部', bounds: [[22.0, 120.0], [25.0, 121.2]], color: '#8b5cf6' },
}

function pinColor(waveHeight: number | null, windSpeed: number | null): string {
  const h = waveHeight ?? 0
  const w = windSpeed ?? 0
  if (h > 2.0 || w > 20) return '#ef4444'
  if (h > 1.5 || w > 15) return '#f97316'
  if (h > 1.0 || w > 10) return '#eab308'
  return '#22c55e'
}

function SpotPin({ map, spot }: { map: L.Map; spot: Spot }) {
  const { data } = useCWAData(spot.id)
  const snap = data?.snapshot

  const color = snap
    ? pinColor(snap.wave_height ?? null, snap.wind_speed ?? null)
    : '#9ca3af'

  useEffect(() => {
    const icon = L.divIcon({
      className: '',
      html: `<div style="width:12px;height:12px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.5)"></div>`,
      iconAnchor: [6, 6],
    })
    const marker = L.marker([spot.lat, spot.lng], { icon })
      .bindTooltip(spot.name, { permanent: false, direction: 'top' })
    marker.addTo(map)
    return () => { marker.remove() }
  }, [map, spot, color])

  return null
}

export default function TaiwanMap({ onSelectSpot }: { onSelectSpot: (s: Spot) => void }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const zoomedRegion = useRef<string | null>(null)

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const map = L.map(containerRef.current, {
      center: [23.6, 121.0],
      zoom: 7,
      zoomControl: false,
      attributionControl: false,
    })

    L.tileLayer(ESRI_TILE, { attribution: ESRI_ATTR, maxZoom: 18 }).addTo(map)

    Object.entries(REGIONS).forEach(([key, region]) => {
      const bounds = region.bounds as [[number, number], [number, number]]
      const rect = L.rectangle(bounds, {
        color: region.color,
        weight: 2,
        fillOpacity: 0.1,
        fillColor: region.color,
      })

      rect.on('click', () => {
        if (zoomedRegion.current === key) return
        zoomedRegion.current = key
        map.flyToBounds(bounds, { padding: [20, 20], duration: 0.8 })

        const regionSpots = SPOTS.filter(s => s.region === key)
        regionSpots.forEach(spot => {
          const icon = L.divIcon({
            className: '',
            html: `<div style="background:#22c55e;color:white;padding:2px 6px;border-radius:4px;font-size:11px;white-space:nowrap;font-family:system-ui">${spot.name}</div>`,
            iconAnchor: [0, 0],
          })
          const m = L.marker([spot.lat, spot.lng], { icon })
          m.on('click', () => onSelectSpot(spot))
          m.addTo(map)
        })
      })

      const center = [
        (bounds[0][0] + bounds[1][0]) / 2,
        (bounds[0][1] + bounds[1][1]) / 2,
      ] as [number, number]

      L.marker(center, {
        icon: L.divIcon({
          className: '',
          html: `<div style="color:${region.color};font-size:13px;font-weight:600;text-shadow:0 1px 3px rgba(0,0,0,0.8);font-family:system-ui">${region.label}</div>`,
          iconAnchor: [20, 10],
        }),
      }).addTo(map)

      rect.addTo(map)
    })

    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, [onSelectSpot])

  return <div ref={containerRef} className="w-full h-full" />
}
