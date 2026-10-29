import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Orb, ORB_LABEL, type OrbState } from '../components/Orb'
import { GameArt } from '../components/GameArt'
import { tr } from '../lib/i18n'
import { GAMES, useSession, type GameId } from '../lib/store'
import { TEAM } from '../lib/team'

const STATES: OrbState[] = ['idle', 'watching', 'processing', 'verified', 'review']
const PIPE = [
  ['Gameplay', 'Real play, camera + microphone'],
  ['Evidence', 'Frames, audio and hashes extracted'],
  ['Events', 'Goals, tiles, cards, speech detected'],
  ['Rules', 'Deterministic engine scores them'],
  ['Host review', 'Uncertain calls wait for a human'],
  ['Verified score', 'Sealed, replayable, auditable'],
]

export default function Launch() {
  const { s } = useSession()
  const [orb, setOrb] = useState<OrbState>('idle')
  return (
    <div>
      <section className="bg-navy text-white relative overflow-hidden">
        <div className="absolute inset-0 lattice opacity-40" aria-hidden />
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 pt-14 pb-20 grid lg:grid-cols-[1.1fr_.9fr] gap-10 items-center">
          <div className="rise">
            <p className="label !text-gold">6th Annual COE STEM Programming with AI · AI for Family</p>
            <h1 className="text-[2.6rem] sm:text-6xl leading-[1.04] mt-4 !text-ivory">{tr('hero.title', s.lang)}</h1>
            <p className="mt-5 text-lg text-white/75 max-w-xl">{tr('hero.sub', s.lang)}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/setup" className="btn btn-gold">{tr('hero.cta', s.lang)} →</Link>
              <Link to="/replay?report=sample-football_goal" className="btn btn-ghost !text-white !border-white/30">See an AI Referee Replay</Link>
            </div>
            <dl className="mt-10 grid grid-cols-3 gap-4 max-w-lg text-sm">
              {[['3', 'games'], ['100%', 'points backed by evidence'], ['0', 'unverified goals counted']].map(([a, b]) => (
                <div key={b}><dt className="display text-3xl text-gold">{a}</dt><dd className="text-white/65 mt-1">{b}</dd></div>
              ))}
            </dl>
          </div>
          <div className="flex flex-col items-center">
            <Orb state={orb} size={380} className="max-w-full" />
            <div className="mt-2 text-center">
              <p className="mono text-sm text-gold" aria-live="polite">AI Referee · {ORB_LABEL[orb]}</p>
              <div className="mt-3 flex flex-wrap justify-center gap-2">
                {STATES.map((st) => (
                  <button key={st} onClick={() => setOrb(st)} className={`rounded-full px-3 py-1.5 text-xs font-semibold border transition ${orb === st ? 'bg-ivory text-navy border-ivory' : 'border-white/25 text-white/75 hover:border-white'}`}>{ORB_LABEL[st]}</button>
                ))}
              </div>
              <p className="text-xs text-white/50 mt-3">The orb mirrors the real judging state. Move your pointer over it.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 sm:px-6 py-16">
        <p className="label">The fair-play pipeline</p>
        <h2 className="text-3xl sm:text-4xl mt-2 mb-8 max-w-2xl">AI that shows its work, not just its answer.</h2>
        <ol className="grid sm:grid-cols-2 lg:grid-cols-6 gap-3">
          {PIPE.map(([t, d], i) => (
            <li key={t} className="card p-4 relative">
              <span className="mono text-xs text-teal">0{i + 1}</span>
              <div className="display text-lg mt-1 text-navy">{t}</div>
              <p className="text-sm mt-1 text-charcoal/75">{d}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="mx-auto max-w-7xl px-4 sm:px-6 pb-16">
        <div className="flex items-end justify-between flex-wrap gap-3 mb-6">
          <div><p className="label">The collection</p><h2 className="text-3xl sm:text-4xl mt-2">Three games. Team and individual.</h2></div>
          <Link to="/games" className="btn btn-ghost">Open game library →</Link>
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          {(Object.keys(GAMES) as GameId[]).map((g) => (
            <Link to="/games" key={g} className="card overflow-hidden group block transition hover:-translate-y-1 hover:shadow-xl">
              <GameArt game={g} className="w-full h-44 object-cover" />
              <div className="p-5">
                <div className="flex items-center justify-between"><h3 className="text-xl">{GAMES[g].name}</h3><span className="text-xs font-semibold rounded-full bg-ivory border border-line px-2.5 py-1">{GAMES[g].mode}</span></div>
                <p className="text-sm mt-2 text-charcoal/75">{GAMES[g].tagline}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 sm:px-6 pb-16">
        <div className="card p-6 sm:p-8 grid md:grid-cols-[1fr_auto] gap-6 items-center">
          <div>
            <p className="label">Team {TEAM.number} · Code {TEAM.code}</p>
            <h2 className="text-3xl mt-1 mb-3">Built by</h2>
            <ul className="grid sm:grid-cols-3 gap-3">{TEAM.members.map((m) => (
              <li key={m.name} className="rounded-xl bg-ivory border border-line px-4 py-3"><div className="font-semibold text-navy">{m.name}</div><div className="text-sm text-charcoal/70">Grade {m.grade.slice(1)}</div></li>))}</ul>
          </div>
          <div className="rounded-2xl bg-navy text-ivory px-6 py-5 text-sm"><div className="label !text-gold">Selected track</div><div className="display text-xl mt-1">{TEAM.track}</div><div className="mt-1 text-white/70">Family AI Game Day</div></div>
        </div>
      </section>

      <section className="bg-paper border-t border-line">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-14 grid md:grid-cols-3 gap-8">
          {[['Explainable', 'Every judgment links to the exact frames, the rule applied, the score change and a confidence note.'],
            ['Honest about doubt', 'If the AI cannot see the ball cross the line, it says NEEDS_REVIEW. A human host decides — and it is logged.'],
            ['Tamper-evident', 'Source videos are hashed and reports are signed. Edit a report and verification fails.']].map(([t, d]) => (
            <div key={t}><h3 className="text-xl mb-2">{t}</h3><p className="text-charcoal/80">{d}</p></div>
          ))}
        </div>
      </section>
    </div>
  )
}
