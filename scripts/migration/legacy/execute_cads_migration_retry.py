#!/usr/bin/env python3
"""
Execute CADS migration with connection retry logic.
"""
import os
import sys
import logging
import time
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cads_migration_retry.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def try_alternative_connection():
    """Try alternative connection methods."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Try different connection approaches
        database_url = os.getenv('DATABASE_URL')
        
        # Parse the URL to try different connection methods
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
        if not match:
            raise ValueError("Could not parse DATABASE_URL")
        
        user, password, host, port, database = match.groups()
        
        # Try direct IP resolution first
        logger.info("Attempting to resolve host IP...")
        
        # Alternative connection parameters
        connection_params = {
            'host': host,
            'port': int(port),
            'database': database,
            'user': user,
            'password': password,
            'cursor_factory': RealDictCursor,
            'connect_timeout': 30,
            'sslmode': 'require'
        }
        
        # Try connection with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Connection attempt {attempt + 1}/{max_retries}")
                conn = psycopg2.connect(**connection_params)
                logger.info("Connection successful!")
                return conn
                
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait 5 seconds before retry
                else:
                    raise
        
        return None
        
    except ImportError:
        logger.error("psycopg2 not available")
        return None
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return None


def execute_sql_with_connection(conn, sql_content: str):
    """Execute SQL content with the given connection."""
    try:
        with conn.cursor() as cursor:
            # Split SQL into individual statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            logger.info(f"Executing {len(statements)} SQL statements...")
            
            for i, statement in enumerate(statements, 1):
                if statement:
                    try:
                        logger.debug(f"Executing statement {i}: {statement[:100]}...")
                        cursor.execute(statement)
                        conn.commit()
                        logger.debug(f"Statement {i} completed successfully")
                    except Exception as e:
                        logger.error(f"Error in statement {i}: {e}")
                        logger.error(f"Statement was: {statement}")
                        conn.rollback()
                        # Continue with next statement for non-critical errors
                        if "already exists" not in str(e).lower():
                            raise
            
            logger.info("All SQL statements executed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error executing SQL: {e}")
        return False


def get_migration_results(conn):
    """Get results of the migration."""
    try:
        with conn.cursor() as cursor:
            # Check table counts
            tables_to_check = ['cads_researchers', 'cads_works', 'cads_topics']
            results = {}
            
            for table in tables_to_check:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table};")
                    result = cursor.fetchone()
                    results[table] = result['count'] if result else 0
                except Exception as e:
                    logger.warning(f"Could not get count for {table}: {e}")
                    results[table] = "Error"
            
            return results
            
    except Exception as e:
        logger.error(f"Error getting migration results: {e}")
        return {}


def main():
    """Main function to execute CADS migration."""
    try:
        print("🚀 Starting CADS Migration with Retry Logic...")
        print("="*60)
        
        # Check if SQL file exists
        sql_file = "create_cads_tables.sql"
        if not os.path.exists(sql_file):
            print(f"❌ SQL file not found: {sql_file}")
            return False
        
        # Read SQL content
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        logger.info(f"Read SQL file: {len(sql_content)} characters")
        
        # Try to establish connection
        print("🔌 Attempting database connection...")
        conn = try_alternative_connection()
        
        if not conn:
            print("❌ Could not establish database connection")
            print("\n💡 Alternative approach:")
            print("1. Copy the contents of create_cads_tables.sql")
            print("2. Go to your Supabase Dashboard → SQL Editor")
            print("3. Paste and run the SQL script manually")
            return False
        
        try:
            print("✅ Database connection established!")
            print("📝 Executing CADS migration SQL...")
            
            # Execute the SQL
            success = execute_sql_with_connection(conn, sql_content)
            
            if success:
                print("✅ CADS migration completed successfully!")
                
                # Get results
                print("\n📊 Migration Results:")
                results = get_migration_results(conn)
                
                for table, count in results.items():
                    print(f"   {table}: {count} records")
                
                print("\n🎯 Tables Created:")
                print("   - cads_researchers (CADS faculty)")
                print("   - cads_works (Publications)")
                print("   - cads_topics (Research topics)")
                print("   - cads_researcher_summary (Summary view)")
                
                print("\n✨ CADS subset is ready for use!")
                return True
            else:
                print("❌ Migration failed during SQL execution")
                return False
                
        finally:
            conn.close()
            logger.info("Database connection closed")
        
    except Exception as e:
        logger.error(f"Migration execution failed: {e}")
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)