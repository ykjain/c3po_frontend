#!/usr/bin/env python3
"""
Flask server for the HCA Lung Atlas Tree website.
Serves program data with lazy loading endpoints.
"""

import json
import os
from flask import Flask, render_template, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from PIL import Image
import io

# Import chat module
try:
    from chat import chat_bp
    CHAT_AVAILABLE = True
except ImportError as e:
    print(f"Chat module not available: {e}")
    CHAT_AVAILABLE = False
    chat_bp = None

app = Flask(__name__)
CORS(app)

# Register chat blueprint if available
if CHAT_AVAILABLE and chat_bp:
    app.register_blueprint(chat_bp)
    print("Chat module registered successfully")
else:
    print("Chat module not registered")

# Global variable to store program data
programs_data = {}
tree_structure = {}

def load_data():
    """Load program data and tree structure on startup."""
    global programs_data, tree_structure
    
    # Load programs data
    programs_file = '/mnt/vdd/hca_lung_atlas_tree/display/programs.json'
    if os.path.exists(programs_file):
        with open(programs_file, 'r') as f:
            programs_data = json.load(f)
    
    # Load tree structure
    tree_file = '/mnt/vdd/hca_lung_atlas_tree/test_setup/tree.json'
    if os.path.exists(tree_file):
        with open(tree_file, 'r') as f:
            tree_structure = json.load(f)

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/api/tree')
def get_tree():
    """Get the tree structure for navigation."""
    return jsonify(tree_structure)

@app.route('/api/node/<node_name>')
def get_node_programs(node_name):
    """Get program list for a specific node (without heavy data)."""
    if node_name not in programs_data:
        return jsonify({'error': 'Node not found'}), 404
    
    node_data = programs_data[node_name]
    
    # Return basic program info including summary for headers
    program_summaries = {}
    for prog_name, prog_data in node_data.get('programs', {}).items():
        # Extract summary (first sentence before "Evidence:")
        description = prog_data.get('description', '')
        summary = ''
        if description:
            # Split by "Evidence:" and take the first part
            parts = description.split('Evidence:')
            if len(parts) > 1:
                summary = parts[0].strip()
            else:
                # If no "Evidence:" found, take first sentence or first 200 chars
                sentences = description.split('.')
                if len(sentences) > 1:
                    summary = sentences[0] + '.'
                else:
                    summary = description[:200] + ('...' if len(description) > 200 else '')
        
        program_summaries[prog_name] = {
            'total_genes': prog_data.get('total_genes', 0),
            'summary': summary,
            'has_description': bool(prog_data.get('description')),
            'has_genes': bool(prog_data.get('genes')),
            'has_loadings': bool(prog_data.get('loadings')),
            'images': {
                'program_violins_cell_type': prog_data.get('program_violins_cell_type'),
                'program_violins_leiden': prog_data.get('program_violins_leiden'),
                'program_umap_leiden': prog_data.get('program_umap_leiden'),
                'program_umap_activity': prog_data.get('program_umap_activity')
            }
        }
    
    return jsonify({
        'node_name': node_data.get('node_name'),
        'report_file': node_data.get('report_file'),
        'processed_at': node_data.get('processed_at'),
        'programs': program_summaries,
        'node_info': node_data.get('node_info', {})
    })

@app.route('/api/program/<node_name>/<program_name>/description')
def get_program_description(node_name, program_name):
    """Get program description (lazy loaded)."""
    if node_name not in programs_data:
        return jsonify({'error': 'Node not found'}), 404
    
    programs = programs_data[node_name].get('programs', {})
    if program_name not in programs:
        return jsonify({'error': 'Program not found'}), 404
    
    description = programs[program_name].get('description', '')
    return jsonify({'description': description})

@app.route('/api/program/<node_name>/<program_name>/genes')
def get_program_genes(node_name, program_name):
    """Get program genes (lazy loaded)."""
    if node_name not in programs_data:
        return jsonify({'error': 'Node not found'}), 404
    
    programs = programs_data[node_name].get('programs', {})
    if program_name not in programs:
        return jsonify({'error': 'Program not found'}), 404
    
    genes = programs[program_name].get('genes', [])
    total_genes = programs[program_name].get('total_genes', len(genes))
    
    return jsonify({
        'genes': genes,
        'total_genes': total_genes
    })

@app.route('/api/program/<node_name>/<program_name>/loadings')
def get_program_loadings(node_name, program_name):
    """Get program loadings (lazy loaded)."""
    if node_name not in programs_data:
        return jsonify({'error': 'Node not found'}), 404
    
    programs = programs_data[node_name].get('programs', {})
    if program_name not in programs:
        return jsonify({'error': 'Program not found'}), 404
    
    loadings = programs[program_name].get('loadings', {})
    return jsonify({'loadings': loadings})

@app.route('/api/images/<path:filepath>')
def serve_images(filepath):
    """Serve compressed image files for better performance."""
    # Extract the directory and filename from the full path
    full_path = f'/mnt/vdd/hca_lung_atlas_tree/test_setup/assets/{filepath}'
    
    if not os.path.exists(full_path):
        return jsonify({'error': 'Image not found'}), 404
    
    # Check if client wants compressed images (default to yes)
    compress = request.args.get('compress', 'true').lower() == 'true'
    quality = int(request.args.get('quality', '85'))  # Default 85% quality
    
    if not compress:
        # Serve original image
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        return send_from_directory(directory, filename)
    
    try:
        # Open and compress the image
        with Image.open(full_path) as img:
            # Convert RGBA to RGB if necessary (for JPEG compression)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if image is very large (optional optimization)
            max_width = int(request.args.get('max_width', '1200'))
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Save to memory buffer
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=quality, optimize=True)
            img_buffer.seek(0)
            
            return Response(
                img_buffer.getvalue(),
                mimetype='image/jpeg',
                headers={
                    'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                    'Content-Disposition': f'inline; filename="{os.path.basename(filepath)}.jpg"'
                }
            )
            
    except Exception as e:
        print(f"Error compressing image {filepath}: {e}")
        # Fallback to original image
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        return send_from_directory(directory, filename)

@app.route('/api/node/<node_name>/summary')
def get_node_summary(node_name):
    """Get node summary figures and program labels."""
    summary_base_path = '/home/ubuntu/hca_lung_atlas_files/node_summary_figures'
    
    # Check if directory exists for this node
    node_summary_path = os.path.join(summary_base_path, node_name)
    if not os.path.exists(node_summary_path):
        return jsonify({'error': 'Node summary not found'}), 404
    
    # Get the three heatmap images
    figures = {}
    figure_files = [
        'cell_type_by_program_activity_heatmap.png',
        'cluster_by_cell_type_heatmap.png', 
        'leiden_cluster_by_program_activity_heatmap.png'
    ]
    
    for fig_file in figure_files:
        fig_path = os.path.join(node_summary_path, fig_file)
        if os.path.exists(fig_path):
            # Use relative path for serving
            figures[fig_file.replace('.png', '')] = f'/api/node-summary-image/{node_name}/{fig_file}'
    
    # Get program labels
    labels_path = os.path.join(node_summary_path, 'program_labels.json')
    program_labels = {}
    if os.path.exists(labels_path):
        try:
            with open(labels_path, 'r', encoding='utf-8') as f:
                program_labels = json.load(f)
        except Exception as e:
            print(f"Error loading program labels for {node_name}: {e}")
    
    # Get cell type counts
    cell_counts_path = os.path.join(node_summary_path, 'cell_type_counts.json')
    cell_type_counts = {}
    if os.path.exists(cell_counts_path):
        try:
            with open(cell_counts_path, 'r', encoding='utf-8') as f:
                raw_counts = json.load(f)
                # Filter out zero values and sort by count descending
                cell_type_counts = {k: v for k, v in raw_counts.items() if v > 0}
                cell_type_counts = dict(sorted(cell_type_counts.items(), key=lambda x: x[1], reverse=True))
        except Exception as e:
            print(f"Error loading cell type counts for {node_name}: {e}")
    
    # Get gene counts from programs data if available
    program_gene_counts = {}
    if node_name in programs_data:
        node_programs = programs_data[node_name].get('programs', {})
        for prog_key, prog_data in node_programs.items():
            # Extract program number from key (e.g., 'program_0' -> '0')
            prog_num = prog_key.replace('program_', '')
            total_genes = prog_data.get('total_genes', 0)
            if total_genes:
                program_gene_counts[prog_num] = total_genes
    
    return jsonify({
        'node_name': node_name,
        'figures': figures,
        'program_labels': program_labels,
        'program_gene_counts': program_gene_counts,
        'cell_type_counts': cell_type_counts
    })

@app.route('/api/node-summary-image/<node_name>/<filename>')
def serve_node_summary_image(node_name, filename):
    """Serve node summary images."""
    summary_base_path = '/home/ubuntu/hca_lung_atlas_files/node_summary_figures'
    node_path = os.path.join(summary_base_path, node_name)
    
    if not os.path.exists(node_path):
        return "Node not found", 404
    
    return send_from_directory(node_path, filename)

@app.route('/api/interactive-plot/<node_name>/<plot_name>')
def serve_interactive_plot(node_name, plot_name):
    """Serve interactive Plotly HTML files."""
    summary_base_path = '/home/ubuntu/hca_lung_atlas_files/node_summary_figures'
    node_summary_path = os.path.join(summary_base_path, node_name)
    
    if not os.path.exists(node_summary_path):
        return jsonify({'error': 'Node not found'}), 404
    
    # Map plot names to actual file names
    plot_files = {
        'umap_cell_type': 'umap_cell_type.html'
    }
    
    if plot_name not in plot_files:
        return jsonify({'error': 'Plot not found'}), 404
    
    file_path = os.path.join(node_summary_path, plot_files[plot_name])
    if not os.path.exists(file_path):
        return jsonify({'error': 'Plot file not found'}), 404
    
    return send_from_directory(node_summary_path, plot_files[plot_name], mimetype='text/html')

@app.route('/api/stats')
def get_stats():
    """Get overall statistics."""
    total_nodes = len(programs_data)
    total_programs = sum(len(node_data.get('programs', {})) for node_data in programs_data.values())
    
    nodes_with_programs = []
    for node_name, node_data in programs_data.items():
        program_count = len(node_data.get('programs', {}))
        if program_count > 0:
            nodes_with_programs.append({
                'node_name': node_name,
                'program_count': program_count
            })
    
    return jsonify({
        'total_nodes': total_nodes,
        'total_programs': total_programs,
        'nodes_with_programs': nodes_with_programs
    })

if __name__ == '__main__':
    load_data()
    print(f"Loaded data for {len(programs_data)} nodes")
    print(f"Total programs: {sum(len(node_data.get('programs', {})) for node_data in programs_data.values())}")
    app.run(host='0.0.0.0', port=12534, debug=True)
