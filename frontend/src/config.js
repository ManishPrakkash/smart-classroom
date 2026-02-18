// API Configuration
const isNative = () => typeof window !== 'undefined' && window.Capacitor !== undefined

export const getApiBaseUrl = () => {
  if (isNative()) {
    const piIp   = import.meta.env.VITE_PI_IP   || 'localhost'
    const apiPort = import.meta.env.VITE_API_PORT || 8000
    return `http://${piIp}:${apiPort}`
  }
  return '/api'
}

export const API_BASE = getApiBaseUrl()
