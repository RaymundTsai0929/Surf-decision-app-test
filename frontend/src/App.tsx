import { useState } from 'react'
import { useSwipeable } from 'react-swipeable'
import { motion, AnimatePresence } from 'framer-motion'
import PhoneFrame from './components/PhoneFrame'
import Screen1Portrait from './screens/Screen1Portrait'
import Screen2Landscape from './screens/Screen2Landscape'
import OnboardingQuiz from './screens/OnboardingQuiz'
import TaiwanMap from './screens/TaiwanMap'
import { getQuizRecord } from './utils/quizStorage'
import type { Spot } from './data/spots'

export default function App() {
  const [selectedSpot, setSelectedSpot] = useState<Spot | null>(null)
  const [screen, setScreen] = useState<0 | 1>(0)
  const [sarSpeedMs, setSarSpeedMs] = useState<number | null>(null)
  const [endpointDangerous, setEndpointDangerous] = useState(false)
  const quizDone = !!getQuizRecord()

  const handlers = useSwipeable({
    onSwipedLeft: () => setScreen(1),
    onSwipedRight: () => setScreen(0),
    trackMouse: false,
    delta: 50,
  })

  if (!quizDone) {
    return (
      <PhoneFrame>
        <OnboardingQuiz onComplete={() => window.location.reload()} />
      </PhoneFrame>
    )
  }

  return (
    <PhoneFrame>
      {!selectedSpot ? (
        <TaiwanMap onSelectSpot={(spot) => { setSelectedSpot(spot); setScreen(0) }} />
      ) : (
        <div className="relative w-full h-full overflow-hidden" {...handlers}>
          <AnimatePresence initial={false}>
            {screen === 0 ? (
              <motion.div
                key="s1"
                className="absolute inset-0"
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '-100%' }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              >
                <Screen1Portrait
                  spot={selectedSpot}
                  onSarResult={(speed, dangerous) => {
                    setSarSpeedMs(speed)
                    setEndpointDangerous(dangerous)
                  }}
                />
              </motion.div>
            ) : (
              <motion.div
                key="s2"
                className="absolute inset-0"
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '-100%' }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              >
                <Screen2Landscape
                  spot={selectedSpot}
                  sarSpeedMs={sarSpeedMs}
                  endpointDangerous={endpointDangerous}
                />
              </motion.div>
            )}
          </AnimatePresence>

          <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5 z-50 pointer-events-none">
            <div className={`w-1.5 h-1.5 rounded-full transition-colors ${screen === 0 ? 'bg-white' : 'bg-white/40'}`} />
            <div className={`w-1.5 h-1.5 rounded-full transition-colors ${screen === 1 ? 'bg-white' : 'bg-white/40'}`} />
          </div>
        </div>
      )}
    </PhoneFrame>
  )
}
