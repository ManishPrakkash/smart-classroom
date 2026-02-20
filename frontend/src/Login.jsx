// ── Login Page ────────────────────────────────────────────────────────────────
// Matches the existing dark violet design system exactly.
// Roll number → "24CS071@smartclass.local" email, password = roll number by default.

import { useState } from 'react'
import { useAuth }  from './AuthContext'
import './Login.css'

// Friendly error messages for Firebase Auth error codes
function friendlyError(code) {
  switch (code) {
    case 'auth/invalid-credential':
    case 'auth/wrong-password':
    case 'auth/user-not-found':
      return 'Invalid roll number or password.'
    case 'auth/too-many-requests':
      return 'Too many attempts. Try again in a few minutes.'
    case 'auth/network-request-failed':
      return 'No internet connection.'
    default:
      return 'Login failed. Please try again.'
  }
}

// Eye / eye-off icon
function IconEye({ open }) {
  return open ? (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path d="M1 12S5 4 12 4s11 8 11 8-4 8-11 8S1 12 1 12z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8"/>
    </svg>
  ) : (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
      <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  )
}

export default function Login() {
  const { login }           = useAuth()
  const [rollNo,  setRollNo]  = useState('')
  const [password, setPass]   = useState('')
  const [showPass, setShow]   = useState(false)
  const [error,   setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const roll = rollNo.trim().toUpperCase()
    if (!roll) { setError('Please enter your roll number.'); return }
    if (!password) { setError('Please enter your password.'); return }

    setError('')
    setLoading(true)
    try {
      await login(roll, password)
      // AuthContext.onAuthStateChanged handles state update → App re-renders
    } catch (err) {
      setError(friendlyError(err.code))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-screen">
      {/* Background glow */}
      <div className="login-glow login-glow--1" />
      <div className="login-glow login-glow--2" />

      <div className="login-card">
        {/* Logo / brand mark */}
        <div className="login-brand">
          <div className="login-brand__icon">
            <svg width="28" height="28" viewBox="0 0 36 36" fill="none">
              <circle cx="18" cy="17" r="13" fill="rgba(124,111,247,0.15)" />
              <path
                d="M12 17C12 12.582 14.686 9 18 9s6 3.582 6 8c0 2.8-1.4 5-3 7h-6c-1.6-2-3-4.2-3-7z"
                fill="rgba(124,111,247,0.3)"
                stroke="#7c6ff7"
                strokeWidth="1.6"
                strokeLinejoin="round"
              />
              <rect x="15" y="24" width="6" height="1.8" rx="0.5" fill="#7c6ff7" />
              <rect x="15.5" y="25.8" width="5" height="1.8" rx="0.5" fill="#6d62e0" />
              <line x1="18" y1="3"  x2="18" y2="5.5" stroke="#7c6ff7" strokeWidth="1.5" strokeLinecap="round" />
              <line x1="8"  y1="6"  x2="9.8" y2="7.8" stroke="#7c6ff7" strokeWidth="1.5" strokeLinecap="round" />
              <line x1="28" y1="6"  x2="26.2" y2="7.8" stroke="#7c6ff7" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
          <div>
            <h1 className="login-brand__title">Smart Switch</h1>
            <p className="login-brand__sub">Smart Classroom Control</p>
          </div>
        </div>

        {/* Form */}
        <form className="login-form" onSubmit={handleSubmit} noValidate>
          {/* Roll Number */}
          <div className="login-field">
            <label className="login-label">Roll Number</label>
            <div className="login-input-wrap">
              <svg className="login-input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
                <rect x="5" y="2" width="14" height="20" rx="2" stroke="currentColor" strokeWidth="1.8"/>
                <line x1="9" y1="7"  x2="15" y2="7"  stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                <line x1="9" y1="11" x2="15" y2="11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                <line x1="9" y1="15" x2="12" y2="15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
              <input
                className="login-input"
                type="text"
                placeholder="e.g. 24CS071"
                value={rollNo}
                onChange={e => { setRollNo(e.target.value.toUpperCase()); setError('') }}
                autoCapitalize="characters"
                autoCorrect="off"
                autoComplete="username"
                spellCheck={false}
                disabled={loading}
              />
            </div>
          </div>

          {/* Password */}
          <div className="login-field">
            <label className="login-label">Password</label>
            <div className="login-input-wrap">
              <svg className="login-input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
                <rect x="5" y="11" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.8"/>
                <path d="M8 11V7a4 4 0 0 1 8 0v4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
                <circle cx="12" cy="16" r="1.5" fill="currentColor"/>
              </svg>
              <input
                className="login-input"
                type={showPass ? 'text' : 'password'}
                placeholder="Enter your password"
                value={password}
                onChange={e => { setPass(e.target.value); setError('') }}
                autoComplete="current-password"
                disabled={loading}
              />
              <button
                type="button"
                className="login-eye"
                onClick={() => setShow(s => !s)}
                tabIndex={-1}
                aria-label="Toggle password visibility"
              >
                <IconEye open={showPass} />
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="login-error" role="alert">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.8"/>
                <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
                <circle cx="12" cy="16" r="1" fill="currentColor"/>
              </svg>
              {error}
            </div>
          )}

          {/* Submit */}
          <button className="login-btn" type="submit" disabled={loading}>
            {loading ? <span className="login-spinner" /> : 'Sign In'}
          </button>
        </form>

        <p className="login-hint">
          Default password is your roll number.<br />Contact admin to reset.
        </p>
      </div>
    </div>
  )
}
