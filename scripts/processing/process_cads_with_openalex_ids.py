#!/usr/bin/env python3
"""
Process all CADS professors using their known OpenAlex IDs.
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
        logging.FileHandler('cads_openalex_pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# CADS Professors with their OpenAlex IDs
CADS_PROFESSORS = {
    "Alice Olmstead": "https://openalex.org/A5019067286",
    "Apan Qasem": "https://openalex.org/A5112322145",
    "Araceli Martinez Ortiz": "https://openalex.org/A5005740605",
    "Barbara Hewitt": "https://openalex.org/A5072047829",
    "Byoung-Hee You": "https://openalex.org/A5112339270",
    "Carolyn Chang": "https://openalex.org/A5070750747",
    "Christopher Rhodes": "https://openalex.org/A5019155974",
    "Chul-Ho Lee": "https://openalex.org/A5100622990",
    "Cindy Royal": "https://openalex.org/A5051698859",
    "Clara Novoa": "https://openalex.org/A5063996848",
    "Craig Hanks": "https://openalex.org/A5042004507",
    "Cynthia Luxford": "https://openalex.org/A5051845622",
    "Damian Valles Molina": "https://openalex.org/A5058206555",
    "David Gibbs": "https://openalex.org/A5079734791",
    "Denise Gobert": "https://openalex.org/A5071647515",
    "Dincer Konur": "https://openalex.org/A5041389869",
    "Dominick Fazarro": "https://openalex.org/A5048697958",
    "Eduardo Perez": "https://openalex.org/A5019624555",
    "Edwin Chow": "https://openalex.org/A5002836475",
    "Edwin Piner": "https://openalex.org/A5063322161",
    "Eleanor Close": "https://openalex.org/A5026315010",
    "Emily Zhu": "https://openalex.org/A5064116412",
    "Erica Nason": "https://openalex.org/A5033189368",
    "Eunsang Cho": "https://openalex.org/A5069721379",
    "Francis Mendez": "https://openalex.org/A5103567917",
    "Gregory Lakomski": "https://openalex.org/A5051996968",
    "Heather Galloway": "https://openalex.org/A5032390815",
    "Hsing-Huang Tseng": "https://openalex.org/A5109228226",
    "Hyunhwan Kim": "https://openalex.org/A5018350211",
    "In-Hyouk Song": "https://openalex.org/A5073610568",
    "Ivan Ojeda-Ruiz": "https://openalex.org/A5010639862",
    "Jana Minifie": "https://openalex.org/A5112624029",
    "Jelena Tesic": "https://openalex.org/A5068828260",
    "Jennifer Irvin": "https://openalex.org/A5067439284",
    "Jitendra Tate": "https://openalex.org/A5033762724",
    "Karen Lewis": "https://openalex.org/A5087160649",
    "Keshav Bhandari": "https://openalex.org/A5049757799",
    "Kimberly Talley": "https://openalex.org/A5032705712",
    "Larry Price": "https://openalex.org/A5046299069",
    "Lucia Summers": "https://openalex.org/A5081345383",
    "Maria Resendiz": "https://openalex.org/A5076542050",
    "Mina Guirguis": "https://openalex.org/A5071514799",
    "Monica Hughes": "https://openalex.org/A5042276141",
    "Mylene Farias": "https://openalex.org/A5022483402",
    "Nicole Taylor": "https://openalex.org/A5010161184",
    "Nikoleta Theodoropoulou": "https://openalex.org/A5054127238",
    "Rasim Musal": "https://openalex.org/A5066837050",
    "Ravindranath Droopad": "https://openalex.org/A5006352776",
    "Sarah Fritts": "https://openalex.org/A5018573019",
    "Satyajit Dutta": "https://openalex.org/A5084870824",
    "Semih Aslan": "https://openalex.org/A5036196802",
    "Shannon Williams": "https://openalex.org/A5108934652",
    "Steven Whitten": "https://openalex.org/A5049712400",
    "Subasish Das": "https://openalex.org/A5053621729",
    "Tahir Ekin": "https://openalex.org/A5088154684",
    "Tania Betancourt": "https://openalex.org/A5059795073",
    "Thomas Keller": "https://openalex.org/A5073574614",
    "Togay Ozbakkaloglu": "https://openalex.org/A5017593645",
    "Tongdan Jin": "https://openalex.org/A5012285299",
    "Toni Watt": "https://openalex.org/A5052174768",
    "Ty Schepis": "https://openalex.org/A5062179727",
    "Vangelis Metsis": "https://openalex.org/A5031305480",
    "Wenquan Dong": "https://openalex.org/A5039309764",
    "Wilhelmus Geerts": "https://openalex.org/A5072558155",
    "William Brittain": "https://openalex.org/A5004843671",
    "Xiangping Liu": "https://openalex.org/A5101828368",
    "Xiaoxi Shen": "https://openalex.org/A5100624448",
    "Yihong 'Maggie' Chen": "https://openalex.org/A5035691964",
    "Yihong Yuan": "https://openalex.org/A5044707397",
    "Yong Yang": "https://openalex.org/A5100402375",
    "Young Ju Lee": "https://openalex.org/A5100742029",
    "Ziliang Zong": "https://openalex.org/A5008451482"
}

class CADSOpenAlexPipeline:
    """Pipeline to process CADS professors using their OpenAlex IDs."""
    
    def __init__(self):
        self.connection = None
        self.openalex_email = os.getenv('OPENALEX_EMAIL', 'test@texasstate.edu')
        self.processed_count = 0
        self.found_count = 0
        self.total_works = 0
        self.total_citations = 0
        self.total_topics = 0
        
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
    
    def get_author_from_openalex(self, openalex_id: str) -> Dict[str, Any]:
        """Get author data from OpenAlex using the ID."""
        try:
            # Extract the ID part from the URL
            author_id = openalex_id.split('/')[-1]
            
            url = f"https://api.openalex.org/authors/{author_id}"
            params = {
                'mailto': self.openalex_email
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching author {author_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting author from OpenAlex {openalex_id}: {e}")
            return None
    
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
    
    def store_work(self, work: Dict[str, Any], researcher_id: str) -> str:
        """Store a work in database."""
        try:
            with self.connection.cursor() as cursor:
                # Check if work already exists
                cursor.execute("""
                    SELECT id FROM works WHERE openalex_id = %s;
                """, (work['id'],))
                
                existing = cursor.fetchone()
                if existing:
                    return existing['id']
                
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
                result = cursor.fetchone()
                return result['id']
                
        except Exception as e:
            logger.error(f"Error storing work {work.get('id', 'unknown')}: {e}")
            self.connection.rollback()
            return None
    
    def store_topics(self, work_id: str, topics_data: List[Dict[str, Any]]) -> int:
        """Store topics for a work."""
        try:
            topics_stored = 0
            
            with self.connection.cursor() as cursor:
                for topic in topics_data:
                    try:
                        cursor.execute("""
                            INSERT INTO topics (work_id, name, type, score)
                            VALUES (%s, %s, %s, %s);
                        """, (
                            work_id,
                            topic.get('display_name', ''),
                            'topic',  # Default type
                            topic.get('score', 0.0)
                        ))
                        topics_stored += 1
                    except Exception as e:
                        logger.debug(f"Error storing topic: {e}")
                        continue
                
                self.connection.commit()
                return topics_stored
                
        except Exception as e:
            logger.error(f"Error storing topics for work {work_id}: {e}")
            self.connection.rollback()
            return 0
    
    def process_professor(self, name: str, openalex_id: str) -> bool:
        """Process a single professor."""
        try:
            logger.info(f"Processing: {name}")
            
            # Get author data from OpenAlex
            author = self.get_author_from_openalex(openalex_id)
            
            if not author:
                logger.error(f"Could not fetch author data for {name}")
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
                work_id = self.store_work(work, researcher_id)
                if work_id:
                    works_stored += 1
                    self.total_works += 1
                    self.total_citations += work.get('cited_by_count', 0)
                    
                    # Store topics
                    topics_data = work.get('topics', [])
                    if topics_data:
                        topics_stored = self.store_topics(work_id, topics_data)
                        self.total_topics += topics_stored
            
            logger.info(f"✅ Processed {name}: {works_stored} works, {self.total_topics} topics stored")
            self.found_count += 1
            return True
            
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
            return False
        finally:
            self.processed_count += 1
    
    def run_pipeline(self):
        """Run the complete pipeline for all CADS professors."""
        try:
            logger.info("🚀 Starting CADS Professors Pipeline with OpenAlex IDs")
            logger.info("="*60)
            
            # Connect to database
            if not self.connect_database():
                return False
            
            logger.info(f"Processing {len(CADS_PROFESSORS)} CADS professors...")
            
            # Process each professor
            for i, (name, openalex_id) in enumerate(CADS_PROFESSORS.items(), 1):
                logger.info(f"\n[{i}/{len(CADS_PROFESSORS)}] Processing: {name}")
                
                success = self.process_professor(name, openalex_id)
                
                if success:
                    logger.info(f"✅ Successfully processed {name}")
                else:
                    logger.warning(f"❌ Could not process {name}")
                
                # Progress update every 10 professors
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(CADS_PROFESSORS)} processed, {self.found_count} found")
                
                # Rate limiting
                time.sleep(0.5)
            
            # Final summary
            logger.info("\n" + "="*60)
            logger.info("🎯 CADS Professors Pipeline Complete!")
            logger.info(f"📊 Processed: {self.processed_count}/{len(CADS_PROFESSORS)} professors")
            logger.info(f"✅ Found: {self.found_count} professors in OpenAlex")
            logger.info(f"📚 Total Works: {self.total_works}")
            logger.info(f"🏷️  Total Topics: {self.total_topics}")
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
    pipeline = CADSOpenAlexPipeline()
    success = pipeline.run_pipeline()
    
    if success:
        print("\n🎉 Pipeline completed successfully!")
        print("All CADS professors have been processed and stored in the database.")
    else:
        print("\n❌ Pipeline failed. Check the log file for errors.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)