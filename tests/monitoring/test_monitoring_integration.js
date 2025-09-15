// Test script for monitoring integration
// This script can be run in the browser console to test monitoring functionality

console.log('🧪 Testing CADS Monitoring Integration...');

// Test 1: Check if monitoring libraries are loaded
function testMonitoringLibrariesLoaded() {
    console.log('\n1. Testing monitoring libraries...');
    
    const sentryLoaded = typeof Sentry !== 'undefined';
    const vercelAnalyticsLoaded = typeof window.va !== 'undefined';
    
    console.log(`   Sentry loaded: ${sentryLoaded ? '✅' : '❌'}`);
    console.log(`   Vercel Analytics loaded: ${vercelAnalyticsLoaded ? '✅' : '❌'}`);
    
    return { sentryLoaded, vercelAnalyticsLoaded };
}

// Test 2: Test custom event tracking
function testEventTracking() {
    console.log('\n2. Testing event tracking...');
    
    try {
        if (typeof window.trackEvent === 'function') {
            window.trackEvent('Test Event', {
                test_property: 'test_value',
                timestamp: new Date().toISOString()
            });
            console.log('   Custom event tracking: ✅');
            return true;
        } else {
            console.log('   Custom event tracking: ❌ (trackEvent function not found)');
            return false;
        }
    } catch (error) {
        console.log('   Custom event tracking: ❌', error.message);
        return false;
    }
}

// Test 3: Test error reporting
function testErrorReporting() {
    console.log('\n3. Testing error reporting...');
    
    try {
        // Test Sentry error capture
        if (typeof Sentry !== 'undefined') {
            Sentry.captureMessage('Test error message', 'info');
            console.log('   Sentry error reporting: ✅');
        } else {
            console.log('   Sentry error reporting: ❌ (Sentry not loaded)');
        }
        
        // Test custom error handling
        if (typeof window.showError === 'function') {
            // Don't actually show the error, just test the function exists
            console.log('   Custom error handling: ✅');
            return true;
        } else {
            console.log('   Custom error handling: ❌ (showError function not found)');
            return false;
        }
    } catch (error) {
        console.log('   Error reporting test failed: ❌', error.message);
        return false;
    }
}

// Test 4: Test performance monitoring
function testPerformanceMonitoring() {
    console.log('\n4. Testing performance monitoring...');
    
    try {
        if (typeof window.trackPerformance === 'function') {
            window.trackPerformance('test_metric', 123, 'ms');
            console.log('   Performance tracking: ✅');
            return true;
        } else {
            console.log('   Performance tracking: ❌ (trackPerformance function not found)');
            return false;
        }
    } catch (error) {
        console.log('   Performance monitoring test failed: ❌', error.message);
        return false;
    }
}

// Test 5: Test Core Web Vitals
function testCoreWebVitals() {
    console.log('\n5. Testing Core Web Vitals...');
    
    try {
        // Check if PerformanceObserver is supported
        if (typeof PerformanceObserver !== 'undefined') {
            console.log('   PerformanceObserver supported: ✅');
            
            // Check if the Web Vitals tracking is set up
            const hasLCPObserver = performance.getEntriesByType('largest-contentful-paint').length > 0;
            console.log(`   LCP tracking: ${hasLCPObserver ? '✅' : '⚠️ (may not be available yet)'}`);
            
            return true;
        } else {
            console.log('   PerformanceObserver: ❌ (not supported in this browser)');
            return false;
        }
    } catch (error) {
        console.log('   Core Web Vitals test failed: ❌', error.message);
        return false;
    }
}

// Test 6: Test application state monitoring
function testApplicationMonitoring() {
    console.log('\n6. Testing application monitoring...');
    
    try {
        if (typeof window.CADSVisualization !== 'undefined') {
            const app = window.CADSVisualization;
            console.log('   Application object accessible: ✅');
            
            // Check if performance tracking is initialized
            if (app.performance) {
                console.log('   Performance tracking initialized: ✅');
                console.log(`   Load start time: ${app.performance.loadStartTime}`);
                console.log(`   Error count: ${app.performance.errorCount}`);
                console.log(`   Interaction count: ${app.performance.interactionCount}`);
                return true;
            } else {
                console.log('   Performance tracking: ❌ (not initialized)');
                return false;
            }
        } else {
            console.log('   Application monitoring: ❌ (CADSVisualization not found)');
            return false;
        }
    } catch (error) {
        console.log('   Application monitoring test failed: ❌', error.message);
        return false;
    }
}

// Test 7: Test environment detection
function testEnvironmentDetection() {
    console.log('\n7. Testing environment detection...');
    
    try {
        const isLocalhost = window.location.hostname === 'localhost';
        const environment = isLocalhost ? 'development' : 'production';
        
        console.log(`   Current environment: ${environment}`);
        console.log(`   Hostname: ${window.location.hostname}`);
        
        // Check if Sentry is configured with correct environment
        if (typeof Sentry !== 'undefined' && Sentry.getCurrentHub) {
            const hub = Sentry.getCurrentHub();
            const client = hub.getClient();
            if (client && client.getOptions) {
                const options = client.getOptions();
                console.log(`   Sentry environment: ${options.environment || 'not set'}`);
            }
        }
        
        return true;
    } catch (error) {
        console.log('   Environment detection test failed: ❌', error.message);
        return false;
    }
}

// Run all tests
function runAllTests() {
    console.log('🧪 Running CADS Monitoring Integration Tests...');
    
    const results = {
        librariesLoaded: testMonitoringLibrariesLoaded(),
        eventTracking: testEventTracking(),
        errorReporting: testErrorReporting(),
        performanceMonitoring: testPerformanceMonitoring(),
        coreWebVitals: testCoreWebVitals(),
        applicationMonitoring: testApplicationMonitoring(),
        environmentDetection: testEnvironmentDetection()
    };
    
    console.log('\n📊 Test Results Summary:');
    const passedTests = Object.values(results).filter(result => 
        typeof result === 'boolean' ? result : result.sentryLoaded || result.vercelAnalyticsLoaded
    ).length;
    const totalTests = Object.keys(results).length;
    
    console.log(`   Passed: ${passedTests}/${totalTests} tests`);
    
    if (passedTests === totalTests) {
        console.log('   Status: ✅ All tests passed!');
    } else {
        console.log('   Status: ⚠️ Some tests failed - check configuration');
    }
    
    return results;
}

// Auto-run tests if this script is executed directly
if (typeof window !== 'undefined') {
    // Wait a bit for the page to load
    setTimeout(runAllTests, 1000);
}

// Export for manual testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        runAllTests,
        testMonitoringLibrariesLoaded,
        testEventTracking,
        testErrorReporting,
        testPerformanceMonitoring,
        testCoreWebVitals,
        testApplicationMonitoring,
        testEnvironmentDetection
    };
}