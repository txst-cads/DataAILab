// Release Tracking Configuration for CADS Research Visualization
// Handles deployment correlation and release management

class ReleaseTracker {
    constructor() {
        this.releaseInfo = this.detectReleaseInfo();
        this.deploymentInfo = this.detectDeploymentInfo();
        
        this.initializeReleaseTracking();
    }

    // Detect release information
    detectReleaseInfo() {
        // Try to get version from meta tag
        const versionMeta = document.querySelector('meta[name="version"]');
        const version = versionMeta?.content || this.generateVersionFromTimestamp();
        
        // Try to get commit hash from meta tag or environment
        const commitMeta = document.querySelector('meta[name="commit"]');
        const commit = commitMeta?.content || this.detectCommitHash();
        
        return {
            version: version,
            commit: commit,
            timestamp: new Date().toISOString(),
            environment: this.detectEnvironment()
        };
    }

    // Detect deployment information
    detectDeploymentInfo() {
        return {
            platform: this.detectPlatform(),
            region: this.detectRegion(),
            buildId: this.detectBuildId(),
            deploymentUrl: window.location.origin
        };
    }

    // Generate version from timestamp if not available
    generateVersionFromTimestamp() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hour = String(now.getHours()).padStart(2, '0');
        const minute = String(now.getMinutes()).padStart(2, '0');
        
        return `${year}.${month}.${day}.${hour}${minute}`;
    }

    // Detect commit hash from various sources
    detectCommitHash() {
        // Try to get from Vercel environment
        if (window.location.hostname.includes('vercel.app')) {
            // Vercel exposes commit hash in some cases
            const urlParts = window.location.hostname.split('-');
            const possibleHash = urlParts[urlParts.length - 2];
            if (possibleHash && possibleHash.length >= 7) {
                return possibleHash.substring(0, 7);
            }
        }
        
        // Try to get from build-time injection
        if (typeof BUILD_COMMIT !== 'undefined') {
            return BUILD_COMMIT;
        }
        
        return 'unknown';
    }

    // Detect environment
    detectEnvironment() {
        const hostname = window.location.hostname;
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'development';
        }
        
        if (hostname.includes('staging') || hostname.includes('preview')) {
            return 'staging';
        }
        
        if (hostname.includes('vercel.app') && !hostname.includes('main')) {
            return 'preview';
        }
        
        return 'production';
    }

    // Detect deployment platform
    detectPlatform() {
        const hostname = window.location.hostname;
        
        if (hostname.includes('vercel.app') || hostname.includes('vercel.com')) {
            return 'vercel';
        }
        
        if (hostname.includes('netlify.app') || hostname.includes('netlify.com')) {
            return 'netlify';
        }
        
        if (hostname.includes('github.io')) {
            return 'github-pages';
        }
        
        if (hostname === 'localhost') {
            return 'local';
        }
        
        return 'unknown';
    }

    // Detect deployment region (Vercel-specific)
    detectRegion() {
        // Vercel exposes region in headers, but we can't access them from client-side
        // This would need to be injected at build time
        return typeof BUILD_REGION !== 'undefined' ? BUILD_REGION : 'unknown';
    }

    // Detect build ID
    detectBuildId() {
        // Try to get from build-time injection
        if (typeof BUILD_ID !== 'undefined') {
            return BUILD_ID;
        }
        
        // Generate from timestamp as fallback
        return Date.now().toString();
    }

    // Initialize release tracking
    initializeReleaseTracking() {
        console.log('🚀 Release tracking initialized:', this.releaseInfo);
        
        // Set up Sentry release tracking
        this.setupSentryRelease();
        
        // Track deployment event
        this.trackDeployment();
        
        // Set up release context
        this.setReleaseContext();
    }

    // Set up Sentry release tracking
    setupSentryRelease() {
        if (typeof Sentry !== 'undefined') {
            try {
                // Set release information
                Sentry.setTag('release', this.releaseInfo.version);
                Sentry.setTag('commit', this.releaseInfo.commit);
                Sentry.setTag('environment', this.releaseInfo.environment);
                
                // Set deployment context
                Sentry.setContext('deployment', {
                    platform: this.deploymentInfo.platform,
                    region: this.deploymentInfo.region,
                    buildId: this.deploymentInfo.buildId,
                    deploymentUrl: this.deploymentInfo.deploymentUrl,
                    timestamp: this.releaseInfo.timestamp
                });
                
                console.log('✅ Sentry release tracking configured');
            } catch (error) {
                console.warn('⚠️ Failed to configure Sentry release tracking:', error);
            }
        }
    }

    // Track deployment event
    trackDeployment() {
        try {
            if (typeof window.trackEvent === 'function') {
                window.trackEvent('Deployment', {
                    version: this.releaseInfo.version,
                    commit: this.releaseInfo.commit,
                    environment: this.releaseInfo.environment,
                    platform: this.deploymentInfo.platform,
                    region: this.deploymentInfo.region,
                    buildId: this.deploymentInfo.buildId,
                    timestamp: this.releaseInfo.timestamp
                });
            }
            
            // Track with Vercel Analytics
            if (window.va) {
                window.va('track', 'App Deployed', {
                    version: this.releaseInfo.version,
                    environment: this.releaseInfo.environment,
                    platform: this.deploymentInfo.platform
                });
            }
        } catch (error) {
            console.warn('Failed to track deployment:', error);
        }
    }

    // Set release context for debugging
    setReleaseContext() {
        // Expose release info globally for debugging
        window.RELEASE_INFO = {
            ...this.releaseInfo,
            ...this.deploymentInfo
        };
        
        // Add to page title in development
        if (this.releaseInfo.environment === 'development') {
            document.title += ` (${this.releaseInfo.version})`;
        }
        
        // Add version info to console
        console.log(`📦 CADS Visualization v${this.releaseInfo.version} (${this.releaseInfo.commit})`);
        console.log(`🌍 Environment: ${this.releaseInfo.environment} on ${this.deploymentInfo.platform}`);
    }

    // Get release information
    getReleaseInfo() {
        return {
            ...this.releaseInfo,
            ...this.deploymentInfo
        };
    }

    // Check if this is a new release
    isNewRelease() {
        const lastVersion = localStorage.getItem('cads-last-version');
        const currentVersion = this.releaseInfo.version;
        
        if (lastVersion !== currentVersion) {
            localStorage.setItem('cads-last-version', currentVersion);
            return true;
        }
        
        return false;
    }

    // Track release adoption
    trackReleaseAdoption() {
        if (this.isNewRelease()) {
            try {
                if (typeof window.trackEvent === 'function') {
                    window.trackEvent('New Release Adopted', {
                        version: this.releaseInfo.version,
                        previousVersion: localStorage.getItem('cads-previous-version') || 'unknown',
                        environment: this.releaseInfo.environment,
                        timestamp: new Date().toISOString()
                    });
                }
                
                // Store previous version for next time
                const currentVersion = localStorage.getItem('cads-last-version');
                if (currentVersion) {
                    localStorage.setItem('cads-previous-version', currentVersion);
                }
            } catch (error) {
                console.warn('Failed to track release adoption:', error);
            }
        }
    }
}

// Initialize release tracker
let releaseTracker;

function initializeReleaseTracking() {
    if (!releaseTracker) {
        releaseTracker = new ReleaseTracker();
        
        // Track release adoption
        releaseTracker.trackReleaseAdoption();
        
        // Expose for debugging
        window.releaseTracker = releaseTracker;
        
        console.log('✅ Release tracking initialized');
    }
    return releaseTracker;
}

// Auto-initialize when script loads
if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeReleaseTracking);
    } else {
        initializeReleaseTracking();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ReleaseTracker, initializeReleaseTracking };
} else {
    window.ReleaseTracker = ReleaseTracker;
    window.initializeReleaseTracking = initializeReleaseTracking;
}