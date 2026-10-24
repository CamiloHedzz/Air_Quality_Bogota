import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  assetsInclude: ['**/*.TTF'],
  server: {
    proxy: Object.fromEntries(['/api/predictions', '/api/maps', '/django_plotly_dash', '/static'].map(path =>
      [path, { target: 'http://127.0.0.1:8000', changeOrigin: true }]))
  },
})
