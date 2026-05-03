import { useEffect, useRef, useState, useCallback } from 'react'
import p5 from 'p5'
import L from 'leaflet'
import type { Spot } from '../data/spots'
import type { CWASnapshot } from '../hooks/useCWAData'

interface Props {
  spot: Spot
  map: L.Map
  snapshot: CWASnapshot | null
  showParticles: boolean
  onDotMoved?: (lat: number, lng: number, speed: number, dirDeg: number) => void
  trajectoryPoints?: { lat: number; lng: number }[]
}

const MAX_PARTICLES = 50

function degToRad(d: number) { return (d * Math.PI) / 180 }

function latlngToPixel(map: L.Map, lat: number, lng: number): [number, number] {
  const pt = map.latLngToContainerPoint(L.latLng(lat, lng))
  return [pt.x, pt.y]
}

function pixelToLatlng(map: L.Map, x: number, y: number): [number, number] {
  const ll = map.containerPointToLatLng(L.point(x, y))
  return [ll.lat, ll.lng]
}

// Vector sum: array of [speed_ms, direction_deg_from_north] → {speed, dirDeg, vx, vy}
function vectorSum(forces: [number, number][]) {
  const vx = forces.reduce((s, [sp, d]) => s + sp * Math.sin(degToRad(d)), 0)
  const vy = forces.reduce((s, [sp, d]) => s + sp * Math.cos(degToRad(d)), 0)
  const speed = Math.hypot(vx, vy)
  const dirDeg = ((Math.atan2(vx, vy) * 180) / Math.PI + 360) % 360
  return { speed, dirDeg, vx, vy }
}

// Reflect velocity against a line segment edge normal
function reflectVelocity(vx: number, vy: number, ex: number, ey: number): [number, number] {
  const len = Math.hypot(ex, ey)
  if (len === 0) return [vx, vy]
  const nx = -ey / len
  const ny = ex / len
  const dot = vx * nx + vy * ny
  return [vx - 2 * dot * nx, vy - 2 * dot * ny]
}

// Check if point (px,py) is near segment (ax,ay)→(bx,by), return t∈[0,1] or null
function segmentProximity(px: number, py: number, ax: number, ay: number, bx: number, by: number, threshold: number): boolean {
  const dx = bx - ax, dy = by - ay
  const lenSq = dx * dx + dy * dy
  if (lenSq === 0) return Math.hypot(px - ax, py - ay) < threshold
  const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / lenSq))
  const cx = ax + t * dx, cy = ay + t * dy
  return Math.hypot(px - cx, py - cy) < threshold
}

export default function DriftCanvas({ spot, map, snapshot, showParticles, onDotMoved, trajectoryPoints }: Props) {
  const canvasRef = useRef<HTMLDivElement>(null)
  const p5Ref = useRef<p5 | null>(null)
  const dotPosRef = useRef<[number, number]>([spot.refLat, spot.refLng])
  const isDraggingRef = useRef(false)
  const [dotScreen, setDotScreen] = useState<[number, number]>([0, 0])

  const getForces = useCallback((): [number, number][] => {
    if (!snapshot) return []
    const wh = snapshot.wave_height ?? 0
    const wd = snapshot.wave_direction ?? 0
    const ws = snapshot.wind_speed ?? 0
    const wdir = snapshot.wind_direction ?? 0
    return [
      [wh * 0.8, wd],
      [wh * 0.3, (wd + 30) % 360],
      [ws * 0.03, wdir],
    ]
  }, [snapshot])

  // Sync dot screen position on map move/zoom
  useEffect(() => {
    const sync = () => {
      const [lat, lng] = dotPosRef.current
      setDotScreen(latlngToPixel(map, lat, lng))
    }
    sync()
    map.on('move zoom', sync)
    return () => { map.off('move zoom', sync) }
  }, [map])

  // p5 particle flow field
  useEffect(() => {
    if (!canvasRef.current) return

    const sketch = (p: p5) => {
      interface Particle { lat: number; lng: number; age: number }
      const particles: Particle[] = []

      const spawnParticle = (): Particle => {
        const [swLat, swLng, neLat, neLng] = spot.bounds
        return {
          lat: swLat + Math.random() * (neLat - swLat),
          lng: swLng + Math.random() * (neLng - swLng),
          age: Math.random() * 200,
        }
      }

      p.setup = () => {
        const parent = canvasRef.current!
        p.createCanvas(parent.offsetWidth, parent.offsetHeight)
        p.clear()
        for (let i = 0; i < MAX_PARTICLES; i++) particles.push(spawnParticle())
      }

      p.draw = () => {
        p.clear()
        if (!showParticles) return

        const forces = getForces()
        if (!forces.length) return
        const { vx, vy, speed } = vectorSum(forces)
        if (speed === 0) return

        // pixels per second at current zoom (approx via latLngToLayerPoint delta)
        const pt0 = map.latLngToContainerPoint(L.latLng(spot.refLat, spot.refLng))
        const pt1 = map.latLngToContainerPoint(L.latLng(spot.refLat + 0.001, spot.refLng))
        const pixPerDeg = Math.abs(pt1.y - pt0.y) / 0.001
        const degPerMeter = 1 / 111_000
        const pixPerMeter = pixPerDeg * degPerMeter
        const pxVx = vx * pixPerMeter * 60  // scale for visibility
        const pxVy = -vy * pixPerMeter * 60 // invert y for screen

        const coastPixels = spot.coastline.map(c => latlngToPixel(map, c.lat, c.lng))

        for (const particle of particles) {
          particle.age++
          if (particle.age > 300) {
            Object.assign(particle, spawnParticle())
            continue
          }

          let [px, py] = latlngToPixel(map, particle.lat, particle.lng)
          let curVx = pxVx, curVy = pxVy

          // Boundary collision
          for (let i = 0; i < coastPixels.length - 1; i++) {
            const [ax, ay] = coastPixels[i]
            const [bx, by] = coastPixels[i + 1]
            if (segmentProximity(px, py, ax, ay, bx, by, 6)) {
              ;[curVx, curVy] = reflectVelocity(curVx, curVy, bx - ax, by - ay)
            }
          }

          px += curVx
          py += curVy

          // Fade by age
          const alpha = p.map(particle.age, 0, 300, 200, 0)
          p.stroke(100, 200, 255, alpha)
          p.strokeWeight(1.5)
          p.noFill()
          const [ox, oy] = latlngToPixel(map, particle.lat, particle.lng)
          p.line(ox, oy, px, py)

          // Update geographic position
          const [newLat, newLng] = pixelToLatlng(map, px, py)
          particle.lat = newLat
          particle.lng = newLng
        }

        // Draw coastline
        if (coastPixels.length > 1) {
          p.stroke(255, 255, 255, 80)
          p.strokeWeight(1)
          p.noFill()
          p.beginShape()
          coastPixels.forEach(([cx, cy]) => p.vertex(cx, cy))
          p.endShape()
        }
      }

      p.windowResized = () => {
        if (canvasRef.current) p.resizeCanvas(canvasRef.current.offsetWidth, canvasRef.current.offsetHeight)
      }
    }

    p5Ref.current = new p5(sketch, canvasRef.current)
    return () => { p5Ref.current?.remove(); p5Ref.current = null }
  }, [spot, map, showParticles, getForces])

  // Draggable dot handlers
  const handleDotPointerDown = (e: React.PointerEvent) => {
    e.stopPropagation()
    isDraggingRef.current = true
    map.dragging.disable()
  }

  const handlePointerMove = useCallback((e: PointerEvent) => {
    if (!isDraggingRef.current) return
    const rect = (canvasRef.current?.parentElement ?? document.body).getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const [lat, lng] = pixelToLatlng(map, x, y)
    dotPosRef.current = [lat, lng]
    setDotScreen([x, y])

    const forces = getForces()
    const { speed, dirDeg } = forces.length ? vectorSum(forces) : { speed: 0, dirDeg: 0 }
    onDotMoved?.(lat, lng, speed, dirDeg)
  }, [map, getForces, onDotMoved])

  const handlePointerUp = useCallback(() => {
    isDraggingRef.current = false
    map.dragging.enable()
  }, [map])

  useEffect(() => {
    window.addEventListener('pointermove', handlePointerMove)
    window.addEventListener('pointerup', handlePointerUp)
    return () => {
      window.removeEventListener('pointermove', handlePointerMove)
      window.removeEventListener('pointerup', handlePointerUp)
    }
  }, [handlePointerMove, handlePointerUp])

  const forces = getForces()
  const { speed, dirDeg } = forces.length ? vectorSum(forces) : { speed: 0, dirDeg: 0 }
  const arrowLen = 28
  const arrowRad = degToRad(dirDeg)
  const ax = dotScreen[0] + arrowLen * Math.sin(arrowRad)
  const ay = dotScreen[1] - arrowLen * Math.cos(arrowRad)

  return (
    <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 400 }}>
      {/* p5 canvas layer */}
      <div ref={canvasRef} className="absolute inset-0" />

      {/* Trajectory polyline */}
      {trajectoryPoints && trajectoryPoints.length > 1 && (
        <svg className="absolute inset-0 w-full h-full overflow-visible">
          <polyline
            points={trajectoryPoints.map(p => latlngToPixel(map, p.lat, p.lng).join(',')).join(' ')}
            fill="none"
            stroke="#facc15"
            strokeWidth="2"
            strokeDasharray="4 3"
            opacity="0.8"
          />
        </svg>
      )}

      {/* Static arrow */}
      <svg className="absolute inset-0 w-full h-full overflow-visible pointer-events-none">
        {speed > 0 && (
          <>
            <line
              x1={dotScreen[0]} y1={dotScreen[1]}
              x2={ax} y2={ay}
              stroke="#facc15" strokeWidth="2"
            />
            <polygon
              points={`${ax},${ay} ${ax - 5 * Math.cos(arrowRad - 0.5)},${ay + 5 * Math.sin(arrowRad - 0.5)} ${ax - 5 * Math.cos(arrowRad + 0.5)},${ay + 5 * Math.sin(arrowRad + 0.5)}`}
              fill="#facc15"
            />
            <text
              x={ax + 8} y={ay}
              fill="#facc15" fontSize="11" fontFamily="system-ui" dominantBaseline="middle"
            >
              {speed.toFixed(1)} m/s
            </text>
          </>
        )}
      </svg>

      {/* Draggable yellow dot */}
      <div
        className="absolute w-4 h-4 rounded-full bg-yellow-400 border-2 border-white shadow-lg cursor-grab active:cursor-grabbing pointer-events-auto"
        style={{
          left: dotScreen[0] - 8,
          top: dotScreen[1] - 8,
          zIndex: 500,
          touchAction: 'none',
        }}
        onPointerDown={handleDotPointerDown}
      />
    </div>
  )
}
