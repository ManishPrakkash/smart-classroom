import { Capacitor } from '@capacitor/core'

// API Configuration
const PI_IP   = import.meta.env.VITE_PI_IP   || 'localhost'
const API_PORT = import.meta.env.VITE_API_PORT || 8000
const DIRECT_URL = `http://${PI_IP}:${API_PORT}`

export const getApiBaseUrl = () => {
  // Running inside the native Android/iOS app (capacitor:// protocol)
  if (Capacitor.isNativePlatform()) {
    return DIRECT_URL
  }

  // Loaded from file system or capacitor:// in a WebView without the proxy
  if (typeof window !== 'undefined') {
    const proto = window.location?.protocol
    if (proto === 'file:' || proto === 'capacitor:') {
      return DIRECT_URL
    }
  }

  // Browser dev-server: use the Vite proxy (/api → backend)
  return '/api'
}

export const API_BASE = getApiBaseUrl()
