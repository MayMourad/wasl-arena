import type { GameId } from '../lib/store'

/** Original vector art for the three game cards (no third-party assets). */
export function GameArt({ game, className = '' }: { game: GameId; className?: string }) {
  if (game === 'football')
    return (
      <svg viewBox="0 0 400 240" className={className} role="img" aria-label="Football pitch with tracked ball path">
        <rect width="400" height="240" fill="#167E80" /><rect width="400" height="240" fill="url(#g1)" />
        <defs><linearGradient id="g1" x1="0" x2="1"><stop offset="0" stopColor="#0f5f61" /><stop offset="1" stopColor="#1b9294" /></linearGradient></defs>
        {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => <rect key={i} x={i * 50} width="25" height="240" fill="#fff" opacity=".05" />)}
        <g stroke="#F7F3EB" strokeWidth="2.5" fill="none" opacity=".85"><rect x="14" y="14" width="372" height="212" rx="4" /><line x1="200" y1="14" x2="200" y2="226" /><circle cx="200" cy="120" r="36" /><rect x="14" y="76" width="44" height="88" /><rect x="342" y="76" width="44" height="88" /></g>
        <path d="M70 168 C140 110 220 190 330 118" stroke="#C6A36B" strokeWidth="3" strokeDasharray="7 7" fill="none" />
        <g fill="#B92D39"><rect x="96" y="150" width="14" height="24" rx="4" /><rect x="168" y="96" width="14" height="24" rx="4" /></g>
        <g fill="#12243A"><rect x="262" y="142" width="14" height="24" rx="4" /><rect x="236" y="70" width="14" height="24" rx="4" /></g>
        <rect x="90" y="142" width="26" height="38" fill="none" stroke="#C6A36B" strokeWidth="2" /><circle cx="330" cy="118" r="9" fill="#F7F3EB" stroke="#C6A36B" strokeWidth="3" />
        <text x="92" y="136" fontSize="11" fill="#F7F3EB" fontWeight="700">A1</text>
      </svg>
    )
  if (game === 'falaj')
    return (
      <svg viewBox="0 0 400 240" className={className} role="img" aria-label="Falaj irrigation channel network">
        <rect width="400" height="240" fill="#12243A" />
        <g stroke="#C6A36B" strokeOpacity=".18">{[0, 1, 2, 3, 4, 5].map((i) => <g key={i}><line x1={50 + i * 60} y1="20" x2={50 + i * 60} y2="220" /><line x1="50" y1={20 + i * 40} x2="350" y2={20 + i * 40} /></g>)}</g>
        <path d="M30 120 H110 V60 H230 V120 H350 M110 120 V180 H230 V120 M230 60 H350" stroke="#2FB5B8" strokeWidth="11" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        <path d="M30 120 H110 V60 H230 V120 H350" stroke="#9FE8EA" strokeWidth="3" strokeDasharray="4 12" fill="none"><animate attributeName="stroke-dashoffset" from="64" to="0" dur="2s" repeatCount="indefinite" /></path>
        <circle cx="30" cy="120" r="16" fill="#F7F3EB" /><text x="30" y="124" textAnchor="middle" fontSize="9" fontWeight="700" fill="#12243A">WELL</text>
        {[[350, 60], [350, 120], [350, 180]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r="14" fill="#C6A36B" />)}
        <rect x="190" y="150" width="30" height="26" rx="6" fill="#5C6470" />
      </svg>
    )
  return (
    <svg viewBox="0 0 400 240" className={className} role="img" aria-label="Souq market arches with product cards">
      <rect width="400" height="240" fill="#B92D39" /><rect width="400" height="240" fill="url(#g3)" />
      <defs><linearGradient id="g3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#8f1f2b" /><stop offset="1" stopColor="#c8404b" /></linearGradient></defs>
      <g fill="none" stroke="#C6A36B" strokeWidth="3" opacity=".85">{[0, 1, 2, 3].map((i) => <path key={i} d={`M${20 + i * 96} 120 V60 Q${68 + i * 96} 4 ${116 + i * 96} 60 V120`} />)}</g>
      {[0, 1, 2].map((i) => (
        <g key={i} transform={`translate(${52 + i * 108} ${112}) rotate(${(i - 1) * 6})`}>
          <rect width="86" height="108" rx="10" fill="#F7F3EB" /><rect x="14" y="14" width="58" height="58" rx="4" fill="#12243A" />
          <g fill="#F7F3EB">{[0, 1, 2, 3, 4].map((a) => [0, 1, 2, 3, 4].map((b) => ((a * 3 + b * 5 + i) % 3 === 0 ? <rect key={a + '-' + b} x={20 + a * 10} y={20 + b * 10} width="8" height="8" /> : null)))}</g>
          <text x="43" y="96" textAnchor="middle" fontSize="11" fontWeight="700" fill="#12243A">{['Dates', 'Coffee', 'Oud'][i]}</text>
        </g>
      ))}
      <path d="M200 20 V40 M188 20 H212" stroke="#C6A36B" strokeWidth="3" /><path d="M190 40 h20 l-4 18 h-12z" fill="#C6A36B" />
    </svg>
  )
}
