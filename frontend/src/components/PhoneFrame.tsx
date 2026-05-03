import { useEffect, useState, ReactNode } from 'react'

const PHONE_W = 390
const PHONE_H = 844

export default function PhoneFrame({ children }: { children: ReactNode }) {
  const [isDesktop, setIsDesktop] = useState(window.innerWidth > 500)

  useEffect(() => {
    const handler = () => setIsDesktop(window.innerWidth > 500)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  if (!isDesktop) return <>{children}</>

  return (
    <div className="flex items-center justify-center w-screen h-screen bg-gray-900">
      <div
        style={{ width: PHONE_W, height: PHONE_H }}
        className="relative rounded-[48px] overflow-hidden border-4 border-gray-700 shadow-2xl bg-black"
      >
        {/* notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-28 h-7 bg-black rounded-b-2xl z-50" />
        <div className="w-full h-full overflow-hidden">
          {children}
        </div>
      </div>
    </div>
  )
}
