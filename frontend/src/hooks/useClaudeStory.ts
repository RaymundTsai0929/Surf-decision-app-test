import { useState, useCallback, useRef } from 'react'
import type { CWASnapshot } from './useCWAData'
import type { Level } from '../utils/quizStorage'

interface StoryRequest {
  effective_level: Level
  spot_name: string
  wave_height?: number | null
  wave_period?: number | null
  wind_speed?: number | null
  wind_direction?: number | null
  gust?: number | null
  tide?: number | null
  sea_temp?: number | null
  sar_speed_ms?: number | null
  endpoint_dangerous?: boolean
  irregular_wave?: boolean
}

interface CacheEntry {
  narrative: string
  hourKey: number
}

// Per-spot-per-hour memory cache
const _cache = new Map<string, CacheEntry>()

function hourKey() {
  return Math.floor(Date.now() / 3_600_000)
}

export function useClaudeStory() {
  const [narrative, setNarrative] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const fetch_ = useCallback(async (
    spotName: string,
    effectiveLevel: Level,
    snapshot: CWASnapshot | null,
    sarSpeedMs: number | null,
    endpointDangerous: boolean,
  ) => {
    const key = `${spotName}:${effectiveLevel}:${hourKey()}`
    const cached = _cache.get(key)
    if (cached && cached.hourKey === hourKey()) {
      setNarrative(cached.narrative)
      return
    }

    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl
    setLoading(true)
    setError(null)

    const body: StoryRequest = {
      effective_level: effectiveLevel,
      spot_name: spotName,
      wave_height: snapshot?.wave_height,
      wave_period: snapshot?.wave_period,
      wind_speed: snapshot?.wind_speed,
      wind_direction: snapshot?.wind_direction,
      gust: snapshot?.gust,
      tide: snapshot?.tide,
      sea_temp: snapshot?.sea_temp,
      sar_speed_ms: sarSpeedMs,
      endpoint_dangerous: endpointDangerous,
      irregular_wave: (snapshot?.wave_period ?? 99) < 7,
    }

    try {
      const res = await fetch('/api/v1/story', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: ctrl.signal,
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      _cache.set(key, { narrative: data.narrative, hourKey: hourKey() })
      setNarrative(data.narrative)
    } catch (e) {
      if ((e as Error).name !== 'AbortError') {
        setError((e as Error).message)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  return { narrative, loading, error, fetchStory: fetch_ }
}
