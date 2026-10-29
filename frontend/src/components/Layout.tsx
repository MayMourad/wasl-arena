import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { health } from '../lib/api'
import { tr } from '../lib/i18n'
import { useSession } from '../lib/store'
import { TEAM } from '../lib/team'

const LINKS = [
  ['/', 'nav.launch'], ['/setup', 'nav.setup'], ['/games', 'nav.library'], ['/prepare', 'nav.prepare'],
  ['/arena', 'nav.arena'], ['/replay', 'nav.replay'], ['/cup', 'nav.cup'], ['/lab', 'nav.lab'],
] as const

export function Logo({ light = false }: { light?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <svg width="30" height="30" viewBox="0 0 64 64" aria-hidden><rect width="64" height="64" rx="14" fill={light ? '#F7F3EB' : '#12243A'} /><path d="M10 20l8 24 7-16 7 16 8-24" fill="none" stroke="#C6A36B" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" /><circle cx="52" cy="14" r="5" fill="#167E80" /></svg>
      <span className="display text-xl font-semibold" style={{ color: light ? '#F7F3EB' : undefined }}>WASL <span className="font-normal opacity-70">Arena</span></span>
    </span>
  )
}

export default function Layout() {
  const { s, set } = useSession()
  const [open, setOpen] = useState(false)
  const [api, setApi] = useState<'checking' | 'online' | 'offline'>('checking')
  const loc = useLocation()
  useEffect(() => { setOpen(false); window.scrollTo(0, 0) }, [loc.pathname])
  useEffect(() => { void health().then((h) => setApi(h ? 'online' : 'offline')) }, [])
  const dark = loc.pathname === '/'

  return (
    <div className="min-h-screen flex flex-col">
      <header className={`sticky top-0 z-40 backdrop-blur ${dark ? 'bg-navy/80 border-b border-white/10' : 'bg-ivory/85 border-b border-line'}`}>
        <div className="mx-auto max-w-7xl px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <NavLink to="/" aria-label="WASL Arena home"><Logo light={dark} /></NavLink>
          <nav className="hidden lg:flex items-center gap-1" aria-label="Primary">
            {LINKS.map(([to, k]) => (
              <NavLink key={to} to={to} end={to === '/'}
                className={({ isActive }) => `px-3 py-2 rounded-full text-sm font-medium transition-colors ${dark ? (isActive ? 'bg-white/15 text-white' : 'text-white/70 hover:text-white') : (isActive ? 'bg-navy text-white' : 'text-charcoal/70 hover:text-navy hover:bg-white')}`}>
                {tr(k, s.lang)}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            <span title={api === 'online' ? 'AI Referee backend connected' : api === 'offline' ? 'Backend not reachable: live judging unavailable, sample replays still work' : 'Checking backend'}
              className={`hidden sm:inline-flex items-center gap-1.5 text-xs font-medium rounded-full px-2.5 py-1 ${dark ? 'bg-white/10 text-white/80' : 'bg-white border border-line text-charcoal/80'}`}>
              <span className={`size-2 rounded-full ${api === 'online' ? 'bg-teal' : api === 'offline' ? 'bg-red' : 'bg-gold'}`} />
              {api === 'online' ? 'AI judge online' : api === 'offline' ? 'AI judge offline' : 'Connecting'}
            </span>
            <button className={`btn btn-ghost !py-1.5 !px-3 text-sm ${dark ? '!text-white !border-white/25' : ''}`} onClick={() => set({ lang: s.lang === 'en' ? 'ar' : 'en' })} aria-label="Switch language">
              {s.lang === 'en' ? 'العربية' : 'English'}
            </button>
            <button className={`lg:hidden btn btn-ghost !px-3 ${dark ? '!text-white !border-white/25' : ''}`} onClick={() => setOpen(!open)} aria-expanded={open} aria-label="Menu">☰</button>
          </div>
        </div>
        {open && (
          <nav className={`lg:hidden px-4 pb-4 grid grid-cols-2 gap-2 ${dark ? 'bg-navy' : 'bg-ivory'}`}>
            {LINKS.map(([to, k]) => <NavLink key={to} to={to} end={to === '/'} className="btn btn-ghost !justify-start !text-sm">{tr(k, s.lang)}</NavLink>)}
          </nav>
        )}
      </header>
      <main className="flex-1"><Outlet /></main>
      <footer className={`${dark ? 'bg-navy text-white/70' : 'text-charcoal/60'} text-sm border-t ${dark ? 'border-white/10' : 'border-line'}`}>
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-6 grid gap-3 md:grid-cols-2">
          <div>
            <p className={`font-semibold ${dark ? 'text-gold' : 'text-navy'}`}>Team {TEAM.number} · Team code {TEAM.code} · {TEAM.track}</p>
            <p>{TEAM.members.map((m) => `${m.name} (${m.grade})`).join(' · ')}</p>
          </div>
          <div className="md:text-right">
            <p>6th Annual COE STEM Programming with AI Competition · AI for Family</p>
            <p>Every score is backed by replayable evidence. Uncertain detections are never counted without host review.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
