import type { Any } from '../lib/api'

const OPEN: Record<string, number[]> = { STRAIGHT: [0, 2], ELBOW: [0, 1], TEE: [0, 1, 2], CROSS: [0, 1, 2, 3] }
const DIR = [[0, -1], [1, 0], [0, 1], [-1, 0]] // N,E,S,W as (dx,dy)
const C = 84

/** Digital twin of the physical Falaj board, rebuilt from AI-detected tiles. Water animates only along
 *  edges the rule engine traced; leaks are marked where the AI saw an unmatched open end. */
export function FalajTwin({ snapshot, layout, animate = true }: { snapshot: Any; layout: Any; animate?: boolean }) {
  const tiles: Any[] = snapshot?.tiles ?? []
  const an: Any = snapshot?.analysis ?? { edges: [], reached_destinations: [], leaks: [], reached_tiles: [] }
  const mid = (r: number, c: number) => [c * C + C / 2, r * C + C / 2]
  const reached = new Set(an.reached_tiles.map((t: number[]) => t.join(',')))
  const size = layout.size * C
  const src = layout.source.cell
  const sideIdx: Record<string, number> = { north: 0, east: 1, south: 2, west: 3 }
  return (
    <svg viewBox={`-30 -10 ${size + 60} ${size + 20}`} className="w-full h-auto" role="img" aria-label="Digital reconstruction of the Falaj board">
      <rect x="-14" y="-10" width={size + 28} height={size + 20} rx="18" fill="#E9DFC9" />
      {Array.from({ length: 25 }, (_, i) => (
        <rect key={i} x={(i % 5) * C + 3} y={Math.floor(i / 5) * C + 3} width={C - 6} height={C - 6} rx="8" fill="#FFFDF8" stroke="#E3DCCD" />
      ))}
      {layout.rocks.map((r: number[]) => { const [x, y] = mid(r[0], r[1]); return <g key={r.join()}><path d={`M${x - 26} ${y + 18} L${x - 14} ${y - 22} L${x + 12} ${y - 26} L${x + 28} ${y + 4} L${x + 16} ${y + 24} Z`} fill="#8A8F98" stroke="#5C6470" strokeWidth="2" /></g> })}
      {tiles.map((t) => {
        const [x, y] = mid(t.cell[0], t.cell[1])
        const on = reached.has(t.cell.join(','))
        const sides = OPEN[t.type].map((s: number) => (s + t.rot) % 4)
        return (
          <g key={t.cell.join()}>
            <rect x={t.cell[1] * C + 3} y={t.cell[0] * C + 3} width={C - 6} height={C - 6} rx="8" fill="#F1E8D4" stroke={on ? '#167E80' : '#C9BFA6'} strokeWidth={on ? 2.5 : 1.5} />
            {sides.map((s: number) => <line key={s} x1={x} y1={y} x2={x + DIR[s][0] * (C / 2 - 3)} y2={y + DIR[s][1] * (C / 2 - 3)} stroke="#A9885A" strokeWidth="14" strokeLinecap="round" />)}
            <circle cx={x} cy={y} r="7" fill="#A9885A" />
          </g>
        )
      })}
      {/* water along traced edges */}
      {an.edges.map((e: Any, i: number) => {
        const [x1, y1] = mid(e.from[0], e.from[1]); const [x2, y2] = mid(e.to[0], e.to[1])
        const len = Math.hypot(x2 - x1, y2 - y1)
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#2FB5B8" strokeWidth="8" strokeLinecap="round"
          strokeDasharray={animate ? len : undefined} strokeDashoffset={animate ? len : undefined}
          style={animate ? { animation: `flow .7s ${0.25 * i}s ease-out forwards` } : undefined} />
      })}
      {/* well */}
      {(() => { const [x, y] = mid(src[0], src[1]); const [dx, dy] = DIR[layout.source.side]; return <g><circle cx={x} cy={y} r="30" fill="#12243A" /><circle cx={x} cy={y} r="22" fill="#167E80" /><text x={x} y={y + 5} textAnchor="middle" fontSize="13" fill="#fff" fontWeight="700">WELL</text><line x1={x} y1={y} x2={x + dx * C / 2} y2={y + dy * C / 2} stroke="#2FB5B8" strokeWidth="8" strokeLinecap="round" /></g> })()}
      {layout.destinations.map((d: number[], i: number) => {
        const [x, y] = mid(d[0], d[1]); const ok = an.reached_destinations.some((r: number[]) => r[0] === d[0] && r[1] === d[1])
        return <g key={i}><circle cx={x} cy={y} r="31" fill={ok ? '#C6A36B' : '#EFE6D2'} stroke={ok ? '#12243A' : '#B92D39'} strokeWidth="3" strokeDasharray={ok ? undefined : '5 4'} />
          <path d={`M${x} ${y + 14} V${y - 4} M${x} ${y - 4} q-12 -2 -14 -12 M${x} ${y - 4} q12 -2 14 -12 M${x} ${y + 2} q-10 0 -12 -8 M${x} ${y + 2} q10 0 12 -8`} stroke={ok ? '#12243A' : '#8A8F98'} strokeWidth="3" fill="none" strokeLinecap="round" />
          <text x={x} y={y + 46} textAnchor="middle" fontSize="11" fontWeight="700" fill={ok ? '#167E80' : '#B92D39'}>{ok ? 'WATERED +3' : 'DRY'}</text></g>
      })}
      {an.leaks.map((l: Any, i: number) => {
        const [x, y] = mid(l.cell[0], l.cell[1]); const [dx, dy] = DIR[sideIdx[l.side]]
        return <g key={i}><circle cx={x + dx * C / 2} cy={y + dy * C / 2} r="11" fill="#B92D39" /><text x={x + dx * C / 2} y={y + dy * C / 2 + 4} textAnchor="middle" fontSize="12" fill="#fff" fontWeight="700">−1</text></g>
      })}
    </svg>
  )
}
