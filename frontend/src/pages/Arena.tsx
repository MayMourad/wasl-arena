import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Judging } from '../components/Judging'
import { Orb, type OrbState } from '../components/Orb'
import { getJob, importReport, submitJudging, type Any } from '../lib/api'
import { GAMES, useSession, type GameId } from '../lib/store'

type Turn = { round: number; subject: string; label: string }

const fmt = (t: number) => `${String(Math.floor(t / 60)).padStart(2, '0')}:${String(Math.floor(t % 60)).padStart(2, '0')}`

export default function Arena() {
  const { s, set, record, nameOf } = useSession()
  const nav = useNavigate()
  const game: GameId = s.game ?? 'football'
  const named = s.players.filter((p) => p.name.trim())

  const turns: Turn[] = useMemo(() => {
    if (game === 'football') return [{ round: 1, subject: 'match', label: `${s.teams.A.name} vs ${s.teams.B.name}` }]
    const r = Math.min(s.settings.rounds, 5)
    const out: Turn[] = []
    for (let i = 1; i <= r; i++) {
      if (game === 'falaj') (['A', 'B'] as const).forEach((t) => out.push({ round: i, subject: t, label: s.teams[t].name }))
      else (named.length ? named : s.players).forEach((p) => out.push({ round: i, subject: p.id, label: nameOf(p.id) }))
    }
    return out
  }, [game, s.settings.rounds, s.teams, s.players])

  const [turnIdx, setTurnIdx] = useState(0)
  const turn = turns[Math.min(turnIdx, turns.length - 1)]
  const duration = game === 'football' ? s.settings.footballSeconds : game === 'falaj' ? s.settings.roundSeconds : 120
  const [left, setLeft] = useState(duration)
  const [running, setRunning] = useState(false)
  useEffect(() => { setLeft(duration); setRunning(false) }, [duration, turnIdx, game])
  useEffect(() => {
    if (!running) return
    const id = setInterval(() => setLeft((l) => { if (l <= 1) { setRunning(false); return 0 } return l - 1 }), 1000)
    return () => clearInterval(id)
  }, [running])

  // camera + recording
  const vid = useRef<HTMLVideoElement>(null)
  const stream = useRef<MediaStream | null>(null)
  const rec = useRef<MediaRecorder | null>(null)
  const chunks = useRef<Blob[]>([])
  const [camOn, setCamOn] = useState(false)
  const [recording, setRecording] = useState(false)
  const [clip, setClip] = useState<{ blob: Blob; name: string; url: string } | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [job, setJob] = useState<Any | null>(null)
  const [busy, setBusy] = useState(false)

  async function camera() {
    try {
      const st = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: true })
      stream.current = st; setCamOn(true); setMsg(null)
      requestAnimationFrame(() => { if (vid.current) { vid.current.srcObject = st; void vid.current.play() } })
    } catch { setMsg('Camera or microphone permission was denied or unavailable. You can upload a video file instead.') }
  }
  function stopCamera() { stream.current?.getTracks().forEach((t) => t.stop()); stream.current = null; setCamOn(false) }
  useEffect(() => () => stopCamera(), [])

  function startRec() {
    if (!stream.current) return
    const mime = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm', 'video/mp4'].find((m) => MediaRecorder.isTypeSupported(m))
    chunks.current = []
    const r = new MediaRecorder(stream.current, mime ? { mimeType: mime } : undefined)
    r.ondataavailable = (e) => e.data.size && chunks.current.push(e.data)
    r.onstop = () => {
      const blob = new Blob(chunks.current, { type: r.mimeType || 'video/webm' })
      setClip({ blob, name: `${game}-r${turn.round}-${turn.subject}.${blob.type.includes('mp4') ? 'mp4' : 'webm'}`, url: URL.createObjectURL(blob) })
    }
    r.start(1000); rec.current = r; setRecording(true); setClip(null)
  }
  function stopRec() { rec.current?.stop(); setRecording(false) }
  useEffect(() => { if (left === 0 && recording) stopRec() }, [left, recording])

  function startRound() {
    record('turn_started', { game, round: turn.round, subject: turn.subject })
    setLeft(duration); setRunning(true)
    if (camOn && !recording) startRec()
  }
  function onFile(f?: File | null) {
    if (!f) return
    setClip({ blob: f, name: f.name, url: URL.createObjectURL(f) }); setMsg(null)
  }

  function buildConfig(): Record<string, unknown> {
    const g = s.settings.goal
    if (game === 'football') {
      return {
        teams: { A: { name: s.teams.A.name, color: s.teams.A.color }, B: { name: s.teams.B.name, color: s.teams.B.color } },
        ball: { color: s.settings.teamColors.ball },
        goals: { A_attacks: [[1 - g.depth, g.top], [1, g.top], [1, g.bottom], [1 - g.depth, g.bottom]], B_attacks: [[0, g.top], [g.depth, g.top], [g.depth, g.bottom], [0, g.bottom]] },
        regulation_seconds: s.settings.footballSeconds,
        players_per_team: Math.max(1, ...(['A', 'B'] as const).map((t) => s.teams[t].playerIds.length)) + 1,
      }
    }
    if (game === 'falaj') return { round_seconds: s.settings.roundSeconds }
    return { mission: s.settings.mission }
  }

  async function send() {
    if (!clip) return
    setBusy(true); setMsg(null); setJob({ stage: 'uploaded', progress: 0, detail: 'uploading', status: 'running' })
    record('video_submitted', { game, round: turn.round, subject: turn.subject, file: clip.name, bytes: clip.blob.size })
    try {
      const { job_id, report_id } = await submitJudging(game, clip.blob, clip.name, buildConfig())
      for (;;) {
        const j = await getJob(job_id); setJob(j)
        if (j.status === 'done') break
        if (j.status === 'error') throw new Error(j.error || 'judging failed')
        await new Promise((r) => setTimeout(r, 600))
      }
      sessionStorage.setItem('wasl-pending', JSON.stringify({ game, round: turn.round, subject: turn.subject, label: turn.label }))
      record('report_received', { report_id, game })
      nav(`/replay?report=${report_id}`)
    } catch (e) {
      setMsg(`${(e as Error).message}. Is the AI judge backend reachable? You can still explore sample replays.`); setBusy(false); setJob(null)
    }
  }

  async function onImport(f?: File | null) {
    if (!f) return
    try {
      const r = await importReport(f)
      if (!r.ok) { setMsg('Report REJECTED: ' + r.reasons.join('; ')); return }
      sessionStorage.setItem('wasl-pending', JSON.stringify({ game, round: turn.round, subject: turn.subject, label: turn.label }))
      record('report_imported', { report_id: r.report_id }); nav(`/replay?report=${r.report_id}`)
    } catch { setMsg('Could not reach the verifier. Start the backend to import reports.') }
  }

  const results = s.results.filter((r) => r.game === game)
  const done = (t: Turn) => results.some((r) => r.round === t.round && r.subject === t.subject)
  const orb: OrbState = busy ? 'processing' : recording ? 'watching' : 'idle'
  const total = (sub: string) => results.filter((r) => r.subject === sub).reduce((a, r) => a + r.score, 0)

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 py-8">
      <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
        <div><p className="label">Live arena · {GAMES[game].mode} game</p><h1 className="text-4xl mt-1">{GAMES[game].name}</h1>
          <p className="mt-1 text-charcoal/75">{game === 'football' ? 'Match' : `Round ${turn.round} of ${Math.min(s.settings.rounds, 5)}`} · <b className="text-navy">{game === 'souq' ? `${turn.label}'s turn` : turn.label}</b></p></div>
        <div className="flex gap-2 flex-wrap">{(Object.keys(GAMES) as GameId[]).map((k) => <button key={k} className={`btn !py-2 !text-sm ${k === game ? 'btn-primary' : 'btn-ghost'}`} onClick={() => { set({ game: k }); setTurnIdx(0); setClip(null) }}>{GAMES[k].name}</button>)}</div>
      </div>

      <div className="grid lg:grid-cols-[1.5fr_1fr] gap-6">
        <div className="space-y-4">
          {job || busy ? <Judging job={job} error={msg} /> : (
            <div className="card overflow-hidden">
              <div className="relative bg-navy aspect-video grid place-items-center">
                {clip && !camOn ? <video src={clip.url} controls className="w-full h-full object-contain bg-black" /> :
                  camOn ? <video ref={vid} muted playsInline className="w-full h-full object-cover" /> :
                    <div className="text-center text-white/80 p-6"><Orb state={orb} size={160} /><p className="mt-2 text-sm">Turn the camera on to record, or upload a clip.</p></div>}
                {recording && <span className="absolute top-3 left-3 flex items-center gap-2 rounded-full bg-red text-white text-xs font-bold px-3 py-1"><span className="size-2 rounded-full bg-white animate-pulse" />REC</span>}
                <span className="absolute top-3 right-3 mono text-2xl font-semibold rounded-xl bg-navy/80 text-ivory px-3 py-1" aria-live="off">{fmt(left)}</span>
              </div>
              <div className="p-4 flex flex-wrap gap-2 items-center">
                {!camOn ? <button className="btn btn-primary" onClick={camera}>● Camera + mic</button> : <button className="btn btn-ghost" onClick={stopCamera}>Turn camera off</button>}
                {camOn && !recording && <button className="btn btn-danger" onClick={startRec}>Record</button>}
                {recording && <button className="btn btn-danger" onClick={stopRec}>■ Stop recording</button>}
                <label className="btn btn-ghost cursor-pointer">Upload video<input type="file" accept="video/*" hidden onChange={(e) => onFile(e.target.files?.[0])} /></label>
                <label className="btn btn-ghost cursor-pointer">Import AI report<input type="file" accept="application/json,.json" hidden onChange={(e) => void onImport(e.target.files?.[0])} /></label>
                <button className="btn btn-teal ml-auto" disabled={!clip} onClick={send}>Send to AI Referee →</button>
              </div>
              {clip && <p className="px-4 pb-3 text-xs text-charcoal/70">Clip ready: {clip.name} · {(clip.blob.size / 1e6).toFixed(1)} MB. It is hashed on upload so the judging report can be traced to this exact file.</p>}
              {camOn && clip && <button className="mx-4 mb-4 text-sm underline" onClick={() => { stopCamera() }}>Preview recorded clip</button>}
              {msg && <p role="alert" className="mx-4 mb-4 rounded-xl bg-red/10 text-red px-4 py-3 text-sm">{msg} <Link to="/replay?report=sample-football_goal" className="underline font-semibold">Open a sample replay</Link></p>}
            </div>
          )}
          <div className="card p-5">
            <h2 className="text-lg mb-3">Host controls</h2>
            <div className="flex flex-wrap gap-2">
              <button className="btn btn-primary" onClick={startRound} disabled={running}>▶ Start {game === 'football' ? 'match' : 'round'}</button>
              <button className="btn btn-ghost" onClick={() => setRunning(!running)} disabled={left === 0}>{running ? 'Pause' : 'Resume'}</button>
              <button className="btn btn-ghost" onClick={() => { setRunning(false); setLeft(duration) }}>Reset timer</button>
              <button className="btn btn-ghost" disabled={turnIdx === 0} onClick={() => setTurnIdx(turnIdx - 1)}>← Previous turn</button>
              <button className="btn btn-ghost" disabled={turnIdx >= turns.length - 1} onClick={() => { record('turn_skipped', { turn: turn.subject }); setTurnIdx(turnIdx + 1); setClip(null) }}>Next turn →</button>
              {game === 'football' && <button className="btn btn-ghost" onClick={() => { set({}); record('host_penalty', { team: 'A', points: -1 }) }} title="Logged in the audit trail">Penalty −1 (log)</button>}
            </div>
            <p className="text-sm text-charcoal/70 mt-3">{game === 'souq' ? `Mission: ${s.settings.mission.requested.join(', ')} · budget AED ${s.settings.mission.budget}.` : game === 'falaj' ? 'Teams build with printed tiles; stop at the buzzer and keep hands off the board.' : `Tie-break: golden goal up to ${s.settings.goldenGoalSeconds}s.`}</p>
          </div>
        </div>

        <aside className="space-y-4">
          <div className="card p-5">
            <h2 className="text-lg mb-3">Turn order</h2>
            <ol className="space-y-1.5">{turns.map((t, i) => (
              <li key={i}><button onClick={() => { setTurnIdx(i); setClip(null) }} className={`w-full flex items-center gap-3 rounded-xl px-3 py-2 text-left text-sm transition ${i === turnIdx ? 'bg-navy text-white' : 'hover:bg-ivory'}`}>
                <span className="mono text-xs opacity-70">R{t.round}</span><span className="flex-1 font-medium">{t.label}</span>
                {done(t) ? <span className="text-xs rounded-full bg-teal text-white px-2 py-0.5">scored</span> : <span className="text-xs opacity-60">pending</span>}</button></li>))}</ol>
          </div>
          <div className="card p-5">
            <h2 className="text-lg mb-3">Verified scoreboard</h2>
            {results.length === 0 ? <p className="text-sm text-charcoal/65">No verified results yet. Scores appear only after the AI report is reviewed and applied.</p> :
              <ul className="space-y-2">{[...new Set(results.map((r) => r.subject))].map((sub) => (
                <li key={sub} className="flex items-center justify-between rounded-xl bg-ivory px-4 py-2.5"><span className="font-medium">{results.find((r) => r.subject === sub)?.subjectLabel}</span><span className="display text-2xl text-navy">{total(sub)}</span></li>))}</ul>}
            <Link to="/cup" className="btn btn-ghost w-full mt-4">Open Family Cup →</Link>
          </div>
        </aside>
      </div>
    </div>
  )
}
