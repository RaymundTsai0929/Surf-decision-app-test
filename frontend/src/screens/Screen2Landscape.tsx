import { useEffect } from 'react'
import type { Spot } from '../data/spots'
import { useCWAData } from '../hooks/useCWAData'
import { useClaudeStory } from '../hooks/useClaudeStory'
import { getQuizRecord } from '../utils/quizStorage'
import { computeEffectiveLevel } from '../utils/deflation'
import VideoPlayer from '../components/VideoPlayer'
import PizzaChart from '../components/PizzaChart'
import AIStory from '../components/AIStory'

interface Props {
  spot: Spot
  sarSpeedMs: number | null
  endpointDangerous: boolean
}

export default function Screen2Landscape({ spot, sarSpeedMs, endpointDangerous }: Props) {
  const { data } = useCWAData(spot.id)
  const { narrative, loading, error, fetchStory } = useClaudeStory()

  const quizLevel = getQuizRecord()?.level ?? 'cautious'
  const effectiveLevel = computeEffectiveLevel(quizLevel, data?.snapshot ?? null, endpointDangerous)

  // Lazy fetch: only called when user triggers (onFetch prop)
  const handleFetch = () => {
    fetchStory(spot.name, effectiveLevel, data?.snapshot ?? null, sarSpeedMs, endpointDangerous)
  }

  // Auto-fetch when screen becomes visible (component mounts)
  useEffect(() => {
    handleFetch()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [spot.id])

  const videoSrc = `/video/${spot.id}.mp4`

  return (
    <div className="w-full h-full flex bg-gray-900 text-white">
      {/* Video — 61.8% golden ratio */}
      <div style={{ width: '61.8%' }} className="relative flex-shrink-0">
        <VideoPlayer src={videoSrc} />
        {/* Spot name overlay */}
        <div className="absolute top-2 left-2 z-10 bg-black/50 backdrop-blur-sm rounded px-2 py-1">
          <span className="text-xs font-medium text-white">{spot.name}</span>
        </div>
      </div>

      {/* Right panel — 38.2% */}
      <div style={{ width: '38.2%' }} className="flex flex-col flex-shrink-0 border-l border-gray-800">
        {/* Pizza chart — top half */}
        <div className="flex-1 border-b border-gray-800 overflow-hidden">
          <PizzaChart snapshot={data?.snapshot ?? null} driftSpeed={sarSpeedMs} />
        </div>

        {/* AI narrative — bottom half */}
        <div className="flex-1 overflow-hidden">
          <AIStory
            narrative={narrative}
            loading={loading}
            error={error}
            onFetch={handleFetch}
          />
        </div>
      </div>
    </div>
  )
}
