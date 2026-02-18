// API Configuration
const isNative = () => typeof window !== 'undefined' && window.Capacitor !== undefined

export const getApiBaseUrl = () => {
  if (isNative()) {
    const piIp = import.meta.env.VITE_PI_IP || 'localhost'
    return `http://${piIp}:8000`
  }
  return '/api'
}

export const API_BASE = getApiBaseUrl()
