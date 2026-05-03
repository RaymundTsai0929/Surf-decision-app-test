import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Spot } from '../data/spots'

const ESRI_TILE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'

export interface SatelliteMapHandle {
  getMap: () => L.Map | null
}

interface Props {
  spot: Spot
  onMapReady?: (map: L.Map) => void
}

const SatelliteMap = forwardRef<SatelliteMapHandle, Props>(({ spot, onMapReady }, ref) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)

  useImperativeHandle(ref, () => ({
    getMap: () => mapRef.current,
  }))

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const map = L.map(containerRef.current, {
      center: [spot.refLat, spot.refLng],
      zoom: 14,
      zoomControl: false,
      attributionControl: false,
    })

    L.tileLayer(ESRI_TILE, { maxZoom: 19 }).addTo(map)

    mapRef.current = map
    onMapReady?.(map)

    return () => { map.remove(); mapRef.current = null }
  }, [spot.id])

  return <div ref={containerRef} className="w-full h-full" />
})

SatelliteMap.displayName = 'SatelliteMap'
export default SatelliteMap
