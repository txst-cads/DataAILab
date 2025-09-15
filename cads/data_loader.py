#!/usr/bin/env python3
"""
CADS Data Loader Module

This module provides the DataProcessor class for loading and processing
research data from the Supabase database, including embedding generation
and data validation.
"""

import os
import sys
import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import logging
from typing import Dict, Tuple, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Main data processing class for CADS research data.
    
    Handles database connections, data loading, embedding generation,
    and data validation for the CADS research visualization pipeline.
    """
    
    def __init__(self):
        """Initialize the DataProcessor with database connection and embedding model."""
        load_dotenv()
        
        # Database configuration
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL must be set in .env file")
        
        # Initialize database connection
        self.engine = create_engine(self.database_url)
        
        # Initialize embedding model (lazy loading)
        self._embedding_model = None
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        logger.info("DataProcessor initialized successfully")
    
    @property
    def embedding_model(self):
        """Lazy load the embedding model to save memory."""
        if self._embedding_model is None:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        return self._embedding_model
    
    def get_database_connection(self):
        """Get a raw database connection for custom queries."""
        return psycopg2.connect(self.database_url)
    
    def parse_pgvector_embedding(self, embedding_str: str) -> np.ndarray:
        """
        Parse pgvector embedding string format to numpy array.
        
        Args:
            embedding_str: String representation of embedding from database
            
        Returns:
            numpy array of embedding values
        """
        if not embedding_str or embedding_str == 'None':
            return None
        
        try:
            # Remove brackets and split by comma
            embedding_str = str(embedding_str).strip()
            if embedding_str.startswith('[') and embedding_str.endswith(']'):
                values_str = embedding_str[1:-1]
                values = [float(x.strip()) for x in values_str.split(',')]
                return np.array(values)
            else:
                logger.warning(f"Unexpected embedding format: {embedding_str[:50]}...")
                return None
        except Exception as e:
            logger.error(f"Error parsing embedding: {e}")
            return None
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for given text using sentence transformer.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            numpy array of embedding values
        """
        if not text or text.strip() == '':
            return np.zeros(384)  # Default embedding size
        
        try:
            # Combine title and abstract for better embeddings
            embedding = self.embedding_model.encode(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.zeros(384)
    
    def load_cads_data_with_researchers(self) -> pd.DataFrame:
        """
        Load CADS works data joined with researcher information.
        
        Returns:
            DataFrame with works and researcher data
        """
        query = """
        SELECT 
            w.id,
            w.openalex_id,
            w.title,
            w.abstract,
            w.keywords,
            w.publication_year,
            w.doi,
            w.citations,
            w.embedding,
            r.full_name,
            r.department,
            r.h_index
        FROM cads_works w
        JOIN cads_researchers r ON w.researcher_id = r.id
        ORDER BY w.publication_year DESC, w.citations DESC
        """
        
        try:
            logger.info("Loading CADS data with researcher information...")
            df = pd.read_sql(query, self.engine)
            logger.info(f"Loaded {len(df)} works with researcher data")
            return df
        except Exception as e:
            logger.error(f"Error loading CADS data: {e}")
            raise
    
    def process_embeddings(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Process embeddings for the dataset, generating missing ones.
        
        Args:
            df: DataFrame with works data
            
        Returns:
            Tuple of (processed_dataframe, embeddings_array)
        """
        logger.info("Processing embeddings...")
        
        embeddings_list = []
        missing_embeddings = 0
        
        for idx, row in df.iterrows():
            # Try to parse existing embedding
            embedding = self.parse_pgvector_embedding(row['embedding'])
            
            if embedding is None:
                # Generate new embedding from title and abstract
                text_content = f"{row['title']} {row['abstract'] or ''}"
                embedding = self.generate_embedding(text_content)
                missing_embeddings += 1
                
                # Save embedding back to database
                self.save_embedding_to_database(row['id'], embedding)
            
            embeddings_list.append(embedding)
        
        embeddings_array = np.array(embeddings_list)
        
        logger.info(f"Processed {len(embeddings_array)} embeddings")
        logger.info(f"Generated {missing_embeddings} missing embeddings")
        
        return df, embeddings_array
    
    def save_embedding_to_database(self, work_id: str, embedding: np.ndarray):
        """
        Save embedding to database in pgvector format.
        
        Args:
            work_id: ID of the work
            embedding: Numpy array of embedding values
        """
        try:
            # Convert numpy array to pgvector format
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE cads_works SET embedding = %s WHERE id = %s",
                    (embedding_str, work_id)
                )
                conn.commit()
                cursor.close()
        except Exception as e:
            logger.error(f"Error saving embedding for work {work_id}: {e}")
    
    def validate_data(self, df: pd.DataFrame, embeddings: np.ndarray) -> Dict:
        """
        Validate the processed data quality.
        
        Args:
            df: Processed DataFrame
            embeddings: Embeddings array
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'total_works': len(df),
            'works_with_researchers': 0,
            'works_with_citations': 0,
            'works_with_abstracts': 0,
            'embedding_dimensions': embeddings.shape[1] if len(embeddings) > 0 else 0,
            'non_zero_embeddings': (embeddings != 0).any(axis=1).sum() if len(embeddings) > 0 else 0,
            'validation_passed': True,
            'missing_columns': []
        }
        
        # Safely check for required columns with try/catch blocks
        try:
            if 'full_name' in df.columns:
                validation_results['works_with_researchers'] = df['full_name'].notna().sum()
            else:
                validation_results['missing_columns'].append('full_name')
                logger.warning("Column 'full_name' not found in DataFrame")
        except Exception as e:
            logger.error(f"Error validating researcher data: {e}")
            validation_results['missing_columns'].append('full_name')
        
        try:
            if 'citations' in df.columns:
                validation_results['works_with_citations'] = df['citations'].notna().sum()
            else:
                validation_results['missing_columns'].append('citations')
                logger.warning("Column 'citations' not found in DataFrame")
        except Exception as e:
            logger.error(f"Error validating citations data: {e}")
            validation_results['missing_columns'].append('citations')
        
        try:
            if 'abstract' in df.columns:
                validation_results['works_with_abstracts'] = df['abstract'].notna().sum()
            else:
                validation_results['missing_columns'].append('abstract')
                logger.warning("Column 'abstract' not found in DataFrame")
        except Exception as e:
            logger.error(f"Error validating abstract data: {e}")
            validation_results['missing_columns'].append('abstract')
        
        try:
            if 'publication_year' in df.columns:
                validation_results['works_with_publication_year'] = df['publication_year'].notna().sum()
            else:
                validation_results['missing_columns'].append('publication_year')
                logger.warning("Column 'publication_year' not found in DataFrame")
        except Exception as e:
            logger.error(f"Error validating publication_year data: {e}")
            validation_results['missing_columns'].append('publication_year')
        
        # Check validation criteria
        if validation_results['total_works'] == 0:
            validation_results['validation_passed'] = False
            logger.error("No works found in dataset")
        
        if validation_results['embedding_dimensions'] != 384:
            validation_results['validation_passed'] = False
            logger.error(f"Unexpected embedding dimensions: {validation_results['embedding_dimensions']}")
        
        if validation_results['non_zero_embeddings'] < validation_results['total_works'] * 0.9:
            logger.warning("Less than 90% of works have non-zero embeddings")
        
        # Warn about missing columns but don't fail validation
        if validation_results['missing_columns']:
            logger.warning(f"Missing expected columns: {validation_results['missing_columns']}")
        
        logger.info(f"Data validation results: {validation_results}")
        return validation_results
    
    def process_production_dataset(self) -> Dict:
        """
        Process the production dataset (works with embeddings only).
        
        Returns:
            Dictionary with processed data, embeddings, and validation results
        """
        logger.info("Processing production dataset...")
        
        # Load data
        df = self.load_cads_data_with_researchers()
        
        # Process embeddings
        df, embeddings = self.process_embeddings(df)
        
        # Validate data
        validation_results = self.validate_data(df, embeddings)
        
        return {
            'data': df,
            'embeddings': embeddings,
            'validation_passed': validation_results['validation_passed'],
            'validation_results': validation_results
        }
    
    def process_complete_dataset(self) -> Dict:
        """
        Process the complete dataset with full embedding generation.
        
        Returns:
            Dictionary with processed data and embeddings
        """
        logger.info("Processing complete dataset...")
        
        # For now, this is the same as production dataset
        # In the future, this could include additional processing steps
        return self.process_production_dataset()


def main():
    """Main function for testing the DataProcessor."""
    try:
        processor = DataProcessor()
        result = processor.process_production_dataset()
        
        print(f"✅ Successfully processed {len(result['data'])} works")
        print(f"✅ Embeddings shape: {result['embeddings'].shape}")
        print(f"✅ Validation passed: {result['validation_passed']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()