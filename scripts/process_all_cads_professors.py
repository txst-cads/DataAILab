#!/usr/bin/env python3
"""
Comprehensive pipeline to find and process all 55 CADS professors from OpenAlex.
Uses the working IPv4 pooler connection.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import logging
import requests
import time
import json
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cads_professors_pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class CADSProfessorPipeline:
    """Pipeline to find and process CADS professors from OpenAlex."""
    
    def __init__(self):
        self.connection = None
        self.openalex_email = os.getenv('OPENALEX_EMAIL', 'test@texasstate.edu')
        self.processed_count = 0
        self.found_count = 0
        self.total_works = 0
        self.total_citations = 0
        
    def connect_database(self):
        """Connect to database using IPv4 pooler."""
        try:
            USER = os.getenv("user")
            PASSWORD = os.getenv("password")
            HOST = os.getenv("host")
            PORT = os.getenv("port")
            DBNAME = os.getenv("dbname")
            
            self.connection = psycopg2.connect(
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
                dbname=DBNAME,
                connect_timeout=30,
                sslmode='require',
                cursor_factory=RealDictCursor
            )
            
            logger.info("✅ Database connection established")
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def load_cads_professors(self) -> List[Dict[str, str]]:
        """Load CADS professors from cads.txt file."""
        professors = []
        
        try:
            with open('cads.txt', 'r') as f:
                lines = f.readlines()
            
            for line in lines[1:]:  # Skip header
                line = line.strip()
                if line and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        surname = parts[0].strip()
                        name = parts[1].strip()
                        professors.append({
                            'surname': surname,
                            'name': name,
                            'full_name': f"{name} {surname}"
                        })
            
            logger.info(f"Loaded {len(professors)} CADS professors")
            return professors
            
        except Exception as e:
            logger.error(f"Error loading professors: {e}")
            return []
    
    def search_openalex_author(self, professor: Dict[str, str]) -> Dict[str, Any]:
        """Search for a professor in OpenAlex."""
        try:
            # Create search queries with different variations
            search_queries = [
                f"{professor['name']} {professor['surname']}",
                f"{professor['surname']}, {professor['name']}",
                f"{professor['name'].split()[0]} {professor['surname']}" if ' ' in professor['name'] else None
            ]
            
            # Remove None values
            search_queries = [q for q in search_queries if q]
            
            for query in search_queries:
                logger.info(f"Searching OpenAlex for: {query}")
                
                # Search OpenAlex API
                url = "https://api.openalex.org/authors"
                params = {
                    'search': query,
                    'filter': 'institutions.country_code:US',
                    'per-page': 10,
                    'mailto': self.openalex_email
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('results'):
                        # Look for Texas State University affiliation
                        for author in data['results']:
                            if self.is_texas_state_author(author, professor):
                                logger.info(f"✅ Found {professor['full_name']} in OpenAlex: {author['id']}")
                                return author
                
                # Rate limiting
                time.sleep(0.1)
            
            logger.warning(f"❌ Not found in OpenAlex: {professor['full_name']}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching OpenAlex for {professor['full_name']}: {e}")
            return None
    
    def is_texas_state_author(self, author: Dict[str, Any], professor: Dict[str, str]) -> bool:
        """Check if the author is affiliated with Texas State University."""
        try:
            # Check name similarity
            author_name = author.get('display_name', '').lower()
            prof_name = professor['full_name'].lower()
            
            # Simple name matching - could be improved
            name_parts = prof_name.split()
            if not all(part in author_name for part in name_parts):
                return False
            
            # Check for Texas State affiliation
            affiliations = author.get('affiliations', [])
            for affiliation in affiliations:
                institution = affiliation.get('institution', {})
                inst_name = institution.get('display_name', '').lower()
                
                if any(keyword in inst_name for keyword in [
                    'texas state', 'texas state university', 'txstate'
                ]):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking Texas State affiliation: {e}")
            return False
    
    def get_author_works(self, author_id: str) -> List[Dict[str, Any]]:
        """Get all works for an author from OpenAlex."""
        try:
            works = []
            page = 1
            per_page = 200
            
            while True:
                url = "https://api.openalex.org/works"
                params = {
                    'filter': f'author.id:{author_id}',
                    'per-page': per_page,
                    'page': page,
                    'mailto': self.openalex_email
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    batch_works = data.get('results', [])
                    
                    if not batch_works:
                        break
                    
                    works.extend(batch_works)
                    
                    # Check if we have more pages
                    if len(batch_works) < per_page:
                        break
                    
                    page += 1
                    time.sleep(0.1)  # Rate limiting
                else:
                    logger.error(f"Error fetching works for {author_id}: {response.status_code}")
                    break
            
            logger.info(f"Found {len(works)} works for author {author_id}")
            return works
            
        except Exception as e:
            logger.error(f"Error getting works for {author_id}: {e}")
            return []
    
    def process_professor(self, professor: Dict[str, str]) -> bool:
        """Process a single professor: find in OpenAlex and store in database."""
        try:
            logger.info(f"Processing: {professor['full_name']}")
            
            # Search for author in OpenAlex
            author = self.search_openalex_author(professor)
            
            if not author:
                return False
            
            # Get Texas State institution ID
            institution_id = self.get_texas_state_institution_id()
            if not institution_id:
                logger.error("Could not find Texas State institution ID")
                return False
            
            # Store researcher
            researcher_id = self.store_researcher(author, institution_id)
            if not researcher_id:
                return False
            
            # Get and store works
            works = self.get_author_works(author['id'])
            works_stored = 0
            
            for work in works:
                if self.store_work(work, researcher_id):
                    works_stored += 1
                    self.total_works += 1
                    self.total_citations += work.get('cited_by_count', 0)
            
            logger.info(f"✅ Processed {professor['full_name']}: {works_stored} works stored")
            self.found_count += 1
            return True
            
        except Exception as e:
            logger.error(f"Error processing {professor['full_name']}: {e}")
            return False
        finally:
            self.processed_count += 1
    
    def get_texas_state_institution_id(self) -> str:
        """Get Texas State University institution ID from database."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id FROM institutions 
                    WHERE LOWER(name) LIKE '%texas state%' 
                    LIMIT 1;
                """)
                result = cursor.fetchone()
                
                if result:
                    return result['id']
                else:
                    # Create Texas State institution if not exists
                    cursor.execute("""
                        INSERT INTO institutions (id, name, country_code, type)
                        VALUES (gen_random_uuid(), 'Texas State University', 'US', 'education')
                        RETURNING id;
                    """)
                    self.connection.commit()
                    result = cursor.fetchone()
                    return result['id']
                    
        except Exception as e:
            logger.error(f"Error getting institution ID: {e}")
            return None
    
    def store_researcher(self, author: Dict[str, Any], institution_id: str) -> str:
        """Store researcher in database."""
        try:
            with self.connection.cursor() as cursor:
                # Check if researcher already exists
                cursor.execute("""
                    SELECT id FROM researchers WHERE openalex_id = %s;
                """, (author['id'],))
                
                existing = cursor.fetchone()
                if existing:
                    return existing['id']
                
                # Insert new researcher
                cursor.execute("""
                    INSERT INTO researchers (
                        institution_id, openalex_id, full_name, h_index, department
                    ) VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    institution_id,
                    author['id'],
                    author.get('display_name', ''),
                    author.get('summary_stats', {}).get('h_index', 0),
                    'Computer Science'  # Default department for CADS
                ))
                
                self.connection.commit()
                result = cursor.fetchone()
                return result['id']
                
        except Exception as e:
            logger.error(f"Error storing researcher: {e}")
            self.connection.rollback()
            return None
    
    def store_work(self, work: Dict[str, Any], researcher_id: str) -> bool:
        """Store a work in database."""
        try:
            with self.connection.cursor() as cursor:
                # Check if work already exists
                cursor.execute("""
                    SELECT id FROM works WHERE openalex_id = %s;
                """, (work['id'],))
                
                if cursor.fetchone():
                    return True  # Already exists
                
                # Extract keywords from concepts
                keywords = []
                for concept in work.get('concepts', []):
                    if concept.get('score', 0) > 0.3:  # Only high-confidence concepts
                        keywords.append(concept.get('display_name', ''))
                
                keywords_str = ', '.join(keywords[:10])  # Limit to top 10
                
                # Insert work
                cursor.execute("""
                    INSERT INTO works (
                        researcher_id, openalex_id, title, abstract, keywords,
                        publication_year, doi, citations
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    researcher_id,
                    work['id'],
                    work.get('title', ''),
                    work.get('abstract', ''),
                    keywords_str,
                    work.get('publication_year'),
                    work.get('doi'),
                    work.get('cited_by_count', 0)
                ))
                
                self.connection.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error storing work {work.get('id', 'unknown')}: {e}")
            self.connection.rollback()
            return False
    
    def run_pipeline(self):
        """Run the complete pipeline for all CADS professors."""
        try:
            logger.info("🚀 Starting CADS Professors Pipeline")
            logger.info("="*60)
            
            # Connect to database
            if not self.connect_database():
                return False
            
            # Load professors
            professors = self.load_cads_professors()
            if not professors:
                return False
            
            logger.info(f"Processing {len(professors)} CADS professors...")
            
            # Process each professor
            for i, professor in enumerate(professors, 1):
                logger.info(f"\n[{i}/{len(professors)}] Processing: {professor['full_name']}")
                
                success = self.process_professor(professor)
                
                if success:
                    logger.info(f"✅ Successfully processed {professor['full_name']}")
                else:
                    logger.warning(f"❌ Could not process {professor['full_name']}")
                
                # Progress update every 10 professors
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(professors)} processed, {self.found_count} found")
                
                # Rate limiting
                time.sleep(0.5)
            
            # Final summary
            logger.info("\n" + "="*60)
            logger.info("🎯 CADS Professors Pipeline Complete!")
            logger.info(f"📊 Processed: {self.processed_count}/{len(professors)} professors")
            logger.info(f"✅ Found: {self.found_count} professors in OpenAlex")
            logger.info(f"📚 Total Works: {self.total_works}")
            logger.info(f"📈 Total Citations: {self.total_citations}")
            
            return True
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return False
        finally:
            if self.connection:
                self.connection.close()
                logger.info("Database connection closed")

def main():
    """Main function."""
    pipeline = CADSProfessorPipeline()
    success = pipeline.run_pipeline()
    
    if success:
        print("\n🎉 Pipeline completed successfully!")
        print("Check the log file for detailed results.")
    else:
        print("\n❌ Pipeline failed. Check the log file for errors.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)