import { useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { GAMES, useSession, type GameId, type Result } from '../lib/store'

const SCALE = [3, 2, 1]

export default function Cup() {
  const { s, reset, loadDemo, nameOf } = useSession()
  useEffect(() => { if (new URLSearchParams(window.location.search).get('demo') && s.results.length === 0) void loadDemo() }, [])
  const has = s.results.length > 0
  const demo = s.results.some((r) => r.sample)
  const by = (g: GameId) => s.results.filter((r) => r.game === g)

  const standings = useMemo(() => {
    const pts: Record<string, { name: string; pts: number; why: string[] }> = {}
    const add = (pid: string, p: number, why: string) => { pts[pid] ??= { name: nameOf(pid), pts: 0, why: [] }; pts[pid].pts += p; pts[pid].why.push(`${why} +${p}`) }
    const teamScores = (g: GameId) => (['A', 'B'] as const).map((t) => ({ t, sc: by(g).filter((r) => r.subject === t).reduce((a, r) => a + r.score, 0), n: by(g).filter((r) => r.subject === t).length }))
    for (const g of ['football', 'falaj'] as const) {
      const ts = teamScores(g); if (!ts.every((x) => x.n > 0)) continue
      const [a, b] = ts
      for (const x of ts) {
        const win = a.sc !== b.sc && x.sc === Math.max(a.sc, b.sc)
        const p = a.sc === b.sc ? 1 : win ? 3 : 0
        if (p) s.teams[x.t].playerIds.forEach((pid) => add(pid, p, `${GAMES[g].name} ${a.sc === b.sc ? 'draw' : 'win'}`))
      }
    }
    const mvp = by('football').find((r) => r.mvp)?.mvp
    if (mvp) { const pl = s.players.find((p) => p.name === mvp); if (pl) add(pl.id, 1, 'Football MVP') }
    const souq = [...new Set(by('souq').map((r) => r.subject))].map((sub) => ({ sub, sc: by('souq').filter((r) => r.subject === sub).reduce((a, r) => a + r.score, 0) })).sort((x, y) => y.sc - x.sc)
    souq.forEach((x, i) => { if (SCALE[i]) add(x.sub, SCALE[i], `Souq Signal #${i + 1}`) })
    return Object.entries(pts).map(([id, v]) => ({ id, ...v })).sort((a, b) => b.pts - a.pts)
  }, [s.results, s.teams, s.players])

  const exportJson = () => {
    const blob = new Blob([JSON.stringify({ family: s.family, exported_at: new Date().toISOString(), results: s.results, standings, audit: s.log }, null, 1)], { type: 'application/json' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'family-cup-results.json'; a.click()
  }
  const rows = (g: GameId) => by(g)
  const label = (r: Result) => `${r.subjectLabel}${r.round > 1 || g2(r) ? ` · R${r.round}` : ''}`
  const g2 = (r: Result) => r.game !== 'football'

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
        <div><p className="label">Family Cup</p><h1 className="text-4xl mt-1">{s.family || 'Your family'}'s results</h1></div>
        <div className="flex gap-2 flex-wrap no-print"><Link to="/games" className="btn btn-primary">Play another game</Link><button className="btn btn-ghost" onClick={exportJson} disabled={!has}>Export JSON</button><button className="btn btn-ghost" onClick={() => window.print()} disabled={!has}>Print</button></div>
      </div>

      {demo && <p className="mb-6 rounded-xl bg-gold/20 border border-gold px-4 py-3 text-sm"><b>Demo data.</b> These results come from synthetic test fixtures processed by the real pipelines. They are not family gameplay.</p>}

      {!has ? (
        <div className="card p-10 text-center"><h2 className="text-2xl mb-2">No verified results yet</h2><p className="text-charcoal/75 mb-6 max-w-lg mx-auto">Results appear here after you judge a clip in the Live Arena and apply the verified result. Nothing is pre-filled.</p>
          <div className="flex gap-3 justify-center flex-wrap"><Link to="/games" className="btn btn-primary">Choose a game</Link><button className="btn btn-ghost" onClick={() => void loadDemo()}>Load demo session</button></div></div>
      ) : (
        <>
          <section className="card p-6 mb-6 bg-navy !border-navy">
            <p className="label !text-gold">Champion</p>
            <div className="flex flex-wrap items-end gap-x-8 gap-y-2 mt-1"><div className="display text-5xl text-ivory">{standings[0]?.name ?? '—'}</div><div className="text-white/75">{standings[0] ? `${standings[0].pts} cup points · ${standings[0].why.join(', ')}` : 'Play more games to decide the cup.'}</div></div>
          </section>

          <div className="grid lg:grid-cols-[1fr_1.2fr] gap-6">
            <section className="card p-6"><h2 className="text-xl mb-4">Standings</h2>
              <ol className="space-y-2">{standings.map((p, i) => { const max = standings[0].pts || 1; return (
                <li key={p.id} className="rounded-xl bg-ivory px-4 py-3"><div className="flex items-center gap-3"><span className="display text-2xl w-7 text-gold">{i + 1}</span><span className="flex-1 font-semibold text-navy">{p.name}</span><span className="display text-2xl text-navy">{p.pts}</span></div>
                  <div className="h-1.5 rounded-full bg-line mt-2"><div className="h-full rounded-full bg-teal" style={{ width: `${(p.pts / max) * 100}%` }} /></div><p className="text-xs text-charcoal/65 mt-1.5">{p.why.join(' · ')}</p></li>) })}</ol>
              <p className="text-xs text-charcoal/60 mt-4">Cup points: team-game win 3, draw 1 · Souq Signal 1st/2nd/3rd = 3/2/1 · Football MVP +1.</p></section>

            <div className="space-y-6">
              {(Object.keys(GAMES) as GameId[]).map((g) => (
                <section key={g} className="card p-6"><div className="flex justify-between items-center mb-3"><h2 className="text-xl">{GAMES[g].name}</h2><span className="text-xs rounded-full bg-ivory border border-line px-2.5 py-1">{GAMES[g].mode}</span></div>
                  {rows(g).length === 0 ? <p className="text-sm text-charcoal/60">Not played yet. <Link className="underline text-teal font-semibold" to="/games">Play it</Link></p> :
                    <table className="w-full text-sm"><tbody>{rows(g).map((r) => <tr key={r.id} className="border-t border-line first:border-0"><td className="py-2 font-medium">{label(r)}</td><td className="py-2 text-charcoal/70">{r.detail}</td><td className="py-2 text-right display text-xl">{r.score}</td><td className="py-2 pl-3 text-right"><Link to={`/replay?report=${r.reportId}`} className="text-teal underline text-xs">Replay</Link>{!r.verified && <span className="ml-2 text-[10px] font-bold text-[#7a5a1c]">REVIEW PENDING</span>}</td></tr>)}</tbody></table>}
                  {g === 'football' && rows(g)[0]?.mvp && <p className="mt-3 text-sm rounded-xl bg-ivory px-3 py-2"><b>MVP:</b> {rows(g)[0].mvp} · longest verified possession</p>}
                </section>))}
            </div>
          </div>
          <div className="mt-8 no-print"><button className="btn btn-ghost" onClick={() => { if (confirm('Clear this session and its results?')) reset() }}>Start a new family session</button></div>
        </>
      )}
    </div>
  )
}
