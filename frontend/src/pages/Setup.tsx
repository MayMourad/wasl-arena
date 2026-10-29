import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSession } from '../lib/store'

const COLORS = ['red', 'blue', 'purple', 'orange', 'teal', 'white']
const SW: Record<string, string> = { red: '#C0262F', blue: '#2447C8', purple: '#7B3FA0', orange: '#E07A1F', teal: '#167E80', white: '#EDEDED', yellow: '#E8CF1B' }
const STEPS = ['Family & language', 'Players', 'Teams', 'Match setup']

export default function Setup() {
  const { s, set, setSettings, record, loadDemo } = useSession()
  const nav = useNavigate()
  const [step, setStep] = useState(0)
  const named = s.players.filter((p) => p.name.trim())

  const toggleTeam = (pid: string, team: 'A' | 'B') => {
    const other = team === 'A' ? 'B' : 'A'
    const t = { ...s.teams }
    t[team] = { ...t[team], playerIds: t[team].playerIds.includes(pid) ? t[team].playerIds.filter((x) => x !== pid) : [...t[team].playerIds, pid] }
    t[other] = { ...t[other], playerIds: t[other].playerIds.filter((x) => x !== pid) }
    set({ teams: t })
  }
  const next = () => (step < 3 ? setStep(step + 1) : finish())
  const finish = () => { set({ ready: true }); record('family_registered', { players: named.map((p) => p.name), teams: { A: s.teams.A.playerIds, B: s.teams.B.playerIds }, settings: s.settings }); nav('/games') }
  const canNext = step === 0 ? s.family.trim().length > 1 : step === 1 ? named.length >= 2 : step === 2 ? s.teams.A.playerIds.length > 0 && s.teams.B.playerIds.length > 0 : true

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 py-10">
      <p className="label">Family setup</p>
      <h1 className="text-4xl mt-1 mb-6">Welcome to Game Day</h1>
      <ol className="flex gap-2 mb-8 overflow-x-auto" aria-label="Progress">
        {STEPS.map((t, i) => (
          <li key={t}><button onClick={() => i <= step && setStep(i)} className={`rounded-full px-4 py-2 text-sm font-semibold whitespace-nowrap transition ${i === step ? 'bg-navy text-white' : i < step ? 'bg-teal/15 text-teal' : 'bg-white border border-line text-charcoal/50'}`}>{i < step ? '✓ ' : `${i + 1}. `}{t}</button></li>
        ))}
      </ol>

      <div className="card p-6 sm:p-8 rise" key={step}>
        {step === 0 && (
          <div className="grid sm:grid-cols-2 gap-6">
            <div><label className="label" htmlFor="fam">Family name</label><input id="fam" className="input mt-2" placeholder="e.g. Al Mansoori Family" value={s.family} onChange={(e) => set({ family: e.target.value })} /></div>
            <div><span className="label">Language</span>
              <div className="mt-2 flex gap-2">{(['en', 'ar'] as const).map((l) => <button key={l} onClick={() => set({ lang: l })} className={`btn flex-1 ${s.lang === l ? 'btn-primary' : 'btn-ghost'}`}>{l === 'en' ? 'English' : 'العربية'}</button>)}</div>
              <p className="text-sm text-charcoal/60 mt-2">Arabic switches the interface to right-to-left. Product cards are bilingual and speech judging accepts Arabic and English.</p></div>
            <div className="sm:col-span-2 text-sm bg-ivory rounded-xl p-4 border border-line">Need a quick look first? <button className="underline font-semibold text-teal" onClick={async () => { await loadDemo(); nav('/cup') }}>Load a demo session</button> built from synthetic test fixtures (clearly labelled).</div>
          </div>
        )}
        {step === 1 && (
          <div>
            <p className="mb-4 text-charcoal/80">Register at least two players (up to six). Football MVP and Souq Signal scores are attributed to these names.</p>
            <div className="grid sm:grid-cols-2 gap-3">
              {s.players.map((p, i) => (
                <div key={p.id} className="flex gap-2"><span className="mono grid place-items-center w-12 rounded-xl bg-ivory border border-line text-sm">P{i + 1}</span>
                  <input className="input" aria-label={`Player ${i + 1} name`} placeholder={`Player ${i + 1} name`} value={p.name} onChange={(e) => set({ players: s.players.map((q) => (q.id === p.id ? { ...q, name: e.target.value } : q)) })} />
                  {s.players.length > 2 && <button className="btn btn-ghost !px-3" aria-label="Remove player" onClick={() => set({ players: s.players.filter((q) => q.id !== p.id) })}>✕</button>}</div>
              ))}
            </div>
            {s.players.length < 6 && <button className="btn btn-ghost mt-4" onClick={() => set({ players: [...s.players, { id: 'p' + (Math.max(...s.players.map((p) => +p.id.slice(1))) + 1), name: '' }] })}>+ Add player</button>}
          </div>
        )}
        {step === 2 && (
          <div className="grid md:grid-cols-2 gap-6">
            {(['A', 'B'] as const).map((tid) => (
              <div key={tid} className="rounded-2xl border border-line p-4">
                <label className="label" htmlFor={`tn${tid}`}>Team {tid} name</label>
                <input id={`tn${tid}`} className="input mt-2" value={s.teams[tid].name} onChange={(e) => set({ teams: { ...s.teams, [tid]: { ...s.teams[tid], name: e.target.value } } })} />
                <span className="label block mt-4">Shirt colour</span>
                <div className="flex gap-2 mt-2 flex-wrap">{COLORS.filter((c) => c !== s.teams[tid === 'A' ? 'B' : 'A'].color).map((c) => (
                  <button key={c} aria-label={c} aria-pressed={s.teams[tid].color === c} onClick={() => { set({ teams: { ...s.teams, [tid]: { ...s.teams[tid], color: c } } }); setSettings({ teamColors: { ...s.settings.teamColors, [tid]: c } }) }}
                    className={`size-9 rounded-full border-2 ${s.teams[tid].color === c ? 'border-navy scale-110' : 'border-line'}`} style={{ background: SW[c] }} />))}</div>
                <span className="label block mt-4">Players</span>
                <div className="flex gap-2 mt-2 flex-wrap">{named.map((p) => (
                  <button key={p.id} onClick={() => toggleTeam(p.id, tid)} aria-pressed={s.teams[tid].playerIds.includes(p.id)} className={`btn !py-1.5 !text-sm ${s.teams[tid].playerIds.includes(p.id) ? 'btn-teal' : 'btn-ghost'}`}>{p.name}</button>))}</div>
              </div>
            ))}
            <p className="md:col-span-2 text-sm text-charcoal/70">Team games (Football AI, Falaj Flow) use these teams. Souq Signal is individual: each player takes a turn.</p>
          </div>
        )}
        {step === 3 && (
          <div className="grid sm:grid-cols-2 gap-6">
            {([['rounds', 'Rounds per game', 1, 5, 1], ['roundSeconds', 'Falaj round (seconds)', 30, 180, 15], ['footballSeconds', 'Football match (seconds)', 30, 600, 30], ['goldenGoalSeconds', 'Tie-break golden goal (seconds)', 15, 180, 15]] as const).map(([k, l, mn, mx, st]) => (
              <div key={k}><label className="label" htmlFor={k}>{l}</label>
                <div className="flex items-center gap-3 mt-2"><input id={k} type="range" min={mn} max={mx} step={st} value={s.settings[k]} onChange={(e) => setSettings({ [k]: +e.target.value })} className="flex-1 accent-teal" /><span className="mono w-12 text-right">{s.settings[k]}</span></div></div>
            ))}
            <div className="sm:col-span-2 rounded-xl bg-ivory border border-line p-4 text-sm"><b>Tie rule:</b> if a team game ends level, a golden-goal extension decides it; if nobody scores, the host records a draw. Falaj ties are broken by shortest valid network, then time. Souq ties by lower spend, then time.</div>
          </div>
        )}
      </div>
      <div className="flex justify-between mt-6">
        <button className="btn btn-ghost" disabled={step === 0} onClick={() => setStep(step - 1)}>← Back</button>
        <button className="btn btn-primary" disabled={!canNext} onClick={next}>{step === 3 ? 'Save & choose a game →' : 'Continue →'}</button>
      </div>
    </div>
  )
}
