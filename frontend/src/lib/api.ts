/* API client. Backend URL comes from VITE_API_URL (empty in dev: Vite proxies /api). */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Any = any

export const API = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ?? ''

/** Static assets (samples, printables) resolve against the deploy base path (works on Vercel and GitHub Pages). */
export const asset = (p: string) => `${import.meta.env.BASE_URL}${p.replace(/^\//, '')}`

export const url = (p: string) => (p.startsWith('http') ? p : `${API}${p}`)

export async function health(): Promise<Any | null> {
  try {
    const r = await fetch(url('/api/health'), { signal: AbortSignal.timeout(4000) })
    return r.ok ? await r.json() : null
  } catch {
    return null
  }
}

export async function submitJudging(game: string, file: Blob, filename: string, config: Record<string, unknown>) {
  const fd = new FormData()
  fd.append('file', file, filename)
  fd.append('config_json', JSON.stringify(config))
  const r = await fetch(url(`/api/judge/${game}`), { method: 'POST', body: fd })
  if (!r.ok) throw new Error(`Upload failed (${r.status})`)
  return (await r.json()) as { job_id: string; report_id: string }
}

export async function getJob(id: string): Promise<Any> {
  const r = await fetch(url(`/api/jobs/${id}`))
  if (!r.ok) throw new Error('job not found')
  return r.json()
}

/** Reports: live API ids, or pre-computed samples ("sample-<fixture>") served statically. */
export async function getReport(id: string): Promise<Any> {
  if (id.startsWith('sample-')) {
    const r = await fetch(asset(`samples/${id.slice(7)}.json`))
    if (!r.ok) throw new Error('sample not found')
    return r.json()
  }
  const r = await fetch(url(`/api/reports/${id}`))
  if (!r.ok) throw new Error('report not found')
  return r.json()
}

export const mediaUrl = (report: Any) =>
  report?.sample ? asset(`samples/${report.sample}.mp4`) : url(`/api/media/${report.report_id}`)

export const evidenceUrl = (report: Any, thumb: string) => (report?.sample ? asset(thumb) : url(thumb))

export async function postReview(id: string, event_id: string, decision: string, by: string, note = '') {
  const r = await fetch(url(`/api/reports/${id}/review`), {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event_id, decision, by, note }),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function postAssignments(id: string, assignments: Record<string, string>, by: string) {
  const r = await fetch(url(`/api/reports/${id}/assignments`), {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ assignments, by }),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function postTranscript(id: string, text: string, by: string) {
  const r = await fetch(url(`/api/reports/${id}/transcript`), {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, by }),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function importReport(file: File) {
  const fd = new FormData()
  fd.append('file', file)
  const r = await fetch(url('/api/reports/verify'), { method: 'POST', body: fd })
  if (!r.ok) throw new Error('could not verify report')
  return r.json() as Promise<{ ok: boolean; reasons: string[]; report_id: string | null }>
}

export async function audit(session: string, action: string, detail: Record<string, unknown>) {
  try { await fetch(url(`/api/audit/${session}`), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action, detail }) }) } catch { /* backend optional for local audit */ }
}

export async function falajPreview(tiles: Any[]) {
  const r = await fetch(url('/api/falaj/analyze'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ layout: 'oasis-1', tiles }) })
  return r.json()
}
