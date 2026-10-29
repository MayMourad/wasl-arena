import { Orb, type OrbState } from './Orb'

/** Staged judging sequence driven by REAL backend job stages (not a timer):
 *  Uploading -> Extracting Evidence -> Detecting Events -> Applying Rules -> Verified Result. */
const STEPS = [
  { key: ['uploaded'], label: 'Uploading', hint: 'Source hashed (SHA-256) on arrival' },
  { key: ['extracting'], label: 'Extracting Evidence', hint: 'FFmpeg decode, frame sampling, audio track' },
  { key: ['detecting', 'transcribing', 'events'], label: 'Detecting Events', hint: 'Tracking, markers, speech, event candidates' },
  { key: ['rules'], label: 'Applying Rules', hint: 'Deterministic rule engine scores each event' },
  { key: ['verified'], label: 'Verified Result', hint: 'Report sealed with hash + signature' },
]

export function Judging({ job, error }: { job: { stage: string; progress: number; detail: string; status: string } | null; error?: string | null }) {
  const idx = job ? Math.max(0, STEPS.findIndex((s) => s.key.includes(job.stage))) : 0
  const done = job?.status === 'done'
  const orb: OrbState = error || job?.status === 'error' ? 'review' : done ? 'verified' : idx >= 1 ? 'processing' : 'watching'
  return (
    <div className="card p-6 sm:p-8 grid md:grid-cols-[auto_1fr] gap-6 items-center rise" role="status" aria-live="polite">
      <div className="mx-auto"><Orb state={orb} size={220} /></div>
      <div>
        <p className="label">AI Referee</p>
        <h3 className="text-2xl mt-1 mb-4">{error ? 'Judging failed' : done ? 'Result verified' : 'Judging in progress'}</h3>
        <ol className="space-y-2.5">
          {STEPS.map((s, i) => {
            const state = done || i < idx ? 'done' : i === idx && !error ? 'active' : 'todo'
            return (
              <li key={s.label} className="flex items-start gap-3">
                <span className={`mt-0.5 grid place-items-center size-6 rounded-full text-xs font-bold shrink-0 ${state === 'done' ? 'bg-teal text-white' : state === 'active' ? 'bg-gold text-navy' : 'bg-line text-charcoal/50'}`}>
                  {state === 'done' ? '✓' : i + 1}
                </span>
                <div className="flex-1">
                  <div className={`font-semibold ${state === 'todo' ? 'text-charcoal/45' : 'text-navy'}`}>{s.label}</div>
                  {state === 'active' && (
                    <>
                      <div className="text-sm text-charcoal/70">{job?.detail || s.hint}</div>
                      <div className="mt-1.5 h-1.5 rounded-full bg-line overflow-hidden"><div className="h-full shimmer bg-teal/70 transition-all" style={{ width: `${Math.max(6, (job?.progress ?? 0) * 100)}%` }} /></div>
                    </>
                  )}
                  {state !== 'active' && <div className="text-xs text-charcoal/50">{s.hint}</div>}
                </div>
              </li>
            )
          })}
        </ol>
        {error && <p className="mt-4 text-red font-medium">{error}</p>}
      </div>
    </div>
  )
}
