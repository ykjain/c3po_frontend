# Testing the Display Website Migration

## Overview
This guide will help you test the migrated display website that now uses the new Plotly HTML-based visualizations from `c3po_display`.

## Prerequisites

1. Ensure you have generated visualizations in `/home/ubuntu/c3po_outputs/`
2. The visualizations should follow the naming pattern: `{node_name}_display_figures/`
3. You should have at least one complete set of visualizations for testing

## Quick Start

### 1. Start the Server

```bash
cd /home/ubuntu/display
python server.py
```

The server should start on `http://0.0.0.0:12534`

### 2. Access the Website

Open your browser and navigate to:
```
http://localhost:12534
```

You should see a login page. Enter the passcode: `182638`

## Test Checklist

### Basic Navigation
- [ ] Tree structure loads on the left sidebar
- [ ] Clicking a node name loads the node content
- [ ] Program cards are displayed for the selected node
- [ ] Stats (total nodes/programs) display in the header

### Node Summary Section
Test with any node that has data (e.g., `root`, `root_c_5`):

- [ ] **Summary Heatmaps Display Correctly**
  - Cell Type by Program Activity heatmap loads in iframe
  - Leiden Cluster by Program Activity heatmap loads in iframe
  - Cluster by Cell Type shows "No image found" (this is expected)
  - All iframes are interactive (can zoom, pan, hover)

- [ ] **Program Labels Display**
  - Program labels show with 1-based indexing (Program 1, Program 2, etc.)
  - Clicking a program label scrolls to that program card
  - Labels match the content of `program_labels.json`

- [ ] **Cell Type Counts Display**
  - Cell type counts are shown if available
  - Counts are sorted by frequency

### Individual Program Cards
Expand a program card by clicking on it:

- [ ] **Program UMAP Displays**
  - Interactive Plotly UMAP loads in iframe
  - Shows "Interactive" badge
  - Zoom/pan/hover works correctly

- [ ] **UMAP - Cell Type Displays**
  - Interactive cell type UMAP loads
  - Coloring by cell type is visible
  - Interactive features work

- [ ] **Program Breakdown Displays**
  - Combined breakdown (cell type + leiden cluster) loads in single iframe
  - Both charts are visible side by side
  - Hover shows cell counts and mean activity values
  - Charts use the same color scale as the UMAP (blue-gray-red diverging)

### Missing Files Handling
- [ ] Missing visualizations show "No image found" message
- [ ] Missing message is styled appropriately (gray text, centered)
- [ ] Page doesn't break when files are missing

### Interactive Features
- [ ] Plotly iframes support:
  - Zoom (click and drag)
  - Pan (shift + click and drag)
  - Reset view (double-click or home button)
  - Hover tooltips with exact values
  - Legend interaction (click to hide/show traces)

## Detailed Test Scenarios

### Scenario 1: Test a Complete Node (e.g., root_c_5)

1. Navigate to `root_c_5` in the tree
2. Verify all summary heatmaps load
3. Check that program labels are 1-based (starts at Program 1)
4. Expand Program 1
5. Verify the UMAP loads and is interactive
6. Verify the breakdown chart loads with both cell type and leiden panels
7. Test zoom functionality on the UMAP
8. Test hover on the breakdown bars to see exact values

### Scenario 2: Test Missing Data Handling

1. Navigate to a node that might have incomplete data
2. Verify that missing files show "No image found"
3. Verify the page layout doesn't break
4. Verify other available visualizations still load correctly

### Scenario 3: Test Program Indexing

1. Pick any node with multiple programs
2. In the summary section, note the program numbers in the labels (should be 1, 2, 3...)
3. Open the individual program cards
4. Verify the program numbers in the card titles match the labels
5. Verify the underlying files are loaded from the correct paths (check browser dev tools > Network tab)

## Troubleshooting

### Issue: Iframes show "File not found"
**Solution**: Check that the output files exist in `/home/ubuntu/c3po_outputs/{node_name}_display_figures/`

### Issue: Program numbers don't match
**Solution**: Verify the `program_descriptions_1indexed.json` file exists and is being used

### Issue: "Node summary not found"
**Solution**: 
- Check that the directory name matches: `{node_name}_display_figures`
- Verify the server is looking in `/home/ubuntu/c3po_outputs/`

### Issue: Blank iframes or loading forever
**Solution**:
- Check browser console (F12) for errors
- Verify the HTML files are valid Plotly outputs
- Check server logs for 404 errors

### Issue: Layout looks broken
**Solution**:
- Clear browser cache (Ctrl+F5)
- Check that `style.css` has been updated with iframe styles
- Verify JavaScript console for errors

## Browser Compatibility

Tested browsers:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge

## Performance Notes

- Initial page load may take a few seconds for nodes with many programs
- Iframes load lazily, so scrolling is smooth
- Plotly visualizations may be slower on large datasets (>100k cells)
- Consider reducing iframe heights if performance is an issue

## Expected Behavior vs Old System

| Feature | Old System | New System |
|---------|------------|------------|
| Visualization Format | Static PNG | Interactive HTML (Plotly) |
| Program Indexing | 0-based | 1-based |
| Per-Program Breakdown | Two separate PNGs | One combined HTML |
| Cluster by Cell Type | Available | Not generated (shows "No image found") |
| Interactivity | None (static images) | Full (zoom, pan, hover) |
| File Size | Smaller (PNG) | Larger (HTML with embedded data) |

## Success Criteria

The migration is successful if:
1. ✅ All available HTML visualizations load in iframes
2. ✅ Missing files show "No image found" gracefully
3. ✅ Program indexing is consistent (1-based throughout)
4. ✅ Interactive features (zoom, hover) work
5. ✅ Page layout is clean and responsive
6. ✅ No JavaScript console errors
7. ✅ Navigation between nodes works smoothly

## Reporting Issues

If you find issues, please note:
- Which node you were viewing
- Which program (if applicable)
- Browser and version
- Screenshot if possible
- Any console errors (F12 > Console)

