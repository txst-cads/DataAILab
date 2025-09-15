#!/usr/bin/env python3
"""
Execute CADS migration using direct SQL execution.
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
        logging.FileHandler('cads_migration_execution.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def execute_sql_file(sql_file_path: str):
    """Execute SQL file using psql command."""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not found in environment variables")
        
        logger.info(f"Executing SQL file: {sql_file_path}")
        
        # Use psql to execute the SQL file
        cmd = ['psql', database_url, '-f', sql_file_path, '-v', 'ON_ERROR_STOP=1']
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("SQL execution completed successfully")
            print("✅ CADS migration completed successfully!")
            print("\n📊 Output:")
            print(result.stdout)
            return True
        else:
            logger.error(f"SQL execution failed with return code: {result.returncode}")
            print("❌ CADS migration failed!")
            print("\n🔍 Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("SQL execution timed out")
        print("⏰ SQL execution timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"Error executing SQL: {e}")
        print(f"❌ Error: {e}")
        return False


def main():
    """Main function to execute CADS migration."""
    try:
        print("🚀 Starting CADS Migration Execution...")
        print("="*50)
        
        # Check if SQL file exists
        sql_file = "create_cads_tables.sql"
        if not os.path.exists(sql_file):
            print(f"❌ SQL file not found: {sql_file}")
            return False
        
        # Execute the SQL file
        success = execute_sql_file(sql_file)
        
        if success:
            print("\n🎯 Migration Summary:")
            print("- Created cads_researchers table")
            print("- Created cads_works table") 
            print("- Created cads_topics table")
            print("- Migrated matching CADS professor data")
            print("- Created cads_researcher_summary view")
            print("\n✨ CADS subset is ready for use!")
        
        return success
        
    except Exception as e:
        logger.error(f"Migration execution failed: {e}")
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)