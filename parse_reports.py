#!/usr/bin/env python3
"""
Script to parse markdown reports from each node and extract image paths for each program.

This script:
1. Goes through each node directory in the assets folder
2. Finds the latest markdown report in the reports directory
3. Parses each program section to extract the 4 key image paths:
   - program_violins_cell_type
   - program_violins_leiden  
   - program_umap_leiden
   - program_umap_activity
4. Outputs the results as JSON files
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
import glob


def find_latest_report(reports_dir):
    """Find the latest markdown report in the reports directory."""
    if not os.path.exists(reports_dir):
        return None
    
    md_files = glob.glob(os.path.join(reports_dir, "*.md"))
    if not md_files:
        return None
    
    # Sort by modification time to get the latest
    latest_file = max(md_files, key=os.path.getmtime)
    return latest_file


def parse_program_images(markdown_content, node_name, assets_base_path):
    """Parse the markdown content to extract image paths for each program."""
    programs = {}
    
    # Split content by program sections
    program_sections = re.split(r'^### Program (\d+)', markdown_content, flags=re.MULTILINE)
    
    # Skip the first section (before any program)
    for i in range(1, len(program_sections), 2):
        if i + 1 >= len(program_sections):
            break
            
        program_num = program_sections[i]
        program_content = program_sections[i + 1]
        
        # Extract the 4 key image paths using regex
        images = {}
        
        # Pattern 1: Program X activity by cell_type
        cell_type_match = re.search(
            r'\*Program \d+ activity by cell_type:\*\s*\n!\[.*?\]\((.*?)\)',
            program_content
        )
        if cell_type_match:
            relative_path = cell_type_match.group(1)
            absolute_path = os.path.join(assets_base_path, node_name, relative_path.replace('../', ''))
            images['program_violins_cell_type'] = absolute_path
        
        # Pattern 2: Program X activity by leiden
        leiden_match = re.search(
            r'\*Program \d+ activity by leiden:\*\s*\n!\[.*?\]\((.*?)\)',
            program_content
        )
        if leiden_match:
            relative_path = leiden_match.group(1)
            absolute_path = os.path.join(assets_base_path, node_name, relative_path.replace('../', ''))
            images['program_violins_leiden'] = absolute_path
        
        # Pattern 3: Program UMAP colored by leiden (this is shared across programs)
        umap_leiden_match = re.search(
            r'\*Program UMAP colored by leiden:\*\s*\n!\[.*?\]\((.*?)\)',
            program_content
        )
        if umap_leiden_match:
            relative_path = umap_leiden_match.group(1)
            absolute_path = os.path.join(assets_base_path, node_name, relative_path.replace('../', ''))
            images['program_umap_leiden'] = absolute_path
        
        # Pattern 4: Program UMAP colored by program X activity
        umap_activity_match = re.search(
            r'\*Program UMAP colored by program \d+ activity:\*\s*\n!\[.*?\]\((.*?)\)',
            program_content
        )
        if umap_activity_match:
            relative_path = umap_activity_match.group(1)
            absolute_path = os.path.join(assets_base_path, node_name, relative_path.replace('../', ''))
            images['program_umap_activity'] = absolute_path
        
        # Only add program if we found at least some images
        if images:
            programs[f'program_{program_num}'] = images
    
    return programs


def parse_node_info(markdown_content, node_name, assets_base_path):
    """Parse node-level information from the markdown report."""
    node_info = {}
    
    try:
        # Extract project name
        project_match = re.search(r'\*\*Project Name:\*\*\s*(.+)', markdown_content)
        if project_match:
            node_info['project_name'] = project_match.group(1).strip()
        
        # Extract cells information
        cells_info = {}
        cells_number_match = re.search(r'- Number of cells:\s*([0-9,]+)', markdown_content)
        if cells_number_match:
            cells_info['number'] = int(cells_number_match.group(1).replace(',', ''))
        
        cells_desc_match = re.search(r'- Description of cells:\s*(.+)', markdown_content)
        if cells_desc_match:
            cells_info['description'] = cells_desc_match.group(1).strip()
        
        # Extract prelabeled clusters
        prelabeled_clusters = {}
        cell_type_match = re.search(r'- cell_type:\s*(\d+)\s*unique values', markdown_content)
        if cell_type_match:
            prelabeled_clusters['cell_type'] = int(cell_type_match.group(1))
        
        leiden_match = re.search(r'- leiden:\s*(\d+)\s*unique values', markdown_content)
        if leiden_match:
            prelabeled_clusters['leiden'] = int(leiden_match.group(1))
        
        if prelabeled_clusters:
            cells_info['prelabeled_clusters'] = prelabeled_clusters
        
        if cells_info:
            node_info['cells'] = cells_info
        
        # Extract genes information
        genes_info = {}
        genes_number_match = re.search(r'- Number of genes:\s*([0-9,]+)', markdown_content)
        if genes_number_match:
            genes_info['number'] = int(genes_number_match.group(1).replace(',', ''))
        
        genes_desc_match = re.search(r'- Description of genes:\s*(.+)', markdown_content)
        if genes_desc_match:
            genes_info['description'] = genes_desc_match.group(1).strip()
        
        if genes_info:
            node_info['genes'] = genes_info
        
        # Extract programs summary
        programs_summary = {}
        
        # Number of programs
        num_programs_match = re.search(r'- Number of programs:\s*(\d+)', markdown_content)
        if num_programs_match:
            programs_summary['number_of_programs'] = int(num_programs_match.group(1))
        
        # Program sizes array
        program_sizes_match = re.search(r'- Program sizes:\s*\[([0-9, ]+)\]', markdown_content)
        if program_sizes_match:
            sizes_str = program_sizes_match.group(1)
            programs_summary['program_sizes'] = [int(x.strip()) for x in sizes_str.split(',')]
        
        # Total unique genes
        total_genes_match = re.search(r'- Total unique genes in programs:\s*([0-9,]+)', markdown_content)
        if total_genes_match:
            programs_summary['total_unique_genes'] = int(total_genes_match.group(1).replace(',', ''))
        
        # Size stats
        size_stats = {}
        stats_match = re.search(r'Min:\s*(\d+),\s*Max:\s*(\d+),\s*Mean:\s*([0-9.]+),\s*Median:\s*([0-9.]+)', markdown_content)
        if stats_match:
            size_stats = {
                'min': int(stats_match.group(1)),
                'max': int(stats_match.group(2)),
                'mean': float(stats_match.group(3)),
                'median': float(stats_match.group(4))
            }
            programs_summary['size_stats'] = size_stats
        
        if programs_summary:
            node_info['programs_summary'] = programs_summary
        
        # Extract overview figures
        overview_figures = {}
        
        # Program correlation heatmap
        corr_heatmap_match = re.search(r'!\[Program Correlation Heatmap\]\(([^)]+)\)', markdown_content)
        if corr_heatmap_match:
            rel_path = corr_heatmap_match.group(1)
            abs_path = os.path.join(assets_base_path, node_name, rel_path.replace('../', ''))
            overview_figures['program_correlation_heatmap'] = abs_path
        
        # UMAP colored by cell_type
        umap_cell_type_match = re.search(r'!\[UMAP Program Vector - cell_type\]\(([^)]+)\)', markdown_content)
        if umap_cell_type_match:
            rel_path = umap_cell_type_match.group(1)
            abs_path = os.path.join(assets_base_path, node_name, rel_path.replace('../', ''))
            overview_figures['program_umap_cell_type'] = abs_path
        
        # UMAP colored by leiden
        umap_leiden_match = re.search(r'!\[UMAP Program Vector - leiden\]\(([^)]+)\)', markdown_content)
        if umap_leiden_match:
            rel_path = umap_leiden_match.group(1)
            abs_path = os.path.join(assets_base_path, node_name, rel_path.replace('../', ''))
            overview_figures['program_umap_leiden'] = abs_path
        
        # Program summary violins
        violins_match = re.search(r'!\[Program Summary Violins - cell_type\]\(([^)]+)\)', markdown_content)
        if violins_match:
            rel_path = violins_match.group(1)
            abs_path = os.path.join(assets_base_path, node_name, rel_path.replace('../', ''))
            overview_figures['program_summary_violins_cell_type'] = abs_path
        
        if overview_figures:
            node_info['overview_figures'] = overview_figures
            
    except Exception as e:
        print(f"Error parsing node info for {node_name}: {e}")
    
    return node_info


def load_program_descriptions(node_path, node_name):
    """Load program descriptions from the program descriptions JSON file."""
    # Construct the expected filename
    if node_name == 'root':
        descriptions_file = os.path.join(node_path, 'root_program_descriptions.json')
    else:
        descriptions_file = os.path.join(node_path, f'{node_name}_program_descriptions.json')
    
    if not os.path.exists(descriptions_file):
        print(f"No program descriptions file found for {node_name}")
        return {}
    
    try:
        with open(descriptions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract program descriptions into a dict keyed by program index
        program_descriptions = {}
        if 'program_descriptions' in data:
            for prog_desc in data['program_descriptions']:
                prog_idx = prog_desc.get('program_index')
                if prog_idx is not None:
                    program_descriptions[prog_idx] = {
                        'total_genes': prog_desc.get('total_genes'),
                        'genes': prog_desc.get('genes'),
                        'loadings': prog_desc.get('loadings'),
                        'description': prog_desc.get('description')
                    }
        
        return program_descriptions
        
    except Exception as e:
        print(f"Error loading program descriptions for {node_name}: {e}")
        return {}


def process_node(node_path, node_name, assets_base_path):
    """Process a single node directory to extract program images, descriptions, and node info."""
    reports_dir = os.path.join(node_path, 'reports')
    latest_report = find_latest_report(reports_dir)
    
    if not latest_report:
        print(f"No markdown report found for {node_name}")
        return None
    
    print(f"Processing {node_name}: {os.path.basename(latest_report)}")
    
    try:
        # Load markdown report
        with open(latest_report, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse node-level information
        node_info = parse_node_info(content, node_name, assets_base_path)
        
        # Parse program images
        programs = parse_program_images(content, node_name, assets_base_path)
        
        # Load program descriptions
        program_descriptions = load_program_descriptions(node_path, node_name)
        
        # Merge images with descriptions
        for program_key, program_data in programs.items():
            # Extract program number from key (e.g., 'program_0' -> 0)
            prog_num = int(program_key.split('_')[1])
            
            # Add description data if available
            if prog_num in program_descriptions:
                program_data.update(program_descriptions[prog_num])
        
        # Build result with node_info
        result = {
            'node_name': node_name,
            'report_file': os.path.basename(latest_report),
            'processed_at': datetime.now().isoformat(),
            'programs': programs
        }
        
        # Add node_info if we found any
        if node_info:
            result['node_info'] = node_info
        
        if programs or node_info:
            return result
        else:
            print(f"No programs or node info found in {node_name}")
            return None
            
    except Exception as e:
        print(f"Error processing {node_name}: {e}")
        return None


def main():
    """Main function to process all nodes."""
    # Base paths
    assets_dir = '/mnt/vdd/hca_lung_atlas_tree/test_setup/assets'
    output_dir = '/mnt/vdd/hca_lung_atlas_tree/display'
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all node directories (starting with 'root')
    node_dirs = []
    for item in os.listdir(assets_dir):
        item_path = os.path.join(assets_dir, item)
        if os.path.isdir(item_path) and item.startswith('root'):
            node_dirs.append((item_path, item))
    
    # Sort to process in consistent order
    node_dirs.sort(key=lambda x: x[1])
    
    print(f"Found {len(node_dirs)} node directories to process")
    
    all_results = {}
    processed_count = 0
    
    # Process each node
    for node_path, node_name in node_dirs:
        result = process_node(node_path, node_name, assets_dir)
        if result:
            all_results[node_name] = result
            processed_count += 1
    
    # Save only the combined results (single JSON file)
    combined_output = os.path.join(output_dir, 'programs.json')
    with open(combined_output, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nProcessing complete!")
    print(f"Processed {processed_count} out of {len(node_dirs)} nodes")
    print(f"Results saved to: {combined_output}")
    
    # Print summary stats
    total_programs = sum(len(result['programs']) for result in all_results.values())
    print(f"Total programs extracted: {total_programs}")
    print(f"Nodes with reports: {list(all_results.keys())}")
    nodes_without_reports = [name for _, name in node_dirs if name not in all_results]
    if nodes_without_reports:
        print(f"Nodes without reports: {nodes_without_reports}")


if __name__ == '__main__':
    main()
