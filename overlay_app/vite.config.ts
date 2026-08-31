import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // El backend Flask sirve overlay_app/build como estático directo
  // (ver backend/app/__init__.py) — mismo patrón que TSH.
  build: {
    outDir: 'build',
  },
})
