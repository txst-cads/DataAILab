#!/usr/bin/env python3
"""
Migrate CADS professors data from main tables to CADS-specific tables.
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
        logging.FileHandler('cads_data_migration.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# CADS Professor names to identify them in the main tables
CADS_PROFESSOR_NAMES = [
    "Apan Qasem", "Barbara Hewitt", "Carolyn Chang", "Chul-Ho Lee", "Cindy Royal",
    "David Gibbs", "Denise Gobert", "Dincer Konur", "Eduardo Perez", "Edwin Chow",
    "Emily Zhu", "Erica Nason", "Eunsang Cho", "Francis Mendez", "Gregory Lakomski",
    "Hyunhwan Kim", "Ivan Ojeda-Ruiz", "Jelena Tesic", "Karen Lewis", "Keshav Bhandari",
    "Larry Price", "Lucia Summers", "Maria Resendiz", "Monica Hughes", "Mylene Farias",
    "Rasim Musal", "Sarah Fritts", "Semih Aslan", "Shannon Williams", "Subasish Das",
    "Tahir Ekin", "Togay Ozbakkaloglu", "Tongdan Jin", "Toni Terling Watt", "Ty S. Schepis",
    "Vangelis Metsis", "Wenquan Dong", "Xiangping Liu", "Xiaoxi Shen", "Yihong Yuan",
    "Young-Ju Lee", "Ziliang Zong"
]

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

def migrate_cads_data():
    """Migrate CADS data from main tables to CADS tables."""
    conn = connect_database()
    
    try:
        with conn.cursor() as cursor:
            logger.info("🚀 Starting CADS data migration...")
            
            # Step 1: Find CADS researchers in main researchers table
            logger.info("Step 1: Finding CADS researchers...")
            
            # Create a pattern for matching CADS professors
            name_patterns = []
            for name in CADS_PROFESSOR_NAMES:
                # Handle different name formats
                parts = name.split()
                if len(parts) >= 2:
                    # Try different combinations
                    name_patterns.extend([
                        f"'{name}'",
                        f"'%{parts[0]}%{parts[-1]}%'",
                        f"'%{parts[-1]}%{parts[0]}%'"
                    ])
            
            # Find CADS researchers
            query = f"""
                SELECT id, openalex_id, full_name, h_index, department, institution_id
                FROM researchers 
                WHERE full_name ILIKE ANY(ARRAY[{','.join(name_patterns)}])
                ORDER BY created_at DESC;
            """
            
            cursor.execute(query)
            cads_researchers = cursor.fetchall()
            
            logger.info(f"Found {len(cads_researchers)} CADS researchers in main table")
            
            # Step 2: Migrate researchers to cads_researchers table
            logger.info("Step 2: Migrating researchers to cads_researchers...")
            
            migrated_researchers = 0
            researcher_mapping = {}  # main_id -> cads_id
            
            for researcher in cads_researchers:
                try:
                    # Check if already exists in CADS table
                    cursor.execute("""
                        SELECT id FROM cads_researchers 
                        WHERE openalex_id = %s;
                    """, (researcher['openalex_id'],))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        researcher_mapping[researcher['id']] = existing['id']
                        logger.debug(f"Researcher {researcher['full_name']} already exists in CADS table")
                    else:
                        # Insert into CADS table
                        cursor.execute("""
                            INSERT INTO cads_researchers 
                            (institution_id, openalex_id, full_name, h_index, department)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id;
                        """, (
                            researcher['institution_id'],
                            researcher['openalex_id'],
                            researcher['full_name'],
                            researcher['h_index'],
                            researcher['department']
                        ))
                        
                        new_id = cursor.fetchone()['id']
                        researcher_mapping[researcher['id']] = new_id
                        migrated_researchers += 1
                        
                        logger.info(f"Migrated researcher: {researcher['full_name']}")
                
                except Exception as e:
                    logger.error(f"Error migrating researcher {researcher['full_name']}: {e}")
                    continue
            
            conn.commit()
            logger.info(f"Migrated {migrated_researchers} new researchers to cads_researchers")
            
            # Step 3: Migrate works to cads_works table
            logger.info("Step 3: Migrating works to cads_works...")
            
            migrated_works = 0
            work_mapping = {}  # main_work_id -> cads_work_id
            
            for main_researcher_id, cads_researcher_id in researcher_mapping.items():
                # Get all works for this researcher
                cursor.execute("""
                    SELECT id, openalex_id, title, abstract, keywords, 
                           publication_year, doi, citations, embedding
                    FROM works 
                    WHERE researcher_id = %s;
                """, (main_researcher_id,))
                
                works = cursor.fetchall()
                
                for work in works:
                    try:
                        # Check if work already exists in CADS table
                        cursor.execute("""
                            SELECT id FROM cads_works 
                            WHERE openalex_id = %s;
                        """, (work['openalex_id'],))
                        
                        existing_work = cursor.fetchone()
                        
                        if existing_work:
                            work_mapping[work['id']] = existing_work['id']
                        else:
                            # Insert into CADS works table
                            cursor.execute("""
                                INSERT INTO cads_works 
                                (researcher_id, openalex_id, title, abstract, keywords,
                                 publication_year, doi, citations, embedding)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                RETURNING id;
                            """, (
                                cads_researcher_id,
                                work['openalex_id'],
                                work['title'],
                                work['abstract'],
                                work['keywords'],
                                work['publication_year'],
                                work['doi'],
                                work['citations'],
                                work['embedding']
                            ))
                            
                            new_work_id = cursor.fetchone()['id']
                            work_mapping[work['id']] = new_work_id
                            migrated_works += 1
                    
                    except Exception as e:
                        logger.error(f"Error migrating work {work.get('title', 'Unknown')}: {e}")
                        continue
            
            conn.commit()
            logger.info(f"Migrated {migrated_works} works to cads_works")
            
            # Step 4: Migrate topics to cads_topics table
            logger.info("Step 4: Migrating topics to cads_topics...")
            
            migrated_topics = 0
            
            for main_work_id, cads_work_id in work_mapping.items():
                # Get all topics for this work
                cursor.execute("""
                    SELECT name, type, score
                    FROM topics 
                    WHERE work_id = %s;
                """, (main_work_id,))
                
                topics = cursor.fetchall()
                
                for topic in topics:
                    try:
                        # Insert into CADS topics table
                        cursor.execute("""
                            INSERT INTO cads_topics 
                            (work_id, name, type, score)
                            VALUES (%s, %s, %s, %s);
                        """, (
                            cads_work_id,
                            topic['name'],
                            topic['type'],
                            topic['score']
                        ))
                        
                        migrated_topics += 1
                    
                    except Exception as e:
                        logger.debug(f"Error migrating topic (likely duplicate): {e}")
                        continue
            
            conn.commit()
            logger.info(f"Migrated {migrated_topics} topics to cads_topics")
            
            # Step 5: Final verification
            logger.info("Step 5: Final verification...")
            
            cursor.execute("SELECT COUNT(*) as count FROM cads_researchers;")
            final_researchers = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM cads_works;")
            final_works = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM cads_topics;")
            final_topics = cursor.fetchone()['count']
            
            logger.info("="*60)
            logger.info("🎯 CADS Data Migration Complete!")
            logger.info(f"📊 Final CADS Tables:")
            logger.info(f"   cads_researchers: {final_researchers}")
            logger.info(f"   cads_works: {final_works}")
            logger.info(f"   cads_topics: {final_topics}")
            logger.info("="*60)
            
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main function."""
    success = migrate_cads_data()
    
    if success:
        print("\n🎉 CADS data migration completed successfully!")
        print("All CADS professors and their works are now in the CADS-specific tables.")
    else:
        print("\n❌ Migration failed. Check the log file for errors.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)