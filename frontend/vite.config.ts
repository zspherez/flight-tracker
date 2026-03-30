import fs from 'fs'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'

const httpsConfig = fs.existsSync('./certs/server.key')
  ? { key: fs.readFileSync('./certs/server.key'), cert: fs.readFileSync('./certs/server.crt') }
  : undefined

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: {
      plugins: [tailwindcss, autoprefixer],
    },
  },
  server: {
    https: httpsConfig,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
