import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { GameArt } from '../components/GameArt'
import { COLOR_SWATCH, PRODUCTS, RULES } from '../lib/catalog'
import { GAMES, useSession, type GameId } from '../lib/store'

const EQUIP: Record<GameId, string[]> = {
  football: ['Phone/laptop on a stable stand at a high angle, whole pitch in frame', 'One brightly coloured ball (yellow or orange works best)', 'Two goals marked on the ground (cones, tape or mini-goals)', 'Contrasting shirts for the two teams (numbers optional)', 'Even daylight, no strong shadows over the goals'],
  falaj: ['Printed Falaj board (5×5) with the four corner markers visible', 'Printed tile sheet cut into 16 tiles (straight, elbow, tee, cross)', 'Camera looking down at the board, all four corner markers in view', 'Round timer visible to the host', 'Hands out of frame at the final whistle'],
  souq: ['Printed Souq product cards (8 products × 2 copies)', 'Camera and microphone facing the player', 'Quiet room so speech can be transcribed', 'Mission card and budget shown by the host', 'Show each chosen card to the camera, then say its name'],
}
const HOW: Record<GameId, string[]> = {
  football: ['Teams line up in their shirt colours; the host sets the camera.', 'Press Start: the match timer runs and the camera records.', 'At full time, stop recording and send the clip to the AI Referee.', 'Review any NEEDS_REVIEW calls, then apply the verified result.'],
  falaj: ['The well is on the left, three farms on the right, a rock in the middle.', 'Each team builds a channel network with printed tiles in 90 seconds.', 'The AI reads every tile, traces the water and finds leaks.', 'Farms watered score +3; leaks −1; speed earns up to +2.'],
  souq: ['The host gives one player a shopping mission and a budget.', 'The player picks cards, shows each to the camera and says its name.', 'The AI recognises the cards, transcribes the speech and checks they agree.', 'Correct items +2, matching speech +1, over budget −2.'],
}

export default function Prepare() {
  const { s, set, setSettings } = useSession()
  const nav = useNavigate()
  const game = s.game ?? 'football'
  const [checked, setChecked] = useState<Record<string, boolean>>({})
  const allReady = EQUIP[game].every((e) => checked[game + e])
  const g = s.settings.goal
  const m = s.settings.mission
  const spend = m.requested.reduce((a, p) => a + PRODUCTS[p].price, 0)

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 py-10">
      <p className="label">Game preparation</p>
      <div className="flex flex-wrap gap-2 my-3">
        {(Object.keys(GAMES) as GameId[]).map((k) => <button key={k} onClick={() => set({ game: k })} aria-pressed={game === k} className={`btn !py-2 !text-sm ${game === k ? 'btn-primary' : 'btn-ghost'}`}>{GAMES[k].name}</button>)}
      </div>
      <h1 className="text-4xl mb-1">{GAMES[game].name}</h1>
      <p className="text-charcoal/75 mb-8">{GAMES[game].mode} game · {GAMES[game].tagline}</p>

      <div className="grid lg:grid-cols-[1.2fr_.8fr] gap-6">
        <div className="space-y-6">
          <section className="card p-6"><h2 className="text-xl mb-3">How it plays</h2>
            <ol className="space-y-2">{HOW[game].map((h, i) => <li key={h} className="flex gap-3"><span className="mono text-teal">0{i + 1}</span><span>{h}</span></li>)}</ol></section>

          <section className="card p-6"><h2 className="text-xl mb-3">Rules, scoring & penalties</h2>
            <table className="w-full text-sm"><tbody>{RULES[game].map(([a, b, c]) => <tr key={a} className="border-t border-line first:border-0"><td className="py-2 pr-3 font-semibold text-navy w-40">{a}</td><td className="py-2 pr-3 mono text-teal w-32">{b}</td><td className="py-2 text-charcoal/80">{c}</td></tr>)}</tbody></table>
            <p className="text-xs text-charcoal/60 mt-3">Rule sets are versioned (WASL-{game.toUpperCase()}-R1.0) and stamped on every judging report.</p></section>

          <section className="card p-6"><h2 className="text-xl mb-1">Calibration & configuration</h2>
            {game === 'football' && (
              <div className="grid sm:grid-cols-2 gap-6 mt-3">
                <div>
                  <div className="relative aspect-video rounded-xl overflow-hidden border border-line"><GameArt game="football" className="absolute inset-0 w-full h-full opacity-90" />
                    <div className="absolute border-2 border-gold bg-gold/25" style={{ left: 0, width: `${g.depth * 100}%`, top: `${g.top * 100}%`, height: `${(g.bottom - g.top) * 100}%` }} />
                    <div className="absolute border-2 border-gold bg-gold/25" style={{ right: 0, width: `${g.depth * 100}%`, top: `${g.top * 100}%`, height: `${(g.bottom - g.top) * 100}%` }} /></div>
                  <p className="text-xs mt-2 text-charcoal/70">Goal zones (gold) are in image coordinates. Frame the camera so each real goal sits inside its zone.</p>
                </div>
                <div className="space-y-3 text-sm">
                  {([['depth', 'Goal-zone depth', 0.04, 0.2], ['top', 'Goal top', 0.1, 0.5], ['bottom', 'Goal bottom', 0.5, 0.9]] as const).map(([k, l, mn, mx]) => (
                    <label key={k} className="block"><span className="label">{l}</span><input type="range" min={mn} max={mx} step={0.01} value={g[k]} className="w-full accent-teal" onChange={(e) => setSettings({ goal: { ...g, [k]: +e.target.value } })} /></label>))}
                  <div><span className="label">Ball colour</span><div className="flex gap-2 mt-1">{['yellow', 'orange', 'white'].map((c) => <button key={c} aria-label={c} aria-pressed={s.settings.teamColors.ball === c} onClick={() => setSettings({ teamColors: { ...s.settings.teamColors, ball: c } })} className={`size-8 rounded-full border-2 ${s.settings.teamColors.ball === c ? 'border-navy scale-110' : 'border-line'}`} style={{ background: COLOR_SWATCH[c] }} />)}</div></div>
                  <div className="flex items-center gap-3 text-sm"><span className="label">Teams</span>{(['A', 'B'] as const).map((t) => <span key={t} className="inline-flex items-center gap-1.5"><span className="size-4 rounded-full border border-line" style={{ background: COLOR_SWATCH[s.teams[t].color] }} />{s.teams[t].name}</span>)}</div>
                </div>
              </div>)}
            {game === 'falaj' && (
              <div className="mt-3 text-sm space-y-2"><p>Layout <b>Oasis crossing</b>: well at left, three farms on the right edge, one rock at the centre. The layout is printed on the board and known to the AI.</p>
                <p>Calibration is automatic: the AI finds the four corner markers on the printed board and maps every tile to its cell. Keep all four corners visible once at the start.</p></div>)}
            {game === 'souq' && (
              <div className="mt-3">
                <p className="text-sm mb-3">Build the mission: pick up to 4 requested products and set the budget.</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">{Object.entries(PRODUCTS).map(([k, p]) => {
                  const on = m.requested.includes(k)
                  return <button key={k} aria-pressed={on} onClick={() => setSettings({ mission: { ...m, requested: on ? m.requested.filter((x) => x !== k) : m.requested.length < 4 ? [...m.requested, k] : m.requested } })} className={`rounded-xl border p-3 text-left transition ${on ? 'border-teal bg-teal/10' : 'border-line bg-white hover:border-navy'}`}><div className="font-semibold text-navy">{p.en}</div><div className="text-sm" dir="rtl">{p.ar}</div><div className="mono text-xs text-charcoal/70">AED {p.price}</div></button>
                })}</div>
                <div className="mt-4 flex items-center gap-4"><label className="label" htmlFor="bud">Budget (AED)</label><input id="bud" type="number" min={10} max={200} step={5} className="input !w-28" value={m.budget} onChange={(e) => setSettings({ mission: { ...m, budget: +e.target.value } })} />
                  <span className={`text-sm ${spend > m.budget ? 'text-red font-semibold' : 'text-charcoal/70'}`}>Requested items cost AED {spend}{spend > m.budget ? ' — over budget: players must choose' : ''}</span></div>
              </div>)}
          </section>
        </div>

        <aside className="space-y-6">
          <section className="card p-6"><h2 className="text-xl mb-3">Equipment checklist</h2>
            <ul className="space-y-2">{EQUIP[game].map((e) => <li key={e}><label className="flex gap-3 items-start cursor-pointer text-sm"><input type="checkbox" className="mt-1 size-4 accent-teal" checked={!!checked[game + e]} onChange={(ev) => setChecked({ ...checked, [game + e]: ev.target.checked })} />{e}</label></li>)}</ul>
            <button className="btn btn-primary w-full mt-5" disabled={!allReady} onClick={() => nav('/arena')}>Everyone ready → Live Arena</button>
            {!allReady && <p className="text-xs text-charcoal/60 mt-2 text-center">Tick every item to continue (or <Link to="/arena" className="underline">skip to the arena</Link>).</p>}
          </section>
          {game !== 'football' && (
            <section className="card p-6"><h2 className="text-xl mb-2">Printables</h2><p className="text-sm text-charcoal/75 mb-3">Print at 100% scale on A4. Each marker is a unique printed code the AI reads.</p>
              <div className="flex flex-col gap-2">
                {game === 'falaj' && <><a className="btn btn-gold" href="/printables/falaj-board.html" target="_blank" rel="noreferrer">⬇ Falaj board (A3/A4)</a><a className="btn btn-ghost" href="/printables/falaj-tiles.html" target="_blank" rel="noreferrer">⬇ Channel tiles (16)</a></>}
                {game === 'souq' && <a className="btn btn-gold" href="/printables/souq-cards.html" target="_blank" rel="noreferrer">⬇ Product cards (16)</a>}
              </div><p className="text-xs text-charcoal/60 mt-3">Opens a print-ready page: use “Print / Save as PDF”.</p></section>)}
          <section className="card p-6 bg-navy !border-navy text-white"><h2 className="text-xl !text-ivory mb-2">Fairness promise</h2><p className="text-sm text-white/80">The AI only scores what it can see and hear. Anything uncertain waits for the host — nothing is guessed.</p></section>
        </aside>
      </div>
    </div>
  )
}
