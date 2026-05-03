import type { CWASnapshot } from '../hooks/useCWAData'

// Fixed thresholds — same across all spots and dates
function waveHeightColor(v: number): string {
  if (v > 2.0)  return '#1e3a5f'
  if (v > 1.5)  return '#1e4d8c'
  if (v > 1.0)  return '#2563b0'
  if (v > 0.5)  return '#60a5d4'
  return '#bfdbf7'
}

function windColor(v: number): string {
  if (v > 20) return '#c2410c'
  if (v > 15) return '#ea580c'
  if (v > 10) return '#ca8a04'
  if (v > 5)  return '#84cc16'
  return '#22c55e'
}

function gustColor(v: number): string {
  if (v > 20) return '#c2410c'
  if (v > 13) return '#ea580c'
  if (v > 8)  return '#ca8a04'
  return '#22c55e'
}

function tideColor(v: number, min: number, max: number): string {
  if (max === min) return '#d1d5db'
  const ratio = (v - min) / (max - min)
  // green (low) → pink (high)
  const r = Math.round(34 + ratio * (236 - 34))
  const g = Math.round(197 - ratio * (197 - 72))
  const b = Math.round(94 + ratio * (153 - 94))
  return `rgb(${r},${g},${b})`
}

function dirArrow(deg: number | null): string {
  if (deg === null) return '--'
  const arrows = ['↓','↙','←','↖','↑','↗','→','↘']
  return arrows[Math.round(((deg + 22.5) % 360) / 45) % 8]
}

function fmt(v: number | null, decimals = 1): string {
  return v === null ? '--' : v.toFixed(decimals)
}

interface Props {
  hourly: CWASnapshot[]
  currentHour?: number
}

export default function DataTable({ hourly, currentHour }: Props) {
  const tidMin = Math.min(...hourly.map(h => h.tide ?? Infinity).filter(isFinite))
  const tidMax = Math.max(...hourly.map(h => h.tide ?? -Infinity).filter(v => v !== -Infinity))
  const now = currentHour ?? new Date().getHours()

  const rows: { label: string; render: (h: CWASnapshot, i: number) => React.ReactNode }[] = [
    {
      label: '浪高 m',
      render: h => (
        <td key="wh" style={{ background: h.wave_height !== null ? waveHeightColor(h.wave_height) : undefined }}
          className="px-2 py-1 text-center text-xs font-medium text-white">
          {fmt(h.wave_height)}
        </td>
      ),
    },
    {
      label: '週期 s',
      render: h => (
        <td key="wp" className="px-2 py-1 text-center text-xs text-gray-200">
          {fmt(h.wave_period)}
        </td>
      ),
    },
    {
      label: '浪向',
      render: h => (
        <td key="wd" className="px-2 py-1 text-center text-sm text-gray-300">
          {dirArrow(h.wave_direction)}
        </td>
      ),
    },
    {
      label: '風速 m/s',
      render: h => (
        <td key="ws" style={{ background: h.wind_speed !== null ? windColor(h.wind_speed) : undefined }}
          className="px-2 py-1 text-center text-xs font-medium text-white">
          {fmt(h.wind_speed)}
        </td>
      ),
    },
    {
      label: '風向',
      render: h => (
        <td key="wdir" className="px-2 py-1 text-center text-sm text-gray-300">
          {dirArrow(h.wind_direction)}
        </td>
      ),
    },
    {
      label: '陣風 m/s',
      render: h => (
        <td key="g" style={{ background: h.gust !== null ? gustColor(h.gust) : undefined }}
          className="px-2 py-1 text-center text-xs font-medium text-white">
          {fmt(h.gust)}
        </td>
      ),
    },
    {
      label: '氣溫 °C',
      render: h => (
        <td key="at" className="px-2 py-1 text-center text-xs text-gray-300">
          {fmt(h.air_temp, 0)}
        </td>
      ),
    },
    {
      label: '海溫 °C',
      render: h => (
        <td key="st" className="px-2 py-1 text-center text-xs text-gray-300">
          {fmt(h.sea_temp, 0)}
        </td>
      ),
    },
    {
      label: '潮汐 m',
      render: (h, i) => (
        <td key="tid" style={{ background: h.tide !== null ? tideColor(h.tide, tidMin, tidMax) : undefined }}
          className="px-2 py-1 text-center text-xs font-medium text-white">
          {fmt(h.tide)}
        </td>
      ),
    },
  ]

  if (!hourly.length) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500 text-sm">
        數據載入中...
      </div>
    )
  }

  return (
    <div className="w-full h-full overflow-auto bg-gray-950">
      <table className="border-collapse min-w-max">
        <thead>
          <tr className="sticky top-0 z-10 bg-gray-900">
            <th className="px-2 py-1 text-left text-xs text-gray-400 sticky left-0 bg-gray-900 min-w-[72px]">
              項目
            </th>
            {hourly.map((_, i) => {
              const hour = (now - Math.floor(hourly.length / 2) + i + 24) % 24
              const isNow = i === Math.floor(hourly.length / 2)
              return (
                <th
                  key={i}
                  className={`px-2 py-1 text-xs font-medium min-w-[44px] text-center ${
                    isNow ? 'text-blue-400 bg-blue-900/30' : 'text-gray-400'
                  }`}
                >
                  {hour.toString().padStart(2, '0')}:00
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map(({ label, render }) => (
            <tr key={label} className="border-t border-gray-800">
              <td className="px-2 py-1 text-xs text-gray-400 sticky left-0 bg-gray-950 whitespace-nowrap">
                {label}
              </td>
              {hourly.map((h, i) => {
                const isNow = i === Math.floor(hourly.length / 2)
                return (
                  <td key={i} className={isNow ? 'ring-1 ring-inset ring-blue-500' : ''}>
                    <table><tbody><tr>{render(h, i)}</tr></tbody></table>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
