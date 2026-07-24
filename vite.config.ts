import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'

// Importación dinámica del plugin de Sentry — solo cuando se hace build de prod
let sentryPlugin: any = []
if (process.env.NODE_ENV === 'production' || process.env.VITE_SENTRY_SOURCEMAPS === 'true') {
  // require() funciona porque Vite ejecuta vite.config.ts con Node directamente
  const { sentryVitePlugin } = await import('@sentry/bundler-plugins/vite')
  // Hard-coded org/proj porque Vite no carga .env.production en Windows bien.
  // Si quieres usar variables locales, usa: npx cross-env SENTRY_ORG=X SENTRY_PROJECT=Y SENTRY_AUTH_TOKEN=Z npm run build
  sentryPlugin = [
    sentryVitePlugin({
      org: 'senasa-mx',
      project: 'javascript-react',
      authToken: process.env.SENTRY_AUTH_TOKEN || '', // si no hay env var, se salta upload (no falla)
    }),
  ]
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tsconfigPaths(), ...sentryPlugin],
  build: {
    sourcemap: true, // Genera source maps — necesario para que los errores en Sentry se vean con código fuente
  },
  server: {
    port: 3000,
    proxy: {
      '/api/v1': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
