export type Level = 'cautious' | 'understanding' | 'proficient'

export interface QuizRecord {
  level: Level
  timestamp: number
  skipped?: boolean
}

const KEY = 'surf_quiz_record'
const COOLDOWN_MS = 7 * 24 * 60 * 60 * 1000

export function getQuizRecord(): QuizRecord | null {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function saveQuizRecord(record: QuizRecord) {
  localStorage.setItem(KEY, JSON.stringify(record))
}

export function cooldownRemaining(): number {
  const rec = getQuizRecord()
  if (!rec) return 0
  const elapsed = Date.now() - rec.timestamp
  return Math.max(0, COOLDOWN_MS - elapsed)
}
