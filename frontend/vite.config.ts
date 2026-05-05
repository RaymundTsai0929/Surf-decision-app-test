import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/Surf-decision-app-test/',
  server: { proxy: { '/api': 'http://localhost:8001' } },
})
