import { lazy, Suspense } from 'react'
import { Route, Routes, Link } from 'react-router-dom'
import Layout from './components/Layout'
import Launch from './pages/Launch'
import Setup from './pages/Setup'
import Library from './pages/Library'
import Prepare from './pages/Prepare'
import Arena from './pages/Arena'
import Cup from './pages/Cup'
import Lab from './pages/Lab'

const Replay = lazy(() => import('./pages/Replay'))

function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-6 py-24 text-center">
      <h1 className="text-4xl mb-3">Page not found</h1>
      <p className="mb-6">That route does not exist in WASL Arena.</p>
      <Link to="/" className="btn btn-primary">Back to launch</Link>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Launch />} />
        <Route path="setup" element={<Setup />} />
        <Route path="games" element={<Library />} />
        <Route path="prepare" element={<Prepare />} />
        <Route path="arena" element={<Arena />} />
        <Route path="replay" element={<Suspense fallback={<div className="p-12 text-center">Loading replay…</div>}><Replay /></Suspense>} />
        <Route path="cup" element={<Cup />} />
        <Route path="lab" element={<Lab />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
