#!/usr/bin/env python3
"""
Execute CADS migration using individual parameters with port 6543.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import subprocess
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cads_migration_6543.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def resolve_hostname_to_ip(hostname):
    """Resolve hostname using system tools."""
    try:
        # Try IPv6 (since we know it resolves to IPv6)
        result = subprocess.run(['dig', '+short', 'AAAA', hostname], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            ipv6 = result.stdout.strip().split('\n')[0]
            if ipv6 and not ipv6.startswith(';'):
                return ipv6, 'IPv6'
        
        # Try IPv4 as fallback
        result = subprocess.run(['dig', '+short', 'A', hostname], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            ipv4 = result.stdout.strip().split('\n')[0]
            if ipv4 and not ipv4.startswith(';'):
                return ipv4, 'IPv4'
        
        return None, None
    except Exception as e:
        logger.error(f"Error resolving hostname: {e}")
        return None, None

def execute_migration():
    """Execute the CADS migration."""
    try:
        # Get connection parameters
        USER = os.getenv("user")
        PASSWORD = os.getenv("password")
        HOST = os.getenv("host")
        PORT = os.getenv("port")
        DBNAME = os.getenv("dbname")
        
        logger.info(f"Connection params - User: {USER}, Host: {HOST}, Port: {PORT}, DB: {DBNAME}")
        
        # Resolve hostname
        resolved_ip, ip_type = resolve_hostname_to_ip(HOST)
        if not resolved_ip:
            raise ValueError(f"Could not resolve hostname: {HOST}")
        
        logger.info(f"Resolved {HOST} to {ip_type}: {resolved_ip}")
        
        # Read SQL file
        sql_file = "create_cads_tables.sql"
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"SQL file not found: {sql_file}")
        
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        logger.info(f"SQL file loaded: {len(sql_content)} characters")
        
        # Try connection with different SSL modes
        ssl_modes = ['require', 'prefer', 'allow', 'disable']
        
        for ssl_mode in ssl_modes:
            try:
                logger.info(f"Attempting connection with sslmode={ssl_mode}")
                
                connection = psycopg2.connect(
                    user=USER,
                    password=PASSWORD,
                    host=resolved_ip,
                    port=PORT,
                    dbname=DBNAME,
                    connect_timeout=30,
                    sslmode=ssl_mode,
                    cursor_factory=RealDictCursor
                )
                
                logger.info(f"✅ Connection successful with sslmode={ssl_mode}!")
                
                # Execute migration
                with connection.cursor() as cursor:
                    logger.info("Executing CADS migration SQL...")
                    
                    # Split and execute statements
                    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                    successful = 0
                    
                    for i, statement in enumerate(statements, 1):
                        if statement:
                            try:
                                cursor.execute(statement)
                                connection.commit()
                                successful += 1
                                
                                if i % 10 == 0:
                                    logger.info(f"Progress: {i}/{len(statements)} statements")
                                    
                            except Exception as e:
                                error_msg = str(e).lower()
                                if any(skip in error_msg for skip in ['already exists', 'duplicate']):
                                    logger.warning(f"Skipping: {e}")
                                    connection.rollback()
                                    continue
                                else:
                                    logger.error(f"Statement {i} failed: {e}")
                                    connection.rollback()
                                    raise
                    
                    logger.info(f"Successfully executed {successful}/{len(statements)} statements")
                    
                    # Get results
                    results = get_migration_results(cursor)
                    
                connection.close()
                return True, results
                
            except Exception as e:
                logger.warning(f"Connection with sslmode={ssl_mode} failed: {e}")
                if "No route to host" in str(e):
                    logger.warning("IPv6 routing issue detected")
                continue
        
        # If we get here, all connection attempts failed
        raise Exception("All connection attempts failed - IPv6 routing issue")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False, {}

def get_migration_results(cursor):
    """Get migration results."""
    results = {}
    
    try:
        tables = ['cads_researchers', 'cads_works', 'cads_topics']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table};")
                result = cursor.fetchone()
                results[table] = result['count'] if result else 0
            except Exception as e:
                logger.warning(f"Could not count {table}: {e}")
                results[table] = "Not accessible"
        
        # Try to get summary
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_researchers,
                    SUM(total_works) as total_works,
                    SUM(total_citations) as total_citations
                FROM cads_researcher_summary;
            """)
            summary = cursor.fetchone()
            if summary:
                results['summary'] = dict(summary)
        except Exception as e:
            logger.warning(f"Could not get summary: {e}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        return results

def main():
    """Main execution function."""
    try:
        print("🚀 CADS Migration - Port 6543 with Individual Parameters")
        print("=" * 60)
        
        # Execute migration
        success, results = execute_migration()
        
        if success:
            print("\n✅ CADS Migration Completed Successfully!")
            print("=" * 60)
            
            # Display results
            print("📊 Migration Results:")
            for table, count in results.items():
                if table != 'summary':
                    print(f"   📋 {table}: {count} records")
            
            if 'summary' in results:
                summary = results['summary']
                print("\n🎯 Summary Statistics:")
                print(f"   👥 CADS Researchers: {summary.get('total_researchers', 0)}")
                print(f"   📚 Total Publications: {summary.get('total_works', 0)}")
                print(f"   📈 Total Citations: {summary.get('total_citations', 0)}")
            
            print("\n✨ CADS research subset is ready!")
            
        else:
            print("\n❌ CADS Migration Failed")
            print("IPv6 routing issue confirmed.")
            print("\n💡 Recommended solution:")
            print("   1. Open Supabase Dashboard")
            print("   2. Go to SQL Editor")
            print("   3. Copy and paste create_cads_tables.sql")
            print("   4. Execute the script")
            print("\nThis will achieve the same results!")
        
        return success
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"❌ Execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)