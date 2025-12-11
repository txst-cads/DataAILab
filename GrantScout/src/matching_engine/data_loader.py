"""
DataLoader class responsible for loading and caching all necessary data files 
and models from persistent storage. Prevents reloading large files on every interaction.
"""

import json
import numpy as np
import pandas as pd
import pickle
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

# Optional streamlit import
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


def _cache_decorator(func):
    """Conditional caching decorator - uses streamlit if available, otherwise no caching."""
    if STREAMLIT_AVAILABLE:
        return st.cache_resource(func)
    return func


class DataLoader:
    """Handles loading and caching of all data files and models."""

    def __init__(self, data_dir: str):
        """Initialize with data directory path."""
        self.data_dir = Path(data_dir)
        self._models_cache = None
        self._data_cache = None

    @_cache_decorator
    def load_models(_self) -> Tuple[Any, Any]:
        """Load the TF-IDF model and SentenceTransformer with caching."""
        print("📚 Loading models...")
        
        # Handle pickle loading issue with dummy class if needed
        try:
            with open(_self.data_dir / 'tfidf_model.pkl', 'rb') as f:
                tfidf_model = pickle.load(f)
        except (AttributeError, ModuleNotFoundError) as e:
            if "ResearcherProfileProcessor" in str(e) or "main" in str(e):
                print("🔧 Fixing pickle compatibility issue...")
                # Create dummy class for pickle compatibility
                class ResearcherProfileProcessor:
                    def comma_tokenizer(self, text: str):
                        return [token.strip() for token in text.split(',') if token.strip()]
                
                # Add class to all possible module locations
                import __main__
                setattr(__main__, 'ResearcherProfileProcessor', ResearcherProfileProcessor)
                setattr(sys.modules['__main__'], 'ResearcherProfileProcessor', ResearcherProfileProcessor)
                
                # Create a fake main module if needed
                if 'main' not in sys.modules:
                    import types
                    fake_main = types.ModuleType('main')
                    sys.modules['main'] = fake_main
                
                setattr(sys.modules['main'], 'ResearcherProfileProcessor', ResearcherProfileProcessor)
                
                # Try loading again
                with open(_self.data_dir / 'tfidf_model.pkl', 'rb') as f:
                    tfidf_model = pickle.load(f)
                print("✅ TF-IDF model loaded successfully")
            else:
                raise e
        
        # Load sentence transformer
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            from sentence_transformers import SentenceTransformer
            sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            sentence_model = None
            print("⚠️ SentenceTransformers not available. Dense similarity will be disabled.")
        
        print("✅ Models loaded successfully")
        return tfidf_model, sentence_model

    @_cache_decorator
    def load_data_files(_self) -> Dict[str, Any]:
        """Load all data files with caching."""
        print("📂 Loading data files...")
        
        # Load researcher vectors
        researcher_data = np.load(_self.data_dir / 'researcher_vectors.npz', allow_pickle=True)
        vectors = researcher_data['vectors']
        researcher_ids = researcher_data['researcher_ids']
        researcher_vectors = dict(zip(researcher_ids, vectors))
        
        # Load conceptual profiles (paper embeddings)
        conceptual_data = np.load(_self.data_dir / 'conceptual_profiles.npz', allow_pickle=True)
        embeddings = conceptual_data['embeddings']
        work_ids = conceptual_data['work_ids']
        conceptual_profiles = dict(zip(work_ids, embeddings))
        
        # Load evidence index
        with open(_self.data_dir / 'evidence_index.json', 'r') as f:
            evidence_index = json.load(f)
        
        # Load researcher metadata
        researcher_metadata = pd.read_parquet(_self.data_dir / 'researcher_metadata.parquet')
        
        print(f"✅ Loaded {len(researcher_vectors)} researchers")
        
        return {
            'researcher_vectors': researcher_vectors,
            'conceptual_profiles': conceptual_profiles,
            'evidence_index': evidence_index,
            'researcher_metadata': researcher_metadata
        }
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all loaded data and models in a structured way."""
        tfidf_model, sentence_model = self.load_models()
        data_files = self.load_data_files()
        
        return {
            'models': {
                'tfidf_model': tfidf_model,
                'sentence_model': sentence_model
            },
            'data': data_files
        }
    
    def diagnose_data_quality(self, all_data: Dict[str, Any]) -> None:
        """Diagnose potential data quality issues."""
        print("\n🔍 DIAGNOSING DATA QUALITY")
        print("-" * 40)
        
        models = all_data['models']
        data = all_data['data']
        
        # Check TF-IDF model
        try:
            vocab_size = len(models['tfidf_model'].get_feature_names_out())
            print(f"TF-IDF vocabulary size: {vocab_size}")
            
            vocab = list(models['tfidf_model'].get_feature_names_out())
            print(f"First 10 TF-IDF features: {vocab[:10]}")
        except Exception as e:
            print(f"❌ Error accessing TF-IDF vocabulary: {e}")
        
        # Check researcher vectors
        researcher_vectors = data['researcher_vectors']
        print(f"Researcher vectors: {len(researcher_vectors)}")
        if researcher_vectors:
            sample_vector = next(iter(researcher_vectors.values()))
            print(f"Vector dimensions: {sample_vector.shape}")
        
        # Check conceptual profiles
        conceptual_profiles = data['conceptual_profiles']
        print(f"Conceptual profiles: {len(conceptual_profiles)}")
        if conceptual_profiles:
            sample_embedding = next(iter(conceptual_profiles.values()))
            print(f"Embedding dimensions: {sample_embedding.shape}")
        
        # Check evidence index
        evidence_index = data['evidence_index']
        print(f"Evidence index researchers: {len(evidence_index)}")
        
        # Check overlap between evidence index and conceptual profiles
        all_evidence_papers = set()
        for researcher_papers in evidence_index.values():
            for topic_papers in researcher_papers.values():
                all_evidence_papers.update(topic_papers)
        
        conceptual_papers = set(conceptual_profiles.keys())
        overlap = all_evidence_papers.intersection(conceptual_papers)
        
        print(f"Papers in evidence index: {len(all_evidence_papers)}")
        print(f"Papers with embeddings: {len(conceptual_papers)}")
        print(f"Overlap: {len(overlap)}")
        
        if len(overlap) == 0:
            print("❌ CRITICAL: No overlap between evidence index and conceptual profiles!")
        elif len(overlap) < len(all_evidence_papers) * 0.5:
            print("⚠️ WARNING: Low overlap between evidence index and conceptual profiles!")
        
        print("-" * 40)
