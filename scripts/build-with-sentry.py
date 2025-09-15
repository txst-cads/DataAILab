#!/usr/bin/env python3
"""
Build script that injects Sentry configuration into HTML files
"""

import os
import sys
import re
import shutil
from pathlib import Path

def get_sentry_config():
    """Get Sentry configuration from environment variables"""
    sentry_dsn = os.getenv('SENTRY_DSN')
    sentry_environment = os.getenv('VERCEL_ENV', 'production')
    
    return {
        'dsn': sentry_dsn,
        'environment': sentry_environment,
        'release': os.getenv('SENTRY_RELEASE', 'unknown')
    }

def inject_sentry_config(html_content, config):
    """Inject Sentry configuration into HTML content"""
    if not config['dsn']:
        print("⚠️  SENTRY_DSN not found - Sentry will be disabled")
        # Remove Sentry script tag if no DSN
        html_content = re.sub(
            r'<script[^>]*sentry[^>]*></script>',
            '<!-- Sentry disabled - no DSN provided -->',
            html_content,
            flags=re.IGNORECASE
        )
        return html_content
    
    # Replace the hardcoded Sentry script with dynamic configuration
    sentry_script = f'''
    <!-- Sentry Error Tracking (Dynamic Configuration) -->
    <script src="https://browser.sentry-cdn.com/7.100.1/bundle.tracing.min.js" integrity="sha384-wbvA2NmqqALPaRHQ4+7eEp6vwvk1cJ4z3UJ3W7xOZFj+g4H5yALFPO9LHoB4cU0K" crossorigin="anonymous"></script>
    <script>
        if (typeof Sentry !== 'undefined') {{
            Sentry.init({{
                dsn: '{config['dsn']}',
                environment: '{config['environment']}',
                release: '{config['release']}',
                integrations: [
                    new Sentry.BrowserTracing({{
                        // Performance monitoring
                        tracingOrigins: [window.location.hostname, /^\\/api/],
                    }}),
                ],
                // Performance Monitoring
                tracesSampleRate: {config['environment'] == 'production' and '0.1' or '1.0'},
                // Session Replay (optional)
                replaysSessionSampleRate: 0.1,
                replaysOnErrorSampleRate: 1.0,
                beforeSend(event, hint) {{
                    // Filter out known non-issues
                    if (event.exception) {{
                        const error = event.exception.values[0];
                        if (error && error.value) {{
                            // Skip ResizeObserver loop errors (common browser bug)
                            if (error.value.includes('ResizeObserver loop')) {{
                                return null;
                            }}
                        }}
                    }}
                    return event;
                }}
            }});
            
            // Add additional context
            Sentry.setContext('application', {{
                name: 'CADS Research Visualization',
                version: document.querySelector('meta[name="version"]')?.content || 'unknown',
                buildTime: '{os.getenv("BUILD_TIME", "unknown")}',
                commitSha: '{os.getenv("GITHUB_SHA", "unknown")[:8]}'
            }});
            
            console.log('✅ Sentry initialized successfully');
        }}
    </script>
    '''
    
    # Replace existing Sentry script tag
    html_content = re.sub(
        r'<!-- Sentry Error Tracking -->.*?</script>',
        sentry_script.strip(),
        html_content,
        flags=re.DOTALL
    )
    
    return html_content

def main():
    """Main build process"""
    print("🔨 Building CADS Visualizer with Sentry integration...")
    
    # Get paths
    source_dir = Path('visuals/public-prod')
    if not source_dir.exists():
        print("❌ Source directory 'visuals/public-prod' not found")
        sys.exit(1)
    
    # Get Sentry configuration
    sentry_config = get_sentry_config()
    print(f"📊 Sentry DSN: {'SET' if sentry_config['dsn'] else 'NOT SET'}")
    print(f"🌍 Environment: {sentry_config['environment']}")
    print(f"🏷️  Release: {sentry_config['release']}")
    
    # Process HTML files
    html_files = list(source_dir.glob('*.html'))
    for html_file in html_files:
        print(f"📝 Processing {html_file.name}...")
        
        # Read original content
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Inject Sentry configuration
        updated_content = inject_sentry_config(content, sentry_config)
        
        # Write updated content
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ Updated {html_file.name}")
    
    print("🎉 Build completed successfully!")

if __name__ == '__main__':
    main()