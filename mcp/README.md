# HCA Lung Atlas Tree FastMCP Server

A FastMCP server that wraps the complete functionality of the HCA Lung Atlas Tree API, making it easy to integrate with AI assistants and other MCP-compatible tools.

## Features

The FastMCP server provides access to all API functionality through these tools:

### Navigation & Overview
- **`get_tree_structure`** - Get the complete tree structure for navigation
- **`get_atlas_stats`** - Get overall statistics about the atlas

### Data Access
- **`get_node_programs`** - Get program list and summary for a specific node
- **`get_program_description`** - Get detailed description for a specific program
- **`get_program_genes`** - Get genes associated with a specific program
- **`get_program_loadings`** - Get loadings data for a specific program

### Analysis & Search
- **`get_node_summary`** - Get summary figures and program labels for a node
- **`search_programs_by_gene`** - Search for programs containing a specific gene
- **`analyze_node_composition`** - Comprehensive analysis of node composition

### Visualization
- **`get_interactive_plot`** - Get interactive plot HTML content

## Installation

1. Ensure you have the required dependencies:
```bash
pip install fastmcp aiohttp uvicorn
```

2. Make sure your HCA Lung Atlas Tree server is running on port 12534

## Usage

### Running the FastMCP Server

From the mcp directory:
```bash
python3 server.py
```

The server will start on `http://localhost:8000` by default.

### Custom Configuration

Set environment variables:
```bash
export HCA_ATLAS_BASE_URL="http://your-server:12534"
python3 server.py
```

### Integration with AI Assistants

This FastMCP server can be integrated with AI assistants that support FastMCP, such as:

1. **Claude Desktop** - Add to your FastMCP configuration
2. **Custom AI applications** - Use FastMCP client libraries
3. **Other FastMCP-compatible tools**

### Claude Desktop Configuration

Add to your Claude Desktop FastMCP configuration:

```json
{
  "fastmcp": {
    "hca-lung-atlas-tree": {
      "url": "http://localhost:8000",
      "description": "HCA Lung Atlas Tree API access"
    }
  }
}
```

## API Coverage

The FastMCP server wraps these original API endpoints:

- `GET /api/tree` → `get_tree_structure`
- `GET /api/node/<node_name>` → `get_node_programs`
- `GET /api/program/<node_name>/<program_name>/description` → `get_program_description`
- `GET /api/program/<node_name>/<program_name>/genes` → `get_program_genes`
- `GET /api/program/<node_name>/<program_name>/loadings` → `get_program_loadings`
- `GET /api/node/<node_name>/summary` → `get_node_summary`
- `GET /api/stats` → `get_atlas_stats`
- `GET /api/interactive-plot/<node_name>/<plot_name>` → `get_interactive_plot`

Plus additional high-level tools:
- `search_programs_by_gene` - Cross-node gene search
- `analyze_node_composition` - Comprehensive node analysis

## Example Queries

Once integrated with an AI assistant, you can ask questions like:

- "What genes are in program_0 of the alveolar_epithelial node?"
- "Search for programs containing the ACTA2 gene"
- "Give me an overview of the lung atlas structure"
- "Analyze the cellular composition of the immune_cells node"
- "What are the statistics for the entire atlas?"

## Files

- **`server.py`** - Main FastMCP server implementation
- **`config.py`** - Configuration settings
- **`README.md`** - This documentation

## Error Handling

The FastMCP server includes robust error handling:
- Connection errors to the Flask API
- Invalid node/program names
- Missing data gracefully handled
- Detailed error messages returned

## Development

To run in development mode with auto-reload:
```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

## Testing

Test the server by making HTTP requests to the FastMCP endpoints or by integrating with a FastMCP client.

## License

Same as the HCA Lung Atlas Tree project.
