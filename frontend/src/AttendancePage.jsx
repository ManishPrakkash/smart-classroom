import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { db } from './firebase'
import {
  collection, doc, getDoc, writeBatch, serverTimestamp, onSnapshot,
} from 'firebase/firestore'
import { useAuth } from './AuthContext'
import { STUDENTS } from './students'
import { API_BASE } from './config'
import './AttendancePage.css'

// â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function todayISO() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function shiftDate(iso, days) {
  const d = new Date(iso + 'T00:00:00')
  d.setDate(d.getDate() + days)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function formatDateDisplay(iso) {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })
}

function formatYear(iso) {
  return new Date(iso + 'T00:00:00').getFullYear()
}

function getInitials(name) {
  return name.split(' ').slice(0, 2).map(w => w[0]).join('')
}

// Default record map - everyone absent, written to Firestore on first load of each day
function buildDefaultRecords() {
  const records = {}
  STUDENTS.forEach(s => {
    records[s.rollNo] = { status: 'absent', odType: null, source: 'manual' }
  })
  return records
}

// â”€â”€ Icons â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function IconChevronLeft() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
      <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2.2"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconChevronRight() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
      <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2.2"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconShare() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8"
        stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <polyline points="16 6 12 2 8 6" stroke="currentColor" strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round" />
      <line x1="12" y1="2" x2="12" y2="15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function IconCheck() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
      <polyline points="20 6 9 17 4 12" stroke="currentColor" strokeWidth="2.5"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconWhatsApp() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
    </svg>
  )
}

// â”€â”€ Pill label helper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function getPillLabel(status, odType) {
  if (status === 'od') {
    if (odType === 'internal') return 'Int OD'
    if (odType === 'external') return 'Ext OD'
    return 'OD'
  }
  return { present: 'Present', absent: 'Absent', late: 'Late' }[status] ?? status
}

// ── Camera Panel ────────────────────────────────────────────────────────────
// Polls backend for face-detection engine status.
// Shows live annotated camera feed while scanning.
// Attendance syncs automatically via Firestore onSnapshot in the parent.

const POLL_MS = 2000 // poll every 2s while running

function CameraPanel({ date, isAdmin }) {
  const [status,   setStatus] = useState(null)
  const [busy,     setBusy]   = useState(false)
  const [error,    setError]  = useState(null)
  const frameRef   = useRef(null)
  const frameTimer = useRef(null)

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/attendance/camera`, { signal: AbortSignal.timeout(5000) })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setStatus(data)
      setError(null)
    } catch {
      setError('Camera unavailable')
    }
  }, [])

  // Status polling
  useEffect(() => {
    fetchStatus()
    const t = setInterval(fetchStatus, status?.state === 'running' ? POLL_MS : 15000)
    return () => clearInterval(t)
  }, [fetchStatus, status?.state])

  // Refresh live frame every 200 ms while running
  useEffect(() => {
    clearInterval(frameTimer.current)
    if (status?.state === 'running') {
      frameTimer.current = setInterval(() => {
        if (frameRef.current)
          frameRef.current.src = `${API_BASE}/attendance/camera/frame?t=${Date.now()}`
      }, 200)
    }
    return () => clearInterval(frameTimer.current)
  }, [status?.state])

  async function handleStart() {
    setBusy(true)
    try {
      const res = await fetch(`${API_BASE}/attendance/camera/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date }),
      })
      const data = await res.json()
      if (!data.ok) setError(data.reason ?? 'Failed to start')
      else { setError(null); fetchStatus() }
    } catch { setError('Could not reach backend') }
    finally { setBusy(false) }
  }

  async function handleStop() {
    setBusy(true)
    try {
      await fetch(`${API_BASE}/attendance/camera/stop`, { method: 'POST' })
      clearInterval(frameTimer.current)
      fetchStatus()
    } catch { setError('Could not reach backend') }
    finally { setBusy(false) }
  }

  if (!status && !error) return null

  const running  = status?.state === 'running'
  const detected = status?.detected ?? []

  return (
    <div className={`cam-panel ${running ? 'cam-panel--running' : ''}`}>
      <div className="cam-panel__head">
        <span className={`cam-dot ${running ? 'cam-dot--live' : ''}`} />
        <span className="cam-panel__title">
          {running ? 'Face Detection — Scanning…' : 'Face Detection'}
        </span>
        {running && status?.fps > 0 && (
          <span className="cam-panel__fps">{status.fps} fps</span>
        )}
        <span className="cam-panel__spacer" />
        {error && <span className="cam-panel__err">{error}</span>}
        {isAdmin && (
          running
            ? <button className="cam-btn cam-btn--stop"  onClick={handleStop}  disabled={busy}>■ Stop</button>
            : <button className="cam-btn cam-btn--start" onClick={handleStart} disabled={busy || status?.available === false}>
                {status?.available === false ? 'Unavailable' : '▶ Start Scan'}
              </button>
        )}
      </div>

      {/* Live annotated camera feed */}
      {running && (
        <div className="cam-feed-wrap">
          <img
            ref={frameRef}
            className="cam-feed"
            alt="Live camera"
            src={`${API_BASE}/attendance/camera/frame?t=${Date.now()}`}
            onError={e => { e.target.style.display = 'none' }}
            onLoad={e  => { e.target.style.display = 'block' }}
          />
          <div className="cam-feed__overlay">
            {detected.length === 0
              ? <span className="cam-feed__hint">Scanning for faces…</span>
              : <span className="cam-feed__hint cam-feed__hint--ok">
                  {detected.length} student{detected.length > 1 ? 's' : ''} confirmed present ✓
                </span>
            }
          </div>
        </div>
      )}
    </div>
  )
}

// â”€â”€ Date Bar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function DateBar({ date, onChange }) {
  const today = todayISO()
  const inputRef = useRef(null)

  return (
    <div className="att-datebar">
      <button className="att-datebar__arrow" onClick={() => onChange(shiftDate(date, -1))}>
        <IconChevronLeft />
      </button>

      <button
        className="att-datebar__center"
        onClick={() => {
          try { inputRef.current?.showPicker() }
          catch { inputRef.current?.click() }
        }}
      >
        {date === today && <span className="att-datebar__chip">Today</span>}
        <span className="att-datebar__day">{formatDateDisplay(date)}</span>
        <span className="att-datebar__year">
          {formatYear(date)}
          <svg className="att-datebar__cal" width="13" height="13" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="4" width="18" height="18" rx="3" stroke="currentColor" strokeWidth="1.8"/>
            <path d="M16 2v4M8 2v4M3 10h18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
          </svg>
        </span>
        <input
          ref={inputRef}
          type="date"
          className="att-datebar__input"
          value={date}
          max={today}
          onChange={e => e.target.value && onChange(e.target.value)}
          tabIndex={-1}
        />
      </button>

      <button
        className="att-datebar__arrow"
        onClick={() => onChange(shiftDate(date, 1))}
        disabled={date >= today}
      >
        <IconChevronRight />
      </button>
    </div>
  )
}

// â”€â”€ Summary Cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function SummaryCards({ counts, total, activeFilter, onFilter }) {
  const cards = [
    { id: 'present', label: 'Present', color: 'green' },
    { id: 'absent',  label: 'Absent',  color: 'red' },
    { id: 'late',    label: 'Late',    color: 'amber' },
    { id: 'od',      label: 'On Duty', color: 'sky' },
  ]
  return (
    <div className="att-cards">
      {cards.map(c => {
        const pct = total > 0 ? Math.round((counts[c.id] / total) * 100) : 0
        const isActive = activeFilter === c.id
        return (
          <button
            key={c.id}
            className={`att-card att-card--${c.color} ${isActive ? 'att-card--active' : ''}`}
            onClick={() => onFilter(isActive ? 'all' : c.id)}
          >
            <span className="att-card__num">{counts[c.id]}</span>
            <span className="att-card__lbl">{c.label}</span>
            <span className="att-card__pct">{pct}%</span>
          </button>
        )
      })}
    </div>
  )
}

// â”€â”€ Search Bar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function SearchBar({ query, onChange, date, onDateChange }) {
  const calInputRef = useRef(null)
  const today = todayISO()

  return (
    <div className="att-search">
      <input
        className="att-search__input"
        type="text"
        placeholder="Search by name or roll number"
        value={query}
        onChange={e => onChange(e.target.value)}
        autoCapitalize="off"
        spellCheck={false}
      />
      {query && (
        <button className="att-search__clear" onClick={() => onChange('')}>&times;</button>
      )}
      <button
        className={`att-search__cal-btn ${date !== today ? 'att-search__cal-btn--active' : ''}`}
        title="Pick date"
        onClick={() => {
          try { calInputRef.current?.showPicker() }
          catch { calInputRef.current?.click() }
        }}
      >
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
          <rect x="3" y="4" width="18" height="18" rx="3" stroke="currentColor" strokeWidth="1.8"/>
          <path d="M16 2v4M8 2v4M3 10h18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
        </svg>
        <input
          ref={calInputRef}
          type="date"
          className="att-datebar__input"
          value={date}
          max={today}
          onChange={e => e.target.value && onDateChange(e.target.value)}
          tabIndex={-1}
        />
      </button>
    </div>
  )
}

// â”€â”€ Student Row â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function StudentRow({ student, record, onCycle, isAdmin, index }) {
  const { rollNo, name } = student
  const { status, odType } = record
  const initials   = getInitials(name)
  const pillLabel  = getPillLabel(status, odType ?? null)
  const [open, setOpen] = useState(false)
  const groupRef   = useRef(null)

  // Close when tapping outside
  useEffect(() => {
    if (!open) return
    function onOutside(e) {
      if (groupRef.current && !groupRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('pointerdown', onOutside)
    return () => document.removeEventListener('pointerdown', onOutside)
  }, [open])

  const handleSelect = (newStatus, newOdType = null) => {
    if (!isAdmin) return
    onCycle(rollNo, newStatus, newOdType)
    setOpen(false)
  }

  return (
    <div
      className={`att-row att-row--${status}`}
      style={{ animationDelay: `${Math.min(index * 20, 260)}ms` }}
    >
      <div className={`att-avatar att-avatar--${status}`}>
        {initials}
      </div>

      <div className="att-row__info">
        <span className="att-row__name">{name}</span>
        <span className="att-row__roll">{rollNo}</span>
      </div>

      <div ref={groupRef} className={`att-status-group${open ? ' att-status-group--open' : ''}`}>
        {!open ? (
          /* ── Collapsed: single status pill ── */
          <button
            className={`att-pill att-pill--${status} ${isAdmin ? 'att-pill--tap' : ''}`}
            onClick={() => { if (isAdmin) setOpen(true) }}
            disabled={!isAdmin}
          >
            {pillLabel}
            {isAdmin && <span className="att-pill__caret">{'›'}</span>}
          </button>
        ) : (
          /* ── Expanded: 5 option buttons ── */
          <>
            <button
              className={`att-sg-btn att-sg-btn--present${status === 'present' ? ' att-sg-btn--active' : ''}`}
              onClick={() => handleSelect('present', null)}
              title="Present"
            >✓</button>
            <button
              className={`att-sg-btn att-sg-btn--absent${status === 'absent' ? ' att-sg-btn--active' : ''}`}
              onClick={() => handleSelect('absent', null)}
              title="Absent"
            >✗</button>
            <button
              className={`att-sg-btn att-sg-btn--late${status === 'late' ? ' att-sg-btn--active' : ''}`}
              onClick={() => handleSelect('late', null)}
              title="Late"
            >L</button>
            <button
              className={`att-sg-btn att-sg-btn--od${status === 'od' && odType === 'internal' ? ' att-sg-btn--active' : ''}`}
              onClick={() => handleSelect('od', 'internal')}
              title="OD Internal"
            >INT</button>
            <button
              className={`att-sg-btn att-sg-btn--od${status === 'od' && odType === 'external' ? ' att-sg-btn--active' : ''}`}
              onClick={() => handleSelect('od', 'external')}
              title="OD External"
            >EXT</button>
          </>
        )}
      </div>
    </div>
  )
}

// â”€â”€ Export Sheet â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function buildExportText(date, records) {
  const total   = STUDENTS.length
  const present = STUDENTS.filter(s => records[s.rollNo]?.status === 'present').length
  const absent  = STUDENTS.filter(s => records[s.rollNo]?.status === 'absent').length
  const late    = STUDENTS.filter(s => records[s.rollNo]?.status === 'late').length
  const od      = STUDENTS.filter(s => records[s.rollNo]?.status === 'od').length

  // Each student on its own line as a bullet
  const toLines = fn =>
    STUDENTS.filter(s => fn(records[s.rollNo]))
            .map(s => `  \u2022 ${s.rollNo} - ${s.name}`)
            .join('\n')

  const absentLines = toLines(r => r?.status === 'absent')
  const lateLines   = toLines(r => r?.status === 'late')
  const intODLines  = toLines(r => r?.status === 'od' && r?.odType === 'internal')
  const extODLines  = toLines(r => r?.status === 'od' && r?.odType === 'external')

  const parts = [
    '\uD83D\uDCCA *ATTENDANCE UPDATE* \uD83D\uDCCA',
    '\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501',
    `\uD83D\uDCC5 Date: ${date}`,
    '\uD83D\uDCDA Class: 24CS (Batch 2024)',
    '',
    `\uD83D\uDC65 Total Students: ${total}`,
    `\u2705 Present: ${present}`,
    `\u274C Absent: ${absent}`,
    `\u23F0 Late: ${late}`,
    `\uD83D\uDFE1 On Duty: ${od}`,
  ]

  if (absentLines) parts.push('', '\u274C *Absentees:*', absentLines)
  if (lateLines)   parts.push('', '\u23F0 *Late Arrivals:*', lateLines)
  if (intODLines)  parts.push('', '\uD83D\uDFE1 *Internal OD:*', intODLines)
  if (extODLines)  parts.push('', '\uD83D\uDFE0 *External OD:*', extODLines)

  return parts.join('\n')
}

function ExportSheet({ date, records, onClose }) {
  const text = useMemo(() => buildExportText(date, records), [date, records])

  function handleSendWhatsApp() {
    const url = 'https://wa.me/?text=' + encodeURIComponent(text)
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  return (
    <div className="att-backdrop" onClick={onClose}>
      <div className="att-sheet" onClick={e => e.stopPropagation()}>
        <div className="att-sheet__handle" />
        <div className="att-sheet__header">
          <div>
            <p className="att-sheet__title">WhatsApp Report</p>
            <p className="att-sheet__sub">{date}</p>
          </div>
          <button className="att-sheet__close" onClick={onClose}>&times;</button>
        </div>
        <pre className="att-sheet__preview">{text}</pre>
        <button className="att-sheet__copy" onClick={handleSendWhatsApp}>
          <IconWhatsApp /> Send via WhatsApp
        </button>
      </div>
    </div>
  )
}

// â”€â”€ Main Page â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export default function AttendancePage() {
  const { profile } = useAuth()
  const isAdmin = !!profile?.isAdmin

  const [date,       setDate]       = useState(todayISO)
  const [records,    setRecords]    = useState({})
  const [filter,     setFilter]     = useState('all')
  const [query,      setQuery]      = useState('')
  const [loading,    setLoading]    = useState(true)
  const [saveState,  setSaveState]  = useState('idle') // idle | saving | saved | error
  const [showExport, setShowExport] = useState(false)

  const autoSaveTimer = useRef(null)
  const recordsRef    = useRef(records)
  const dateRef       = useRef(date)
  recordsRef.current  = records
  dateRef.current     = date

  // ── Real-time Firestore listener ──────────────────────────────────────────
  // Attaches an onSnapshot listener to attendance/{date}/records.
  // Any write from the Python backend (camera detection) or manual save
  // triggers this listener and merges only the changed documents into state,
  // so camera-detected "present" updates appear instantly without polling.
  const unsubRef = useRef(null)

  const attachListener = useCallback((d) => {
    // Detach previous listener
    if (unsubRef.current) { unsubRef.current(); unsubRef.current = null }

    const recordsCol = collection(db, 'attendance', d, 'records')
    unsubRef.current = onSnapshot(recordsCol, (qs) => {
      const updates = {}
      qs.docChanges().forEach(change => {
        if (change.type === 'added' || change.type === 'modified') {
          updates[change.doc.id] = change.doc.data()
        }
        if (change.type === 'removed') {
          updates[change.doc.id] = { status: 'absent', odType: null, source: 'manual' }
        }
      })
      if (Object.keys(updates).length > 0) {
        setRecords(prev => ({ ...prev, ...updates }))
        setSaveState('saved')
      }
    }, (err) => {
      console.error('Firestore listener error:', err)
    })
  }, [])

  // Cleanup listener on unmount
  useEffect(() => () => { if (unsubRef.current) unsubRef.current() }, [])

  const loadDate = useCallback(async (d) => {
    setLoading(true)
    setFilter('all')
    setQuery('')
    setSaveState('idle')
    clearTimeout(autoSaveTimer.current)
    try {
      const snap = await getDoc(doc(db, 'attendance', d))
      if (snap.exists()) {
        // ── Day already initialised ────────────────────────────────────────
        // Set default records immediately so UI isn't blank while listener loads
        setRecords(buildDefaultRecords())
        // Attach real-time listener — initial snapshot will populate all records
        attachListener(d)
        setSaveState('saved')
      } else {
        // ── New day — initialise everyone as absent then attach listener ───
        setRecords(buildDefaultRecords())
        if (isAdmin) {
          setSaveState('saving')
          try {
            const batch = writeBatch(db)
            batch.set(doc(db, 'attendance', d), {
              date: d,
              classLabel: '24CS (Batch 2024)',
              createdAt: serverTimestamp(),
              markedAt: serverTimestamp(),
              markedBy: 'auto-init',
            })
            STUDENTS.forEach(s => {
              batch.set(doc(db, 'attendance', d, 'records', s.rollNo), {
                rollNo: s.rollNo,
                name: s.name,
                status: 'absent',
                odType: null,
                source: 'manual',
                updatedAt: serverTimestamp(),
              })
            })
            await batch.commit()
            setSaveState('saved')
          } catch (initErr) {
            console.error('Attendance init error:', initErr)
            setSaveState('idle')
          }
        }
        // Attach listener after init (or for non-admins viewing)
        attachListener(d)
      }
    } catch (err) {
      console.error('Attendance load error:', err)
      setRecords(buildDefaultRecords())
      setSaveState('idle')
    } finally {
      setLoading(false)
    }
  }, [isAdmin, attachListener])

  useEffect(() => { loadDate(date) }, [date, loadDate])

  // ── Auto-save (debounced 1.5 s after last change) ────────────────────────────
  const doSave = useCallback(async () => {
    if (!isAdmin) return
    setSaveState('saving')
    try {
      const d = dateRef.current
      const rec = recordsRef.current
      const batch = writeBatch(db)
      batch.set(doc(db, 'attendance', d), {
        date: d, classLabel: '24CS (Batch 2024)',
        markedAt: serverTimestamp(), markedBy: profile?.rollNo ?? 'admin',
      })
      STUDENTS.forEach(s => {
        const r = rec[s.rollNo]
        if (!r) return
        batch.set(doc(db, 'attendance', d, 'records', s.rollNo), {
          rollNo: s.rollNo, name: s.name,
          status: r.status, odType: r.odType ?? null,
          source: r.source ?? 'manual', updatedAt: serverTimestamp(),
        })
      })
      await batch.commit()
      setSaveState('saved')
    } catch (err) {
      console.error('Auto-save error:', err)
      setSaveState('error')
    }
  }, [isAdmin, profile])

  // Status mutation — triggers debounced auto-save
  function handleCycle(rollNo, newStatus, newOdType) {
    if (!isAdmin) return
    setRecords(prev => ({
      ...prev,
      [rollNo]: { ...prev[rollNo], status: newStatus, odType: newOdType, source: 'manual' },
    }))
    setSaveState('dirty')
    clearTimeout(autoSaveTimer.current)
    autoSaveTimer.current = setTimeout(doSave, 1500)
  }

  // Cancel pending timer if date changes
  useEffect(() => () => clearTimeout(autoSaveTimer.current), [date])

  // Computed counts
  const counts = useMemo(() => {
    const c = { present: 0, absent: 0, late: 0, od: 0 }
    Object.values(records).forEach(r => {
      if      (r.status === 'present') c.present++
      else if (r.status === 'absent')  c.absent++
      else if (r.status === 'late')    c.late++
      else if (r.status === 'od')      c.od++
    })
    return c
  }, [records])

  // Filtered student list
  const visibleStudents = useMemo(() => {
    const q = query.trim().toLowerCase()
    return STUDENTS.filter(s => {
      const statusMatch = filter === 'all' || records[s.rollNo]?.status === filter
      const textMatch   = !q || s.name.toLowerCase().includes(q) || s.rollNo.toLowerCase().includes(q)
      return statusMatch && textMatch
    })
  }, [filter, query, records])

  return (
    <div className="att-page">

      {/* Header */}
      <div className="att-header">
        <div>
          <h2 className="att-header__title">Attendance</h2>
          <p className="att-header__sub">CSE-B &middot; {STUDENTS.length} students</p>
        </div>
        <div className="att-header__right">
          {saveState === 'saving' && <span className="att-saved-badge att-saved-badge--saving">Saving…</span>}
          {saveState === 'saved'  && <span className="att-saved-badge att-saved-badge--ok">✓ Saved</span>}
          {saveState === 'error'  && <span className="att-saved-badge att-saved-badge--err">! Failed</span>}
          {saveState === 'dirty'  && <span className="att-saved-badge att-saved-badge--dirty">Unsaved</span>}
          <button className="att-icon-btn" onClick={() => setShowExport(true)} title="Export report">
            <IconShare />
          </button>
        </div>
      </div>

      {/* Date bar */}
      <DateBar date={date} onChange={setDate} />

      {/* Camera face-detection panel */}
      <CameraPanel date={date} isAdmin={isAdmin} />

      {/* Summary cards — tap to filter */}
      <SummaryCards
        counts={counts}
        total={STUDENTS.length}
        activeFilter={filter}
        onFilter={setFilter}
      />

      {/* Search */}
      <SearchBar query={query} onChange={setQuery} date={date} onDateChange={setDate} />

      {/* List meta */}
      <div className="att-list-meta">
        <span className="att-list-meta__count">
          {visibleStudents.length} student{visibleStudents.length !== 1 ? 's' : ''}
          {(query || filter !== 'all') ? ' shown' : ''}
        </span>
        {isAdmin && <span className="att-list-meta__hint">Tap a button to mark status</span>}
      </div>

      {/* Student list */}
      {loading ? (
        <div className="att-loading">
          <div className="att-loading__ring" />
          <span>Loading attendance...</span>
        </div>
      ) : visibleStudents.length === 0 ? (
        <div className="att-empty">
          <span className="att-empty__icon">{'\uD83D\uDD0D'}</span>
          <span>No students match your search.</span>
        </div>
      ) : (
        <div className="att-list">
          {visibleStudents.map((s, i) => (
            <StudentRow
              key={s.rollNo}
              student={s}
              record={records[s.rollNo] ?? { status: 'absent', odType: null, source: 'manual' }}
              onCycle={handleCycle}
              isAdmin={isAdmin}
              index={i}
            />
          ))}
        </div>
      )}


      {/* Export bottom sheet */}
      {showExport && (
        <ExportSheet date={date} records={records} onClose={() => setShowExport(false)} />
      )}
    </div>
  )
}

