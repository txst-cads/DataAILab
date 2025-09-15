#!/usr/bin/env python3
"""
Alternative CADS migration approach with enhanced connectivity options.
"""
import os
import sys
import logging
import time
import socket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cads_migration_alternative.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def test_connectivity():
    """Test various connectivity options."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        return False, "DATABASE_URL not found"
    
    # Parse the URL
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
    if not match:
        return False, "Invalid DATABASE_URL format"
    
    username, password, host, port, database = match.groups()
    port = int(port)
    
    logger.info(f"Testing connectivity to {host}:{port}")
    
    # Test 1: Socket connection
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            logger.info("✅ Socket connection successful")
            return True, "Socket connection works"
        else:
            logger.warning(f"❌ Socket connection failed: {result}")
    except Exception as e:
        logger.warning(f"❌ Socket test failed: {e}")
    
    # Test 2: Try alternative DNS resolution
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '1.1.1.1']  # Use public DNS
        answers = resolver.resolve(host, 'A')
        for answer in answers:
            logger.info(f"DNS resolved {host} to {answer}")
            return True, f"DNS resolution successful: {answer}"
    except ImportError:
        logger.info("dnspython not available for alternative DNS resolution")
    except Exception as e:
        logger.warning(f"Alternative DNS resolution failed: {e}")
    
    return False, "All connectivity tests failed"


def execute_migration_with_retry():
    """Execute migration with enhanced retry logic."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not found")
        
        # Test connectivity first
        connected, message = test_connectivity()
        logger.info(f"Connectivity test: {message}")
        
        # Read SQL file
        sql_file = "create_cads_tables.sql"
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"SQL file not found: {sql_file}")
        
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        logger.info(f"SQL file loaded: {len(sql_content)} characters")
        
        # Try different connection approaches
        connection_configs = [
            # Standard connection
            {
                'dsn': database_url,
                'connect_timeout': 30,
                'sslmode': 'require'
            },
            # Connection with different SSL mode
            {
                'dsn': database_url,
                'connect_timeout': 60,
                'sslmode': 'prefer'
            },
            # Connection without SSL requirement
            {
                'dsn': database_url,
                'connect_timeout': 30,
                'sslmode': 'allow'
            }
        ]
        
        for i, config in enumerate(connection_configs, 1):
            try:
                logger.info(f"Trying connection approach {i}/3...")
                
                conn = psycopg2.connect(
                    config['dsn'],
                    cursor_factory=RealDictCursor,
                    **{k: v for k, v in config.items() if k != 'dsn'}
                )
                
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
                                
                                if j % 5 == 0:
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
                logger.warning(f"Connection approach {i} failed: {e}")
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
        print("🚀 CADS Migration - Alternative Approach")
        print("=" * 60)
        
        # Check prerequisites
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in .env file")
            return False
        
        print(f"🔗 Database URL: {database_url[:50]}...")
        
        # Execute migration
        success, results = execute_migration_with_retry()
        
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
            print("Please check the log file for details.")
            print("\n💡 Alternative: Use Supabase Dashboard SQL Editor")
            print("   1. Copy create_cads_tables.sql content")
            print("   2. Paste into Supabase SQL Editor")
            print("   3. Execute manually")
        
        return success
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"❌ Execution failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)