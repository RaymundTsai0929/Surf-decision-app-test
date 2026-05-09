import { useState, useRef, useEffect } from 'react'
import { QUIZ_QUESTIONS } from '../data/quiz'
import { saveQuizRecord, type Level } from '../utils/quizStorage'

function scoreToLevel(total: number): Level {
  if (total >= 14) return 'proficient'
  if (total >= 8) return 'understanding'
  return 'cautious'
}

export default function OnboardingQuiz({ onComplete }: { onComplete: () => void }) {
  const [current, setCurrent] = useState(0)
  const [scores, setScores] = useState<number[]>([])
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null)
  const [done, setDone] = useState(false)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => { if (timeoutRef.current) clearTimeout(timeoutRef.current) }
  }, [])

  const question = QUIZ_QUESTIONS[current]
  const total = QUIZ_QUESTIONS.length
  const progress = ((current + 1) / total) * 100

  const handleOption = (score: number, idx: number) => {
    if (selectedIdx !== null) return
    setSelectedIdx(idx)
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => {
      const next = [...scores, score]
      if (current + 1 >= total) {
        const sum = next.reduce((a, b) => a + b, 0)
        saveQuizRecord({ level: scoreToLevel(sum), timestamp: Date.now() })
        setDone(true)
      } else {
        setScores(next)
        setCurrent(c => c + 1)
        setSelectedIdx(null)
      }
    }, 300)
  }

  const handleSkip = () => {
    saveQuizRecord({ level: 'cautious', timestamp: Date.now(), skipped: true })
    onComplete()
  }

  if (done) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-[#111827] text-white p-6">
        <div className="text-center max-w-xs">
          <div className="text-4xl mb-4">🏄</div>
          <h2 className="text-xl font-bold mb-2">測驗完成！</h2>
          <p className="text-[#9ca3af] text-sm mb-6">已根據你的回答建立個人化設定。</p>
          <button
            className="bg-[#3b82f6] hover:bg-[#2563eb] text-white px-8 py-3 rounded-xl font-medium transition-colors"
            onClick={onComplete}
          >
            進入 App
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full h-full flex flex-col bg-[#111827]">
      {/* Progress bar */}
      <div className="w-full h-1 bg-gray-800">
        <div
          className="h-full bg-[#3b82f6] transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Header */}
      <div className="flex justify-between items-center p-4">
        <span className="text-[#9ca3af] text-sm">{current + 1} / {total}</span>
        <button
          onClick={handleSkip}
          className="text-[#9ca3af] text-sm hover:text-gray-400 transition-colors"
        >
          跳過測驗
        </button>
      </div>

      {/* Question */}
      <div className="flex-1 flex flex-col justify-center px-6">
        <h2 className="text-white text-lg font-semibold mb-8 leading-snug">
          {question.text}
        </h2>

        <div className="space-y-3">
          {question.options.map((opt, i) => (
            <button
              key={i}
              onClick={() => handleOption(opt.score, i)}
              disabled={selectedIdx !== null}
              className={`w-full rounded-xl border px-4 py-3 text-left text-sm transition-all ${
                selectedIdx === i
                  ? 'border-[#3b82f6] bg-[#3b82f6]/20 text-white'
                  : selectedIdx !== null
                  ? 'border-[#374151] bg-[#1f2937]/50 text-[#6b7280]'
                  : 'border-[#374151] bg-[#1f2937] text-[#9ca3af] hover:border-[#4b5563]'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
