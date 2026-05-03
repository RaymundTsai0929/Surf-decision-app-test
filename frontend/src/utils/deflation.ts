import type { Level } from './quizStorage'
import type { CWASnapshot } from '../hooks/useCWAData'

const LEVELS: Level[] = ['cautious', 'understanding', 'proficient']

function deflect(level: Level, steps: number): Level {
  const idx = Math.max(0, LEVELS.indexOf(level) - steps)
  return LEVELS[idx]
}

export function computeEffectiveLevel(
  quizLevel: Level,
  snapshot: CWASnapshot | null,
  endpointDangerous: boolean,
): Level {
  // Fixed safety margin: always deflect by 1
  let effective = deflect(quizLevel, 1)

  if (endpointDangerous) {
    return 'cautious'
  }

  if (!snapshot) return effective

  const wh = snapshot.wave_height ?? 0
  const ws = snapshot.wind_speed ?? 0
  const wp = snapshot.wave_period ?? 99

  // Each triggered condition deflects one additional step
  let extra = 0
  if (wh > 2.0) extra++
  if (ws > 12.86) extra++ // 25 kt ≈ 12.86 m/s
  if (wp < 7) extra++

  effective = deflect(effective, extra)
  return effective
}
