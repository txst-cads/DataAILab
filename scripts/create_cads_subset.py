#!/usr/bin/env python3
"""
Create CADS subset tables and populate them with matching researcher data.
This script reads professor names from cads.txt and creates cads_researchers and cads_works tables
with data for only those researchers whose names match the list.
"""
import os
import sys
import logging
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database.database_manager import DatabaseManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cads_subset.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class CADSSubsetCreator:
    """Creates CADS subset tables and populates them with matching data."""
    
    def __init__(self):
        """Initialize the CADS subset creator."""
        self.db_manager = DatabaseManager()
        self.cads_professors = []
        
    def connect_database(self):
        """Connect to the database."""
        try:
            self.db_manager.connect()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def read_cads_professors(self, file_path: str = "cads.txt") -> List[Tuple[str, str]]:
        """
        Read CADS professors from the text file.
        
        Args:
            file_path: Path to the cads.txt file
            
        Returns:
            List of (surname, name) tuples
        """
        professors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                
            # Skip the header line
            for line in lines[1:]:
                line = line.strip()
                if line and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        surname = parts[0].strip()
                        name = parts[1].strip()
                        professors.append((surname, name))
                        
            logger.info(f"Read {len(professors)} CADS professors from {file_path}")
            return professors
            
        except Exception as e:
            logger.error(f"Error reading CADS professors file: {e}")
            raise
    
    def create_cads_tables(self):
        """Create CADS subset tables with the same schema as original tables."""
        try:
            logger.info("Creating CADS subset tables...")
            
            # Create cads_researchers table
            create_cads_researchers_query = """
            CREATE TABLE IF NOT EXISTS cads_researchers (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                institution_id UUID NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
                openalex_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                h_index INTEGER,
                department TEXT,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            );
            
            -- Create indexes for cads_researchers
            CREATE INDEX IF NOT EXISTS idx_cads_researchers_openalex_id ON cads_researchers(openalex_id);
            CREATE INDEX IF NOT EXISTS idx_cads_researchers_institution_id ON cads_researchers(institution_id);
            CREATE INDEX IF NOT EXISTS idx_cads_researchers_full_name ON cads_researchers(full_name);
            CREATE INDEX IF NOT EXISTS idx_cads_researchers_h_index ON cads_researchers(h_index);
            
            -- Create trigger for updated_at
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_cads_researchers_updated_at') THEN
                    CREATE TRIGGER update_cads_researchers_updated_at 
                    BEFORE UPDATE ON cads_researchers 
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                END IF;
            END $$;
            """
            
            self.db_manager.execute_query(create_cads_researchers_query)
            logger.info("Created cads_researchers table")
            
            # Create cads_works table
            create_cads_works_query = """
            CREATE TABLE IF NOT EXISTS cads_works (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                researcher_id UUID NOT NULL REFERENCES cads_researchers(id) ON DELETE CASCADE,
                openalex_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                abstract TEXT,
                keywords TEXT,
                publication_year INTEGER,
                doi TEXT,
                citations INTEGER DEFAULT 0,
                embedding VECTOR(384),
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            );
            
            -- Create indexes for cads_works
            CREATE INDEX IF NOT EXISTS idx_cads_works_openalex_id ON cads_works(openalex_id);
            CREATE INDEX IF NOT EXISTS idx_cads_works_researcher_id ON cads_works(researcher_id);
            CREATE INDEX IF NOT EXISTS idx_cads_works_publication_year ON cads_works(publication_year);
            CREATE INDEX IF NOT EXISTS idx_cads_works_citations ON cads_works(citations);
            CREATE INDEX IF NOT EXISTS idx_cads_works_title ON cads_works USING gin(to_tsvector('english', title));
            CREATE INDEX IF NOT EXISTS idx_cads_works_abstract ON cads_works USING gin(to_tsvector('english', abstract));
            
            -- Vector similarity index for embeddings
            CREATE INDEX IF NOT EXISTS idx_cads_works_embedding ON cads_works USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
            
            -- Create trigger for updated_at
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_cads_works_updated_at') THEN
                    CREATE TRIGGER update_cads_works_updated_at 
                    BEFORE UPDATE ON cads_works 
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                END IF;
            END $$;
            
            -- Add constraints
            ALTER TABLE cads_works ADD CONSTRAINT IF NOT EXISTS chk_cads_works_publication_year_valid 
            CHECK (publication_year >= 1900 AND publication_year <= EXTRACT(YEAR FROM CURRENT_DATE) + 1);
            ALTER TABLE cads_works ADD CONSTRAINT IF NOT EXISTS chk_cads_works_citations_positive 
            CHECK (citations >= 0);
            """
            
            self.db_manager.execute_query(create_cads_works_query)
            logger.info("Created cads_works table")
            
            # Create cads_topics table
            create_cads_topics_query = """
            CREATE TABLE IF NOT EXISTS cads_topics (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                work_id UUID NOT NULL REFERENCES cads_works(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                score FLOAT8,
                created_at TIMESTAMPTZ DEFAULT now()
            );
            
            -- Create indexes for cads_topics
            CREATE INDEX IF NOT EXISTS idx_cads_topics_work_id ON cads_topics(work_id);
            CREATE INDEX IF NOT EXISTS idx_cads_topics_name ON cads_topics(name);
            CREATE INDEX IF NOT EXISTS idx_cads_topics_type ON cads_topics(type);
            CREATE INDEX IF NOT EXISTS idx_cads_topics_score ON cads_topics(score);
            
            -- Add constraint
            ALTER TABLE cads_topics ADD CONSTRAINT IF NOT EXISTS chk_cads_topics_score_range 
            CHECK (score >= 0.0 AND score <= 1.0);
            """
            
            self.db_manager.execute_query(create_cads_topics_query)
            logger.info("Created cads_topics table")
            
        except Exception as e:
            logger.error(f"Error creating CADS tables: {e}")
            raise
    
    def find_matching_researchers(self, professors: List[Tuple[str, str]]) -> List[Dict]:
        """
        Find researchers in the database that match the CADS professor names.
        
        Args:
            professors: List of (surname, name) tuples
            
        Returns:
            List of matching researcher records
        """
        matching_researchers = []
        
        try:
            logger.info(f"Searching for {len(professors)} CADS professors in the database...")
            
            for surname, name in professors:
                # Try different name matching strategies
                search_patterns = [
                    f"{name} {surname}",  # "John Smith"
                    f"{surname}, {name}",  # "Smith, John"
                    f"{surname} {name}",  # "Smith John"
                    f"{name.split()[0]} {surname}" if ' ' in name else f"{name} {surname}",  # First name only
                ]
                
                found = False
                for pattern in search_patterns:
                    if found:
                        break
                        
                    # Search for researchers with similar names
                    search_query = """
                    SELECT * FROM researchers 
                    WHERE LOWER(full_name) LIKE LOWER(%s)
                    OR LOWER(full_name) LIKE LOWER(%s)
                    OR LOWER(full_name) LIKE LOWER(%s);
                    """
                    
                    like_patterns = [
                        f"%{pattern}%",
                        f"%{name}%{surname}%",
                        f"%{surname}%{name}%"
                    ]
                    
                    results = self.db_manager.execute_query(
                        search_query, 
                        tuple(like_patterns), 
                        fetch=True
                    )
                    
                    if results:
                        for result in results:
                            # Additional validation to avoid false positives
                            full_name = result['full_name'].lower()
                            if (name.lower() in full_name and surname.lower() in full_name):
                                matching_researchers.append(dict(result))
                                logger.info(f"Found match: {result['full_name']} for {name} {surname}")
                                found = True
                                break
                
                if not found:
                    logger.warning(f"No match found for: {name} {surname}")
            
            logger.info(f"Found {len(matching_researchers)} matching researchers")
            return matching_researchers
            
        except Exception as e:
            logger.error(f"Error finding matching researchers: {e}")
            raise
    
    def copy_researcher_data(self, researchers: List[Dict]) -> Dict[str, str]:
        """
        Copy matching researchers to cads_researchers table.
        
        Args:
            researchers: List of researcher records to copy
            
        Returns:
            Dictionary mapping original researcher IDs to new CADS researcher IDs
        """
        id_mapping = {}
        
        try:
            logger.info(f"Copying {len(researchers)} researchers to cads_researchers table...")
            
            for researcher in researchers:
                # Insert into cads_researchers table
                insert_query = """
                INSERT INTO cads_researchers (institution_id, openalex_id, full_name, h_index, department)
                VALUES (%(institution_id)s, %(openalex_id)s, %(full_name)s, %(h_index)s, %(department)s)
                ON CONFLICT (openalex_id) DO NOTHING
                RETURNING id;
                """
                
                result = self.db_manager.execute_query(insert_query, researcher, fetch=True)
                
                if result:
                    new_id = result[0]['id']
                    id_mapping[str(researcher['id'])] = str(new_id)
                    logger.debug(f"Copied researcher: {researcher['full_name']} (ID: {new_id})")
                else:
                    # Handle conflict case - get existing ID
                    existing_query = "SELECT id FROM cads_researchers WHERE openalex_id = %s;"
                    existing_result = self.db_manager.execute_query(
                        existing_query, 
                        (researcher['openalex_id'],), 
                        fetch=True
                    )
                    if existing_result:
                        existing_id = existing_result[0]['id']
                        id_mapping[str(researcher['id'])] = str(existing_id)
                        logger.debug(f"Researcher already exists: {researcher['full_name']} (ID: {existing_id})")
            
            logger.info(f"Successfully copied {len(id_mapping)} researchers")
            return id_mapping
            
        except Exception as e:
            logger.error(f"Error copying researcher data: {e}")
            raise
    
    def copy_works_data(self, researcher_id_mapping: Dict[str, str]):
        """
        Copy works for the CADS researchers to cads_works table.
        
        Args:
            researcher_id_mapping: Mapping of original researcher IDs to CADS researcher IDs
        """
        try:
            logger.info("Copying works for CADS researchers...")
            
            total_works = 0
            total_topics = 0
            
            for original_id, cads_id in researcher_id_mapping.items():
                # Get all works for this researcher
                works_query = "SELECT * FROM works WHERE researcher_id = %s;"
                works = self.db_manager.execute_query(works_query, (original_id,), fetch=True)
                
                if works:
                    logger.info(f"Copying {len(works)} works for researcher {cads_id}")
                    
                    for work in works:
                        # Insert work into cads_works table
                        work_data = dict(work)
                        work_data['researcher_id'] = cads_id  # Update to CADS researcher ID
                        original_work_id = work_data.pop('id')  # Remove original ID
                        
                        insert_work_query = """
                        INSERT INTO cads_works (researcher_id, openalex_id, title, abstract, keywords, 
                                              publication_year, doi, citations, embedding)
                        VALUES (%(researcher_id)s, %(openalex_id)s, %(title)s, %(abstract)s, %(keywords)s,
                                %(publication_year)s, %(doi)s, %(citations)s, %(embedding)s)
                        ON CONFLICT (openalex_id) DO NOTHING
                        RETURNING id;
                        """
                        
                        work_result = self.db_manager.execute_query(insert_work_query, work_data, fetch=True)
                        
                        if work_result:
                            new_work_id = work_result[0]['id']
                            total_works += 1
                            
                            # Copy topics for this work
                            topics_query = "SELECT * FROM topics WHERE work_id = %s;"
                            topics = self.db_manager.execute_query(topics_query, (original_work_id,), fetch=True)
                            
                            if topics:
                                for topic in topics:
                                    topic_data = dict(topic)
                                    topic_data['work_id'] = new_work_id  # Update to CADS work ID
                                    topic_data.pop('id')  # Remove original ID
                                    
                                    insert_topic_query = """
                                    INSERT INTO cads_topics (work_id, name, type, score)
                                    VALUES (%(work_id)s, %(name)s, %(type)s, %(score)s);
                                    """
                                    
                                    self.db_manager.execute_query(insert_topic_query, topic_data)
                                    total_topics += 1
            
            logger.info(f"Successfully copied {total_works} works and {total_topics} topics")
            
        except Exception as e:
            logger.error(f"Error copying works data: {e}")
            raise
    
    def generate_report(self):
        """Generate a report of the CADS subset creation."""
        try:
            logger.info("Generating CADS subset report...")
            
            # Get statistics
            researchers_count_query = "SELECT COUNT(*) as count FROM cads_researchers;"
            researchers_count = self.db_manager.execute_query(researchers_count_query, fetch=True)[0]['count']
            
            works_count_query = "SELECT COUNT(*) as count FROM cads_works;"
            works_count = self.db_manager.execute_query(works_count_query, fetch=True)[0]['count']
            
            topics_count_query = "SELECT COUNT(*) as count FROM cads_topics;"
            topics_count = self.db_manager.execute_query(topics_count_query, fetch=True)[0]['count']
            
            # Get average works per researcher
            avg_works_query = """
            SELECT AVG(work_count) as avg_works
            FROM (
                SELECT COUNT(w.id) as work_count
                FROM cads_researchers r
                LEFT JOIN cads_works w ON r.id = w.researcher_id
                GROUP BY r.id
            ) subq;
            """
            avg_works_result = self.db_manager.execute_query(avg_works_query, fetch=True)
            avg_works = float(avg_works_result[0]['avg_works'] or 0)
            
            # Print report
            print("\n" + "="*60)
            print("CADS SUBSET CREATION REPORT")
            print("="*60)
            print(f"📊 CADS RESEARCHERS: {researchers_count}")
            print(f"📚 CADS WORKS: {works_count}")
            print(f"🏷️  CADS TOPICS: {topics_count}")
            print(f"📈 AVERAGE WORKS PER RESEARCHER: {avg_works:.1f}")
            print("="*60)
            
            # List all CADS researchers
            researchers_query = "SELECT full_name, h_index FROM cads_researchers ORDER BY full_name;"
            researchers = self.db_manager.execute_query(researchers_query, fetch=True)
            
            print("\n📋 CADS RESEARCHERS:")
            for i, researcher in enumerate(researchers, 1):
                h_index = researcher['h_index'] or 'N/A'
                print(f"  {i:2d}. {researcher['full_name']} (H-index: {h_index})")
            
            print("\n✅ CADS subset creation completed successfully!")
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
    
    def run(self):
        """Run the complete CADS subset creation process."""
        try:
            logger.info("Starting CADS subset creation process...")
            
            # Connect to database
            self.connect_database()
            
            # Read CADS professors
            professors = self.read_cads_professors()
            
            # Create CADS tables
            self.create_cads_tables()
            
            # Find matching researchers
            matching_researchers = self.find_matching_researchers(professors)
            
            if not matching_researchers:
                logger.warning("No matching researchers found. Exiting.")
                return
            
            # Copy researcher data
            id_mapping = self.copy_researcher_data(matching_researchers)
            
            # Copy works data
            self.copy_works_data(id_mapping)
            
            # Generate report
            self.generate_report()
            
            logger.info("CADS subset creation completed successfully!")
            
        except Exception as e:
            logger.error(f"CADS subset creation failed: {e}")
            raise
        finally:
            self.db_manager.close()


def main():
    """Main function to run the CADS subset creation."""
    try:
        creator = CADSSubsetCreator()
        creator.run()
        return True
        
    except Exception as e:
        logger.error(f"CADS subset creation failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)