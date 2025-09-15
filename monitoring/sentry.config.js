// Sentry Configuration for CADS Research Visualization
// This file contains the Sentry setup configuration

const SENTRY_CONFIG = {
    // Replace with your actual Sentry DSN
    dsn: 'https://your-sentry-dsn@sentry.io/project-id',
    
    // Environment detection
    environment: window.location.hostname === 'localhost' ? 'development' : 'production',
    
    // Integrations
    integrations: [
        new Sentry.BrowserTracing({
            // Set sampling rate for performance monitoring
            tracePropagationTargets: [window.location.hostname, /^\//],
        }),
        new Sentry.Replay({
            // Capture replays on errors and a sample of sessions
            maskAllText: false,
            blockAllMedia: false,
        }),
    ],
    
    // Performance Monitoring
    tracesSampleRate: 0.1, // Capture 10% of transactions for performance monitoring
    
    // Session Replay
    replaysSessionSampleRate: 0.1, // 10% of sessions will be recorded
    replaysOnErrorSampleRate: 1.0, // 100% of sessions with an error will be recorded
    
    // Error filtering
    beforeSend(event) {
        // Filter out development errors
        if (window.location.hostname === 'localhost') {
            return null;
        }
        
        // Filter out known non-critical errors
        if (event.exception) {
            const error = event.exception.values[0];
            if (error && error.value) {
                // Filter out network errors that are not actionable
                if (error.value.includes('NetworkError') || 
                    error.value.includes('Failed to fetch')) {
                    return null;
                }
                
                // Filter out browser extension errors
                if (error.value.includes('extension://') || 
                    error.value.includes('chrome-extension://')) {
                    return null;
                }
            }
        }
        
        return event;
    },
    
    // Release tracking
    release: 'cads-visualization@' + (document.querySelector('meta[name="version"]')?.content || 'unknown'),
    
    // Additional context
    initialScope: {
        tags: {
            component: 'cads-visualization',
            framework: 'vanilla-js',
            visualization: 'deck.gl'
        },
        user: {
            id: 'anonymous',
            ip_address: '{{auto}}'
        },
        contexts: {
            browser: {
                name: navigator.userAgent,
                version: navigator.appVersion
            },
            device: {
                screen_resolution: `${screen.width}x${screen.height}`,
                viewport: `${window.innerWidth}x${window.innerHeight}`
            }
        }
    }
};

// Initialize Sentry if available
function initializeSentry() {
    if (typeof Sentry !== 'undefined') {
        try {
            Sentry.init(SENTRY_CONFIG);
            console.log('✅ Sentry initialized successfully');
            
            // Set additional context
            Sentry.setContext('application', {
                name: 'CADS Research Visualization',
                version: SENTRY_CONFIG.release,
                environment: SENTRY_CONFIG.environment
            });
            
        } catch (error) {
            console.error('❌ Failed to initialize Sentry:', error);
        }
    } else {
        console.warn('⚠️ Sentry SDK not loaded');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SENTRY_CONFIG, initializeSentry };
} else {
    window.SENTRY_CONFIG = SENTRY_CONFIG;
    window.initializeSentry = initializeSentry;
}