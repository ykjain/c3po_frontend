# HCA Lung Atlas Tree - Display Website

A Flask-based web application for visualizing cellular program analysis results from the C3PO pipeline.

## Overview

This application provides an interactive interface for exploring:
- Gene expression programs across a hierarchical cell population tree
- UMAP visualizations colored by program activity, cell types, and Leiden clusters
- Heatmaps showing program activity across cell types and clusters
- Program-specific breakdowns with detailed statistics

## Recent Updates (2024)

**Migration to Plotly HTML Visualizations**

The display system has been updated to use interactive Plotly HTML visualizations instead of static PNG images. Key changes:

- 🎨 **Interactive Visualizations**: All plots now support zoom, pan, and hover
- 🔢 **1-based Program Indexing**: Programs now numbered 1, 2, 3... (instead of 0, 1, 2...)
- 📊 **Combined Breakdowns**: Cell type and Leiden cluster analyses in single interactive view
- 📁 **New Data Source**: `/home/ubuntu/c3po_outputs/{node_name}_display_figures/`

See [MIGRATION_NOTES.md](./MIGRATION_NOTES.md) for detailed changes.

## Prerequisites

### Data Requirements

Your data should be organized as follows:

```
/home/ubuntu/c3po_outputs/
├── {node_name}_display_figures/
│   ├── program_umaps/
│   │   ├── program_1.html
│   │   ├── program_2.html
│   │   └── ...
│   ├── per_program_heatmaps/
│   │   ├── program_1_breakdown.html
│   │   ├── program_2_breakdown.html
│   │   └── ...
│   ├── umap_by_cell_type.html
│   ├── heatmap_programs_by_cell_type.html
│   ├── heatmap_programs_by_leiden.html
│   ├── program_labels.json
│   ├── program_descriptions_1indexed.json
│   └── cell_type_counts.json
```

### Generating Visualizations

Use the `c3po_display` pipeline to generate visualizations:

```bash
cd /home/ubuntu/c3po_display
uv run python calculate.py <input_dir> <output_dir>
```

Or for batch processing:

```bash
cd /home/ubuntu/c3po_display
uv run python run_batch.py --paths gs://bucket/path/node1 gs://bucket/path/node2
```

### Python Dependencies

```bash
pip install flask flask-cors pillow pyyaml
```

Or use the provided requirements:
```bash
pip install -r requirements.txt  # if you create one
```

## Installation & Setup

1. **Clone or navigate to the display directory**:
   ```bash
   cd /home/ubuntu/display
   ```

2. **Configure data paths** (if needed):
   
   Edit `server.py` to update the base path (default: `/home/ubuntu/c3po_outputs/`):
   ```python
   summary_base_path = '/home/ubuntu/c3po_outputs'
   ```

3. **Update programs data** (if using legacy format):
   
   Update the `load_data()` function in `server.py` to point to your `programs.json` and `tree.json` files.

## Running the Server

### Development Mode

```bash
python server.py
```

The server will start on `http://0.0.0.0:12534`

### Production Mode

For production, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:12534 server:app
```

### As a Service (systemd)

Create `/etc/systemd/system/hca-display.service`:

```ini
[Unit]
Description=HCA Lung Atlas Display Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/home/ubuntu/display
ExecStart=/usr/bin/python3 /home/ubuntu/display/server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable hca-display
sudo systemctl start hca-display
```

## Usage

1. **Access the website**: Navigate to `http://localhost:12534` (or your server's address)

2. **Login**: Enter the passcode (default: `182638`)
   - Change the passcode in `server.py`: `PASSCODE = 'your_new_passcode'`

3. **Navigate the tree**: 
   - Click on nodes in the left sidebar to explore different cell populations
   - The tree structure is hierarchical (root → clusters → subclusters)

4. **View visualizations**:
   - **Summary Section**: Overview heatmaps for the entire node
   - **Program Cards**: Individual program details (click to expand)
   - **Interactive Plots**: Zoom, pan, and hover over plots for details

5. **Explore programs**:
   - Click program labels in the summary to jump to that program
   - Each program shows UMAP, breakdown charts, and gene information

## File Structure

```
display/
├── server.py                 # Flask backend
├── main.py                   # Alternative entry point
├── templates/
│   ├── index.html           # Main application template
│   └── login.html           # Login page
├── static/
│   ├── css/
│   │   ├── style.css        # Main styles (updated for iframes)
│   │   └── chat.css         # Chat interface styles
│   └── js/
│       ├── app.js           # Main application logic (updated for HTML viz)
│       └── chat.js          # Chat functionality
├── chat/                     # Chat module (optional)
├── programs.json            # Legacy program data
├── MIGRATION_NOTES.md       # Detailed migration documentation
├── TEST_MIGRATION.md        # Testing guide
└── README.md                # This file
```

## API Endpoints

### Core Endpoints

- `GET /` - Main application page (requires auth)
- `GET /login` - Login page
- `POST /login` - Login handler
- `GET /logout` - Logout handler

### Data Endpoints

- `GET /api/stats` - Overall statistics
- `GET /api/tree` - Tree structure for navigation
- `GET /api/node/<node_name>` - Node metadata and program list
- `GET /api/node/<node_name>/summary` - Node summary figures and labels
- `GET /api/program/<node_name>/<program_name>/description` - Program description
- `GET /api/program/<node_name>/<program_name>/genes` - Program gene list
- `GET /api/program/<node_name>/<program_name>/loadings` - Program loadings

### Visualization Endpoints

- `GET /api/node-summary-html/<node_name>/<filepath>` - Serve HTML visualizations
- `GET /api/interactive-plot/<node_name>/<plot_name>` - Serve interactive plots
- `GET /api/images/<filepath>` - Serve compressed images (legacy)

## Configuration

### Security

**Change the default passcode** in `server.py`:
```python
PASSCODE = 'your_secure_passcode'
```

**Change the secret key** for sessions:
```python
app.secret_key = 'your-secret-key-here'
```

### Paths

Update data paths in `server.py`:

```python
# Visualization data
summary_base_path = '/home/ubuntu/c3po_outputs'

# Legacy program data
programs_file = '/path/to/programs.json'
tree_file = '/path/to/tree.json'
```

## Troubleshooting

### Issue: "Node summary not found"
- Check that output directories follow the pattern: `{node_name}_display_figures`
- Verify files exist in `/home/ubuntu/c3po_outputs/`

### Issue: Blank iframes
- Check browser console (F12) for errors
- Verify HTML files are valid Plotly outputs
- Check file permissions

### Issue: Program numbers don't match
- Ensure `program_descriptions_1indexed.json` exists
- Old 0-indexed `program_descriptions.json` will cause mismatches

### Issue: "No image found" messages
- This is expected for visualizations not generated by the pipeline
- `cluster_by_cell_type_heatmap` is not currently generated

## Testing

See [TEST_MIGRATION.md](./TEST_MIGRATION.md) for a comprehensive testing guide.

Quick test:
```bash
# Start server
python server.py

# In browser
# 1. Go to http://localhost:12534
# 2. Login with passcode
# 3. Select a node with data
# 4. Verify visualizations load
```

## Development

### Adding New Visualizations

1. Generate the visualization in `c3po_display` pipeline
2. Update `server.py` to include the file in the API response
3. Update `app.js` to render the visualization
4. Test with a sample node

### Modifying Styles

- Edit `static/css/style.css` for global styles
- Edit `static/css/chat.css` for chat interface
- CSS custom properties (variables) are defined in `:root` selector

### Debugging

Enable Flask debug mode in `server.py`:
```python
app.run(host='0.0.0.0', port=12534, debug=True)
```

Check browser console (F12) for JavaScript errors.

## Performance Optimization

For large datasets:

1. **Lazy Loading**: Iframes load on-demand (already implemented)
2. **Caching**: Consider adding Redis for API response caching
3. **CDN**: Serve static files from a CDN
4. **Compression**: Enable gzip compression in production

## Contributing

When making changes:
1. Update relevant documentation (this README, MIGRATION_NOTES.md)
2. Test with multiple nodes/programs
3. Check browser console for errors
4. Verify mobile responsiveness

## License

[Add your license information here]

## Contact

[Add contact information or links to issue tracker]

## Acknowledgments

- Original CRC immune hubs design inspiration
- HCA Lung Atlas project
- Plotly for interactive visualizations

