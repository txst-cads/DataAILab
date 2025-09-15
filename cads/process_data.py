#!/usr/bin/env python3
"""
CADS Process Data Module

Main pipeline orchestration for the CADS research data processing.
Coordinates data loading, UMAP reduction, HDBSCAN clustering, and theme generation.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import logging

# Import core modules
from data_loader import DataProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_and_process_data():
    """
    Main function to load and process CADS research data.
    
    Returns:
        Dictionary with processed data and embeddings
    """
    logger.info("Starting CADS data processing pipeline...")
    
    try:
        # Initialize data processor
        processor = DataProcessor()
        
        # Process the production dataset
        result = processor.process_production_dataset()
        
        logger.info("Data processing completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in data processing pipeline: {e}")
        raise


def compute_clusters(data_dict=None):
    """
    Compute clusters using UMAP and HDBSCAN.
    
    Args:
        data_dict: Optional dictionary with data and embeddings
        
    Returns:
        Dictionary with clustering results
    """
    logger.info("Computing clusters...")
    
    try:
        # If no data provided, load it
        if data_dict is None:
            data_dict = load_and_process_data()
        
        data = data_dict['data']
        embeddings = data_dict['embeddings']
        
        # Check if we have pre-computed results
        data_dir = Path(__file__).parent / 'data'
        umap_file = data_dir / 'umap_coordinates.json'
        clustering_file = data_dir / 'clustering_results.json'
        
        if umap_file.exists() and clustering_file.exists():
            logger.info("Loading pre-computed clustering results...")
            
            # Load UMAP coordinates
            with open(umap_file, 'r') as f:
                umap_data = json.load(f)
            
            # Load clustering results
            with open(clustering_file, 'r') as f:
                clustering_data = json.load(f)
            
            # Convert to numpy arrays
            umap_coords = np.array([[point['x'], point['y']] for point in umap_data])
            cluster_labels = np.array([point['cluster'] for point in clustering_data])
            
            logger.info(f"Loaded {len(umap_coords)} UMAP coordinates")
            logger.info(f"Found {len(set(cluster_labels))} unique clusters")
            
            return {
                'data': data,
                'embeddings': embeddings,
                'umap_coordinates': umap_coords,
                'cluster_labels': cluster_labels,
                'n_clusters': len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            }
        
        else:
            logger.info("Pre-computed clustering results not found")
            logger.info("Running UMAP and HDBSCAN clustering...")
            
            try:
                # Import ML libraries
                import umap
                import hdbscan
                
                # Run UMAP dimensionality reduction
                logger.info("Running UMAP dimensionality reduction...")
                umap_model = umap.UMAP(
                    n_neighbors=15,
                    min_dist=0.1,
                    n_components=2,
                    metric='cosine',
                    random_state=42
                )
                umap_coords = umap_model.fit_transform(embeddings)
                logger.info(f"UMAP completed: {umap_coords.shape}")
                
                # Run HDBSCAN clustering
                logger.info("Running HDBSCAN clustering...")
                hdbscan_model = hdbscan.HDBSCAN(
                    min_cluster_size=5,
                    min_samples=3,
                    metric='euclidean',
                    cluster_selection_method='eom'
                )
                cluster_labels = hdbscan_model.fit_predict(umap_coords)
                n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
                logger.info(f"HDBSCAN completed: {n_clusters} clusters found")
                
                # Save results for future use
                logger.info("Saving clustering results...")
                
                # Save UMAP coordinates
                umap_data = [{'x': float(coord[0]), 'y': float(coord[1])} for coord in umap_coords]
                with open(umap_file, 'w') as f:
                    json.dump(umap_data, f, indent=2)
                
                # Save clustering results
                clustering_data = [{'cluster': int(label)} for label in cluster_labels]
                with open(clustering_file, 'w') as f:
                    json.dump(clustering_data, f, indent=2)
                
                logger.info("Results saved successfully")
                
                return {
                    'data': data,
                    'embeddings': embeddings,
                    'umap_coordinates': umap_coords,
                    'cluster_labels': cluster_labels,
                    'n_clusters': n_clusters
                }
                
            except ImportError as e:
                logger.error(f"ML dependencies not available: {e}")
                return {
                    'data': data,
                    'embeddings': embeddings,
                    'umap_coordinates': None,
                    'cluster_labels': None,
                    'n_clusters': 0,
                    'message': 'Clustering requires ML dependencies (umap-learn, hdbscan)'
                }
            
    except Exception as e:
        logger.error(f"Error computing clusters: {e}")
        raise


def save_results(results_dict, output_dir='data'):
    """
    Save processing results to JSON files.
    
    Args:
        results_dict: Dictionary with processing results
        output_dir: Directory to save results
    """
    output_path = Path(__file__).parent / output_dir
    output_path.mkdir(exist_ok=True)
    
    try:
        # Save basic data info
        data_info = {
            'total_works': len(results_dict['data']),
            'embedding_dimensions': results_dict['embeddings'].shape[1],
            'n_clusters': results_dict.get('n_clusters', 0),
            'processing_timestamp': pd.Timestamp.now().isoformat()
        }
        
        with open(output_path / 'processing_summary.json', 'w') as f:
            json.dump(data_info, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")


def main():
    """Main function for running the complete pipeline."""
    try:
        logger.info("Starting CADS processing pipeline...")
        
        # Load and process data
        data_results = load_and_process_data()
        
        # Compute clusters
        cluster_results = compute_clusters(data_results)
        
        # Save results
        save_results(cluster_results)
        
        # Print summary
        print("\n" + "="*50)
        print("🎉 CADS Processing Pipeline Complete!")
        print("="*50)
        print(f"📊 Total works processed: {len(cluster_results['data'])}")
        print(f"🧮 Embedding dimensions: {cluster_results['embeddings'].shape[1]}")
        print(f"🎯 Number of clusters: {cluster_results.get('n_clusters', 'N/A')}")
        print(f"✅ Validation passed: {data_results.get('validation_passed', 'N/A')}")
        
        if cluster_results.get('message'):
            print(f"ℹ️  Note: {cluster_results['message']}")
        
        print("="*50)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()