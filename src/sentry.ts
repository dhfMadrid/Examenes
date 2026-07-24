import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN || 'https://1cbc59bdb2ae4b7dcc522721b43e18f5@o4511778608513024.ingest.de.sentry.io/4511778622341200',

  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],

  tracesSampleRate: import.meta.env.PROD ? 0.1 : 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,

  dataCollection: {
    userInfo: false,
    httpBodies: [],
  },

  enableLogs: true,
});
