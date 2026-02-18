import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
  },
  server: {
    port: 3000,
    host: '0.0.0.0',  // Allow network access for mobile testing
    proxy: {
      '/api': {
        target: `http://${process.env.VITE_PI_IP || 'localhost'}:${process.env.VITE_API_PORT || 8000}`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
