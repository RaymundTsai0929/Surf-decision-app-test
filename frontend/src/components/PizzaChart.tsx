import type { CWASnapshot } from '../hooks/useCWAData'

interface Props {
  snapshot: CWASnapshot | null
  driftSpeed: number | null
}

interface Metric {
  label: string
  value: string
  unit: string
  color: string
}

function buildMetrics(snapshot: CWASnapshot | null, driftSpeed: number | null): Metric[] {
  const fmt = (v: number | null, d = 1) => v === null ? '--' : v.toFixed(d)
  return [
    { label: '浪高',  value: fmt(snapshot?.wave_height ?? null), unit: 'm',   color: '#3b82f6' },
    { label: '週期',  value: fmt(snapshot?.wave_period ?? null), unit: 's',   color: '#6366f1' },
    { label: '風速',  value: fmt(snapshot?.wind_speed ?? null),  unit: 'm/s', color: '#22c55e' },
    { label: '陣風',  value: fmt(snapshot?.gust ?? null),        unit: 'm/s', color: '#84cc16' },
    { label: '漂流速', value: fmt(driftSpeed, 2),                 unit: 'm/s', color: '#facc15' },
  ]
}

export default function PizzaChart({ snapshot, driftSpeed }: Props) {
  const metrics = buildMetrics(snapshot, driftSpeed)
  const total = metrics.length
  const sliceAngle = (2 * Math.PI) / total
  const outerRadius = 70
  const innerRadius = 45
  const cx = 80
  const cy = 80

  const createArc = (startAngle: number, endAngle: number) => {
    const x1 = cx + outerRadius * Math.cos(startAngle)
    const y1 = cy + outerRadius * Math.sin(startAngle)
    const x2 = cx + outerRadius * Math.cos(endAngle)
    const y2 = cy + outerRadius * Math.sin(endAngle)
    const x3 = cx + innerRadius * Math.cos(endAngle)
    const y3 = cy + innerRadius * Math.sin(endAngle)
    const x4 = cx + innerRadius * Math.cos(startAngle)
    const y4 = cy + innerRadius * Math.sin(startAngle)
    return `M ${x1} ${y1} A ${outerRadius} ${outerRadius} 0 0 1 ${x2} ${y2} L ${x3} ${y3} A ${innerRadius} ${innerRadius} 0 0 0 ${x4} ${y4} Z`
  }

  return (
    <div className="w-full h-full flex flex-col items-center justify-center bg-[#111827] p-4">
      <svg width="160" height="160" viewBox="0 0 160 160">
        {metrics.map((m, i) => {
          const startAngle = i * sliceAngle - Math.PI / 2
          const endAngle = (i + 1) * sliceAngle - Math.PI / 2
          const midAngle = (startAngle + endAngle) / 2
          const textX = cx + (outerRadius - 15) * Math.cos(midAngle)
          const textY = cy + (outerRadius - 15) * Math.sin(midAngle)
          return (
            <g key={m.label}>
              <path d={createArc(startAngle, endAngle)} fill={m.color} opacity={0.85} />
              <text x={textX} y={textY - 2} textAnchor="middle" fill="white" fontSize="9" fontWeight="600">
                {m.value}
              </text>
              <text x={textX} y={textY + 7} textAnchor="middle" fill="white" fontSize="7" opacity="0.8">
                {m.unit}
              </text>
            </g>
          )
        })}
        {/* center hole */}
        <circle cx={cx} cy={cy} r={innerRadius - 2} fill="#111827" />
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap gap-x-3 gap-y-1 justify-center mt-3">
        {metrics.map(m => (
          <div key={m.label} className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: m.color }} />
            <span className="text-[#9ca3af] text-xs">{m.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
