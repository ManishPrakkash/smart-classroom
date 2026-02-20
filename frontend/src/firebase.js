// ── Firebase initialisation ───────────────────────────────────────────────────
// All config values come from .env (VITE_ prefix = exposed to browser bundle).
// Firebase API keys are intentionally public-facing; security is enforced by
// Firestore Security Rules, NOT by hiding these values.

import { initializeApp }       from 'firebase/app'
import { getAuth }             from 'firebase/auth'
import { getFirestore }        from 'firebase/firestore'

const firebaseConfig = {
  apiKey:            import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain:        import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId:         import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket:     import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId:             import.meta.env.VITE_FIREBASE_APP_ID,
}

const app = initializeApp(firebaseConfig)

export const auth = getAuth(app)
export const db   = getFirestore(app)
export default app
