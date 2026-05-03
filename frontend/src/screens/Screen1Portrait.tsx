import { useState, useRef, useCallback } from 'react'
import L from 'leaflet'
import type { Spot } from '../data/spots'
import { useCWAData } from '../hooks/useCWAData'
import SatelliteMap from '../components/SatelliteMap'
import DriftCanvas from '../components/DriftCanvas'
import DataTable from '../components/DataTable'

interface DriftResult {
  speed_ms: number
  trajectory: { lat: number; lng: number }[]
  endpoint_dangerous: boolean
}

interface Props {
  spot: Spot
  onSarResult?: (speedMs: number, dangerous: boolean) => void
}

export default function Screen1Portrait({ spot, onSarResult }: Props) {
  const { data, loading } = useCWAData(spot.id)
  const [map, setMap] = useState<L.Map | null>(null)
  const [showParticles, setShowParticles] = useState(true)
  const [trajectoryPoints, setTrajectoryPoints] = useState<{ lat: number; lng: number }[]>([])
  const [driftLoading, setDriftLoading] = useState(false)
  const [isDangerous, setIsDangerous] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const handleDotMoved = useCallback(async (lat: number, lng: number) => {
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl
    setDriftLoading(true)
    try {
      const res = await fetch(
        `/api/v1/drift?lat=${lat}&lng=${lng}&spot=${encodeURIComponent(spot.id)}`,
        { signal: ctrl.signal }
      )
      if (!res.ok) return
      const result: DriftResult = await res.json()
      setTrajectoryPoints(result.trajectory)
      setIsDangerous(result.endpoint_dangerous)
      onSarResult?.(result.speed_ms, result.endpoint_dangerous)
    } catch {
      // aborted or network error — ignore
    } finally {
      setDriftLoading(false)
    }
  }, [spot.id, onSarResult])

  return (
    <div className="w-full h-full flex flex-col bg-gray-900 text-white">
      {/* Map area — 38.2% golden ratio */}
      <div style={{ height: '38.2%' }} className="relative flex-shrink-0">
        <SatelliteMap spot={spot} onMapReady={setMap} />
        {map && (
          <DriftCanvas
            spot={spot}
            map={map}
            snapshot={data?.snapshot ?? null}
            showParticles={showParticles}
            onDotMoved={handleDotMoved}
            trajectoryPoints={trajectoryPoints}
          />
        )}

        {/* Top-left: spot name */}
        <div className="absolute top-2 left-2 z-[500] bg-black/50 backdrop-blur-sm rounded px-2 py-1">
          <span className="text-xs font-medium text-white">{spot.name}</span>
        </div>

        {/* Top-right controls */}
        <div className="absolute top-2 right-2 z-[500] flex gap-1">
          <button
            onClick={() => setShowParticles(p => !p)}
            className={`text-xs rounded px-2 py-1 backdrop-blur-sm transition-colors ${
              showParticles
                ? 'bg-blue-500/70 text-white'
                : 'bg-black/50 text-gray-400'
            }`}
          >
            流場
          </button>
          {driftLoading && (
            <div className="bg-black/50 backdrop-blur-sm rounded px-2 py-1">
              <span className="text-xs text-yellow-400">計算中…</span>
            </div>
          )}
          {isDangerous && !driftLoading && trajectoryPoints.length > 0 && (
            <div className="bg-red-600/80 backdrop-blur-sm rounded px-2 py-1">
              <span className="text-xs text-white font-bold">⚠ 危險區域</span>
            </div>
          )}
        </div>
      </div>

      {/* Data table — 61.8% golden ratio */}
      <div style={{ height: '61.8%' }} className="flex-shrink-0 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm">
            數據載入中…
          </div>
        ) : (
          <DataTable hourly={data?.hourly ?? []} />
        )}
      </div>
    </div>
  )
}
