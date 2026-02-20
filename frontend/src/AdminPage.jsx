// ── Admin Page ─────────────────────────────────────────────────────────────────
// Lists all users from Firestore /users collection.
// Admins can toggle isAdmin for any user.
// Only accessible when profile.isAdmin === true (enforced in App.jsx + Firestore rules).

import { useState, useEffect, useCallback } from 'react'
import {
  collection,
  getDocs,
  doc,
  updateDoc,
  orderBy,
  query,
} from 'firebase/firestore'
import { db }       from './firebase'
import { useAuth }  from './AuthContext'
import './AdminPage.css'

// ── User Row ──────────────────────────────────────────────────────────────────

function UserRow({ user, currentUid, onToggleAdmin }) {
  const [busy, setBusy] = useState(false)
  const isSelf = user.uid === currentUid

  const handleToggle = async () => {
    if (isSelf || busy) return   // cannot revoke own admin
    setBusy(true)
    await onToggleAdmin(user.uid, !user.isAdmin)
    setBusy(false)
  }

  return (
    <div className={`admin-row ${user.isAdmin ? 'admin-row--admin' : ''}`}>
      <div className="admin-row__info">
        <span className="admin-row__roll">{user.rollNo}</span>
        <span className="admin-row__name">{user.displayName}</span>
      </div>
      <div className="admin-row__right">
        {user.isAdmin && (
          <span className="admin-badge">Admin</span>
        )}
        <button
          className={`sched-toggle ${user.isAdmin ? 'sched-toggle--on' : ''} ${isSelf ? 'admin-toggle--disabled' : ''}`}
          onClick={handleToggle}
          disabled={busy || isSelf}
          title={isSelf ? "Can't remove your own admin" : user.isAdmin ? 'Revoke admin' : 'Make admin'}
        >
          {busy
            ? <span className="admin-spinner" />
            : <span className="sched-toggle__thumb" />
          }
        </button>
      </div>
    </div>
  )
}

// ── Admin Page ─────────────────────────────────────────────────────────────────

export default function AdminPage() {
  const { profile }      = useAuth()
  const [users,  setUsers]   = useState([])
  const [loading, setLoading] = useState(true)
  const [search,  setSearch]  = useState('')
  const [error,   setError]   = useState('')

  const fetchUsers = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const q    = query(collection(db, 'users'), orderBy('rollNo'))
      const snap = await getDocs(q)
      setUsers(snap.docs.map(d => ({ uid: d.id, ...d.data() })))
    } catch (err) {
      setError('Failed to load users. Check Firestore rules.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchUsers() }, [fetchUsers])

  const handleToggleAdmin = async (uid, newVal) => {
    try {
      await updateDoc(doc(db, 'users', uid), { isAdmin: newVal })
      setUsers(prev => prev.map(u => u.uid === uid ? { ...u, isAdmin: newVal } : u))
    } catch (err) {
      console.error('[Admin] toggleAdmin error:', err)
      setError('Failed to update. Check your permissions.')
    }
  }

  const filtered = users.filter(u =>
    u.rollNo?.toLowerCase().includes(search.toLowerCase()) ||
    u.displayName?.toLowerCase().includes(search.toLowerCase())
  )

  const adminCount = users.filter(u => u.isAdmin).length

  return (
    <div className="admin-page">
      {/* Header */}
      <header className="sched-header">
        <div>
          <h1 className="sched-title">Admin Panel</h1>
          <p className="sched-sub">{users.length} users &bull; {adminCount} admin{adminCount !== 1 ? 's' : ''}</p>
        </div>
        <button className="admin-refresh" onClick={fetchUsers} title="Refresh">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M1 4v6h6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M23 20v-6h-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4-4.64 4.36A9 9 0 0 1 3.51 15"
              stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </header>

      {/* Search */}
      <div className="admin-search-wrap">
        <svg className="admin-search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none">
          <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="1.8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
        </svg>
        <input
          className="admin-search"
          type="text"
          placeholder="Search roll no. or name…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        {search && (
          <button className="admin-search-clear" onClick={() => setSearch('')}>×</button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="admin-error">{error}</div>
      )}

      {/* List */}
      <div className="admin-list">
        {loading ? (
          <div className="sched-empty">
            <div className="admin-loading-spinner" />
            <p>Loading users…</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="sched-empty">
            <p>No users found</p>
          </div>
        ) : (
          filtered.map(u => (
            <UserRow
              key={u.uid}
              user={u}
              currentUid={profile?.uid}
              onToggleAdmin={handleToggleAdmin}
            />
          ))
        )}
      </div>
    </div>
  )
}
