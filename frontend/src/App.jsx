import { useState, useEffect, useCallback, useRef } from 'react'
import { Network } from '@capacitor/network'
import { API_BASE } from './config'
import Navbar from './Navbar'
import SchedulePage from './SchedulePage'
import './App.css'

// ── Icons ────────────────────────────────────────────────

function IconBulb({ on }) {
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
      {on && <circle cx="18" cy="17" r="13" fill="rgba(245,158,11,0.15)" />}
      <path
        d="M12 17C12 12.582 14.686 9 18 9s6 3.582 6 8c0 2.8-1.4 5-3 7h-6c-1.6-2-3-4.2-3-7z"
        fill={on ? 'rgba(245,158,11,0.25)' : 'transparent'}
        stroke={on ? '#f59e0b' : 'rgba(255,255,255,0.25)'}
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <rect x="15" y="24" width="6" height="1.8" rx="0.5" fill={on ? '#f59e0b' : 'rgba(255,255,255,0.2)'} />
      <rect x="15.5" y="25.8" width="5" height="1.8" rx="0.5" fill={on ? '#d97706' : 'rgba(255,255,255,0.15)'} />
      <rect x="16" y="27.6" width="4" height="1.4" rx="0.5" fill={on ? '#b45309' : 'rgba(255,255,255,0.1)'} />
      {on && <>
        <line x1="18" y1="3"  x2="18" y2="5.5" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="8"  y1="6"  x2="9.8" y2="7.8" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="28" y1="6"  x2="26.2" y2="7.8" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="4"  y1="17" x2="6.5" y2="17" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="32" y1="17" x2="29.5" y2="17" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" />
      </>}
    </svg>
  )
}

function IconFan({ on }) {
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
      {on && <circle cx="18" cy="18" r="13" fill="rgba(56,189,248,0.1)" />}
      <circle cx="18" cy="18" r="12" stroke={on ? '#38bdf8' : 'rgba(255,255,255,0.2)'} strokeWidth="1.4" />
      <g className={on ? 'fan-blades spinning' : 'fan-blades'} style={{ transformOrigin: '18px 18px' }}>
        <path d="M18 18 Q15.5 11 18 7  Q21.5 11 18 18Z" fill={on ? '#38bdf8' : 'rgba(255,255,255,0.25)'} />
        <path d="M18 18 Q25 15.5 29 18 Q25 21.5 18 18Z" fill={on ? '#38bdf8' : 'rgba(255,255,255,0.25)'} />
        <path d="M18 18 Q20.5 25 18 29 Q14.5 25 18 18Z" fill={on ? '#38bdf8' : 'rgba(255,255,255,0.25)'} />
        <path d="M18 18 Q11 20.5 7  18 Q11 14.5 18 18Z" fill={on ? '#38bdf8' : 'rgba(255,255,255,0.25)'} />
      </g>
      <circle cx="18" cy="18" r="3.5" fill={on ? '#0ea5e9' : '#2a2a3a'} />
      <circle cx="18" cy="18" r="1.5" fill={on ? '#fff' : '#555'} />
    </svg>
  )
}

// ── Device Card ──────────────────────────────────────────

function DeviceCard({ name, isOn, onToggle, index }) {
  const [loading, setLoading] = useState(false)
  const isLight = name.toLowerCase().includes('light')
  const isFan   = name.toLowerCase().includes('fan')

  const color     = isLight ? 'var(--amber)' : isFan ? 'var(--sky)' : 'var(--accent)'
  const dimColor  = isLight ? 'var(--amber-dim)' : isFan ? 'var(--sky-dim)' : 'var(--accent-dim)'
  const glowColor = isLight ? 'var(--amber-glow)' : isFan ? 'var(--sky-glow)' : 'var(--accent-glow)'

  const label     = name.replace(/([a-z])(\d)/g, '$1 $2').replace(/^./, s => s.toUpperCase())
  const typeLabel = isLight ? 'Light' : isFan ? 'Fan' : 'Device'

  const handleToggle = async () => {
    if (loading) return
    setLoading(true)
    await onToggle(name, !isOn)
    setLoading(false)
  }

  return (
    <div
      className={`card ${isOn ? 'card--on' : ''}`}
      style={{ '--card-color': color, '--card-dim': dimColor, '--card-glow': glowColor, animationDelay: `${index * 60}ms` }}
      onClick={handleToggle}
    >
      <div className="card__icon">
        {isLight ? <IconBulb on={isOn} /> : isFan ? <IconFan on={isOn} /> : null}
      </div>
      <div className="card__info">
        <span className="card__name">{label}</span>
        <span className="card__type">{typeLabel}</span>
      </div>
      <div
        className={`card__status-dot ${isOn ? 'card__status-dot--on' : ''}`}
        style={{ '--card-color': color }}
      />
      {loading && <div className="card__shimmer" />}
    </div>
  )
}

// ── Section ──────────────────────────────────────────────

function Section({ title, icon, devices, states, onToggle, allOn, onAllToggle }) {
  return (
    <section className="section">
      <div className="section__header">
        <div className="section__title">
          <span className="section__icon">{icon}</span>
          <span>{title}</span>
        </div>
        <button
          className={`section__all-btn ${allOn ? 'section__all-btn--on' : ''}`}
          onClick={onAllToggle}
        >
          {allOn ? 'All Off' : 'All On'}
        </button>
      </div>
      <div className="grid">
        {devices.map((name, i) => (
          <DeviceCard key={name} name={name} isOn={states[name] ?? false} onToggle={onToggle} index={i} />
        ))}
      </div>
    </section>
  )
}

// ── Home Page ────────────────────────────────────────────

function HomePage({ devices, states, setStates, connected, setConnected, loading, error, onRetry }) {
  const lights = devices.filter(d => d.toLowerCase().includes('light'))
  const fans   = devices.filter(d => d.toLowerCase().includes('fan'))
  const allLightsOn = lights.length > 0 && lights.every(d => states[d])
  const allFansOn   = fans.length   > 0 && fans.every(d => states[d])
  const onCount = devices.filter(d => states[d]).length

  const toggleDevice = async (name, newState) => {
    const state = newState ? 'on' : 'off'
    try {
      const res = await fetch(`${API_BASE}/control/${name}/${state}`)
      if (!res.ok) throw new Error()
      setStates(prev => ({ ...prev, [name]: newState }))
      setConnected(true)
    } catch {
      setConnected(false)
    }
  }

  const toggleAll = async (list, turnOn) => {
    for (const d of list) await toggleDevice(d, turnOn)
  }

  if (loading) return (
    <div className="splash">
      <div className="splash__spinner" />
      <p>Connecting…</p>
    </div>
  )

  if (error) return (
    <div className="splash">
      <span className="splash__icon">⚠️</span>
      <p className="splash__msg">Can't reach the server</p>
      <p className="splash__sub">{API_BASE}</p>
      <button className="btn-primary" onClick={onRetry}>Retry</button>
    </div>
  )

  return (
    <>
      {/* Header */}
      <header className="header">
        <div className="header__left">
          <h1 className="header__title">Smart Switch</h1>
          <p className="header__sub">{onCount} of {devices.length} active</p>
        </div>
        <div className={`pill ${connected ? 'pill--on' : 'pill--off'}`}>
          <span className="pill__dot" />
          {connected ? 'Live' : 'Offline'}
        </div>
      </header>

      {/* Summary bar */}
      <div className="summary">
        <div className="summary__item">
          <span className="summary__val">{lights.filter(d => states[d]).length}</span>
          <span className="summary__label">Lights On</span>
        </div>
        <div className="summary__divider" />
        <div className="summary__item">
          <span className="summary__val">{fans.filter(d => states[d]).length}</span>
          <span className="summary__label">Fans On</span>
        </div>
        <div className="summary__divider" />
        <button
          className={`summary__master ${onCount === devices.length ? 'summary__master--on' : ''}`}
          onClick={() => toggleAll(devices, onCount !== devices.length)}
        >
          {onCount === devices.length ? 'All Off' : 'All On'}
        </button>
      </div>

      {/* Device sections */}
      <main className="content">
        {lights.length > 0 && (
          <Section title="Lights" icon="💡" devices={lights} states={states} onToggle={toggleDevice}
            allOn={allLightsOn} onAllToggle={() => toggleAll(lights, !allLightsOn)} />
        )}
        {fans.length > 0 && (
          <Section title="Fans" icon="🌀" devices={fans} states={states} onToggle={toggleDevice}
            allOn={allFansOn} onAllToggle={() => toggleAll(fans, !allFansOn)} />
        )}
      </main>
    </>
  )
}

// ── Root App ─────────────────────────────────────────────

export default function App() {
  const [page, setPage]           = useState('home')
  const [devices, setDevices]     = useState([])
  const [states, setStates]       = useState({})
  const [connected, setConnected] = useState(false)
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)
  const pollRef                   = useRef(null)

  // Initial device fetch
  const fetchDevices = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await fetch(`${API_BASE}/devices`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const list = await res.json()
      setDevices(list)
      setStates(Object.fromEntries(list.map(d => [d, false])))
      setConnected(true)
    } catch (e) {
      setError(e.message)
      setConnected(false)
    } finally {
      setLoading(false)
    }
  }, [])

  // Poll /states every 1 s to instantly reflect physical switch changes
  const pollStates = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/states`)
      if (!res.ok) return
      const data = await res.json()
      setStates(data)
      setConnected(true)
    } catch {
      setConnected(false)
    }
  }, [])

  useEffect(() => {
    fetchDevices()
  }, [fetchDevices])

  // Start polling once devices are loaded (every 1 s for fast physical-switch sync)
  useEffect(() => {
    if (devices.length === 0) return
    pollRef.current = setInterval(pollStates, 1000)
    return () => clearInterval(pollRef.current)
  }, [devices.length, pollStates])

  // Capacitor network listener
  useEffect(() => {
    if (!window.Capacitor) return
    Network.addListener('networkStatusChange', s => {
      setConnected(s.connected)
      if (s.connected) fetchDevices()
    })
    return () => Network.removeAllListeners()
  }, [fetchDevices])

  return (
    <div className="app">
      <div className="page-content">
        {page === 'home' ? (
          <HomePage
            devices={devices}
            states={states}
            setStates={setStates}
            connected={connected}
            setConnected={setConnected}
            loading={loading}
            error={error}
            onRetry={fetchDevices}
          />
        ) : (
          <SchedulePage allDevices={devices} />
        )}
      </div>
      <Navbar page={page} setPage={setPage} />
    </div>
  )
}
