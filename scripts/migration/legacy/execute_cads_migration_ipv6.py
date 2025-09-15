#!/usr/bin/env python3
"""
Execute CADS migration using IPv6 address with enhanced error handling.
"""
import os
import sys
import logging
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cads_migration_ipv6.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def execute_migration_with_ipv6():
    """Execute migration using IPv6 address."""
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
        
        username, password, host, port, database = match.groups()
        
        # Read SQL file
        sql_file = "create_cads_tables.sql"
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"SQL file not found: {sql_file}")
        
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        logger.info(f"SQL file loaded: {len(sql_content)} characters")
        
        # Try different connection approaches
        connection_attempts = [
            # Original hostname
            {"host": host, "description": "original hostname"},
            # IPv6 address
            {"host": "2600:1f16:1cd0:330a:d13:ed41:8501:1be5", "description": "IPv6 address"},
            # Try with different timeout and SSL settings
            {"host": host, "description": "hostname with extended timeout", "timeout": 60, "sslmode": "prefer"},
        ]
        
        for i, attempt in enumerate(connection_attempts, 1):
            try:
                logger.info(f"Connection attempt {i}: {attempt['description']}")
                
                conn_params = {
                    'host': attempt['host'],
                    'port': port,
                    'database': database,
                    'user': username,
                    'password': password,
                    'connect_timeout': attempt.get('timeout', 30),
                    'sslmode': attempt.get('sslmode', 'require'),
                    'cursor_factory': RealDictCursor
                }
                
                conn = psycopg2.connect(**conn_params)
                logger.info(f"✅ Connection successful with {attempt['description']}!")
                
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
                logger.warning(f"Attempt {i} failed: {e}")
                if i == len(connection_attempts):
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
        print("🚀 CADS Migration - IPv6 Enhanced Approach")
        print("=" * 60)
        
        # Execute migration
        success, results = execute_migration_with_ipv6()
        
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
            print("All connection methods failed.")
            print("\n💡 Manual execution recommended:")
            print("   1. Open Supabase Dashboard")
            print("   2. Go to SQL Editor")
            print("   3. Copy and paste create_cads_tables.sql")
            print("   4. Execute the script")
        
        return success
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"❌ Execution failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)