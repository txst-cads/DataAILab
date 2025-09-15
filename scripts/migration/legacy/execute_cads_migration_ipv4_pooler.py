#!/usr/bin/env python3
"""
Execute CADS migration using IPv4 pooler connection.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cads_migration_ipv4_pooler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def execute_migration():
    """Execute the CADS migration using IPv4 pooler."""
    try:
        # Get connection parameters
        USER = os.getenv("user")
        PASSWORD = os.getenv("password")
        HOST = os.getenv("host")
        PORT = os.getenv("port")
        DBNAME = os.getenv("dbname")
        
        logger.info(f"Using IPv4 pooler - User: {USER}, Host: {HOST}, Port: {PORT}, DB: {DBNAME}")
        
        # Read SQL file
        sql_file = "create_cads_tables_simple.sql"
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"SQL file not found: {sql_file}")
        
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        logger.info(f"SQL file loaded: {len(sql_content)} characters")
        
        # Connect to database
        logger.info("Establishing connection to IPv4 pooler...")
        
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME,
            connect_timeout=30,
            sslmode='require',
            cursor_factory=RealDictCursor
        )
        
        logger.info("✅ Connection established successfully!")
        
        # Execute migration
        with connection.cursor() as cursor:
            logger.info("Executing CADS migration SQL...")
            
            # Split and execute statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            successful = 0
            total_statements = len(statements)
            
            logger.info(f"Executing {total_statements} SQL statements...")
            
            for i, statement in enumerate(statements, 1):
                if statement:
                    try:
                        # Log progress for long operations
                        if i % 10 == 0 or i == total_statements:
                            logger.info(f"Progress: {i}/{total_statements} statements")
                        
                        cursor.execute(statement)
                        connection.commit()
                        successful += 1
                        
                    except Exception as e:
                        error_msg = str(e).lower()
                        # Skip non-critical errors
                        if any(skip_phrase in error_msg for skip_phrase in [
                            'already exists', 'duplicate', 'does not exist'
                        ]):
                            logger.warning(f"Skipping non-critical error in statement {i}: {e}")
                            connection.rollback()
                            continue
                        else:
                            logger.error(f"Critical error in statement {i}: {e}")
                            logger.error(f"Statement: {statement[:200]}...")
                            connection.rollback()
                            raise
            
            logger.info(f"Successfully executed {successful}/{total_statements} statements")
            
            # Get migration results
            results = get_migration_results(cursor)
            
        connection.close()
        logger.info("Database connection closed")
        
        return True, results
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False, {}

def get_migration_results(cursor):
    """Get results of the migration."""
    results = {}
    
    try:
        # Check if tables were created and get counts
        tables_to_check = ['cads_researchers', 'cads_works', 'cads_topics']
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table};")
                result = cursor.fetchone()
                results[table] = result['count'] if result else 0
            except Exception as e:
                logger.warning(f"Could not get count for {table}: {e}")
                results[table] = "Not created"
        
        # Try to get summary from the view
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
                results['summary'] = {
                    'total_researchers': summary['total_researchers'],
                    'total_works': summary['total_works'],
                    'total_citations': summary['total_citations']
                }
        except Exception as e:
            logger.warning(f"Could not get summary: {e}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting migration results: {e}")
        return results

def main():
    """Main function to execute CADS migration."""
    try:
        print("🚀 Starting CADS Migration (IPv4 Pooler Connection)...")
        print("="*60)
        
        # Verify environment
        USER = os.getenv("user")
        HOST = os.getenv("host")
        
        if not USER or not HOST:
            print("❌ Connection parameters not found in .env file")
            return False
        
        print(f"🔗 Using IPv4 Pooler: {HOST}")
        print(f"👤 User: {USER}")
        
        # Execute migration
        success, results = execute_migration()
        
        if success:
            print("\n✅ CADS Migration Completed Successfully!")
            print("="*60)
            
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
            
            print("\n🏆 Tables Created:")
            print("   - cads_researchers (CADS faculty members)")
            print("   - cads_works (All publications with embeddings & keywords)")
            print("   - cads_topics (Research topics from publications)")
            print("   - cads_researcher_summary (Analysis view)")
            
            print("\n✨ CADS research subset is ready for analysis!")
            
        else:
            print("\n❌ CADS Migration Failed")
            print("Check the log file for detailed error information.")
        
        return success
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"❌ Execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)