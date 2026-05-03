import { useState } from 'react'
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

  const question = QUIZ_QUESTIONS[current]
  const total = QUIZ_QUESTIONS.length

  const handleOption = (score: number, idx: number) => {
    if (selectedIdx !== null) return
    setSelectedIdx(idx)
    setTimeout(() => {
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
    }, 400)
  }

  const handleSkip = () => {
    saveQuizRecord({ level: 'cautious', timestamp: Date.now(), skipped: true })
    onComplete()
  }

  if (done) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-900 text-white p-6">
        <div className="text-center max-w-xs">
          <div className="text-4xl mb-4">🏄</div>
          <h2 className="text-xl font-bold mb-2">測驗完成！</h2>
          <p className="text-gray-400 text-sm mb-6">
            已根據你的回答建立個人化設定。
          </p>
          <button
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-medium transition-colors"
            onClick={onComplete}
          >
            進入 App
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full h-full flex flex-col bg-gray-900 text-white">
      {/* Progress bar */}
      <div className="w-full h-1 bg-gray-800">
        <div
          className="h-full bg-blue-500 transition-all duration-300"
          style={{ width: `${(current / total) * 100}%` }}
        />
      </div>

      <div className="flex-1 flex flex-col justify-between p-6">
        <div>
          <div className="flex items-center justify-between mb-6">
            <span className="text-xs text-gray-500">{current + 1} / {total}</span>
            <button
              onClick={handleSkip}
              className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
            >
              跳過測驗
            </button>
          </div>
          <h2 className="text-lg font-semibold leading-snug mb-8">
            {question.text}
          </h2>
        </div>

        <div className="space-y-3">
          {question.options.map((opt, i) => (
            <button
              key={i}
              onClick={() => handleOption(opt.score, i)}
              disabled={selectedIdx !== null}
              className={`w-full text-left px-4 py-3 rounded-xl border transition-all text-sm ${
                selectedIdx === i
                  ? 'border-blue-500 bg-blue-500/20 text-white'
                  : selectedIdx !== null
                  ? 'border-gray-700 bg-gray-800/50 text-gray-500'
                  : 'border-gray-700 bg-gray-800 text-gray-200 hover:border-gray-500'
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
