import { useState, useEffect } from 'react'
import { API_BASE } from './config'
import './SchedulePage.css'

const ALL_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const EMPTY_FORM = {
  label: '',
  devices: [],
  on_time: '08:00',
  off_time: '18:00',
  days: [0, 1, 2, 3, 4],
  enabled: true,
}

function DayPicker({ selected, onChange }) {
  const toggle = (i) =>
    onChange(selected.includes(i) ? selected.filter(d => d !== i) : [...selected, i].sort())
  return (
    <div className="day-picker">
      {ALL_DAYS.map((d, i) => (
        <button
          key={d}
          className={`day-btn ${selected.includes(i) ? 'day-btn--on' : ''}`}
          onClick={() => toggle(i)}
          type="button"
        >
          {d}
        </button>
      ))}
    </div>
  )
}

function DevicePicker({ allDevices, selected, onChange }) {
  const toggle = (d) =>
    onChange(selected.includes(d) ? selected.filter(x => x !== d) : [...selected, d])
  return (
    <div className="device-picker">
      {allDevices.map(d => (
        <button
          key={d}
          className={`device-chip ${selected.includes(d) ? 'device-chip--on' : ''}`}
          onClick={() => toggle(d)}
          type="button"
        >
          {d.includes('light') ? '💡' : '🌀'} {d.replace(/([a-z])(\d)/, '$1 $2')}
        </button>
      ))}
    </div>
  )
}

function ScheduleCard({ sched, onDelete, onToggle }) {
  const activeDays = sched.days.map(i => ALL_DAYS[i]).join(', ')
  return (
    <div className={`sched-card ${sched.enabled ? 'sched-card--on' : 'sched-card--off'}`}>
      <div className="sched-card__top">
        <div>
          <p className="sched-card__label">{sched.label || 'Untitled'}</p>
          <p className="sched-card__devices">
            {sched.devices.map(d => d.replace(/([a-z])(\d)/, '$1 $2')).join(', ')}
          </p>
        </div>
        <div className="sched-card__actions">
          <button
            className={`sched-toggle ${sched.enabled ? 'sched-toggle--on' : ''}`}
            onClick={() => onToggle(sched.id)}
          >
            <span className="sched-toggle__thumb" />
          </button>
        </div>
      </div>
      <div className="sched-card__bottom">
        <div className="sched-card__times">
          <span className="sched-time on">▶ {sched.on_time}</span>
          <span className="sched-time off">■ {sched.off_time}</span>
        </div>
        <div className="sched-card__days">{activeDays}</div>
        <button className="sched-delete" onClick={() => onDelete(sched.id)}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>
    </div>
  )
}

function CreateSheet({ allDevices, onSave, onClose }) {
  const [form, setForm] = useState(EMPTY_FORM)
  const [saving, setSaving] = useState(false)

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const handleSave = async () => {
    if (!form.devices.length) return
    setSaving(true)
    await onSave(form)
    setSaving(false)
    onClose()
  }

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={e => e.stopPropagation()}>
        <div className="sheet__handle" />
        <h2 className="sheet__title">New Schedule</h2>

        <div className="form-group">
          <label className="form-label">Label</label>
          <input
            className="form-input"
            placeholder="e.g. Morning Lights"
            value={form.label}
            onChange={e => set('label', e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Devices</label>
          <DevicePicker allDevices={allDevices} selected={form.devices} onChange={v => set('devices', v)} />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Turn On</label>
            <input className="form-input" type="time" value={form.on_time} onChange={e => set('on_time', e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Turn Off</label>
            <input className="form-input" type="time" value={form.off_time} onChange={e => set('off_time', e.target.value)} />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Days</label>
          <DayPicker selected={form.days} onChange={v => set('days', v)} />
        </div>

        <button
          className="btn-save"
          onClick={handleSave}
          disabled={saving || !form.devices.length}
        >
          {saving ? 'Saving…' : 'Save Schedule'}
        </button>
      </div>
    </div>
  )
}

export default function SchedulePage({ allDevices }) {
  const [schedules, setSchedules] = useState([])
  const [loading, setLoading]     = useState(true)
  const [showForm, setShowForm]   = useState(false)

  const fetchSchedules = async () => {
    try {
      const res = await fetch(`${API_BASE}/schedules`)
      if (res.ok) setSchedules(await res.json())
    } catch { /* offline */ }
    setLoading(false)
  }

  useEffect(() => { fetchSchedules() }, [])

  const handleSave = async (form) => {
    const res = await fetch(`${API_BASE}/schedules`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })
    if (res.ok) {
      const created = await res.json()
      setSchedules(prev => [...prev, created])
    }
  }

  const handleDelete = async (id) => {
    await fetch(`${API_BASE}/schedules/${id}`, { method: 'DELETE' })
    setSchedules(prev => prev.filter(s => s.id !== id))
  }

  const handleToggle = async (id) => {
    const res = await fetch(`${API_BASE}/schedules/${id}/toggle`, { method: 'PATCH' })
    if (res.ok) {
      const updated = await res.json()
      setSchedules(prev => prev.map(s => s.id === id ? updated : s))
    }
  }

  return (
    <div className="sched-page">
      <header className="sched-header">
        <div>
          <h1 className="sched-title">Schedules</h1>
          <p className="sched-sub">{schedules.length} schedule{schedules.length !== 1 ? 's' : ''}</p>
        </div>
        <button className="fab" onClick={() => setShowForm(true)}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <line x1="12" y1="5" x2="12" y2="19" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
            <line x1="5" y1="12" x2="19" y2="12" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
          </svg>
        </button>
      </header>

      <div className="sched-list">
        {loading ? (
          <div className="sched-empty">Loading…</div>
        ) : schedules.length === 0 ? (
          <div className="sched-empty">
            <p>No schedules yet</p>
            <p className="sched-empty__sub">Tap + to create one</p>
          </div>
        ) : (
          schedules.map(s => (
            <ScheduleCard
              key={s.id}
              sched={s}
              onDelete={handleDelete}
              onToggle={handleToggle}
            />
          ))
        )}
      </div>

      {showForm && (
        <CreateSheet
          allDevices={allDevices}
          onSave={handleSave}
          onClose={() => setShowForm(false)}
        />
      )}
    </div>
  )
}
