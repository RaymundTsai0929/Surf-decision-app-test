import { useEffect, useState, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  landscape?: boolean
}

export default function PhoneFrame({ children, landscape = false }: Props) {
  const [isDesktop, setIsDesktop] = useState(window.innerWidth > 500)

  useEffect(() => {
    const handler = () => setIsDesktop(window.innerWidth > 500)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  if (!isDesktop) return <>{children}</>

  const w = landscape ? 844 : 390
  const h = landscape ? 390 : 844

  return (
    <div className="flex items-center justify-center w-screen h-screen bg-gray-900">
      <div
        style={{ width: w, height: h, transition: 'width 0.35s ease, height 0.35s ease' }}
        className="relative rounded-[48px] overflow-hidden border-4 border-gray-700 shadow-2xl bg-black"
      >
        {/* notch — only in portrait */}
        {!landscape && (
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-28 h-7 bg-black rounded-b-2xl z-50" />
        )}
        <div className="w-full h-full overflow-hidden">
          {children}
        </div>
      </div>
    </div>
  )
}
