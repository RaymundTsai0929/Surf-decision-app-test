import { useState, useEffect } from 'react'

export interface CWASnapshot {
  wave_height: number | null
  wave_period: number | null
  wave_direction: number | null
  wind_speed: number | null
  wind_direction: number | null
  gust: number | null
  air_temp: number | null
  sea_temp: number | null
  tide: number | null
}

export interface CWAData {
  spot: string
  snapshot: CWASnapshot
  hourly: CWASnapshot[]
}

export function useCWAData(spotId: string) {
  const [data, setData] = useState<CWAData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!spotId) return
    setLoading(true)
    setError(null)
    fetch(`/api/v1/conditions?spot=${encodeURIComponent(spotId)}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [spotId])

  return { data, loading, error }
}
