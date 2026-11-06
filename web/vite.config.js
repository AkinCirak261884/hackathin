import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'

// Fixtures live in ../fixtures (shared, read-only for Lane C).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@fixtures': fileURLToPath(new URL('../fixtures', import.meta.url)) },
  },
  server: {
    host: true, // reachable from your phone on the same wifi
    fs: { allow: ['..'] },
  },
})
