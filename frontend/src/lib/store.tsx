import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { asset, audit, type Any } from './api'

export type GameId = 'football' | 'falaj' | 'souq'
export type Player = { id: string; name: string }
export type Team = { id: 'A' | 'B'; name: string; color: string; playerIds: string[] }
export type Result = {
  id: string; game: GameId; reportId: string; round: number; subject: string; subjectLabel: string
  score: number; detail: string; verified: boolean; sample?: boolean; at: string; mvp?: string | null; winner?: string | null
}
export type Settings = {
  rounds: number; roundSeconds: number; footballSeconds: number; goldenGoalSeconds: number
  teamColors: { A: string; B: string; ball: string }
  mission: { requested: string[]; budget: number }
  goal: { depth: number; top: number; bottom: number }
}
export type Session = {
  id: string; family: string; lang: 'en' | 'ar'; players: Player[]; teams: Record<'A' | 'B', Team>
  game: GameId | null; settings: Settings; results: Result[]; log: { at: string; action: string; hash: string; prev: string }[]
  ready: boolean
}

const DEFAULT: Session = {
  id: 'wasl-' + Math.random().toString(36).slice(2, 10),
  family: '', lang: 'en', ready: false,
  players: [{ id: 'p1', name: '' }, { id: 'p2', name: '' }, { id: 'p3', name: '' }, { id: 'p4', name: '' }],
  teams: { A: { id: 'A', name: 'Team A', color: 'red', playerIds: ['p1', 'p2'] }, B: { id: 'B', name: 'Team B', color: 'blue', playerIds: ['p3', 'p4'] } },
  game: null,
  settings: {
    rounds: 3, roundSeconds: 90, footballSeconds: 120, goldenGoalSeconds: 60,
    teamColors: { A: 'red', B: 'blue', ball: 'yellow' },
    mission: { requested: ['dates', 'coffee', 'pottery'], budget: 60 },
    goal: { depth: 0.1, top: 0.3, bottom: 0.7 },
  },
  results: [], log: [],
}

async function sha256(text: string) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('')
}

type Ctx = {
  s: Session
  set: (patch: Partial<Session>) => void
  setSettings: (patch: Partial<Settings>) => void
  record: (action: string, detail?: Record<string, unknown>) => void
  addResult: (r: Omit<Result, 'id' | 'at'>) => void
  reset: () => void
  loadDemo: () => Promise<void>
  nameOf: (id: string) => string
}
const C = createContext<Ctx>(null as unknown as Ctx)
export const useSession = () => useContext(C)

export function SessionProvider({ children }: { children: ReactNode }) {
  const [s, setS] = useState<Session>(() => {
    try { const raw = localStorage.getItem('wasl-session'); if (raw) return { ...DEFAULT, ...JSON.parse(raw) } } catch { /* ignore */ }
    return DEFAULT
  })
  useEffect(() => {
    try { localStorage.setItem('wasl-session', JSON.stringify(s)) } catch { /* private mode */ }
    document.documentElement.dir = s.lang === 'ar' ? 'rtl' : 'ltr'
    document.documentElement.lang = s.lang
  }, [s])

  const record = useCallback((action: string, detail: Record<string, unknown> = {}) => {
    setS((cur) => {
      const prev = cur.log.length ? cur.log[cur.log.length - 1].hash : 'GENESIS'
      const at = new Date().toISOString()
      const entry = { at, action, prev, hash: '' }
      void sha256(JSON.stringify({ at, action, detail, prev })).then((h) => {
        setS((c2) => ({ ...c2, log: c2.log.map((e) => (e.at === at && e.action === action && !e.hash ? { ...e, hash: h } : e)) }))
      })
      void audit(cur.id, action, detail)
      return { ...cur, log: [...cur.log, entry] }
    })
  }, [])

  const set = useCallback((patch: Partial<Session>) => setS((c) => ({ ...c, ...patch })), [])
  const setSettings = useCallback((patch: Partial<Settings>) => setS((c) => ({ ...c, settings: { ...c.settings, ...patch } })), [])
  const addResult = useCallback((r: Omit<Result, 'id' | 'at'>) => {
    setS((c) => ({ ...c, results: [...c.results.filter((x) => !(x.game === r.game && x.round === r.round && x.subject === r.subject)), { ...r, id: crypto.randomUUID(), at: new Date().toISOString() }] }))
    record('apply_result', { game: r.game, round: r.round, subject: r.subject, score: r.score, report: r.reportId, verified: r.verified })
  }, [record])
  const reset = useCallback(() => { localStorage.removeItem('wasl-session'); setS({ ...DEFAULT, id: 'wasl-' + Math.random().toString(36).slice(2, 10) }) }, [])

  const nameOf = useCallback((id: string) => s.players.find((p) => p.id === id)?.name || `Player ${id.replace('p', '')}`, [s.players])

  /** Demo session built from the pre-computed sample reports (synthetic fixtures; flagged sample:true). */
  const loadDemo = useCallback(async () => {
    const get = async (n: string): Promise<Any> => (await fetch(asset(`samples/${n}.json`))).json()
    const [fb, fv, fp, sc, sb] = await Promise.all(['football_goal', 'falaj_valid', 'falaj_partial', 'souq_correct', 'souq_budget_dup'].map(get))
    const players = ['Sara', 'Omar', 'Mariam', 'Khalid'].map((n, i) => ({ id: `p${i + 1}`, name: n }))
    const mk = (g: GameId, round: number, subject: string, label: string, rep: Any, score: number, extra: Partial<Result> = {}): Result => ({
      id: crypto.randomUUID(), game: g, reportId: 'sample-' + rep.sample, round, subject, subjectLabel: label, score,
      detail: 'Synthetic fixture sample', verified: true, sample: true, at: new Date().toISOString(), ...extra })
    setS((c) => ({
      ...c, family: c.family || 'Al Mansoori Family (demo)', players, ready: true,
      results: [
        mk('football', 1, 'A', 'Team A', fb, fb.summary.score.A, { mvp: 'Sara', winner: 'A', detail: `Team A ${fb.summary.score.A} - ${fb.summary.score.B} Team B` }),
        mk('football', 1, 'B', 'Team B', fb, fb.summary.score.B, { mvp: 'Sara', winner: 'A', detail: `Team A ${fb.summary.score.A} - ${fb.summary.score.B} Team B` }),
        mk('falaj', 1, 'A', 'Team A', fv, fv.summary.score.total, { detail: 'All 3 farms watered' }),
        mk('falaj', 1, 'B', 'Team B', fp, fp.summary.score.total, { detail: '2 farms watered, 1 leak' }),
        mk('souq', 1, 'p1', 'Sara', sc, sc.summary.score.total, { detail: `AED ${sc.summary.spend} spent` }),
        mk('souq', 1, 'p2', 'Omar', sb, sb.summary.score.total, { detail: `AED ${sb.summary.spend} spent` }),
      ],
    }))
    record('load_demo_session', { note: 'synthetic fixture samples' })
  }, [record])

  const v = useMemo(() => ({ s, set, setSettings, record, addResult, reset, loadDemo, nameOf }), [s, set, setSettings, record, addResult, reset, loadDemo, nameOf])
  return <C.Provider value={v}>{children}</C.Provider>
}

export const GAMES: Record<GameId, { name: string; ar: string; mode: 'Team' | 'Individual'; tagline: string }> = {
  football: { name: 'Football AI', ar: 'كرة القدم', mode: 'Team', tagline: 'Goals, possession and MVP from real tracking' },
  falaj: { name: 'Falaj Flow', ar: 'فلج', mode: 'Team', tagline: 'Build the channels. The AI traces the water.' },
  souq: { name: 'Souq Signal', ar: 'إشارة السوق', mode: 'Individual', tagline: 'Show it. Say it. Stay in budget.' },
}
