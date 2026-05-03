import type { CWASnapshot } from '../hooks/useCWAData'

interface Props {
  snapshot: CWASnapshot | null
  driftSpeed: number | null
}

interface Slice {
  label: string
  value: string
  unit: string
  color: string
}

function buildSlices(snapshot: CWASnapshot | null, driftSpeed: number | null): Slice[] {
  const fmt = (v: number | null, d = 1) => v === null ? '--' : v.toFixed(d)
  return [
    { label: '浪高', value: fmt(snapshot?.wave_height ?? null), unit: 'm', color: '#3b82f6' },
    { label: '週期', value: fmt(snapshot?.wave_period ?? null), unit: 's', color: '#6366f1' },
    { label: '風速', value: fmt(snapshot?.wind_speed ?? null), unit: 'm/s', color: '#22c55e' },
    { label: '陣風', value: fmt(snapshot?.gust ?? null), unit: 'm/s', color: '#84cc16' },
    { label: '漂流速', value: fmt(driftSpeed, 2), unit: 'm/s', color: '#facc15' },
  ]
}

// Draw a single arc path for a pie slice
function slicePath(cx: number, cy: number, r: number, startAngle: number, endAngle: number): string {
  const toRad = (a: number) => (a - 90) * (Math.PI / 180)
  const x1 = cx + r * Math.cos(toRad(startAngle))
  const y1 = cy + r * Math.sin(toRad(startAngle))
  const x2 = cx + r * Math.cos(toRad(endAngle))
  const y2 = cy + r * Math.sin(toRad(endAngle))
  const large = endAngle - startAngle > 180 ? 1 : 0
  return `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`
}

export default function PizzaChart({ snapshot, driftSpeed }: Props) {
  const slices = buildSlices(snapshot, driftSpeed)
  const n = slices.length
  const angleEach = 360 / n
  const cx = 80, cy = 80, r = 68, innerR = 34

  return (
    <div className="flex flex-col items-center justify-center w-full h-full gap-1 py-2">
      <svg width={160} height={160} viewBox="0 0 160 160">
        {slices.map((s, i) => {
          const start = i * angleEach
          const end = start + angleEach
          const mid = ((start + end) / 2 - 90) * (Math.PI / 180)
          const labelR = r * 0.65
          const lx = cx + labelR * Math.cos(mid)
          const ly = cy + labelR * Math.sin(mid)
          return (
            <g key={s.label}>
              <path d={slicePath(cx, cy, r, start, end)} fill={s.color} opacity={0.85} />
              {/* inner cut for donut */}
              <path d={slicePath(cx, cy, innerR, start, end)} fill="#111827" />
              {/* value label on slice */}
              <text
                x={lx} y={ly - 4}
                textAnchor="middle" dominantBaseline="middle"
                fontSize="9" fill="white" fontWeight="600"
              >
                {s.value}
              </text>
              <text
                x={lx} y={ly + 6}
                textAnchor="middle" dominantBaseline="middle"
                fontSize="7" fill="white" opacity="0.7"
              >
                {s.unit}
              </text>
            </g>
          )
        })}
        {/* center */}
        <circle cx={cx} cy={cy} r={innerR - 2} fill="#111827" />
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 px-2">
        {slices.map(s => (
          <div key={s.label} className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: s.color }} />
            <span className="text-xs text-gray-300">{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
