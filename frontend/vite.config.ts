import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Allow overriding the backend host/port via environment variables so the
// same config works both locally and inside Docker Compose.
const backendHost = process.env.VITE_BACKEND_HOST ?? 'localhost'
const backendPort = process.env.VITE_BACKEND_PORT ?? '8000'
const backendHttp = `http://${backendHost}:${backendPort}`
const backendWs = `ws://${backendHost}:${backendPort}`

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: backendHttp,
        changeOrigin: true,
      },
      '/ws': {
        target: backendWs,
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
