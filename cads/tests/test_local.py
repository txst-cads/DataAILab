#!/usr/bin/env python3
"""
Local testing script for CADS Research Visualization
Starts a simple HTTP server to test the application locally
"""

import http.server
import socketserver
import webbrowser
import threading
import time
import os
from pathlib import Path

class CompressedHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler that serves compressed files correctly"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='public', **kwargs)
    
    def end_headers(self):
        # Add CORS headers for local testing
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def guess_type(self, path):
        """Override to handle .gz files correctly"""
        if path.endswith('.json.gz'):
            return 'application/json'
        return super().guess_type(path)
    
    def do_GET(self):
        """Handle GET requests with proper compression headers"""
        if self.path.endswith('.json.gz'):
            # Serve compressed JSON with proper headers
            try:
                file_path = Path('public') / self.path.lstrip('/')
                if file_path.exists():
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Encoding', 'gzip')
                    self.send_header('Cache-Control', 'public, max-age=3600')
                    self.end_headers()
                    
                    with open(file_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return
                else:
                    self.send_error(404)
                    return
            except Exception as e:
                print(f"Error serving {self.path}: {e}")
                self.send_error(500)
                return
        
        # Default handling for other files
        super().do_GET()

def start_server(port=8000):
    """Start the local HTTP server"""
    try:
        with socketserver.TCPServer(("", port), CompressedHTTPRequestHandler) as httpd:
            print(f"🌐 Starting local server at http://localhost:{port}")
            print(f"📁 Serving files from: {Path('public').absolute()}")
            print("🔄 Server is running... Press Ctrl+C to stop")
            
            # Open browser after a short delay
            def open_browser():
                time.sleep(1)
                webbrowser.open(f'http://localhost:{port}')
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Try a different port:")
            print(f"   python test_local.py --port 8001")
        else:
            print(f"❌ Server error: {e}")

def check_prerequisites():
    """Check if all required files exist"""
    print("🔍 Checking prerequisites...")
    
    required_files = [
        'public/index.html',
        'public/app.js',
        'public/data/visualization-data.json.gz'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing required files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        print("\nRun the following to prepare files:")
        print("  python deploy.py")
        return False
    
    print("✅ All required files present")
    return True

def show_testing_instructions():
    """Show instructions for testing the application"""
    print("\n🧪 Testing Instructions:")
    print("=" * 25)
    print()
    print("1. The application should load automatically in your browser")
    print("2. Check the browser console for any errors")
    print("3. Verify the following functionality:")
    print("   - ✅ Visualization loads and displays points")
    print("   - ✅ Hover tooltips work correctly")
    print("   - ✅ Filter controls work (researcher, year, theme)")
    print("   - ✅ Search functionality works")
    print("   - ✅ Pan and zoom interactions are smooth")
    print("4. Check loading performance:")
    print("   - Open browser DevTools (F12)")
    print("   - Go to Network tab")
    print("   - Refresh the page")
    print("   - Verify total load time is <500ms")
    print("5. Test on different screen sizes (responsive design)")
    print()
    print("If everything works correctly, the application is ready for deployment!")

def main():
    """Main function"""
    print("🎯 CADS Research Visualization - Local Testing")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('public').exists():
        print("❌ 'public' directory not found. Make sure you're in the visuals/ directory")
        return
    
    # Check prerequisites
    if not check_prerequisites():
        return
    
    # Show testing instructions
    show_testing_instructions()
    
    # Start the server
    print("\n🚀 Starting local test server...")
    start_server()

if __name__ == "__main__":
    import sys
    
    # Handle command line arguments
    port = 8000
    if len(sys.argv) > 1:
        if sys.argv[1] == '--port' and len(sys.argv) > 2:
            try:
                port = int(sys.argv[2])
            except ValueError:
                print("❌ Invalid port number")
                sys.exit(1)
    
    main()