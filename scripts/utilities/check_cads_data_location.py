#!/usr/bin/env python3
"""
Check where the CADS data was actually stored and migrate it to CADS tables.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_database():
    """Connect to database using IPv4 pooler."""
    USER = os.getenv("user")
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    PORT = os.getenv("port")
    DBNAME = os.getenv("dbname")
    
    return psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        connect_timeout=30,
        sslmode='require',
        cursor_factory=RealDictCursor
    )

def check_data_locations():
    """Check where the CADS data is actually stored."""
    conn = connect_database()
    
    try:
        with conn.cursor() as cursor:
            print("🔍 Checking data locations...")
            print("="*60)
            
            # Check CADS tables (should be the target)
            print("\n📋 CADS Tables (Target):")
            cursor.execute("SELECT COUNT(*) as count FROM cads_researchers;")
            cads_researchers = cursor.fetchone()['count']
            print(f"   cads_researchers: {cads_researchers}")
            
            cursor.execute("SELECT COUNT(*) as count FROM cads_works;")
            cads_works = cursor.fetchone()['count']
            print(f"   cads_works: {cads_works}")
            
            cursor.execute("SELECT COUNT(*) as count FROM cads_topics;")
            cads_topics = cursor.fetchone()['count']
            print(f"   cads_topics: {cads_topics}")
            
            # Check main tables (where data might have gone)
            print("\n📋 Main Tables (Where data likely went):")
            cursor.execute("SELECT COUNT(*) as count FROM researchers;")
            main_researchers = cursor.fetchone()['count']
            print(f"   researchers: {main_researchers}")
            
            cursor.execute("SELECT COUNT(*) as count FROM works;")
            main_works = cursor.fetchone()['count']
            print(f"   works: {main_works}")
            
            cursor.execute("SELECT COUNT(*) as count FROM topics;")
            main_topics = cursor.fetchone()['count']
            print(f"   topics: {main_topics}")
            
            # Check recent researchers (likely CADS professors)
            print("\n👥 Recent Researchers (likely CADS professors):")
            cursor.execute("""
                SELECT full_name, created_at, 
                       (SELECT COUNT(*) FROM works WHERE researcher_id = r.id) as work_count
                FROM researchers r 
                ORDER BY created_at DESC 
                LIMIT 10;
            """)
            recent_researchers = cursor.fetchall()
            
            for researcher in recent_researchers:
                print(f"   {researcher['full_name']}: {researcher['work_count']} works (created: {researcher['created_at']})")
            
            print(f"\n🎯 Analysis:")
            print(f"   CADS tables have minimal data ({cads_researchers} researchers)")
            print(f"   Main tables have much more data ({main_researchers} researchers)")
            print(f"   The pipeline likely stored data in main tables instead of CADS tables")
            
    finally:
        conn.close()

if __name__ == "__main__":
    check_data_locations()