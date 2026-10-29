import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import type { Any } from '../lib/api'

const GAME: Record<string, string> = { football: 'Football AI', falaj: 'Falaj Flow', souq: 'Souq Signal' }

export default function Lab() {
  const [ev, setEv] = useState<Any | null>(null)
  const [fail, setFail] = useState(false)
  useEffect(() => { fetch('/evaluation.json').then((r) => r.json()).then(setEv).catch(() => setFail(true)) }, [])
  if (fail) return <div className="p-16 text-center">evaluation.json missing. Run <code>python tools/export_samples.py</code>.</div>
  if (!ev) return <div className="p-16 text-center text-charcoal/60">Loading results…</div>
  const fx: Any[] = ev.fixtures
  const files = [...new Set((ev.pytest.cases as Any[]).map((c) => c.file))]
  const g = ev.transcription_check

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10">
      <p className="label">Evaluation lab</p>
      <h1 className="text-4xl mt-1 mb-2">What was actually tested</h1>
      <p className="text-charcoal/75 max-w-3xl mb-6">Everything on this page was produced by running the code. Generated {ev.generated_at.slice(0, 19).replace('T', ' ')} UTC. Nothing is hand-entered.</p>

      <div className="grid sm:grid-cols-3 gap-4 mb-6">
        {[[`${ev.pytest.passed}/${ev.pytest.total}`, 'automated tests passed', ev.pytest.failed ? 'text-red' : 'text-teal'], [`${fx.filter((f) => f.pass).length}/${fx.length}`, 'synthetic fixtures match ground truth', 'text-teal'], ['0', 'real family clips analysed so far', 'text-[#7a5a1c]']].map(([a, b, c]) => (
          <div key={b} className="card p-5"><div className={`display text-4xl ${c}`}>{a}</div><div className="text-sm mt-1 text-charcoal/75">{b}</div></div>))}
      </div>

      <div className="rounded-2xl border-2 border-gold bg-gold/15 p-5 mb-8"><p className="font-bold text-navy mb-1">Honesty note: synthetic vs real</p>
        <p className="text-sm">The nine fixtures below are <b>synthetic renders</b> with known ground truth, made to test the pipelines. They are not real gameplay. {ev.real_footage.note} Real recorded footage should be judged through the Live Arena and reported separately.</p></div>

      <section className="card p-6 mb-6"><h2 className="text-xl mb-4">Pipeline test cases (synthetic fixtures, real code path)</h2>
        <div className="overflow-x-auto"><table className="w-full text-sm min-w-[640px]"><thead><tr className="text-left text-xs uppercase tracking-wider text-charcoal/60"><th className="pb-2">Case</th><th>Game</th><th>Expected</th><th>Actual (pipeline output)</th><th>Result</th><th /></tr></thead>
          <tbody>{fx.map((f) => <tr key={f.name} className="border-t border-line align-top"><td className="py-2.5 mono text-xs">{f.name}</td><td>{GAME[f.game]}</td>
            <td className="mono text-xs">{Object.entries(f.expected).filter(([k]) => k !== 'status').map(([k, v]) => `${k}=${v}`).join(', ')}</td>
            <td className="mono text-xs">{Object.entries(f.actual).map(([k, v]) => `${k}=${v}`).join(', ')}</td>
            <td><span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${f.pass ? 'bg-teal/15 text-teal' : 'bg-red/10 text-red'}`}>{f.pass ? 'PASS' : 'FAIL'}</span></td>
            <td><Link to={`/replay?report=${f.report}`} className="text-teal underline text-xs">Replay</Link></td></tr>)}</tbody></table></div>
        <p className="text-xs text-charcoal/60 mt-3">Souq fixtures use scripted transcripts for deterministic scoring; the live speech check is below.</p></section>

      <section className="card p-6 mb-6"><h2 className="text-xl mb-3">Speech transcription check (live model call)</h2>
        {g?.status === 'OK' ? (<><p className="text-sm mb-2">Synthetic text-to-speech audio (“I choose dates / Coffee please / And the pottery”) was sent to <span className="mono">{g.source}</span> and returned:</p>
          <ul className="text-sm space-y-1 mb-2">{g.segments.map((s: Any, i: number) => <li key={i}><span className="mono text-teal text-xs mr-2">{s.start}–{s.end}s</span>“{s.text}”</li>)}</ul>
          <p className="text-sm">Deterministic scoring on that transcript: <b>{g.total}</b> points (expected {g.expected_total}) · <Link className="text-teal underline" to={`/replay?report=${g.report}`}>open replay</Link></p></>) :
          <p className="text-sm text-[#7a5a1c]">Transcription was not available when this evaluation ran ({g?.reason ?? g?.status}). Spoken-match points stayed NEEDS_REVIEW, as designed.</p>}</section>

      <section className="card p-6 mb-6"><h2 className="text-xl mb-3">Automated test suite ({ev.pytest.passed}/{ev.pytest.total} passed)</h2>
        {files.map((f) => { const cs = (ev.pytest.cases as Any[]).filter((c) => c.file === f); return (
          <details key={f} className="border-t border-line py-2 first:border-0"><summary className="cursor-pointer font-semibold text-navy text-sm">{f} <span className="text-charcoal/60 font-normal">· {cs.filter((c) => c.status === 'passed').length}/{cs.length} passed</span></summary>
            <ul className="mt-2 grid sm:grid-cols-2 gap-x-6 gap-y-1">{cs.map((c) => <li key={c.name} className="text-xs mono"><span className={c.status === 'passed' ? 'text-teal' : 'text-red'}>{c.status === 'passed' ? '✓' : '✗'}</span> {c.name}</li>)}</ul></details>) })}</section>

      <section className="grid md:grid-cols-2 gap-6">
        <div className="card p-6"><h2 className="text-xl mb-3">Limitations</h2><ul className="list-disc pl-5 text-sm space-y-1.5">
          <li>Football needs a fixed camera, a single-colour ball and contrasting shirts; shirt numbers are not read, so the host assigns tracks to players.</li>
          <li>Colour segmentation is lighting-sensitive; calibration presets may need tuning on the day.</li>
          <li>Falaj and Souq read printed markers; a damaged or hidden marker counts as absent.</li>
          <li>Speech timing is approximate (±~1 s); matching uses a 5-second window.</li>
          <li>Detection scores are heuristics, not calibrated probabilities. No accuracy percentage is claimed.</li></ul></div>
        <div className="card p-6"><h2 className="text-xl mb-3">Reproduce</h2><pre className="mono text-xs bg-ivory rounded-xl p-4 overflow-auto">{`cd backend
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
python ../tools/make_fixtures.py
pytest
python ../tools/export_samples.py`}</pre></div>
      </section>
    </div>
  )
}
