import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { FalajTwin } from '../components/FalajTwin'
import { Orb, type OrbState } from '../components/Orb'
import { evidenceUrl, getReport, importReport, mediaUrl, postAssignments, postReview, postTranscript, type Any } from '../lib/api'
import { PRODUCTS } from '../lib/catalog'
import { GAMES, useSession, type GameId } from '../lib/store'

const SAMPLES: [string, string][] = [
  ['sample-football_goal', 'Football · valid goal'], ['sample-football_nogoal', 'Football · no goal'], ['sample-football_uncertain', 'Football · uncertain (needs review)'],
  ['sample-falaj_valid', 'Falaj · complete route'], ['sample-falaj_partial', 'Falaj · partial network'], ['sample-falaj_rock', 'Falaj · blocked by rock'],
  ['sample-souq_correct_gemini', 'Souq · correct (live speech transcription)'], ['sample-souq_mismatch', 'Souq · audio/video mismatch'], ['sample-souq_budget_dup', 'Souq · budget + duplicate'],
]
const LABEL: Record<string, string> = { GOAL: 'Goal', POSSIBLE_GOAL: 'Possible goal', DEST_CONNECTED: 'Farm watered', LEAK: 'Leak', TIME_BONUS: 'Speed bonus', PLACEMENT_ISSUE: 'Placement issue',
  REQUESTED_ITEM: 'Requested item', EXTRA_ITEM: 'Extra item', SPOKEN_MATCH: 'Spoken match', DUPLICATE_ITEM: 'Duplicate', BUDGET_EXCEEDED: 'Over budget', AUDIO_VIDEO_MISMATCH: 'Audio ≠ video', POSSESSION_SEGMENT: 'Possession' }
const RULE_TEXT: Record<string, string> = {
  'FB-1': 'FB-1 · A goal needs the ball observed entering the goal zone after being seen outside it: +1', 'FB-2': 'FB-2 · Unsupported goals score 0 until the host accepts them', 'FB-5': 'FB-5 · Possession counts only observed ball time',
  'FF-0': 'FF-0 · Tiles may only sit on playable cells', 'FF-1': 'FF-1 · Each farm reached by water: +3', 'FF-2': 'FF-2 · Each leak (unmatched open end): −1', 'FF-3': 'FF-3 · All farms watered fast: ≤45 s +2, ≤70 s +1',
  'SS-1': 'SS-1 · Requested product shown to the camera: +2', 'SS-2': 'SS-2 · Product named within ±5 s of showing it: +1', 'SS-3': 'SS-3 · Distinct card prices over budget: −2', 'SS-4': 'SS-4 · Repeat of the same product: no extra points', 'SS-5': 'SS-5 · Audio and video disagree: host review',
}
const STATUS: Record<string, string> = { VERIFIED: 'bg-teal/15 text-teal border-teal/40', NEEDS_REVIEW: 'bg-gold/25 text-[#7a5a1c] border-gold', REJECTED: 'bg-red/10 text-red border-red/40' }
const eff = (e: Any) => (e.review?.decision === 'ACCEPTED' ? 'VERIFIED' : e.review?.decision === 'REJECTED' ? 'REJECTED' : e.status)
const Chip = ({ s }: { s: string }) => <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-bold tracking-wide ${STATUS[s] ?? ''}`}>{s.replace('_', ' ')}</span>
const short = (h?: string) => (h ? `${h.slice(0, 10)}…${h.slice(-6)}` : '—')

export default function Replay() {
  const [sp] = useSearchParams()
  const nav = useNavigate()
  const { s, addResult, record } = useSession()
  const id = sp.get('report')
  const [report, setReport] = useState<Any | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [sel, setSel] = useState<string | null>(null)
  const [t, setT] = useState(0)
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState<string | null>(null)
  const [live, setLive] = useState(false)
  const vid = useRef<HTMLVideoElement>(null)
  const cv = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    setReport(null); setErr(null); setSel(null); setLive(false)
    if (!id) return
    getReport(id).then((r) => { setReport(r); const first = r.events.find((e: Any) => e.status === 'NEEDS_REVIEW') ?? r.events.find((e: Any) => e.type !== 'POSSESSION_SEGMENT'); setSel(first?.id ?? null) }).catch(() => setErr('Could not load this report. Is the AI judge backend running?'))
  }, [id])

  const game: GameId | null = report?.game ?? null
  const events: Any[] = report?.events ?? []
  const shown = events.filter((e) => e.type !== 'POSSESSION_SEGMENT')
  const selected = events.find((e) => e.id === sel)
  const pending = shown.filter((e) => eff(e) === 'NEEDS_REVIEW').length
  const orb: OrbState = !report ? 'idle' : pending ? 'review' : 'verified'
  const dur = report?.source?.duration_s ?? 0

  const seek = useCallback((time: number) => { if (vid.current) { vid.current.currentTime = Math.max(0, time - 0.3); setT(time) } }, [])
  useEffect(() => { if (selected && vid.current) seek(selected.t_start) }, [sel])

  // overlay painter synced to playback
  useEffect(() => {
    if (!report) return
    let raf = 0
    const paint = () => {
      const v = vid.current, c = cv.current
      if (v && c) {
        const w = v.clientWidth, h = v.clientHeight
        if (c.width !== w || c.height !== h) { c.width = w; c.height = h }
        const ctx = c.getContext('2d')!
        ctx.clearRect(0, 0, w, h)
        const time = v.currentTime
        setT((p) => (Math.abs(p - time) > 0.05 ? time : p))
        const ov: Any[] = report.overlay ?? []
        let lo = 0, hi = ov.length - 1
        while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (ov[mid].t <= time) lo = mid; else hi = mid - 1 }
        const f = ov[lo]
        if (report.game === 'football') {
          ctx.lineWidth = 2
          for (const [k, col] of [['A_attacks', '#B92D39'], ['B_attacks', '#C6A36B']] as const) {
            const poly = report.config.goals[k]; ctx.strokeStyle = col; ctx.fillStyle = col + '33'; ctx.beginPath()
            poly.forEach(([x, y]: number[], i: number) => (i ? ctx.lineTo(x * w, y * h) : ctx.moveTo(x * w, y * h))); ctx.closePath(); ctx.fill(); ctx.stroke()
          }
          if (f && Math.abs(f.t - time) < 0.4) {
            ctx.font = '600 12px Inter'
            for (const [pid, team, x0, y0, x1, y1] of f.p) { ctx.strokeStyle = team === 'A' ? '#B92D39' : '#2F6BFF'; ctx.lineWidth = 2; ctx.strokeRect(x0 * w, y0 * h, (x1 - x0) * w, (y1 - y0) * h); ctx.fillStyle = '#fff'; ctx.fillText(pid, x0 * w, y0 * h - 4) }
            if (f.ball) { const [bx, by, br] = f.ball; ctx.strokeStyle = '#FFD84A'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(bx * w, by * h, Math.max(10, br * w * 2), 0, 7); ctx.stroke(); ctx.fillStyle = '#FFD84A'; ctx.fillText('BALL', bx * w + 12, by * h - 10) }
            else { ctx.fillStyle = '#FFD84A'; ctx.font = '700 13px Inter'; ctx.fillText('ball not observed', 14, h - 14) }
          }
        } else if (report.game === 'souq' && f && Math.abs(f.t - time) < 0.5) {
          const sx = w / (report.source.width || 1280), sy = h / (report.source.height || 720)
          for (const [cid, ...q] of f.cards) {
            ctx.strokeStyle = '#2FB5B8'; ctx.lineWidth = 4; ctx.beginPath()
            for (let i = 0; i < 4; i++) (i ? ctx.lineTo(q[i * 2] * sx, q[i * 2 + 1] * sy) : ctx.moveTo(q[0] * sx, q[1] * sy)); ctx.closePath(); ctx.stroke()
            const prod = Object.entries(PRODUCTS).find(([k]) => report.metrics.catalog?.[k] && [60, 61, 62, 63, 64, 65, 66, 67].includes(cid) && ['dates', 'coffee', 'spices', 'pottery', 'textile', 'oud', 'honey', 'rosewater'][cid - 60] === k)
            const key = prod?.[0] ?? ['dates', 'coffee', 'spices', 'pottery', 'textile', 'oud', 'honey', 'rosewater'][(cid - 60) % 10]
            const p = PRODUCTS[key]
            if (p) { ctx.fillStyle = '#12243A'; ctx.fillRect(q[0] * sx, q[1] * sy - 26, 150, 24); ctx.fillStyle = '#F7F3EB'; ctx.font = '700 13px Inter'; ctx.fillText(`${p.en} · AED ${p.price}`, q[0] * sx + 6, q[1] * sy - 9) }
          }
        }
      }
      raf = requestAnimationFrame(paint)
    }
    paint()
    return () => cancelAnimationFrame(raf)
  }, [report])

  async function ensureLive(): Promise<Any> {
    if (!report.sample || live) return report
    const blob = new Blob([JSON.stringify(report)], { type: 'application/json' })
    const r = await importReport(new File([blob], 'sample.json'))
    if (!r.ok) throw new Error('Sample cannot be imported by this backend (different signing key). Record or upload a clip to use host review.')
    setLive(true); return report
  }
  async function act<T>(fn: () => Promise<T>) {
    setBusy(true); setNote(null)
    try { return await fn() } catch (e) { setNote((e as Error).message || 'Backend unavailable: host review needs the AI judge backend.') } finally { setBusy(false) }
  }
  const review = (decision: string) => act(async () => {
    await ensureLive()
    const r = await postReview(report.report_id, selected.id, decision, s.family ? `${s.family} host` : 'host')
    setReport({ ...r, sample: report.sample }); record('host_review', { event: selected.id, decision, report: report.report_id })
  })
  const assign = (map: Record<string, string>) => act(async () => { await ensureLive(); const r = await postAssignments(report.report_id, map, 'host'); setReport({ ...r, sample: report.sample }); record('assign_players', { map }) })

  const summ = report?.summary
  const subjects = useMemo(() => {
    if (!game) return []
    if (game === 'football') return [{ v: 'match', l: `${s.teams.A.name} vs ${s.teams.B.name}` }]
    if (game === 'falaj') return (['A', 'B'] as const).map((tm) => ({ v: tm, l: s.teams[tm].name }))
    return s.players.filter((p) => p.name.trim()).map((p) => ({ v: p.id, l: p.name }))
  }, [game, s])
  const pend = useMemo(() => { try { return JSON.parse(sessionStorage.getItem('wasl-pending') || 'null') } catch { return null } }, [report])
  const [subject, setSubject] = useState('')
  useEffect(() => { setSubject(pend && pend.game === game ? pend.subject : subjects[0]?.v ?? '') }, [pend, game, subjects])

  function apply() {
    if (!report || !game) return
    const rd = pend?.round ?? 1
    const synthetic = !!report.synthetic_fixture
    const unresolved = pending
    if (game === 'football') {
      const { A, B } = summ.score
      const winner = summ.winner
      for (const tm of ['A', 'B'] as const)
        addResult({ game, reportId: id!, round: 1, subject: tm, subjectLabel: s.teams[tm].name, score: summ.score[tm], detail: `${s.teams.A.name} ${A} – ${B} ${s.teams.B.name}`, verified: unresolved === 0, sample: synthetic, mvp: summ.mvp?.mvp ?? null, winner })
    } else {
      const label = subjects.find((x) => x.v === subject)?.l ?? subject
      addResult({ game, reportId: id!, round: rd, subject, subjectLabel: label, score: summ.score.total, detail: game === 'souq' ? `AED ${summ.spend} of ${summ.budget}` : `${summ.score.destinations} farms · ${summ.score.leaks} leaks`, verified: unresolved === 0, sample: synthetic })
    }
    sessionStorage.removeItem('wasl-pending')
    nav('/cup')
  }

  if (!id)
    return (
      <div className="mx-auto max-w-5xl px-4 sm:px-6 py-10">
        <p className="label">AI Referee Replay</p><h1 className="text-4xl mt-1 mb-2">Open evidence</h1>
        <p className="text-charcoal/75 mb-6 max-w-2xl">Pick a judging report. Samples were produced by the real pipelines from synthetic test fixtures (not family footage). Use the Live Arena to judge your own clip.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">{SAMPLES.map(([k, l]) => <Link key={k} to={`/replay?report=${k}`} className="card p-5 hover:-translate-y-0.5 hover:shadow-lg transition"><span className="mono text-xs text-teal">SYNTHETIC SAMPLE</span><div className="display text-lg mt-1">{l}</div></Link>)}</div>
        <Link to="/arena" className="btn btn-primary mt-8">Judge my own clip →</Link>
      </div>
    )
  if (err) return <div className="mx-auto max-w-xl px-6 py-20 text-center"><h1 className="text-3xl mb-3">Report unavailable</h1><p className="mb-6">{err}</p><Link to="/replay" className="btn btn-primary">Browse sample replays</Link></div>
  if (!report) return <div className="p-16 text-center text-charcoal/60">Loading evidence…</div>

  const ic = report.integrity_check
  const snaps: Any[] = report.metrics?.snapshots ?? []
  let snapIdx = -1
  snaps.forEach((sn, i) => { if (sn.t_start <= t) snapIdx = i })
  const finalIdx = summ?.final_state_index ?? snaps.length - 1
  const twinIdx = game === 'falaj' ? (snapIdx < 0 ? 0 : snapIdx) : 0
  const twin = snaps[Math.max(0, twinIdx)]
  const poss = report.metrics?.possession

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 py-8">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-4"><Orb state={orb} size={84} />
          <div><p className="label">AI Referee Replay · {GAMES[game!].name}</p><h1 className="text-3xl mt-0.5">{summ?.score?.A !== undefined ? `${s.teams.A.name} ${summ.score.A} – ${summ.score.B} ${s.teams.B.name}` : `Score ${summ?.score?.total ?? '—'}`}</h1>
            <p className="text-sm text-charcoal/70 mt-1">{report.source.filename} · {report.rule_version} · {pending ? <b className="text-[#7a5a1c]">{pending} call(s) need host review</b> : <b className="text-teal">all calls verified</b>}{report.synthetic_fixture && <span className="ml-2 rounded bg-navy text-ivory text-[10px] font-bold px-2 py-0.5">SYNTHETIC FIXTURE, NOT REAL GAMEPLAY</span>}</p></div></div>
        <div className="flex flex-wrap items-center gap-2">
          {game !== 'football' && subjects.length > 0 && <select className="input !w-auto" value={subject} onChange={(e) => setSubject(e.target.value)} aria-label="Apply to">{subjects.map((x) => <option key={x.v} value={x.v}>{x.l}</option>)}</select>}
          <button className="btn btn-teal" onClick={apply}>{pending ? `Apply (${pending} unresolved not counted)` : 'Apply verified result'} →</button>
        </div>
      </div>

      <div className="grid xl:grid-cols-[1.55fr_1fr] gap-6">
        <div className="space-y-4 min-w-0">
          <div className={`grid gap-3 ${game === 'falaj' ? 'md:grid-cols-2' : ''}`}>
            <div className="card overflow-hidden">
              <div className="relative bg-black" style={{ aspectRatio: `${report.source.width || 16} / ${report.source.height || 9}` }}>
                <video ref={vid} src={mediaUrl(report)} controls playsInline className="absolute inset-0 w-full h-full" onLoadedMetadata={() => seek(selected?.t_start ?? 0)} />
                <canvas ref={cv} className="absolute inset-0 pointer-events-none" aria-hidden />
              </div>
              <div className="px-4 py-2 text-xs text-charcoal/70 flex justify-between"><span>Source video · annotations are drawn from the AI's detections</span><span className="mono">{t.toFixed(1)}s</span></div>
            </div>
            {game === 'falaj' && (
              <div className="card p-3"><p className="label px-1 mb-1">Digital reconstruction · {twin ? `state at ${twin.t_start}s` : 'waiting for tiles'}</p>
                {twin && <FalajTwin key={twinIdx} snapshot={twin} layout={report.metrics.layout} animate={twinIdx === finalIdx} />}
                <p className="text-xs text-charcoal/70 px-1">Rebuilt only from tiles the AI read from the board. Water runs only along rule-validated edges.</p></div>)}
          </div>

          <div className="card p-4"><div className="relative h-9 rounded-full bg-ivory border border-line" role="group" aria-label="Event timeline">
            <div className="absolute top-0 bottom-0 w-0.5 bg-navy z-10" style={{ left: `${Math.min(100, (t / (dur || 1)) * 100)}%` }} />
            {shown.map((e) => <button key={e.id} title={`${LABEL[e.type]} @ ${e.t_start}s`} onClick={() => setSel(e.id)} className={`absolute top-1.5 size-6 rounded-full border-2 border-white shadow ${eff(e) === 'VERIFIED' ? 'bg-teal' : eff(e) === 'REJECTED' ? 'bg-red' : 'bg-gold'} ${sel === e.id ? 'ring-2 ring-navy' : ''}`} style={{ left: `calc(${Math.min(96, ((e.t_start ?? 0) / (dur || 1)) * 100)}% - 6px)` }} aria-label={`${LABEL[e.type]} at ${e.t_start} seconds`} />)}
          </div><div className="flex gap-4 text-xs mt-2 text-charcoal/70"><span><i className="inline-block size-2.5 rounded-full bg-teal" /> verified</span><span><i className="inline-block size-2.5 rounded-full bg-gold" /> needs review</span><span><i className="inline-block size-2.5 rounded-full bg-red" /> rejected</span></div></div>

          {game === 'football' && poss && (
            <div className="card p-5"><h2 className="text-lg mb-3">Possession & MVP <span className="text-xs font-normal text-charcoal/60">(observed ball time only)</span></h2>
              <div className="grid sm:grid-cols-2 gap-6">
                <div>{(['A', 'B'] as const).map((tm) => { const pct = summ.possession.percent_of_observed[tm] ?? 0; return <div key={tm} className="mb-3"><div className="flex justify-between text-sm"><b>{s.teams[tm].name}</b><span className="mono">{summ.possession.seconds[tm]}s · {pct}%</span></div><div className="h-3 rounded-full bg-line"><div className="h-full rounded-full" style={{ width: `${pct}%`, background: tm === 'A' ? '#B92D39' : '#2F6BFF' }} /></div></div> })}
                  <p className="text-xs text-charcoal/60">Unknown (ball not observed): {summ.possession.unknown_seconds}s, credited to nobody.</p></div>
                <div><p className="label mb-2">Assign tracks to registered players</p>
                  <div className="space-y-2">{Object.entries(poss.by_track as Record<string, number>).sort((a, b) => b[1] - a[1]).map(([tid, sec]) => { const tm = tid[0] as 'A' | 'B'; return (
                    <div key={tid} className="flex items-center gap-2 text-sm"><span className="mono w-10">{tid}</span><span className="w-14 text-charcoal/60">{sec}s</span>
                      <select className="input !py-1.5" value={report.config.assignments?.[tid] ?? ''} onChange={(e) => void assign({ ...report.config.assignments, [tid]: e.target.value })} aria-label={`Assign track ${tid}`}><option value="">Unassigned</option>{s.teams[tm].playerIds.map((pid) => <option key={pid} value={s.players.find((p) => p.id === pid)?.name || pid}>{s.players.find((p) => p.id === pid)?.name || pid}</option>)}</select></div>) })}</div>
                  <p className="mt-3 rounded-xl bg-ivory border border-line px-3 py-2 text-sm"><b>MVP:</b> {summ.mvp.mvp ? <span className="text-teal font-semibold">{summ.mvp.mvp} ({summ.mvp.seconds}s)</span> : <span className="text-[#7a5a1c]">pending</span>} <span className="text-charcoal/70">— {summ.mvp.reason}</span></p></div></div></div>)}

          {game === 'souq' && (
            <div className="card p-5"><h2 className="text-lg mb-3">Verified basket</h2>
              <div className="grid sm:grid-cols-2 gap-6"><div>
                <ul className="space-y-1.5">{(summ.selected as string[]).map((p) => <li key={p} className="flex justify-between rounded-lg bg-ivory px-3 py-2 text-sm"><span>{PRODUCTS[p].en} <span dir="rtl" className="text-charcoal/60">{PRODUCTS[p].ar}</span>{report.config.mission.requested.includes(p) ? <span className="ml-2 text-teal font-semibold">requested</span> : <span className="ml-2 text-charcoal/50">extra</span>}</span><span className="mono">AED {PRODUCTS[p].price}</span></li>)}</ul>
                <div className="mt-3 flex justify-between text-sm font-semibold"><span>Spend / budget</span><span className={summ.remaining_budget < 0 ? 'text-red' : 'text-navy'}>AED {summ.spend} / {summ.budget} · {summ.remaining_budget >= 0 ? `${summ.remaining_budget} left` : `${-summ.remaining_budget} over`}</span></div></div>
                <div><p className="label mb-1">Transcript · {report.metrics.transcript.source ?? report.metrics.transcript.status}</p>
                  {report.metrics.transcript.segments.length ? <ul className="space-y-1 text-sm">{report.metrics.transcript.segments.map((g: Any, i: number) => <li key={i}><button className="mono text-xs text-teal mr-2" onClick={() => seek(g.start)}>{g.start.toFixed(1)}s</button>“{g.text}”</li>)}</ul> : <TranscriptFallback status={report.metrics.transcript.status} onSubmit={(txt) => act(async () => { await ensureLive(); const r = await postTranscript(report.report_id, txt, 'host'); setReport({ ...r, sample: report.sample }) })} />}
                  <p className="text-xs text-charcoal/60 mt-2">Speech is transcribed by an AI model; it never decides points. Matching and scoring are deterministic.</p></div></div></div>)}
        </div>

        <aside className="space-y-4 min-w-0">
          <div className="card p-5">
            <h2 className="text-lg mb-3">Judged events</h2>
            <ul className="space-y-2 max-h-[22rem] overflow-auto pr-1">{shown.length === 0 && <li className="text-sm text-charcoal/65">No scoring events were detected in this clip.</li>}
              {shown.map((e) => <li key={e.id}><button onClick={() => setSel(e.id)} className={`w-full text-left rounded-xl border p-3 transition ${sel === e.id ? 'border-navy bg-white shadow' : 'border-line bg-ivory hover:bg-white'}`}>
                <div className="flex items-center justify-between gap-2"><span className="font-semibold text-navy">{LABEL[e.type] ?? e.type}{e.team ? ` · ${s.teams[e.team as 'A' | 'B'].name}` : ''}{e.product ? ` · ${PRODUCTS[e.product]?.en}` : ''}</span><Chip s={eff(e)} /></div>
                <div className="flex justify-between text-xs text-charcoal/65 mt-1"><span className="mono">{e.t_start}s</span><span className="mono">{e.points > 0 ? '+' : ''}{e.points} pts{eff(e) !== 'VERIFIED' ? ' (not counted)' : ''}</span></div></button></li>)}</ul>
          </div>

          {selected && (
            <div className="card p-5 rise" key={selected.id}>
              <div className="flex items-center justify-between"><h2 className="text-lg">Why the AI decided this</h2><Chip s={eff(selected)} /></div>
              <p className="mt-3 text-sm">{selected.reason}</p>
              <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
                <dt className="font-semibold text-navy">Rule</dt><dd>{RULE_TEXT[selected.rule_id] ?? selected.rule_id}</dd>
                <dt className="font-semibold text-navy">Score change</dt><dd className="mono">{selected.points > 0 ? '+' : ''}{selected.points} {eff(selected) === 'VERIFIED' ? '(applied)' : '(held back)'}</dd>
                <dt className="font-semibold text-navy">Moment</dt><dd><button className="underline text-teal mono" onClick={() => seek(selected.t_start)}>{selected.t_start}s</button></dd>
                {selected.confidence != null && <><dt className="font-semibold text-navy">Detection score</dt><dd><span className="mono">{selected.confidence}</span> <span className="text-xs text-charcoal/60">heuristic, not a calibrated probability</span></dd></>}
                {selected.review && <><dt className="font-semibold text-navy">Host decision</dt><dd>{selected.review.decision} by {selected.review.by}</dd></>}
              </dl>
              {selected.evidence?.length > 0 && <div className="mt-4"><p className="label mb-2">Evidence frames</p><div className="grid grid-cols-3 gap-2">{selected.evidence.filter((x: Any) => x.thumb).slice(0, 3).map((x: Any, i: number) => <a key={i} href={evidenceUrl(report, x.thumb)} target="_blank" rel="noreferrer" title={x.note}><img src={evidenceUrl(report, x.thumb)} alt={x.note} className="rounded-lg border border-line w-full aspect-video object-cover" loading="lazy" /><span className="block text-[10px] text-charcoal/60 mt-0.5 mono">{x.kind} {x.t}s</span></a>)}</div>
                {selected.evidence.filter((x: Any) => x.kind === 'audio').map((x: Any, i: number) => <p key={i} className="mt-2 text-sm rounded-lg bg-ivory px-3 py-2">🎙 {x.note}</p>)}</div>}
              <div className="mt-5 flex flex-wrap gap-2"><button className="btn btn-teal !py-2" disabled={busy} onClick={() => void review('ACCEPTED')}>Accept</button><button className="btn btn-danger !py-2" disabled={busy} onClick={() => void review('REJECTED')}>Reject</button>{selected.review && <button className="btn btn-ghost !py-2" disabled={busy} onClick={() => void review('CLEARED')}>Clear</button>}</div>
              {note && <p role="alert" className="mt-3 text-sm text-red">{note}</p>}
              <p className="text-xs text-charcoal/60 mt-3">Host decisions recompute the score with the same rule engine and are written to the tamper-evident audit trail.</p>
            </div>)}

          <div className="card p-5"><h2 className="text-lg mb-3">Evidence integrity</h2>
            <dl className="text-xs grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5">
              <dt className="font-semibold text-navy">Source SHA-256</dt><dd className="mono break-all">{short(report.source.sha256_original)}</dd>
              <dt className="font-semibold text-navy">Report SHA-256</dt><dd className="mono break-all">{short(report.integrity?.report_sha256)}</dd>
              <dt className="font-semibold text-navy">Signature</dt><dd className="mono">{short(report.integrity?.signature)} · {report.integrity?.key_id}</dd>
              <dt className="font-semibold text-navy">Verification</dt><dd className={ic?.ok ? 'text-teal font-bold' : 'text-red font-bold'}>{ic ? (ic.ok ? '✓ hash and signature valid' : '✗ ' + ic.reasons.join('; ')) : 'verify via backend'}</dd>
              <dt className="font-semibold text-navy">Rule version</dt><dd className="mono">{report.rule_version}</dd>
              <dt className="font-semibold text-navy">Judge</dt><dd>{report.judge.name} {report.judge.version}</dd></dl>
            <details className="mt-3 text-sm"><summary className="cursor-pointer font-semibold text-navy">Validation checks ({report.validation.checks.filter((c: Any) => c.ok).length}/{report.validation.checks.length})</summary>
              <ul className="mt-2 space-y-1">{report.validation.checks.map((c: Any) => <li key={c.name} className="text-xs"><span className={c.ok ? 'text-teal' : 'text-red'}>{c.ok ? '✓' : '✗'}</span> <b>{c.name}</b> — {c.detail}</li>)}</ul></details>
            <details className="mt-2 text-sm"><summary className="cursor-pointer font-semibold text-navy">Audit trail ({report.audit?.length ?? 0})</summary>
              <ul className="mt-2 space-y-1 text-xs">{(report.audit ?? []).map((a: Any, i: number) => <li key={i} className="mono">{a.at.slice(11, 19)} {a.action} <span className="text-charcoal/50">#{a.hash.slice(0, 8)}</span></li>)}{!report.audit?.length && <li className="text-charcoal/60">No host actions yet.</li>}</ul></details>
            <details className="mt-2 text-sm"><summary className="cursor-pointer font-semibold text-navy">Known limitations</summary><ul className="mt-2 list-disc pl-5 text-xs space-y-1">{report.limitations.map((l: string) => <li key={l}>{l}</li>)}</ul></details>
          </div>
        </aside>
      </div>
    </div>
  )
}

function TranscriptFallback({ status, onSubmit }: { status: string; onSubmit: (t: string) => void }) {
  const [txt, setTxt] = useState('')
  return (
    <div><p className="text-sm text-[#7a5a1c] mb-2">No transcript ({status}). Spoken-match points are held for review. The host may type what was said (recorded as host-entered).</p>
      <textarea className="input" rows={2} value={txt} onChange={(e) => setTxt(e.target.value)} placeholder="e.g. dates, coffee, pottery" />
      <button className="btn btn-ghost !py-1.5 mt-2" disabled={!txt.trim()} onClick={() => onSubmit(txt)}>Use host transcript</button></div>
  )
}
