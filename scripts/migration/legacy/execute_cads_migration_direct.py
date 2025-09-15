#!/usr/bin/env python3
"""
Execute CADS migration using DATABASE_URL from .env file with direct connection.
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
        logging.FileHandler('cads_migration_direct.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def create_connection_with_retries():
    """Create database connection with multiple retry strategies."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not found in environment variables")
        
        logger.info(f"Using DATABASE_URL: {database_url[:50]}...")
        
        # Parse URL components
        import urllib.parse
        parsed = urllib.parse.urlparse(database_url)
        
        logger.info(f"Connecting to host: {parsed.hostname}")
        logger.info(f"Port: {parsed.port}")
        logger.info(f"Database: {parsed.path[1:]}")
        logger.info(f"Username: {parsed.username}")
        
        # Connection parameters
        conn_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],  # Remove leading slash
            'user': parsed.username,
            'password': parsed.password,
            'cursor_factory': RealDictCursor,
            'connect_timeout': 30,
            'sslmode': 'require',
            'application_name': 'CADS_Migration_Script'
        }
        
        # Try connection with retries
        max_retries = 5
        retry_delays = [1, 2, 5, 10, 15]  # Progressive delays
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Connection attempt {attempt + 1}/{max_retries}")
                
                # Try to connect
                conn = psycopg2.connect(**conn_params)
                
                # Test the connection
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()
                    logger.info(f"Connected successfully! Database version: {version['version'][:100]}...")
                
                return conn
                
            except psycopg2.OperationalError as e:
                error_msg = str(e)
                logger.warning(f"Connection attempt {attempt + 1} failed: {error_msg}")
                
                # Check for specific error types
                if "could not translate host name" in error_msg:
                    logger.error("DNS resolution failed - this appears to be a network connectivity issue")
                elif "timeout" in error_msg.lower():
                    logger.warning("Connection timeout - retrying with longer timeout")
                    conn_params['connect_timeout'] = min(60, conn_params['connect_timeout'] * 2)
                elif "authentication failed" in error_msg.lower():
                    logger.error("Authentication failed - check credentials")
                    break
                
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.info(f"Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                else:
                    raise
            
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delays[attempt])
                else:
                    raise
        
        return None
        
    except ImportError:
        logger.error("psycopg2 not available. Install with: pip install psycopg2-binary")
        return None
    except Exception as e:
        logger.error(f"Connection setup failed: {e}")
        return None


def execute_sql_statements(conn, sql_content: str):
    """Execute SQL statements one by one."""
    try:
        # Clean and split SQL into statements
        statements = []
        current_statement = ""
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('--'):
                continue
            
            current_statement += line + '\n'
            
            # Check if statement is complete (ends with semicolon)
            if line.endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        # Add any remaining statement
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        logger.info(f"Executing {len(statements)} SQL statements...")
        
        executed_count = 0
        with conn.cursor() as cursor:
            for i, statement in enumerate(statements, 1):
                if not statement:
                    continue
                
                try:
                    # Log statement type
                    stmt_type = statement.split()[0].upper() if statement.split() else "UNKNOWN"
                    logger.info(f"Executing statement {i}/{len(statements)}: {stmt_type}")
                    
                    # Execute statement
                    cursor.execute(statement)
                    conn.commit()
                    
                    # Get row count if applicable
                    if cursor.rowcount >= 0:
                        logger.info(f"  → Affected {cursor.rowcount} rows")
                    
                    executed_count += 1
                    
                except psycopg2.Error as e:
                    error_msg = str(e)
                    
                    # Handle expected errors gracefully
                    if any(phrase in error_msg.lower() for phrase in [
                        "already exists", "duplicate", "constraint", "does not exist"
                    ]):
                        logger.warning(f"  → Expected error (continuing): {error_msg}")
                        conn.rollback()
                        continue
                    else:
                        logger.error(f"  → SQL Error: {error_msg}")
                        logger.error(f"  → Statement: {statement[:200]}...")
                        conn.rollback()
                        raise
                
                except Exception as e:
                    logger.error(f"  → Unexpected error: {e}")
                    logger.error(f"  → Statement: {statement[:200]}...")
                    conn.rollback()
                    raise
        
        logger.info(f"Successfully executed {executed_count}/{len(statements)} statements")
        return True
        
    except Exception as e:
        logger.error(f"Error executing SQL statements: {e}")
        return False


def get_migration_summary(conn):
    """Get summary of migration results."""
    try:
        results = {}
        
        with conn.cursor() as cursor:
            # Check each table
            tables = ['cads_researchers', 'cads_works', 'cads_topics']
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table};")
                    result = cursor.fetchone()
                    results[table] = result['count'] if result else 0
                except Exception as e:
                    logger.warning(f"Could not get count for {table}: {e}")
                    results[table] = "Error"
            
            # Get sample data from cads_researchers
            try:
                cursor.execute("""
                    SELECT full_name, h_index, department 
                    FROM cads_researchers 
                    ORDER BY full_name 
                    LIMIT 10;
                """)
                sample_researchers = cursor.fetchall()
                results['sample_researchers'] = sample_researchers
            except Exception as e:
                logger.warning(f"Could not get sample researchers: {e}")
                results['sample_researchers'] = []
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting migration summary: {e}")
        return {}


def main():
    """Main function to execute CADS migration."""
    try:
        print("🚀 Starting CADS Migration with Direct Connection...")
        print("="*70)
        
        # Check if SQL file exists
        sql_file = "create_cads_tables.sql"
        if not os.path.exists(sql_file):
            print(f"❌ SQL file not found: {sql_file}")
            print("Please run the create_cads_subset_supabase.py script first to generate the SQL file.")
            return False
        
        # Read SQL content
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        logger.info(f"Read SQL file: {len(sql_content)} characters")
        print(f"📄 SQL file loaded: {len(sql_content)} characters")
        
        # Establish database connection
        print("🔌 Establishing database connection...")
        conn = create_connection_with_retries()
        
        if not conn:
            print("❌ Could not establish database connection")
            print("\n💡 Troubleshooting suggestions:")
            print("1. Check your internet connection")
            print("2. Verify DATABASE_URL in .env file is correct")
            print("3. Ensure Supabase project is active")
            print("4. Try running the SQL manually in Supabase Dashboard")
            return False
        
        try:
            print("✅ Database connection established!")
            print("📝 Executing CADS migration SQL...")
            
            # Execute the SQL
            success = execute_sql_statements(conn, sql_content)
            
            if success:
                print("✅ CADS migration completed successfully!")
                
                # Get migration summary
                print("\n📊 Migration Summary:")
                results = get_migration_summary(conn)
                
                for table, count in results.items():
                    if table != 'sample_researchers':
                        print(f"   📋 {table}: {count} records")
                
                # Show sample researchers
                sample_researchers = results.get('sample_researchers', [])
                if sample_researchers:
                    print(f"\n👥 Sample CADS Researchers Found:")
                    for researcher in sample_researchers[:5]:
                        h_index = researcher['h_index'] or 'N/A'
                        dept = researcher['department'] or 'N/A'
                        print(f"   • {researcher['full_name']} (H-index: {h_index}, Dept: {dept})")
                    
                    if len(sample_researchers) > 5:
                        print(f"   ... and {len(sample_researchers) - 5} more")
                
                print("\n🎯 Tables Created:")
                print("   • cads_researchers - CADS faculty members")
                print("   • cads_works - Publications with embeddings & keywords")
                print("   • cads_topics - Research topics")
                print("   • cads_researcher_summary - Summary view")
                
                print("\n✨ CADS subset is ready for analysis!")
                print("💡 Use the cads_researcher_summary view for easy querying")
                
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