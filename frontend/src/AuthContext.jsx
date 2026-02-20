// ── Auth Context ──────────────────────────────────────────────────────────────
// Wraps the entire app. Provides:
//   user        – Firebase Auth user object (null if logged out)
//   profile     – Firestore /users/{uid} document
//   authLoading – true while Firebase resolves the initial auth state
//   logout()    – signs out and clears profile
//
// Roll numbers are converted to a synthetic email for Firebase Auth:
//   "24CS071"  →  "24cs071@smartclass.local"
//
// Firestore /users/{uid} schema:
//   rollNo            string     "24CS071"
//   displayName       string     "HARI VIGNESH"
//   email             string     "24cs071@smartclass.local"
//   isAdmin           boolean    false
//   isDefaultPassword boolean    true  (false once user changes password)
//   createdAt         Timestamp
//   lastLoginAt       Timestamp

import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import {
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
} from 'firebase/auth'
import {
  doc,
  getDoc,
  updateDoc,
  serverTimestamp,
} from 'firebase/firestore'
import { auth, db } from './firebase'

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Convert roll number to synthetic Firebase email */
export function rollToEmail(rollNo) {
  return `${rollNo.toLowerCase()}@smartclass.local`
}

// ── Context ───────────────────────────────────────────────────────────────────

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user,        setUser]        = useState(null)
  const [profile,     setProfile]     = useState(null)  // Firestore doc data
  const [authLoading, setAuthLoading] = useState(true)

  // Fetch (or re-fetch) the Firestore profile for a given Firebase Auth user
  const loadProfile = useCallback(async (firebaseUser) => {
    if (!firebaseUser) { setProfile(null); return }
    try {
      const ref  = doc(db, 'users', firebaseUser.uid)
      const snap = await getDoc(ref)
      if (snap.exists()) {
        setProfile({ uid: firebaseUser.uid, ...snap.data() })
        // Update lastLoginAt without awaiting (fire-and-forget)
        updateDoc(ref, { lastLoginAt: serverTimestamp() }).catch(() => {})
      } else {
        // Fallback: minimal profile from Auth object
        setProfile({ uid: firebaseUser.uid, displayName: firebaseUser.email, isAdmin: false })
      }
    } catch (err) {
      console.error('[AuthContext] loadProfile error:', err)
      setProfile({ uid: firebaseUser.uid, displayName: '', isAdmin: false })
    }
  }, [])

  // Listen to Firebase Auth state changes
  useEffect(() => {
    const unsub = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser)
      await loadProfile(firebaseUser)
      setAuthLoading(false)
    })
    return unsub
  }, [loadProfile])

  // ── Actions ─────────────────────────────────────────────────────────────────

  const login = async (rollNo, password) => {
    const email = rollToEmail(rollNo.trim().toUpperCase())
    // signInWithEmailAndPassword throws on failure — caller catches
    return signInWithEmailAndPassword(auth, email, password)
  }

  const logout = async () => {
    await signOut(auth)
    setUser(null)
    setProfile(null)
  }

  /** Reload profile from Firestore (e.g. after admin changes isAdmin). */
  const refreshProfile = useCallback(() => loadProfile(user), [user, loadProfile])

  return (
    <AuthContext.Provider value={{ user, profile, authLoading, login, logout, refreshProfile }}>
      {children}
    </AuthContext.Provider>
  )
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
