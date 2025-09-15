// Error Boundary Implementation for CADS Research Visualization
// Provides comprehensive error handling and recovery mechanisms

class ErrorBoundary {
    constructor() {
        this.errorCount = 0;
        this.lastError = null;
        this.recoveryAttempts = 0;
        this.maxRecoveryAttempts = 3;
        
        this.setupGlobalErrorHandlers();
        this.setupUnhandledRejectionHandler();
        this.setupResourceErrorHandler();
    }

    // Set up global error handlers
    setupGlobalErrorHandlers() {
        window.addEventListener('error', (event) => {
            this.handleError({
                type: 'javascript_error',
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error,
                stack: event.error?.stack
            });
        });
    }

    // Handle unhandled promise rejections
    setupUnhandledRejectionHandler() {
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError({
                type: 'promise_rejection',
                message: event.reason?.message || 'Unhandled promise rejection',
                error: event.reason,
                stack: event.reason?.stack
            });
        });
    }

    // Handle resource loading errors
    setupResourceErrorHandler() {
        window.addEventListener('error', (event) => {
            if (event.target !== window) {
                this.handleError({
                    type: 'resource_error',
                    message: `Failed to load resource: ${event.target.src || event.target.href}`,
                    element: event.target.tagName,
                    source: event.target.src || event.target.href
                });
            }
        }, true);
    }

    // Main error handling function
    handleError(errorInfo) {
        this.errorCount++;
        this.lastError = errorInfo;

        console.error('🚨 Error caught by boundary:', errorInfo);

        // Track error
        this.trackError(errorInfo);

        // Report to monitoring services
        this.reportError(errorInfo);

        // Attempt recovery if possible
        this.attemptRecovery(errorInfo);

        // Show user-friendly error message
        this.showUserError(errorInfo);
    }

    // Track error for analytics
    trackError(errorInfo) {
        try {
            if (typeof window.trackEvent === 'function') {
                window.trackEvent('Error Boundary', {
                    error_type: errorInfo.type,
                    error_message: errorInfo.message,
                    error_count: this.errorCount,
                    recovery_attempts: this.recoveryAttempts,
                    timestamp: new Date().toISOString(),
                    user_agent: navigator.userAgent,
                    url: window.location.href
                });
            }
        } catch (trackingError) {
            console.warn('Failed to track error:', trackingError);
        }
    }

    // Report error to monitoring services
    reportError(errorInfo) {
        try {
            // Report to Sentry
            if (typeof Sentry !== 'undefined') {
                Sentry.captureException(errorInfo.error || new Error(errorInfo.message), {
                    tags: {
                        component: 'error-boundary',
                        error_type: errorInfo.type
                    },
                    extra: {
                        errorInfo: errorInfo,
                        errorCount: this.errorCount,
                        recoveryAttempts: this.recoveryAttempts
                    },
                    level: this.getSeverityLevel(errorInfo)
                });
            }

            // Report to Vercel Analytics
            if (window.va) {
                window.va('track', 'Error Boundary Triggered', {
                    error_type: errorInfo.type,
                    error_message: errorInfo.message?.substring(0, 100), // Limit message length
                    severity: this.getSeverityLevel(errorInfo)
                });
            }
        } catch (reportingError) {
            console.warn('Failed to report error:', reportingError);
        }
    }

    // Determine error severity
    getSeverityLevel(errorInfo) {
        if (errorInfo.type === 'resource_error') {
            return 'warning';
        }
        
        if (errorInfo.message?.includes('Network') || 
            errorInfo.message?.includes('fetch')) {
            return 'warning';
        }
        
        if (errorInfo.type === 'promise_rejection') {
            return 'error';
        }
        
        return 'fatal';
    }

    // Attempt to recover from errors
    attemptRecovery(errorInfo) {
        if (this.recoveryAttempts >= this.maxRecoveryAttempts) {
            console.warn('Max recovery attempts reached, giving up');
            return;
        }

        this.recoveryAttempts++;

        try {
            switch (errorInfo.type) {
                case 'resource_error':
                    this.recoverFromResourceError(errorInfo);
                    break;
                    
                case 'javascript_error':
                    this.recoverFromJavaScriptError(errorInfo);
                    break;
                    
                case 'promise_rejection':
                    this.recoverFromPromiseRejection(errorInfo);
                    break;
                    
                default:
                    console.log('No specific recovery strategy for error type:', errorInfo.type);
            }
        } catch (recoveryError) {
            console.error('Recovery attempt failed:', recoveryError);
        }
    }

    // Recover from resource loading errors
    recoverFromResourceError(errorInfo) {
        console.log('Attempting recovery from resource error...');
        
        // If it's a data file, try to reload the application
        if (errorInfo.source?.includes('/data/')) {
            console.log('Data loading error detected, attempting to reload data...');
            
            // Try to reload the visualization if the app object is available
            if (window.CADSVisualization && typeof window.CADSVisualization.loadVisualization === 'function') {
                setTimeout(() => {
                    window.CADSVisualization.loadVisualization();
                }, 2000);
            }
        }
    }

    // Recover from JavaScript errors
    recoverFromJavaScriptError(errorInfo) {
        console.log('Attempting recovery from JavaScript error...');
        
        // If it's a visualization error, try to reinitialize
        if (errorInfo.message?.includes('deck') || 
            errorInfo.message?.includes('WebGL') ||
            errorInfo.filename?.includes('app.js')) {
            
            console.log('Visualization error detected, attempting to reinitialize...');
            
            // Clear any existing visualization
            const mapContainer = document.getElementById('map-container');
            if (mapContainer) {
                mapContainer.innerHTML = '';
            }
            
            // Try to reinitialize after a delay
            setTimeout(() => {
                if (window.CADSVisualization && window.CADSVisualization.data) {
                    try {
                        window.CADSVisualization.initializeDeckGL(window.CADSVisualization.data);
                    } catch (reinitError) {
                        console.error('Failed to reinitialize visualization:', reinitError);
                    }
                }
            }, 3000);
        }
    }

    // Recover from promise rejections
    recoverFromPromiseRejection(errorInfo) {
        console.log('Attempting recovery from promise rejection...');
        
        // If it's a network error, suggest retry
        if (errorInfo.message?.includes('fetch') || 
            errorInfo.message?.includes('network') ||
            errorInfo.message?.includes('load')) {
            
            console.log('Network error detected, will retry data loading...');
            
            // Retry data loading after a delay
            setTimeout(() => {
                if (window.CADSVisualization && typeof window.CADSVisualization.loadVisualization === 'function') {
                    window.CADSVisualization.loadVisualization();
                }
            }, 5000);
        }
    }

    // Show user-friendly error message
    showUserError(errorInfo) {
        try {
            const severity = this.getSeverityLevel(errorInfo);
            let title, message;

            switch (errorInfo.type) {
                case 'resource_error':
                    title = 'Loading Error';
                    message = 'Some resources failed to load. The page will attempt to recover automatically.';
                    break;
                    
                case 'javascript_error':
                    title = 'Application Error';
                    message = 'An unexpected error occurred. The application will attempt to recover.';
                    break;
                    
                case 'promise_rejection':
                    title = 'Network Error';
                    message = 'A network operation failed. Please check your connection.';
                    break;
                    
                default:
                    title = 'Unexpected Error';
                    message = 'An unexpected error occurred. Please refresh the page if problems persist.';
            }

            // Only show error to user for severe errors or after multiple attempts
            if (severity === 'fatal' || this.errorCount > 2) {
                if (typeof window.showError === 'function') {
                    window.showError(title, message);
                } else {
                    // Fallback error display
                    console.error(`${title}: ${message}`);
                    alert(`${title}: ${message}`);
                }
            }
        } catch (displayError) {
            console.error('Failed to show user error:', displayError);
        }
    }

    // Get error statistics
    getErrorStats() {
        return {
            errorCount: this.errorCount,
            lastError: this.lastError,
            recoveryAttempts: this.recoveryAttempts,
            maxRecoveryAttempts: this.maxRecoveryAttempts
        };
    }

    // Reset error boundary state
    reset() {
        this.errorCount = 0;
        this.lastError = null;
        this.recoveryAttempts = 0;
        console.log('Error boundary reset');
    }

    // Check if the application is in a healthy state
    isHealthy() {
        return this.errorCount < 5 && this.recoveryAttempts < this.maxRecoveryAttempts;
    }
}

// Initialize error boundary
let errorBoundary;

function initializeErrorBoundary() {
    if (!errorBoundary) {
        errorBoundary = new ErrorBoundary();
        console.log('✅ Error boundary initialized');
        
        // Expose for debugging
        window.errorBoundary = errorBoundary;
    }
    return errorBoundary;
}

// Auto-initialize when script loads
if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeErrorBoundary);
    } else {
        initializeErrorBoundary();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ErrorBoundary, initializeErrorBoundary };
} else {
    window.ErrorBoundary = ErrorBoundary;
    window.initializeErrorBoundary = initializeErrorBoundary;
}