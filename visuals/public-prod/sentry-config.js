// Step 1: Sentry is installed via package.json dependency
// Step 2: Configure Sentry
import * as Sentry from "@sentry/browser";

Sentry.init({
  // Replace with your actual DSN from Sentry dashboard
  dsn: "YOUR_SENTRY_DSN_HERE",
  
  // Step 3: Add Distributed Tracing (Optional)
  integrations: [
    new Sentry.BrowserTracing({
      // Set tracing origins to track performance across your app
      tracingOrigins: [window.location.hostname, /^\//],
    }),
  ],
  
  // Performance Monitoring
  tracesSampleRate: 0.1, // Capture 10% of transactions for performance monitoring
  
  // Session Replay (captures user interactions)
  replaysSessionSampleRate: 0.1, // 10% of sessions
  replaysOnErrorSampleRate: 1.0, // 100% of sessions with errors
  
  // Environment configuration
  environment: window.location.hostname === 'localhost' ? 'development' : 'production',
  
  // Additional configuration
  beforeSend(event, hint) {
    // Filter out known non-critical errors
    if (event.exception) {
      const error = event.exception.values[0];
      if (error && error.value) {
        // Skip ResizeObserver loop errors (common browser quirk)
        if (error.value.includes('ResizeObserver loop')) {
          return null;
        }
        // Skip network errors that are user-related
        if (error.value.includes('Failed to fetch')) {
          return null;
        }
      }
    }
    return event;
  },
});

// Set additional context for CADS application
Sentry.setContext("application", {
  name: "CADS Research Visualization",
  version: "1.0.0",
  framework: "vanilla-js",
  visualization: "deck.gl"
});

// Step 4: Verify Sentry (this will be in the main app.js)
console.log('✅ Sentry initialized successfully');

// Export Sentry for use in other modules
window.Sentry = Sentry;