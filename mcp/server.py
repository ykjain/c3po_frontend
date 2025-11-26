#!/usr/bin/env python3
"""
FastMCP Server for HCA Lung Atlas Tree API
Standard FastMCP implementation following MCP protocol.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp

# Import FastMCP components
try:
    from fastmcp import FastMCP, Image
except ImportError:
    print("FastMCP not available. Install with: pip install fastmcp")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_BASE_URL = "http://localhost:12534"
BASE_URL = os.environ.get("HCA_ATLAS_BASE_URL", DEFAULT_BASE_URL)

class HCAAtlasAPI:
    """API client for HCA Atlas Tree Flask server."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def ensure_session(self):
        """Ensure we have an active HTTP session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def api_request(self, endpoint: str) -> Dict[str, Any]:
        """Make an API request to the Flask server."""
        await self.ensure_session()
        url = urljoin(self.base_url, endpoint)
        
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API request failed: {response.status} - {await response.text()}")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session and not self.session.closed:
            await self.session.close()

# Global API instance
atlas_api = HCAAtlasAPI()

# Create FastMCP app
app = FastMCP("hca-lung-atlas-tree")

@app.tool()
async def get_tree_structure() -> str:
    """Get the complete tree structure for navigation of the HCA Lung Atlas."""
    try:
        data = await atlas_api.api_request("/api/tree")
        return f"HCA Lung Atlas Tree Structure:\n\n{json.dumps(data, indent=2)}"
    except Exception as e:
        return f"Error getting tree structure: {str(e)}"

@app.tool()
async def get_node_programs(node_name: str) -> str:
    """Get program list and summary information for a specific node in the atlas tree.
    
    Args:
        node_name: Name of the node to get programs for
    """
    try:
        data = await atlas_api.api_request(f"/api/node/{node_name}")
        
        # Format the response nicely
        result = f"Node: {data.get('node_name', node_name)}\n"
        result += f"Processed at: {data.get('processed_at', 'Unknown')}\n"
        result += f"Report file: {data.get('report_file', 'N/A')}\n\n"
        
        programs = data.get('programs', {})
        result += f"Programs ({len(programs)}):\n"
        
        for prog_name, prog_data in programs.items():
            result += f"\n• {prog_name}:\n"
            result += f"  - Total genes: {prog_data.get('total_genes', 0)}\n"
            result += f"  - Has description: {prog_data.get('has_description', False)}\n"
            result += f"  - Has loadings: {prog_data.get('has_loadings', False)}\n"
            if prog_data.get('summary'):
                result += f"  - Summary: {prog_data['summary'][:200]}...\n"
        
        # Add node info if available
        node_info = data.get('node_info', {})
        if node_info:
            result += f"\nNode Information:\n{json.dumps(node_info, indent=2)}"
        
        return result
    except Exception as e:
        return f"Error getting node programs for {node_name}: {str(e)}"

@app.tool()
async def get_program_description(node_name: str, program_name: str) -> str:
    """Get detailed description for a specific program in a node.
    
    Args:
        node_name: Name of the node containing the program
        program_name: Name of the program (e.g., 'program_0')
    """
    try:
        data = await atlas_api.api_request(f"/api/program/{node_name}/{program_name}/description")
        description = data.get('description', 'No description available')
        return f"Program {program_name} in {node_name}:\n\n{description}"
    except Exception as e:
        return f"Error getting program description: {str(e)}"

@app.tool()
async def get_program_genes(node_name: str, program_name: str) -> str:
    """Get the list of genes associated with a specific program.
    
    Args:
        node_name: Name of the node containing the program
        program_name: Name of the program (e.g., 'program_0')
    """
    try:
        data = await atlas_api.api_request(f"/api/program/{node_name}/{program_name}/genes")
        genes = data.get('genes', [])
        total_genes = data.get('total_genes', len(genes))
        
        result = f"Genes in {program_name} ({node_name}):\n"
        result += f"Total genes: {total_genes}\n\n"
        
        if genes:
            result += "Gene list:\n"
            for i, gene in enumerate(genes[:50]):  # Limit to first 50 for display
                result += f"{i+1:3d}. {gene}\n"
            
            if len(genes) > 50:
                result += f"... and {len(genes) - 50} more genes\n"
        else:
            result += "No genes available for this program.\n"
        
        return result
    except Exception as e:
        return f"Error getting program genes: {str(e)}"

@app.tool()
async def get_program_loadings(node_name: str, program_name: str) -> str:
    """Get the loadings data for a specific program.
    
    Args:
        node_name: Name of the node containing the program
        program_name: Name of the program (e.g., 'program_0')
    """
    try:
        data = await atlas_api.api_request(f"/api/program/{node_name}/{program_name}/loadings")
        loadings = data.get('loadings', {})
        
        if not loadings:
            return f"No loadings available for {program_name} in {node_name}"
        
        result = f"Loadings for {program_name} in {node_name}:\n\n"
        result += json.dumps(loadings, indent=2)
        
        return result
    except Exception as e:
        return f"Error getting program loadings: {str(e)}"

@app.tool()
async def get_node_summary(node_name: str) -> str:
    """Get summary figures and program labels for a node.
    
    Args:
        node_name: Name of the node to get summary for
    """
    try:
        data = await atlas_api.api_request(f"/api/node/{node_name}/summary")
        
        result = f"Summary for {node_name}:\n\n"
        
        # Program labels
        program_labels = data.get('program_labels', {})
        if program_labels:
            result += "Program Labels:\n"
            for prog_id, label in program_labels.items():
                result += f"  Program {prog_id}: {label}\n"
            result += "\n"
        
        # Program gene counts
        gene_counts = data.get('program_gene_counts', {})
        if gene_counts:
            result += "Program Gene Counts:\n"
            for prog_id, count in gene_counts.items():
                result += f"  Program {prog_id}: {count} genes\n"
            result += "\n"
        
        # Cell type counts
        cell_counts = data.get('cell_type_counts', {})
        if cell_counts:
            result += "Cell Type Composition:\n"
            for cell_type, count in list(cell_counts.items())[:20]:  # Top 20
                result += f"  {cell_type}: {count} cells\n"
            result += "\n"
        
        # Available figures
        figures = data.get('figures', {})
        if figures:
            result += "Available Summary Figures:\n"
            for fig_name, fig_path in figures.items():
                result += f"  - {fig_name}: {fig_path}\n"
        
        return result
    except Exception as e:
        return f"Error getting node summary: {str(e)}"

@app.tool()
async def get_atlas_stats() -> str:
    """Get overall statistics about the HCA Lung Atlas Tree."""
    try:
        data = await atlas_api.api_request("/api/stats")
        
        result = "HCA Lung Atlas Tree Statistics:\n\n"
        result += f"Total nodes: {data.get('total_nodes', 0)}\n"
        result += f"Total programs: {data.get('total_programs', 0)}\n\n"
        
        nodes_with_programs = data.get('nodes_with_programs', [])
        if nodes_with_programs:
            result += "Nodes with programs:\n"
            for node_info in nodes_with_programs:
                result += f"  - {node_info['node_name']}: {node_info['program_count']} programs\n"
        
        return result
    except Exception as e:
        return f"Error getting atlas stats: {str(e)}"

@app.tool()
async def search_programs_by_gene(gene_name: str, max_results: int = 50) -> str:
    """Search for programs containing a specific gene across all nodes.
    
    Args:
        gene_name: Name of the gene to search for (e.g., 'ACTA2', 'IL7')
        max_results: Maximum number of results to return (default: 50)
    """
    try:
        # Get tree structure to find all nodes
        tree_data = await atlas_api.api_request("/api/tree")
        results = []
        
        # Extract node names from tree structure
        def extract_node_names(tree_node):
            names = []
            if isinstance(tree_node, dict):
                if 'name' in tree_node:
                    names.append(tree_node['name'])
                if 'children' in tree_node:
                    for child in tree_node['children']:
                        names.extend(extract_node_names(child))
            return names
        
        node_names = extract_node_names(tree_data)
        
        for node_name in node_names[:20]:  # Limit search to prevent overwhelming
            try:
                node_data = await atlas_api.api_request(f"/api/node/{node_name}")
                programs = node_data.get('programs', {})
                
                for program_name, program_data in programs.items():
                    if program_data.get('has_genes'):
                        try:
                            genes_data = await atlas_api.api_request(f"/api/program/{node_name}/{program_name}/genes")
                            genes = genes_data.get('genes', [])
                            
                            if gene_name.upper() in [g.upper() for g in genes]:
                                results.append({
                                    'node': node_name,
                                    'program': program_name,
                                    'total_genes': genes_data.get('total_genes', len(genes)),
                                    'summary': program_data.get('summary', '')
                                })
                                
                                if len(results) >= max_results:
                                    break
                        except:
                            continue  # Skip if genes can't be retrieved
                            
                if len(results) >= max_results:
                    break
            except:
                continue  # Skip nodes that can't be accessed
        
        if not results:
            return f"No programs found containing gene '{gene_name}'"
        
        result_text = f"Programs containing gene '{gene_name}' (found {len(results)}):\n\n"
        
        for i, result in enumerate(results, 1):
            result_text += f"{i}. {result['program']} in {result['node']}\n"
            result_text += f"   Total genes: {result['total_genes']}\n"
            if result['summary']:
                result_text += f"   Summary: {result['summary'][:150]}...\n"
            result_text += "\n"
        
        return result_text
    except Exception as e:
        return f"Error searching for gene {gene_name}: {str(e)}"

@app.tool()
async def get_node_images(node_name: str) -> str:
    """Get a list of all available images for a specific node.
    
    Args:
        node_name: Name of the node to get images for
    """
    try:
        # Get node programs to find program-specific images
        node_data = await atlas_api.api_request(f"/api/node/{node_name}")
        
        # Get node summary for summary images
        summary_data = await atlas_api.api_request(f"/api/node/{node_name}/summary")
        
        result = f"Available Images for Node: {node_name}\n"
        result += "=" * 40 + "\n\n"
        
        # Summary-level images
        figures = summary_data.get('figures', {})
        if figures:
            result += "📊 Summary Images:\n"
            for fig_name, fig_path in figures.items():
                result += f"  • {fig_name}\n"
                result += f"    Path: {fig_path}\n"
            result += "\n"
        
        # Overview figures (includes program correlation heatmap)
        node_info = node_data.get('node_info', {})
        overview_figures = node_info.get('overview_figures', {})
        if overview_figures:
            result += "🔬 Overview Figures:\n"
            for fig_name, fig_path in overview_figures.items():
                result += f"  • {fig_name}\n"
                result += f"    Path: {fig_path}\n"
            result += "\n"
        
        # Program-specific images
        programs = node_data.get('programs', {})
        program_images = {}
        
        for prog_name, prog_data in programs.items():
            images = prog_data.get('images', {})
            heatmaps = prog_data.get('heatmaps', {})
            
            if images or heatmaps:
                program_images[prog_name] = {'images': images, 'heatmaps': heatmaps}
        
        if program_images:
            result += "🧬 Program-Specific Images:\n"
            for prog_name, img_data in program_images.items():
                result += f"\n  📁 {prog_name}:\n"
                
                # Regular images
                for img_name, img_path in img_data['images'].items():
                    if img_path:  # Only show if path exists
                        result += f"    • {img_name}: {img_path}\n"
                
                # Heatmaps
                for heatmap_name, heatmap_path in img_data['heatmaps'].items():
                    if heatmap_path:  # Only show if path exists
                        result += f"    • {heatmap_name}: {heatmap_path}\n"
        
        # Interactive plots
        result += "\n🎯 Interactive Plots:\n"
        result += "  • umap_cell_type (use get_interactive_plot tool)\n"
        
        # Instructions
        result += "\n💡 How to Access Images:\n"
        result += "  1. Use 'get_node_image' tool with the image path to get the actual image\n"
        result += "  2. Summary images: use image_type='summary' with filename\n"
        result += "  3. Program images: use image_type='program' with full path\n"
        result += "  4. Overview figures: use image_type='overview' with full path\n"
        result += "  5. Interactive plots: use 'get_interactive_plot' tool\n"
        
        return result
        
    except Exception as e:
        return f"Error getting images for node {node_name}: {str(e)}"

@app.tool()
async def get_node_image(node_name: str, image_path: str, image_type: str = "summary") -> Image:
    """Get the actual image data for a specific image at a node.
    
    Args:
        node_name: Name of the node
        image_path: Path to the image (filename for summary, full path for program/overview)
        image_type: Type of image ("summary", "program", or "overview")
    """
    try:
        await atlas_api.ensure_session()
        
        if image_type == "summary":
            # Summary images: /api/node-summary-image/{node_name}/{filename}
            url = f"{atlas_api.base_url}/api/node-summary-image/{node_name}/{image_path}"
        elif image_type == "program":
            # Program images: /api/images/{image_path}
            url = f"{atlas_api.base_url}/api/images/{image_path}"
        elif image_type == "overview":
            # For overview figures, let's try reading the file directly to avoid Flask's image processing
            # which might be causing the green image issue
            if image_path.startswith('/mnt/vdd/hca_lung_atlas_tree/test_setup/assets/'):
                # Read the original file directly
                try:
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                    
                    # Determine format from file extension
                    if image_path.lower().endswith('.png'):
                        format_type = 'png'
                    elif image_path.lower().endswith(('.jpg', '.jpeg')):
                        # For JPEG, convert to PNG to avoid Cursor rendering issues
                        try:
                            from PIL import Image as PILImage
                            import io
                            
                            # Load and convert to PNG
                            jpeg_image = PILImage.open(io.BytesIO(image_data))
                            png_buffer = io.BytesIO()
                            jpeg_image.save(png_buffer, format='PNG')
                            image_data = png_buffer.getvalue()
                            format_type = 'png'
                        except Exception as e:
                            logger.warning(f"Failed to convert JPEG to PNG: {e}")
                            format_type = 'jpeg'
                    else:
                        format_type = 'png'  # default
                    
                    return Image(
                        data=image_data,
                        format=format_type
                    )
                except Exception as e:
                    logger.error(f"Failed to read file directly: {e}, falling back to API")
                    # Fallback to API method
                    pass
            
            # Fallback: use API method
            clean_path = image_path.replace('/mnt/vdd/hca_lung_atlas_tree/test_setup/assets/', '')
            url = f"{atlas_api.base_url}/api/images/{clean_path}"
        else:
            raise ValueError(f"Invalid image_type: {image_type}. Use 'summary', 'program', or 'overview'")
        
        async with atlas_api.session.get(url) as response:
            if response.status == 200:
                # Get image content
                image_data = await response.read()
                content_type = response.headers.get('Content-Type', 'image/png')
                
                # For JPEG images, let's try converting them to PNG for better compatibility
                # since Cursor seems to have issues with JPEG rendering
                if 'jpeg' in content_type.lower() or 'jpg' in content_type.lower():
                    try:
                        # Convert JPEG to PNG for better MCP client compatibility
                        from PIL import Image as PILImage
                        import io
                        
                        # Load the JPEG image
                        jpeg_image = PILImage.open(io.BytesIO(image_data))
                        
                        # Convert to PNG
                        png_buffer = io.BytesIO()
                        jpeg_image.save(png_buffer, format='PNG')
                        png_data = png_buffer.getvalue()
                        
                        # Return as PNG
                        return Image(
                            data=png_data,
                            format='png'
                        )
                    except Exception as e:
                        logger.warning(f"Failed to convert JPEG to PNG: {e}, returning original")
                        # Fallback to original JPEG
                        return Image(
                            data=image_data,
                            format='jpeg'
                        )
                else:
                    # For PNG and other formats, use as-is
                    if 'png' in content_type.lower():
                        format_type = 'png'
                    elif 'gif' in content_type.lower():
                        format_type = 'gif'
                    elif 'webp' in content_type.lower():
                        format_type = 'webp'
                    else:
                        format_type = 'png'  # default
                    
                    return Image(
                        data=image_data,
                        format=format_type
                    )
            else:
                error_text = await response.text()
                raise Exception(f"Image not found: {response.status} - {error_text}")
                
    except Exception as e:
        # For errors, we need to return a text response since we can't return Image for errors
        # Let's create a simple error image or return text
        error_msg = f"Error getting image {image_path} from {node_name}: {str(e)}"
        logger.error(error_msg)
        
        # Create a simple text-based error response
        # Since we declared return type as Image, we need to handle this differently
        # Let's create a minimal error image
        try:
            # Create a simple 1x1 transparent PNG as error placeholder
            import base64
            # 1x1 transparent PNG
            error_png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
            return Image(data=error_png, format='png')
        except:
            # If even that fails, re-raise the original error
            raise Exception(error_msg)

@app.tool()
async def list_all_node_images() -> str:
    """Get a comprehensive list of all images available across all nodes in the atlas."""
    try:
        # Get tree structure to find all nodes
        tree_data = await atlas_api.api_request("/api/tree")
        
        # Extract node names from tree structure
        def extract_node_names(tree_node):
            names = []
            if isinstance(tree_node, dict):
                if 'name' in tree_node:
                    names.append(tree_node['name'])
                if 'children' in tree_node:
                    for child in tree_node['children']:
                        names.extend(extract_node_names(child))
            return names
        
        node_names = extract_node_names(tree_data)
        
        result = "🖼️  All Available Images in HCA Lung Atlas Tree\n"
        result += "=" * 50 + "\n\n"
        
        total_images = 0
        
        for node_name in node_names[:10]:  # Limit to first 10 nodes to prevent overwhelming
            try:
                # Get node data
                node_data = await atlas_api.api_request(f"/api/node/{node_name}")
                summary_data = await atlas_api.api_request(f"/api/node/{node_name}/summary")
                
                node_image_count = 0
                
                result += f"📁 {node_name}:\n"
                
                # Summary images
                figures = summary_data.get('figures', {})
                if figures:
                    result += f"  📊 Summary Images ({len(figures)}):\n"
                    for fig_name in figures.keys():
                        result += f"    • {fig_name}\n"
                        node_image_count += 1
                
                # Program images
                programs = node_data.get('programs', {})
                program_image_count = 0
                
                for prog_name, prog_data in programs.items():
                    images = prog_data.get('images', {})
                    heatmaps = prog_data.get('heatmaps', {})
                    
                    prog_img_count = len([v for v in images.values() if v]) + len([v for v in heatmaps.values() if v])
                    program_image_count += prog_img_count
                
                if program_image_count > 0:
                    result += f"  🧬 Program Images: {program_image_count} across {len(programs)} programs\n"
                    node_image_count += program_image_count
                
                result += f"  Total: {node_image_count} images\n\n"
                total_images += node_image_count
                
            except Exception as e:
                result += f"  ⚠️  Error accessing {node_name}: {str(e)}\n\n"
                continue
        
        result += f"📈 Grand Total: {total_images} images across {len(node_names)} nodes\n"
        result += f"\n💡 Use 'get_node_images' tool for detailed image list of a specific node\n"
        result += f"💡 Use 'get_node_image' tool to retrieve actual image data\n"
        
        return result
        
    except Exception as e:
        return f"Error listing all images: {str(e)}"

@app.tool()
async def analyze_node_composition(node_name: str) -> str:
    """Analyze the cellular composition and program characteristics of a specific node.
    
    Args:
        node_name: Name of the node to analyze
    """
    try:
        # Get node programs and summary
        node_data = await atlas_api.api_request(f"/api/node/{node_name}")
        summary_data = await atlas_api.api_request(f"/api/node/{node_name}/summary")
        
        analysis = f"Comprehensive Analysis of Node: {node_name}\n"
        analysis += "=" * 50 + "\n\n"
        
        # Basic info
        analysis += f"Processing Date: {node_data.get('processed_at', 'Unknown')}\n"
        analysis += f"Report File: {node_data.get('report_file', 'N/A')}\n\n"
        
        # Program analysis
        programs = node_data.get('programs', {})
        analysis += f"Program Analysis ({len(programs)} programs):\n"
        analysis += "-" * 30 + "\n"
        
        program_labels = summary_data.get('program_labels', {})
        gene_counts = summary_data.get('program_gene_counts', {})
        
        for prog_name, prog_data in programs.items():
            prog_num = prog_name.replace('program_', '')
            analysis += f"\n• {prog_name}:\n"
            
            if prog_num in program_labels:
                analysis += f"  Label: {program_labels[prog_num]}\n"
            
            analysis += f"  Genes: {prog_data.get('total_genes', 0)}\n"
            
            if prog_data.get('summary'):
                analysis += f"  Function: {prog_data['summary'][:200]}...\n"
        
        # Cell composition
        cell_counts = summary_data.get('cell_type_counts', {})
        if cell_counts:
            analysis += f"\n\nCellular Composition:\n"
            analysis += "-" * 20 + "\n"
            
            total_cells = sum(cell_counts.values())
            analysis += f"Total cells: {total_cells:,}\n\n"
            
            analysis += "Top cell types:\n"
            for i, (cell_type, count) in enumerate(list(cell_counts.items())[:10], 1):
                percentage = (count / total_cells) * 100
                analysis += f"  {i:2d}. {cell_type}: {count:,} cells ({percentage:.1f}%)\n"
        
        # Summary insights
        analysis += f"\n\nKey Insights:\n"
        analysis += "-" * 12 + "\n"
        analysis += f"• This node contains {len(programs)} distinct gene programs\n"
        
        if cell_counts:
            dominant_cell_type = max(cell_counts.items(), key=lambda x: x[1])
            analysis += f"• Dominant cell type: {dominant_cell_type[0]} ({(dominant_cell_type[1]/sum(cell_counts.values()))*100:.1f}%)\n"
            analysis += f"• Cell type diversity: {len(cell_counts)} different cell types\n"
        
        total_genes_in_programs = sum(prog_data.get('total_genes', 0) for prog_data in programs.values())
        analysis += f"• Total genes across all programs: {total_genes_in_programs}\n"
        
        return analysis
        
    except Exception as e:
        return f"Error analyzing node {node_name}: {str(e)}"

def main():
    """Main function to run the FastMCP server."""
    # Initialize API connection synchronously when the server starts
    logger.info(f"HCA Lung Atlas Tree FastMCP Server starting (API: {atlas_api.base_url})")
    
    # Run the FastMCP app with HTTP transport for ngrok compatibility
    app.run(transport="streamable-http", host="0.0.0.0", port=17235)

if __name__ == "__main__":
    main()