#!/usr/bin/env python3
"""
Template for generating display figures for each node in a cellular programs tree.

This script iterates through all nodes in a test_setup directory and generates
the necessary figures and metadata files for the web display interface.

Expected output structure for each node:
    <node_dir>/display_figures/
        ├── cell_type_by_program_activity_heatmap.png
        ├── cluster_by_cell_type_heatmap.png
        ├── leiden_cluster_by_program_activity_heatmap.png
        ├── program_labels.json
        ├── cell_type_counts.json
        ├── umap_cell_type.html
        ├── umap_cell_type.png
        └── cell_type_by_program_activity_program_<N>.png (per-program)
        └── leiden_cluster_by_program_activity_program_<N>.png (per-program)
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Import your plotting/analysis libraries here
# import scanpy as sc
# import matplotlib.pyplot as plt
# import seaborn as sns
# import plotly.express as px
# import pandas as pd
# import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NodeDisplayFigureGenerator:
    """Generates display figures for a single node in the tree."""
    
    def __init__(self, node_path: Path, adata_path: Optional[Path] = None):
        """
        Initialize the figure generator for a node.
        
        Args:
            node_path: Path to the node directory
            adata_path: Optional path to the AnnData object for this node
        """
        self.node_path = Path(node_path)
        self.node_name = self.node_path.name
        self.output_dir = self.node_path / "display_figures"
        self.adata_path = adata_path
        self.adata = None
        self.program_scores = None
        self.metadata = None
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Initialized generator for node: {self.node_name}")
    
    def load_node_data(self) -> bool:
        """
        Load all necessary data for the node.
        
        This should load:
        - AnnData object with cell information
        - Program scores/activities
        - Cell type annotations
        - Leiden clusters
        - Any other metadata needed for visualization
        
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        try:
            logger.info(f"Loading data for node: {self.node_name}")
            
            # TODO: Implement data loading logic
            # Example:
            # if self.adata_path and self.adata_path.exists():
            #     self.adata = sc.read_h5ad(self.adata_path)
            # else:
            #     # Look for .h5ad file in node directory
            #     h5ad_files = list(self.node_path.glob("*.h5ad"))
            #     if h5ad_files:
            #         self.adata = sc.read_h5ad(h5ad_files[0])
            
            # Load program scores
            # program_scores_path = self.node_path / "program_scores.csv"
            # if program_scores_path.exists():
            #     self.program_scores = pd.read_csv(program_scores_path, index_col=0)
            
            # Extract metadata from adata.obs
            # self.metadata = self.adata.obs.copy()
            
            logger.info(f"Data loaded successfully for {self.node_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data for {self.node_name}: {e}")
            return False
    
    def generate_cell_type_counts(self) -> Dict[str, int]:
        """
        Generate cell type counts for the node.
        
        Returns:
            Dictionary mapping cell type names to counts
        """
        logger.info(f"Generating cell type counts for {self.node_name}")
        
        # TODO: Implement cell type counting
        # Example:
        # cell_type_counts = self.metadata['cell_type'].value_counts().to_dict()
        
        cell_type_counts = {}  # Placeholder
        
        # Save to JSON
        output_path = self.output_dir / "cell_type_counts.json"
        with open(output_path, 'w') as f:
            json.dump(cell_type_counts, f, indent=2)
        
        logger.info(f"Saved cell type counts to {output_path}")
        return cell_type_counts
    
    def generate_program_labels(self) -> Dict[str, str]:
        """
        Generate program labels/descriptions for the node.
        
        Returns:
            Dictionary mapping program numbers to descriptions
        """
        logger.info(f"Generating program labels for {self.node_name}")
        
        # TODO: Implement program label generation
        # This could involve:
        # - Top genes per program
        # - GO enrichment results
        # - Manual annotations if available
        
        program_labels = {}  # Placeholder
        # Example:
        # for i in range(n_programs):
        #     top_genes = get_top_genes_for_program(i, n=5)
        #     program_labels[str(i)] = f"Program {i}: {', '.join(top_genes)}"
        
        # Save to JSON
        output_path = self.output_dir / "program_labels.json"
        with open(output_path, 'w') as f:
            json.dump(program_labels, f, indent=2)
        
        logger.info(f"Saved program labels to {output_path}")
        return program_labels
    
    def generate_umap_cell_type(self):
        """
        Generate UMAP colored by cell type (both static PNG and interactive HTML).
        """
        logger.info(f"Generating UMAP cell type figures for {self.node_name}")
        
        # TODO: Implement UMAP generation
        # Static version (PNG):
        # fig, ax = plt.subplots(figsize=(10, 8))
        # sc.pl.umap(self.adata, color='cell_type', ax=ax, show=False)
        # plt.savefig(self.output_dir / "umap_cell_type.png", dpi=150, bbox_inches='tight')
        # plt.close()
        
        # Interactive version (HTML with Plotly):
        # fig = px.scatter(
        #     x=self.adata.obsm['X_umap'][:, 0],
        #     y=self.adata.obsm['X_umap'][:, 1],
        #     color=self.adata.obs['cell_type'],
        #     title=f'UMAP - {self.node_name}',
        #     labels={'x': 'UMAP 1', 'y': 'UMAP 2', 'color': 'Cell Type'},
        #     hover_data={'leiden': self.adata.obs['leiden']}
        # )
        # fig.write_html(self.output_dir / "umap_cell_type.html")
        
        logger.info(f"Saved UMAP cell type figures")
    
    def generate_cell_type_by_program_activity_heatmap(self):
        """
        Generate heatmap showing program activity across cell types.
        """
        logger.info(f"Generating cell type by program activity heatmap for {self.node_name}")
        
        # TODO: Implement heatmap generation
        # Steps:
        # 1. Calculate mean program activity per cell type
        # 2. Create heatmap with cell types on one axis, programs on another
        
        # Example:
        # program_cols = [col for col in self.metadata.columns if col.startswith('program_')]
        # cell_type_program_matrix = self.metadata.groupby('cell_type')[program_cols].mean()
        # 
        # fig, ax = plt.subplots(figsize=(12, 8))
        # sns.heatmap(cell_type_program_matrix.T, cmap='viridis', ax=ax)
        # ax.set_xlabel('Cell Type')
        # ax.set_ylabel('Program')
        # ax.set_title(f'Program Activity by Cell Type - {self.node_name}')
        # plt.savefig(self.output_dir / "cell_type_by_program_activity_heatmap.png", 
        #             dpi=150, bbox_inches='tight')
        # plt.close()
        
        logger.info(f"Saved cell type by program activity heatmap")
    
    def generate_cluster_by_cell_type_heatmap(self):
        """
        Generate heatmap showing cell type composition across leiden clusters.
        """
        logger.info(f"Generating cluster by cell type heatmap for {self.node_name}")
        
        # TODO: Implement heatmap generation
        # Steps:
        # 1. Count cells of each type in each cluster
        # 2. Optionally normalize (e.g., by cluster size or cell type total)
        # 3. Create heatmap
        
        # Example:
        # cluster_celltype_counts = pd.crosstab(
        #     self.metadata['leiden'],
        #     self.metadata['cell_type'],
        #     normalize='index'  # or 'columns' or None
        # )
        # 
        # fig, ax = plt.subplots(figsize=(12, 8))
        # sns.heatmap(cluster_celltype_counts, cmap='YlOrRd', ax=ax)
        # ax.set_xlabel('Cell Type')
        # ax.set_ylabel('Leiden Cluster')
        # ax.set_title(f'Cell Type Composition by Cluster - {self.node_name}')
        # plt.savefig(self.output_dir / "cluster_by_cell_type_heatmap.png",
        #             dpi=150, bbox_inches='tight')
        # plt.close()
        
        logger.info(f"Saved cluster by cell type heatmap")
    
    def generate_leiden_cluster_by_program_activity_heatmap(self):
        """
        Generate heatmap showing program activity across leiden clusters.
        """
        logger.info(f"Generating leiden cluster by program activity heatmap for {self.node_name}")
        
        # TODO: Implement heatmap generation
        # Similar to cell_type_by_program_activity but using leiden clusters
        
        # Example:
        # program_cols = [col for col in self.metadata.columns if col.startswith('program_')]
        # cluster_program_matrix = self.metadata.groupby('leiden')[program_cols].mean()
        # 
        # fig, ax = plt.subplots(figsize=(12, 8))
        # sns.heatmap(cluster_program_matrix.T, cmap='viridis', ax=ax)
        # ax.set_xlabel('Leiden Cluster')
        # ax.set_ylabel('Program')
        # ax.set_title(f'Program Activity by Cluster - {self.node_name}')
        # plt.savefig(self.output_dir / "leiden_cluster_by_program_activity_heatmap.png",
        #             dpi=150, bbox_inches='tight')
        # plt.close()
        
        logger.info(f"Saved leiden cluster by program activity heatmap")
    
    def generate_per_program_heatmaps(self):
        """
        Generate per-program heatmaps showing individual program activity.
        
        Creates two types of heatmaps for each program:
        - cell_type_by_program_activity_program_<N>.png
        - leiden_cluster_by_program_activity_program_<N>.png
        """
        logger.info(f"Generating per-program heatmaps for {self.node_name}")
        
        # TODO: Implement per-program heatmap generation
        # Get number of programs
        # program_cols = [col for col in self.metadata.columns if col.startswith('program_')]
        # n_programs = len(program_cols)
        
        # for i in range(n_programs):
        #     program_col = f'program_{i}'
        #     
        #     # Cell type by program activity
        #     celltype_activity = self.metadata.groupby('cell_type')[program_col].mean().sort_values()
        #     fig, ax = plt.subplots(figsize=(8, 6))
        #     celltype_activity.plot(kind='barh', ax=ax, color='steelblue')
        #     ax.set_xlabel('Mean Activity')
        #     ax.set_ylabel('Cell Type')
        #     ax.set_title(f'Program {i} Activity by Cell Type')
        #     plt.tight_layout()
        #     plt.savefig(
        #         self.output_dir / f"cell_type_by_program_activity_program_{i}.png",
        #         dpi=150, bbox_inches='tight'
        #     )
        #     plt.close()
        #     
        #     # Leiden cluster by program activity
        #     cluster_activity = self.metadata.groupby('leiden')[program_col].mean().sort_values()
        #     fig, ax = plt.subplots(figsize=(8, 6))
        #     cluster_activity.plot(kind='barh', ax=ax, color='coral')
        #     ax.set_xlabel('Mean Activity')
        #     ax.set_ylabel('Leiden Cluster')
        #     ax.set_title(f'Program {i} Activity by Cluster')
        #     plt.tight_layout()
        #     plt.savefig(
        #         self.output_dir / f"leiden_cluster_by_program_activity_program_{i}.png",
        #         dpi=150, bbox_inches='tight'
        #     )
        #     plt.close()
        
        logger.info(f"Saved per-program heatmaps")
    
    def run(self) -> bool:
        """
        Main execution method that orchestrates the generation of all figures.
        
        Returns:
            bool: True if all figures generated successfully, False otherwise
        """
        logger.info(f"Starting figure generation for node: {self.node_name}")
        
        try:
            # Load data
            if not self.load_node_data():
                logger.error(f"Failed to load data for {self.node_name}")
                return False
            
            # Generate all figures and metadata
            self.generate_cell_type_counts()
            self.generate_program_labels()
            self.generate_umap_cell_type()
            self.generate_cell_type_by_program_activity_heatmap()
            self.generate_cluster_by_cell_type_heatmap()
            self.generate_leiden_cluster_by_program_activity_heatmap()
            self.generate_per_program_heatmaps()
            
            logger.info(f"Successfully generated all figures for {self.node_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating figures for {self.node_name}: {e}", exc_info=True)
            return False


def find_node_directories(test_setup_path: Path) -> List[Path]:
    """
    Find all node directories within the test_setup directory.
    
    Args:
        test_setup_path: Path to the test_setup directory
        
    Returns:
        List of paths to node directories
    """
    node_dirs = []
    
    # Look for the assets directory which contains node folders
    assets_path = test_setup_path / "assets"
    
    if assets_path.exists() and assets_path.is_dir():
        # Each subdirectory in assets is a node
        for node_dir in assets_path.iterdir():
            if node_dir.is_dir():
                node_dirs.append(node_dir)
    
    # Sort by name for consistent ordering
    node_dirs.sort(key=lambda x: x.name)
    
    logger.info(f"Found {len(node_dirs)} node directories")
    return node_dirs


def process_tree(test_setup_path: Path, adata_path: Optional[Path] = None,
                 node_filter: Optional[List[str]] = None) -> Dict[str, bool]:
    """
    Process all nodes in a tree and generate display figures.
    
    Args:
        test_setup_path: Path to the test_setup directory
        adata_path: Optional path to a directory containing .h5ad files for each node
        node_filter: Optional list of node names to process (process all if None)
        
    Returns:
        Dictionary mapping node names to success status
    """
    logger.info(f"Processing tree at: {test_setup_path}")
    
    # Find all node directories
    node_dirs = find_node_directories(test_setup_path)
    
    if not node_dirs:
        logger.warning("No node directories found!")
        return {}
    
    # Filter nodes if specified
    if node_filter:
        node_dirs = [d for d in node_dirs if d.name in node_filter]
        logger.info(f"Filtered to {len(node_dirs)} nodes")
    
    # Process each node
    results = {}
    for i, node_dir in enumerate(node_dirs, 1):
        logger.info(f"Processing node {i}/{len(node_dirs)}: {node_dir.name}")
        
        # Find corresponding .h5ad file if adata_path provided
        node_adata_path = None
        if adata_path:
            potential_adata = adata_path / f"{node_dir.name}.h5ad"
            if potential_adata.exists():
                node_adata_path = potential_adata
        
        # Create generator and run
        generator = NodeDisplayFigureGenerator(node_dir, node_adata_path)
        success = generator.run()
        results[node_dir.name] = success
        
        if success:
            logger.info(f"✓ Successfully processed {node_dir.name}")
        else:
            logger.error(f"✗ Failed to process {node_dir.name}")
    
    # Summary
    n_success = sum(results.values())
    n_total = len(results)
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing complete: {n_success}/{n_total} nodes successful")
    logger.info(f"{'='*60}\n")
    
    return results


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Generate display figures for cellular programs tree nodes"
    )
    parser.add_argument(
        "test_setup_path",
        type=Path,
        help="Path to the test_setup directory containing node folders"
    )
    parser.add_argument(
        "--adata-path",
        type=Path,
        help="Optional path to directory containing .h5ad files for each node"
    )
    parser.add_argument(
        "--nodes",
        nargs="+",
        help="Optional list of specific node names to process"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(args.log_level)
    
    # Validate paths
    if not args.test_setup_path.exists():
        logger.error(f"test_setup path does not exist: {args.test_setup_path}")
        return 1
    
    if args.adata_path and not args.adata_path.exists():
        logger.error(f"adata path does not exist: {args.adata_path}")
        return 1
    
    # Process the tree
    results = process_tree(
        args.test_setup_path,
        args.adata_path,
        args.nodes
    )
    
    # Return non-zero exit code if any failures
    if not all(results.values()):
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

