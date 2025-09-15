#!/usr/bin/env python3
"""
Execute CADS migration with DNS resolution fix.
"""
import os
import sys
import logging
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cads_migration_fixed.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def resolve_hostname_with_system_tools(hostname):
    """Use system tools to resolve hostname since Python DNS fails."""
    try:
        # Try to get IPv4 address using dig
        result = subprocess.run(
            ['dig', '+short', 'A', hostname],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            ipv4_addresses = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            if ipv4_addresses:
                logger.info(f"Resolved {hostname} to IPv4: {ipv4_addresses[0]}")
                return ipv4_addresses[0]
        
        # If no IPv4, try IPv6
        result = subprocess.run(
            ['dig', '+short', 'AAAA', hostname],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            ipv6_addresses = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            if ipv6_addresses:
                logger.info(f"Resolved {hostname} to IPv6: {ipv6_addresses[0]}")
                return ipv6_addresses[0]
        
        # Fallback: try host command
        result = subprocess.run(
            ['host', hostname],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'has address' in line:
                    ip = line.split()[-1]
                    logger.info(f"Resolved {hostname} to IP via host: {ip}")
                    return ip
                elif 'has IPv6 address' in line:
                    ip = line.split()[-1]
                    logger.info(f"Resolved {hostname} to IPv6 via host: {ip}")
                    return ip
        
        logger.error(f"Could not resolve {hostname} using system tools")
        return None
        
    except Exception as e:
        logger.error(f"Error resolving hostname: {e}")
        return None


def execute_migration_with_resolved_ip():
    """Execute migration using resolved IP address."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not found")
        
        # Parse URL
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
        if not match:
            raise ValueError("Invalid DATABASE_URL format")
        
        username, password, hostname, port, database = match.groups()
        
        logger.info(f"Original hostname: {hostname}")
        
        # Resolve hostname using system tools
        resolved_ip = resolve_hostname_with_system_tools(hostname)
        if not resolved_ip:
            raise ValueError(f"Could not resolve hostname: {hostname}")
        
        # Read SQL file
        sql_file = "create_cads_tables.sql"
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"SQL file not found: {sql_file}")
        
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        logger.info(f"SQL file loaded: {len(sql_content)} characters")
        
        # Try connection with resolved IP
        logger.info(f"Attempting connection to resolved IP: {resolved_ip}")
        
        # Handle IPv6 addresses (need brackets)
        if ':' in resolved_ip and not resolved_ip.startswith('['):
            host_param = f"[{resolved_ip}]"
        else:
            host_param = resolved_ip
        
        connection_configs = [
            # Try with resolved IP
            {
                'host': resolved_ip,
                'port': port,
                'database': database,
                'user': username,
                'password': password,
                'connect_timeout': 30,
                'sslmode': 'require'
            },
            # Try with different SSL mode
            {
                'host': resolved_ip,
                'port': port,
                'database': database,
                'user': username,
                'password': password,
                'connect_timeout': 30,
                'sslmode': 'prefer'
            },
            # Try without SSL requirement
            {
                'host': resolved_ip,
                'port': port,
                'database': database,
                'user': username,
                'password': password,
                'connect_timeout': 30,
                'sslmode': 'allow'
            }
        ]
        
        for i, config in enumerate(connection_configs, 1):
            try:
                logger.info(f"Connection attempt {i}/3 with sslmode={config['sslmode']}")
                
                conn = psycopg2.connect(cursor_factory=RealDictCursor, **config)
                logger.info("✅ Database connection established!")
                
                # Execute migration
                with conn.cursor() as cursor:
                    logger.info("Executing CADS migration SQL...")
                    
                    # Split and execute statements
                    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                    successful = 0
                    
                    for j, statement in enumerate(statements, 1):
                        if statement:
                            try:
                                cursor.execute(statement)
                                conn.commit()
                                successful += 1
                                
                                if j % 10 == 0:
                                    logger.info(f"Progress: {j}/{len(statements)} statements")
                                    
                            except Exception as e:
                                error_msg = str(e).lower()
                                if any(skip in error_msg for skip in ['already exists', 'duplicate']):
                                    logger.warning(f"Skipping: {e}")
                                    conn.rollback()
                                    continue
                                else:
                                    logger.error(f"Statement {j} failed: {e}")
                                    conn.rollback()
                                    raise
                    
                    logger.info(f"Successfully executed {successful}/{len(statements)} statements")
                    
                    # Get results
                    results = get_migration_results(cursor)
                    
                conn.close()
                return True, results
                
            except Exception as e:
                logger.warning(f"Connection attempt {i} failed: {e}")
                if i == len(connection_configs):
                    raise
                continue
        
        return False, {}
        
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
        print("🚀 CADS Migration - DNS Resolution Fix")
        print("=" * 60)
        
        # Execute migration
        success, results = execute_migration_with_resolved_ip()
        
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
            print("Even with DNS resolution fix, connection failed.")
            print("Manual execution in Supabase Dashboard is recommended.")
        
        return success
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"❌ Execution failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)