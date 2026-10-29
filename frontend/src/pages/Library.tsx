import { Link, useNavigate } from 'react-router-dom'
import { GameArt } from '../components/GameArt'
import { GAMES, useSession, type GameId } from '../lib/store'

const INFO: Record<GameId, { ai: string[]; rule: string; players: string; origin: string }> = {
  football: { ai: ['Ball + player tracking', 'Goal-zone detection', 'Possession time → MVP'], rule: 'Goal +1 · golden-goal tie-break', players: '2 teams of 1–3 players', origin: 'The required classic, judged by computer vision' },
  falaj: { ai: ['Printed-marker tile recognition', 'Graph reconstruction', 'Water-route validation'], rule: 'Farm +3 · leak −1 · speed bonus up to +2', players: '2 teams, 90-second rounds', origin: 'Inspired by the UAE falaj irrigation system' },
  souq: { ai: ['Product-card recognition', 'Speech transcription (AR/EN)', 'Audio ↔ video agreement + budget maths'], rule: 'Item +2 · spoken match +1 · over budget −2', players: 'Individual, one mission each', origin: 'Inspired by UAE souq shopping with a limited budget' },
}

export default function Library() {
  const { s, set, record } = useSession()
  const nav = useNavigate()
  const pick = (g: GameId) => { set({ game: g }); record('game_selected', { game: g }); nav('/prepare') }
  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 py-10">
      <p className="label">Game library</p>
      <h1 className="text-4xl mt-1 mb-2">Choose today's game</h1>
      <p className="text-charcoal/75 mb-8 max-w-2xl">{s.family ? `${s.family}, ` : ''}families pick the fun; the AI referee watches, listens and keeps score. Each game exercises a different AI skill.{!s.ready && <> <Link className="underline text-teal font-semibold" to="/setup">Register your family</Link> first for named scoreboards.</>}</p>
      <div className="grid lg:grid-cols-3 gap-6">
        {(Object.keys(GAMES) as GameId[]).map((g, i) => (
          <article key={g} className="card overflow-hidden flex flex-col rise" style={{ animationDelay: `${i * 90}ms` }}>
            <div className="relative"><GameArt game={g} className="w-full h-52" /><span className="absolute top-3 left-3 rounded-full bg-ivory text-navy text-xs font-bold px-3 py-1">{GAMES[g].mode} game</span><span className="absolute top-3 right-3 display text-ivory text-lg" dir="rtl">{GAMES[g].ar}</span></div>
            <div className="p-6 flex-1 flex flex-col">
              <h2 className="text-2xl">{GAMES[g].name}</h2>
              <p className="text-sm text-charcoal/70 mt-1">{INFO[g].origin}</p>
              <p className="label mt-5">AI judges</p>
              <ul className="mt-2 space-y-1.5 text-sm">{INFO[g].ai.map((a) => <li key={a} className="flex gap-2"><span className="text-teal">◆</span>{a}</li>)}</ul>
              <dl className="mt-5 text-sm grid grid-cols-[auto_1fr] gap-x-3 gap-y-1"><dt className="font-semibold text-navy">Scoring</dt><dd>{INFO[g].rule}</dd><dt className="font-semibold text-navy">Play</dt><dd>{INFO[g].players}</dd></dl>
              <button className="btn btn-primary mt-6 w-full" onClick={() => pick(g)}>Play {GAMES[g].name} →</button>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
