/**
 * HCA Lung Atlas Tree - Main Application JavaScript
 * Handles tree navigation, lazy loading, and program display
 */

class HCAAtlasApp {
    constructor() {
        this.currentNode = null;
        this.currentNodeSummary = null;
        this.loadedData = new Map(); // Cache for lazy-loaded data
        this.init();
    }

    // Convert node names from root_cluster_L1C03 format to "Cluster 4" format
    formatNodeName(nodeName) {
        if (nodeName === 'root') {
            return 'All Cells';
        }
        
        // Match pattern like root_c_1, root_c_10, etc.
        const rootCMatch = nodeName.match(/root_c_(\d+)/);
        if (rootCMatch) {
            const clusterNum = parseInt(rootCMatch[1]);
            return `Cluster ${clusterNum - 1}`;
        }
        
        // Match pattern for cell type nodes like root_cell_type_Myeloid
        if (nodeName.startsWith('root_cell_type_')) {
            return nodeName.replace('root_cell_type_', '');
        }
        
        // Match pattern for third-level nodes like root_cluster_L1C00_cluster_L2C01
        const thirdLevelMatch = nodeName.match(/root_cluster_L1C(\d+)_cluster_L2C(\d+)/);
        if (thirdLevelMatch) {
            const l1ClusterNum = parseInt(thirdLevelMatch[1]);
            const l2ClusterNum = parseInt(thirdLevelMatch[2]);
            return `L${l1ClusterNum + 1}C${l2ClusterNum}`;
        }
        
        // Match pattern like root_cluster_L1C03 and extract the number
        const secondLevelMatch = nodeName.match(/root_cluster_L1C(\d+)/);
        if (secondLevelMatch) {
            const clusterNum = parseInt(secondLevelMatch[1]);
            return `Cluster ${clusterNum + 1}`; // Add 1 since L1C00 should be Cluster 1
        }
        
        // Fallback for any other patterns
        return nodeName;
    }

    async init() {
        await this.loadStats();
        await this.loadTree();
        this.bindEvents();
        
        // Automatically load the "All Cells" (root) node on page load
        await this.selectNodeAndExpand('root');
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            document.getElementById('total-nodes').textContent = stats.total_nodes;
            document.getElementById('total-programs').textContent = stats.total_programs;
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    async loadTree() {
        try {
            const response = await fetch('/api/tree');
            const tree = await response.json();
            
            this.renderTree(tree);
            document.getElementById('tree-loading').style.display = 'none';
            document.getElementById('tree-content').style.display = 'block';
        } catch (error) {
            console.error('Failed to load tree:', error);
            document.getElementById('tree-loading').innerHTML = 'Failed to load tree structure.';
        }
    }

    renderTree(tree) {
        const container = document.getElementById('tree-content');
        container.appendChild(this.createTreeNode(tree, 0));
    }

    createTreeNode(node, level) {
        const hasChildren = node.children && node.children.length > 0;
        const isRoot = level === 0;
        
        const nodeElement = document.createElement('div');
        nodeElement.className = isRoot ? 'tree-node' : 'tree-child-container';
        
        const headerClass = isRoot ? 'tree-node-header' : 'tree-child-header';
        const iconClass = hasChildren ? 'fas fa-folder' : 'fas fa-file-alt';
        
        nodeElement.innerHTML = `
            <div class="${headerClass}" data-node="${node.name}" style="cursor: pointer;">
                ${hasChildren ? '<i class="fas fa-chevron-right tree-expand-icon"></i>' : '<i class="fas fa-chevron-right tree-leaf-icon"></i>'}
                <i class="${iconClass} tree-node-icon"></i>
                <span>${this.formatNodeName(node.name)}</span>
            </div>
            <div class="tree-node-content" id="tree-content-${node.name}" style="display: none;"></div>
        `;
        
        // Add direct click handler for debugging
        const header = nodeElement.querySelector(`.${headerClass}`);
        header.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectNodeAndExpand(node.name);
        });
        
        // Recursively add children
        if (hasChildren) {
            const childrenContainer = document.createElement('div');
            childrenContainer.className = 'tree-children';
            
            // Sort children numerically by cluster number
            const sortedChildren = [...node.children].sort((a, b) => {
                // Extract numbers from node names like root_c_1, root_c_10, etc.
                const aMatch = a.name.match(/root_c_(\d+)/);
                const bMatch = b.name.match(/root_c_(\d+)/);
                
                if (aMatch && bMatch) {
                    return parseInt(aMatch[1]) - parseInt(bMatch[1]);
                }
                
                // Fallback to alphabetical if pattern doesn't match
                return a.name.localeCompare(b.name);
            });
            
            sortedChildren.forEach(child => {
                childrenContainer.appendChild(this.createTreeNode(child, level + 1));
            });
            
            nodeElement.appendChild(childrenContainer);
        }
        return nodeElement;
    }

    bindEvents() {
        // Tree node clicks (fallback for global handling)
        document.addEventListener('click', (e) => {
            const nodeHeader = e.target.closest('.tree-node-header, .tree-child-header');
            if (nodeHeader) {
                const nodeName = nodeHeader.getAttribute('data-node');
                this.selectNodeAndExpand(nodeName);
                e.stopPropagation();
            }

            // Program header clicks
            const programHeader = e.target.closest('.program-header');
            if (programHeader) {
                const programCard = programHeader.closest('.program-card');
                this.toggleProgram(programCard);
            }

            // Section header clicks
            const sectionHeader = e.target.closest('.section-header');
            if (sectionHeader) {
                this.toggleSection(sectionHeader);
            }

            // Cluster dropdown header clicks
            const clusterHeader = e.target.closest('.cluster-dropdown-header');
            if (clusterHeader) {
                this.toggleClusterDropdown(clusterHeader);
                e.stopPropagation();
            }

            // Program label clicks (scroll to and expand program)
            const programLabel = e.target.closest('.clickable-program-label');
            if (programLabel) {
                const programName = programLabel.getAttribute('data-program');
                this.scrollToAndExpandProgram(programName);
                e.stopPropagation();
                return;
            }

            // Image container clicks (for modal) - includes both .image-container and .heatmap-item
            const imageContainer = e.target.closest('.image-container, .heatmap-item');
            if (imageContainer) {
                // Check if this is a dual UMAP (program activity + cell type)
                if (imageContainer.classList.contains('program-umap-dual')) {
                    const activityPath = imageContainer.dataset.umapActivityPath;
                    const cellTypePath = imageContainer.dataset.umapCellTypePath;
                    const title = imageContainer.dataset.imageTitle;
                    this.openDualUmapModal(activityPath, cellTypePath, title);
                }
                // Check if this is a cell type UMAP modal
                else if (imageContainer.classList.contains('cell-type-umap-modal')) {
                    const htmlPath = imageContainer.dataset.umapHtmlPath;
                    const title = imageContainer.dataset.imageTitle;
                    this.openSingleUmapModal(htmlPath, title);
                }
                // Check if this is a leiden UMAP modal
                else if (imageContainer.classList.contains('leiden-umap-modal')) {
                    const htmlPath = imageContainer.dataset.umapHtmlPath;
                    const title = imageContainer.dataset.imageTitle;
                    this.openSingleUmapModal(htmlPath, title);
                }
                // Check if this is a combined UMAP
                else if (imageContainer.classList.contains('combined-umap') && imageContainer.dataset.nodeName) {
                    this.openCombinedUmapModal(
                        imageContainer.dataset.nodeName,
                        imageContainer.dataset.imageTitle,
                        imageContainer.dataset.imageSubtitle
                    );
                } else if (imageContainer.dataset.imageSrc) {
                    // Check if this is a program activity UMAP that should show combined view
                    const subtitle = imageContainer.dataset.imageSubtitle;
                    if (subtitle === 'program_umap_activity') {
                        this.openProgramActivityUmapModal(
                            imageContainer.dataset.imageSrc,
                            imageContainer.dataset.imageTitle,
                            imageContainer.dataset.imageSubtitle
                        );
                    } else if (subtitle === 'program_umap_cell_type') {
                        this.openCellTypeUmapModal(
                            imageContainer.dataset.imageSrc,
                            imageContainer.dataset.imageTitle,
                            imageContainer.dataset.imageSubtitle
                        );
                    } else {
                        this.openImageModal(
                            imageContainer.dataset.imageSrc,
                            imageContainer.dataset.imageTitle,
                            imageContainer.dataset.imageSubtitle
                        );
                    }
                }
            }

            // Modal close clicks
            if (e.target.closest('.image-modal-close') || e.target.closest('.image-modal-backdrop')) {
                this.closeImageModal();
            }
        });

        // Keyboard events for modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeImageModal();
            }
        });
    }

    async toggleTreeNode(nodeName) {
        const nodeContentDiv = document.getElementById(`tree-content-${nodeName}`);
        const expandIcon = document.querySelector(`[data-node="${nodeName}"] .tree-expand-icon`);
        
        // Check if this node has an expand icon (i.e., has children)
        const hasExpandIcon = expandIcon !== null;
        
        if (nodeContentDiv.style.display === 'none') {
            // Expand: Update icon if it exists
            if (hasExpandIcon) {
                expandIcon.classList.remove('fa-chevron-right');
                expandIcon.classList.add('fa-chevron-down');
            }
            
            try {
                const response = await fetch(`/api/node/${nodeName}`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const nodeData = await response.json();
                nodeContentDiv.innerHTML = this.createTreeNodeSummary(nodeData);
                nodeContentDiv.style.display = 'block';
            } catch (error) {
                console.error('Failed to load node:', error);
                nodeContentDiv.innerHTML = '<div class="tree-error">Failed to load</div>';
                nodeContentDiv.style.display = 'block';
            }
        } else {
            // Collapse: Update icon if it exists
            if (hasExpandIcon) {
                expandIcon.classList.remove('fa-chevron-down');
                expandIcon.classList.add('fa-chevron-right');
            }
            nodeContentDiv.style.display = 'none';
        }
    }
    
    createTreeNodeSummary(nodeData) {
        const programCount = Object.keys(nodeData.programs).length;
        const nodeInfo = nodeData.node_info || {};
        const cellCount = nodeInfo.cells?.number || 'N/A';
        const geneCount = nodeInfo.genes?.number || 'N/A';
        
        return `
            <div class="tree-node-summary">
                <div class="tree-summary-item">
                    <i class="fas fa-microscope"></i>
                    <span>${typeof cellCount === 'number' ? cellCount.toLocaleString() : cellCount} cells</span>
                </div>
                <div class="tree-summary-item">
                    <i class="fas fa-code-branch"></i>
                    <span>${typeof geneCount === 'number' ? geneCount.toLocaleString() : geneCount} genes</span>
                </div>
                <div class="tree-summary-item">
                    <i class="fas fa-dna"></i>
                    <span>${programCount} programs</span>
                </div>
            </div>
        `;
    }

    async selectNodeAndExpand(nodeName) {
        // Collapse all other node overviews first
        document.querySelectorAll('.tree-node-content').forEach(content => {
            if (content.id !== `tree-content-${nodeName}`) {
                content.style.display = 'none';
                // Also update the chevron icons
                const header = content.previousElementSibling;
                if (header) {
                    const chevron = header.querySelector('.tree-expand-icon');
                    if (chevron) {
                        chevron.classList.remove('fa-chevron-down');
                        chevron.classList.add('fa-chevron-right');
                    }
                }
            }
        });
        
        // Reset all leaf node chevrons to point right
        document.querySelectorAll('.tree-leaf-icon').forEach(leafIcon => {
            leafIcon.classList.remove('fa-chevron-down');
            leafIcon.classList.add('fa-chevron-right');
        });
        
        // Then expand/toggle the current node's sidebar
        await this.toggleTreeNode(nodeName);
        
        // Finally navigate to main content
        await this.selectNodeForMainContent(nodeName);
    }

    async selectNodeForMainContent(nodeName, nodeData = null) {
        // Update active state
        document.querySelectorAll('.tree-node-header, .tree-child-header').forEach(el => {
            el.classList.remove('active');
        });
        const activeHeader = document.querySelector(`[data-node="${nodeName}"]`);
        if (activeHeader) {
            activeHeader.classList.add('active');
            
            // Update leaf node chevron to point down if this is a leaf node
            const leafIcon = activeHeader.querySelector('.tree-leaf-icon');
            if (leafIcon) {
                leafIcon.classList.remove('fa-chevron-right');
                leafIcon.classList.add('fa-chevron-down');
            }
        }

        // Show loading if we don't have data yet
        if (!nodeData) {
            this.showNodeLoading();
            
            try {
                const response = await fetch(`/api/node/${nodeName}`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                nodeData = await response.json();
            } catch (error) {
                console.error('Failed to load node:', error);
                this.showError('Failed to load node data.');
                return;
            }
        }
        
        this.currentNode = nodeName;
        this.renderNodeContent(nodeData);
    }

    showNodeLoading() {
        document.getElementById('welcome-screen').style.display = 'none';
        document.getElementById('node-content').style.display = 'block';
        document.getElementById('programs-loading').style.display = 'block';
        document.getElementById('programs-container').innerHTML = '';
    }

    async renderNodeContent(nodeData) {
        document.getElementById('node-title').textContent = this.formatNodeName(nodeData.node_name);
        document.getElementById('node-meta').textContent = '';
        
        // Store node info for use in other methods
        this.currentNodeInfo = nodeData.node_info;
        
        document.getElementById('programs-loading').style.display = 'none';
        
        // Render node info section if available
        const nodeInfoContainer = document.getElementById('node-info-container');
        if (nodeData.node_info && Object.keys(nodeData.node_info).length > 0) {
            nodeInfoContainer.innerHTML = this.createNodeInfoSection(nodeData.node_info);
            nodeInfoContainer.style.display = 'block';
        } else {
            nodeInfoContainer.style.display = 'none';
        }
        
        // Load and render node summary if available (this will update the node info section)
        await this.loadNodeSummary(nodeData.node_name, nodeData);
        
        // Load and render cell clusters section
        await this.loadCellClusters(nodeData.node_name);
        
        const container = document.getElementById('programs-container');
        container.innerHTML = '';
        
        // Sort programs numerically by program number
        const sortedPrograms = Object.entries(nodeData.programs).sort(([a], [b]) => {
            const numA = parseInt(a.replace('program_', ''));
            const numB = parseInt(b.replace('program_', ''));
            return numA - numB;
        });
        
        sortedPrograms.forEach(([programName, programData]) => {
            const programCard = this.createProgramCard(programName, programData);
            container.appendChild(programCard);
        });
    }

    createProgramCard(programName, programData) {
        const card = document.createElement('div');
        card.className = 'program-card';
        card.setAttribute('data-program', programName);
        
        // Convert program_X to "Program X+1" (1-based indexing for display)
        const programNumber0Based = parseInt(programName.replace('program_', ''));
        const programNumber1Based = programNumber0Based + 1;
        const displayName = `Program ${programNumber1Based}`;
        
        // Get program label from node summary if available (labels use 0-based keys)
        const programNumber = programName.replace('program_', '');
        let programLabel = '';
        if (this.currentNodeSummary && this.currentNodeSummary.program_labels) {
            const label = this.currentNodeSummary.program_labels[programNumber];
            if (label) {
                programLabel = `: ${label}`;
            }
        }
        
        card.innerHTML = `
            <div class="program-header">
                <div class="program-title">
                    <div class="program-header-content">
                        <div class="program-name-row">
                            <span class="program-name">${displayName} (${programData.total_genes} genes)${programLabel}</span>
                            <div class="program-stats">
                                <span class="program-stat">
                                    <i class="fas fa-chevron-right expand-icon"></i>
                                </span>
                            </div>
                        </div>
                        ${programData.summary ? `<div class="program-summary">${programData.summary}</div>` : ''}
                    </div>
                </div>
            </div>
            <div class="program-content">
                ${this.createProgramSections(programName, programData)}
            </div>
        `;
        
        return card;
    }

    createProgramSections(programName, programData) {
        let sections = '';
        
        // Evidence section (description content)
        if (programData.has_description) {
            sections += `
                <div class="program-section">
                    <div class="section-header" data-section="description" data-program="${programName}">
                        <span class="section-title">
                            <i class="fas fa-file-alt"></i>
                            Evidence
                        </span>
                        <i class="fas fa-chevron-right expand-icon"></i>
                    </div>
                    <div class="section-content" data-section="description">
                        <div class="loading">
                            <i class="fas fa-spinner"></i>
                            Loading evidence...
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Visualizations section (includes all images)
        sections += `
            <div class="program-section">
                <div class="section-header" data-section="images" data-program="${programName}">
                    <span class="section-title">
                        <i class="fas fa-images"></i>
                        Visualizations
                    </span>
                    <i class="fas fa-chevron-right expand-icon"></i>
                </div>
                <div class="section-content" data-section="images">
                    ${this.createProgramVisualizations(programData)}
                </div>
            </div>
        `;
        
        // Genes section
        if (programData.has_genes) {
            sections += `
                <div class="program-section">
                    <div class="section-header" data-section="genes" data-program="${programName}">
                        <span class="section-title">
                            <i class="fas fa-dna"></i>
                            Genes (${programData.total_genes})
                        </span>
                        <i class="fas fa-chevron-right expand-icon"></i>
                    </div>
                    <div class="section-content" data-section="genes">
                        <div class="loading">
                            <i class="fas fa-spinner"></i>
                            Loading genes...
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Loadings section
        if (programData.has_loadings) {
            sections += `
                <div class="program-section">
                    <div class="section-header" data-section="loadings" data-program="${programName}">
                        <span class="section-title">
                            <i class="fas fa-chart-bar"></i>
                            Loadings
                        </span>
                        <i class="fas fa-chevron-right expand-icon"></i>
                    </div>
                    <div class="section-content" data-section="loadings">
                        <div class="loading">
                            <i class="fas fa-spinner"></i>
                            Loading loadings...
                        </div>
                    </div>
                </div>
            `;
        }
        
        return sections;
    }

    createProgramVisualizations(programData) {
        let content = '';
        
        // Add per-program heatmaps section if available
        if (programData.heatmaps && Object.keys(programData.heatmaps).length > 0) {
            content += `
                <div class="program-heatmaps-section" style="margin-bottom: 2rem;">
                    <div class="heatmap-row" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(525px, 1fr)); gap: 1.5rem; justify-items: center;">
            `;
            
            // Define heatmap order and titles
            const heatmapConfig = {
                'cell_type_by_program_activity': 'Cell Type Activity',
                'leiden_cluster_by_program_activity': 'Leiden Cluster Activity'
            };
            
            // NEW: Handle combined HTML breakdown (cell type + leiden in one file) - lazy-loaded
            if (programData.heatmaps['cell_type_by_program_activity']) {
                const breakdownPath = programData.heatmaps['cell_type_by_program_activity'];
                const isHtmlFile = breakdownPath && (breakdownPath.endsWith('.html') || breakdownPath.includes('/api/node-summary-html/'));
                
                if (isHtmlFile) {
                    content += `
                        <div style="width: 100%; max-width: 900px; margin: 0 auto; position: relative; min-height: 650px;">
                            <iframe data-src="${breakdownPath}" 
                                    style="width:100%; height:650px; border:none; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1);"
                                    onerror="this.parentElement.innerHTML='<div style=&quot;text-align:center;padding:2rem;&quot;>No breakdown found</div>'">
                            </iframe>
                            <div class="image-loading" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">
                                <i class="fas fa-spinner fa-pulse"></i> Loading...
                            </div>
                        </div>
                    `;
                } else {
                    // Handle PNG breakdown
                    content += `
                        <div class="image-container" 
                             data-image-src="${breakdownPath}" 
                             data-image-title="Program Breakdown" 
                             data-image-subtitle="Activity by Cell Type and Leiden Cluster"
                             style="width: 100%; max-width: 900px; margin: 0 auto; cursor: pointer;">
                            <img src="${breakdownPath}" alt="Program Breakdown" 
                                 style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
                                 onerror="this.parentElement.innerHTML='<div style=&quot;text-align:center;padding:2rem;color:#999;&quot;>No breakdown found</div>'">
                        </div>
                    `;
                }
            }
            
            content += `
                    </div>
                </div>
            `;
        }
        
        // Add UMAP section
        content += this.createImagesGrid(programData.images);
        
        return content;
    }

    createImagesGrid(images, imageMapping = null, context = null) {
        const defaultImageTypes = {
            'program_umap_leiden': 'Program UMAP',
            'program_umap_activity': 'Program UMAP - Activity', 
            'program_umap_cell_type': 'UMAP - Cell Type'
        };
        
        // Use provided imageMapping or default
        const imageTypes = imageMapping || defaultImageTypes;
        
        let grid = '<div class="images-grid">';
        
        Object.entries(images).forEach(([key, path]) => {
            // Only show program_umap_activity, skip the other UMAP types (they'll be in the modal)
            if (key === 'program_umap_leiden' || key === 'program_umap_cell_type') {
                return; // Skip these, they'll be shown in the modal
            }
            
            // If imageMapping is provided, only show images that are in the mapping
            if (imageMapping && !imageMapping.hasOwnProperty(key)) {
                return; // Skip this image
            }
            
            if (path) {
                const title = imageTypes[key] || key;
                
                // Handle combined UMAP comparison
                if (key === 'combined_umap_comparison') {
                    const nodeName = this.currentNode;
                    
                    // Check if path is already an API endpoint or needs processing
                    let thumbnailPath;
                    if (path.startsWith('/api/')) {
                        // Already an API path, just add compression parameters
                        thumbnailPath = `${path}?compress=true&quality=75&max_width=400`;
                    } else {
                        // Regular asset path, process normally
                        thumbnailPath = path ? `/api/images/${path.replace('/mnt/vdd/hca_lung_atlas_tree/test_setup/assets/', '')}?compress=true&quality=75&max_width=400` : '';
                    }
                    
                    grid += `
                        <div class="image-item">
                            <div class="image-header">
                                <div class="image-title">${title}</div>
                                <div class="image-subtitle">${key}</div>
                            </div>
                            <div class="image-container combined-umap" data-node-name="${nodeName}" data-image-title="${title}" data-image-subtitle="${key}">
                                <img src="${thumbnailPath}" alt="${title}" loading="lazy" 
                                     onerror="this.parentElement.innerHTML='<div class=&quot;image-loading&quot;>Image not available</div>'"
                                     onload="this.style.opacity=1" style="opacity:0;transition:opacity 0.3s;cursor:pointer">
                                <div class="combined-badge">
                                    <i class="fas fa-columns"></i>
                                    Comparison
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    // NEW: Handle HTML files (Plotly outputs) with iframes
                    const isHtmlFile = path && (path.endsWith('.html') || path.includes('/api/node-summary-html/'));
                    
                    if (isHtmlFile) {
                        // Render HTML file in iframe (lazy-loaded)
                        const badge = `
                            <div class="combined-badge">
                                <i class="fas fa-mouse-pointer"></i>
                                Interactive
                            </div>
                        `;
                        
                        grid += `
                            <div class="image-item">
                                <div class="image-header">
                                    <div class="image-title">${title}</div>
                                    <div class="image-subtitle">${key}</div>
                                </div>
                                <div class="image-container iframe-container" style="position: relative; min-height: 400px;">
                                    <iframe data-src="${path}" 
                                            style="width:100%; height:400px; border:none; opacity:0; transition:opacity 0.3s;"
                                            onload="this.style.opacity=1"
                                            onerror="this.parentElement.innerHTML='<div class=&quot;image-loading&quot;>No image found</div>'">
                                    </iframe>
                                    <div class="image-loading" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">
                                        <i class="fas fa-spinner fa-pulse"></i> Click to load...
                                    </div>
                                    ${badge}
                                </div>
                            </div>
                        `;
                    } else {
                        // Handle PNG files
                        // Special handling for program_umap_activity - show modal with both HTML UMAPs
                        if (key === 'program_umap_activity') {
                            grid += `
                                <div class="image-item" style="max-width: 455px; margin: 0 auto;">
                                    <div class="image-header">
                                        <div class="image-title">${title}</div>
                                        <div class="image-subtitle">Click to view interactive UMAPs</div>
                                    </div>
                                    <div class="image-container program-umap-dual" 
                                         data-umap-activity-path="${path}"
                                         data-umap-cell-type-path="${images['program_umap_cell_type'] || ''}"
                                         data-image-title="${title}"
                                         style="cursor: pointer;">
                                        <img src="${path}" alt="${title}" loading="lazy" 
                                             style="max-width: 100%; height: auto; border-radius: 8px;"
                                             onerror="this.parentElement.innerHTML='<div class=&quot;image-loading&quot;>Image not found</div>'">
                                        <div class="combined-badge" style="font-size: 11px; padding: 4px 8px; gap: 4px;">
                                            <i class="fas fa-expand-arrows-alt" style="font-size: 10px;"></i>
                                            View Interactive
                                        </div>
                                    </div>
                                </div>
                            `;
                        } else {
                            grid += `
                                <div class="image-item">
                                    <div class="image-header">
                                        <div class="image-title">${title}</div>
                                        <div class="image-subtitle">${key}</div>
                                    </div>
                                    <div class="image-container" 
                                         data-image-src="${path}" 
                                         data-image-title="${title}" 
                                         data-image-subtitle="${key}"
                                         style="cursor: pointer;">
                                        <img src="${path}" alt="${title}" loading="lazy" 
                                             style="max-width: 100%; height: auto; border-radius: 8px;"
                                             onerror="this.parentElement.innerHTML='<div class=&quot;image-loading&quot;>Image not found</div>'">
                                    </div>
                                </div>
                            `;
                        }
                    }
                }
            }
        });
        
        grid += '</div>';
        return grid;
    }

    toggleProgram(programCard) {
        const content = programCard.querySelector('.program-content');
        const icon = programCard.querySelector('.expand-icon');
        
        if (content.classList.contains('expanded')) {
            content.classList.remove('expanded');
            icon.classList.remove('expanded');
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-right');
        } else {
            content.classList.add('expanded');
            icon.classList.add('expanded');
            icon.classList.remove('fa-chevron-right');
            icon.classList.add('fa-chevron-down');
            // Lazy-load iframes when expanding
            this.loadIframesInElement(content);
        }
    }

    toggleClusterDropdown(clusterHeader) {
        const dropdownItem = clusterHeader.closest('.cluster-dropdown-item');
        const content = dropdownItem.querySelector('.cluster-dropdown-content');
        const icon = clusterHeader.querySelector('.cluster-expand-icon');
        
        if (content.style.display === 'none') {
            // Open dropdown
            content.style.display = 'block';
            icon.classList.remove('fa-chevron-right');
            icon.classList.add('fa-chevron-down');
        } else {
            // Close dropdown
            content.style.display = 'none';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-right');
        }
    }
    
    loadIframesInElement(element) {
        // Find all iframes with data-src attribute (not yet loaded)
        const lazyIframes = element.querySelectorAll('iframe[data-src]:not([src])');
        lazyIframes.forEach(iframe => {
            iframe.src = iframe.dataset.src;
            // Optional: add a loaded class for styling
            iframe.classList.add('iframe-loaded');
        });
    }

    scrollToAndExpandProgram(programName) {
        // Find the program card specifically (not the program label)
        const programCard = document.querySelector(`.program-card[data-program="${programName}"]`);
        
        if (!programCard) {
            console.warn(`Program card not found: ${programName}`);
            return;
        }

        // Expand the program if it's not already expanded
        const content = programCard.querySelector('.program-content');
        const icon = programCard.querySelector('.expand-icon');
        
        if (!content.classList.contains('expanded')) {
            content.classList.add('expanded');
            icon.classList.add('expanded');
        }

        // Scroll to the program card with smooth animation
        programCard.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
            inline: 'nearest'
        });

        // Add a brief highlight effect
        programCard.style.transition = 'box-shadow 0.3s ease';
        programCard.style.boxShadow = '0 0 20px rgba(59, 130, 246, 0.5)';
        
        setTimeout(() => {
            programCard.style.boxShadow = '';
        }, 2000);
    }

    async toggleSection(sectionHeader) {
        const section = sectionHeader.getAttribute('data-section');
        const programName = sectionHeader.getAttribute('data-program');
        const content = sectionHeader.nextElementSibling;
        const icon = sectionHeader.querySelector('.expand-icon');
        
        // Handle both CSS class-based and inline style-based sections
        const isExpanded = content.classList.contains('expanded') || content.style.display !== 'none';
        
        if (isExpanded) {
            // Collapse section
            content.classList.remove('expanded');
            icon.classList.remove('expanded');
            content.style.display = 'none';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-right');
            return;
        }
        
        // Expand section
        content.classList.add('expanded');
        icon.classList.add('expanded');
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-right');
        icon.classList.add('fa-chevron-down');
        
        // Load data if not already loaded
        const cacheKey = `${this.currentNode}-${programName}-${section}`;
        if (!this.loadedData.has(cacheKey)) {
            await this.loadSectionData(section, programName, content);
        }
    }

    async loadSectionData(section, programName, contentElement) {
        const cacheKey = `${this.currentNode}-${programName}-${section}`;
        
        try {
            let response;
            switch (section) {
                case 'description':
                    response = await fetch(`/api/program/${this.currentNode}/${programName}/description`);
                    break;
                case 'genes':
                    response = await fetch(`/api/program/${this.currentNode}/${programName}/genes`);
                    break;
                case 'loadings':
                    response = await fetch(`/api/program/${this.currentNode}/${programName}/loadings`);
                    break;
                default:
                    return;
            }
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.loadedData.set(cacheKey, data);
            this.renderSectionData(section, data, contentElement);
            
        } catch (error) {
            console.error(`Failed to load ${section}:`, error);
            contentElement.innerHTML = `<div class="error">Failed to load ${section} data.</div>`;
        }
    }

    renderSectionData(section, data, contentElement) {
        switch (section) {
            case 'description':
                const formattedDescription = this.formatDescription(data.description || 'No description available.');
                contentElement.innerHTML = `
                    <div class="description-content">
                        ${formattedDescription}
                    </div>
                `;
                break;
                
            case 'genes':
                const genesHtml = data.genes.map(gene => 
                    `<span class="gene-tag">${gene}</span>`
                ).join('');
                
                contentElement.innerHTML = `
                    <div class="genes-header">
                        <span class="genes-count">Total genes: ${data.total_genes}</span>
                    </div>
                    <div class="genes-container">
                        ${genesHtml}
                    </div>
                `;
                break;
                
            case 'loadings':
                if (data.loadings && Object.keys(data.loadings).length > 0) {
                    // Sort loadings by value (descending)
                    const sortedLoadings = Object.entries(data.loadings)
                        .map(([gene, loading]) => [gene, Number(loading)])
                        .sort((a, b) => b[1] - a[1]); // Sort by loading value descending
                    
                    const totalLoadings = sortedLoadings.length;
                    let displayLoadings = [];
                    let showingText = '';
                    
                    if (totalLoadings <= 40) {
                        // Show all if 40 or fewer
                        displayLoadings = sortedLoadings;
                        showingText = `Showing all ${totalLoadings} loadings (sorted by value)`;
                    } else {
                        // Show top 20 and bottom 20
                        const top20 = sortedLoadings.slice(0, 20);
                        const bottom20 = sortedLoadings.slice(-20);
                        displayLoadings = [...top20, ...bottom20];
                        showingText = `Showing top 20 and bottom 20 loadings (${totalLoadings} total)`;
                    }
                    
                    const loadingsRows = displayLoadings.map(([gene, loading], index) => {
                        // Add separator row between top 20 and bottom 20
                        const needsSeparator = totalLoadings > 40 && index === 20;
                        const separatorRow = needsSeparator ? 
                            '<tr class="loadings-separator"><td colspan="2" style="text-align: center; font-style: italic; background: #f8f9fa; color: var(--text-secondary);">... middle values omitted ...</td></tr>' : '';
                        
                        const rowClass = totalLoadings > 40 ? (index < 20 ? 'loading-positive' : 'loading-negative') : '';
                        const loadingValue = loading.toFixed(4);
                        const loadingDisplay = loading >= 0 ? `+${loadingValue}` : loadingValue;
                        
                        return separatorRow + `<tr class="${rowClass}"><td>${gene}</td><td style="font-weight: 500;">${loadingDisplay}</td></tr>`;
                    }).join('');
                    
                    contentElement.innerHTML = `
                        <div style="margin-bottom: 1rem;">
                            <p style="color: var(--text-secondary); font-size: 0.9rem;">${showingText}</p>
                        </div>
                        <table class="loadings-table">
                            <thead>
                                <tr>
                                    <th>Gene</th>
                                    <th>Loading Value</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${loadingsRows}
                            </tbody>
                        </table>
                    `;
                } else {
                    contentElement.innerHTML = '<div>No loadings data available.</div>';
                }
                break;
        }
    }

    formatDescription(description) {
        if (!description || description === 'No description available.') {
            return description;
        }
        
        // Remove the summary part (everything before "Evidence:") since it's now in the header
        let formatted = description;
        const evidenceSplit = description.split('Evidence:');
        if (evidenceSplit.length > 1) {
            // Start with "Evidence:" and everything after
            formatted = 'Evidence:' + evidenceSplit[1];
        }
        
        // Format the content
        formatted = formatted
            // Format bullet points (• symbol) first
            .replace(/\s*•\s*/g, '<br>• ')
            // Clean up multiple spaces
            .replace(/\s+/g, ' ')
            // Trim whitespace
            .trim();
        
        // Now handle section headers with consistent formatting
        // Make sure "Evidence:" at the start is properly formatted
        if (formatted.startsWith('Evidence:')) {
            formatted = '<strong>Evidence:</strong>' + formatted.substring(9);
        }
        
        // Handle "Inconsistencies:" section
        formatted = formatted.replace(/\s+(Inconsistencies:)/g, '<br><br><strong>$1</strong>');
        
        return formatted;
    }

    openImageModal(imageSrc, title, subtitle) {
        const modal = document.getElementById('image-modal');
        const modalImg = document.getElementById('image-modal-img');
        const modalTitle = document.getElementById('image-modal-title');
        const modalSubtitle = document.getElementById('image-modal-subtitle');
        const modalBody = modal.querySelector('.image-modal-body');
        
        // Reset modal body to show image
        modalBody.innerHTML = `<img id="image-modal-img" src="${imageSrc}" alt="${title}" />`;
        modalTitle.textContent = title;
        modalSubtitle.textContent = subtitle;
        
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }

    openDualUmapModal(activityPngPath, cellTypePngPath, title) {
        const modal = document.getElementById('image-modal');
        const modalTitle = document.getElementById('image-modal-title');
        const modalSubtitle = document.getElementById('image-modal-subtitle');
        const modalBody = modal.querySelector('.image-modal-body');
        
        // Add class for combined content
        modalBody.classList.add('combined-content');
        
        // Convert PNG paths to HTML paths
        const activityHtmlPath = activityPngPath.replace('.png', '.html');
        const cellTypeHtmlPath = cellTypePngPath.replace('.png', '.html');
        
        // Create side-by-side layout with both HTML iframes - much larger sizing with proper scaling
        modalBody.innerHTML = `
            <div class="combined-umap-container" style="display: flex; gap: 20px; width: 100%; height: 80vh; max-width: 1800px; margin: 0 auto;">
                <div class="umap-panel" style="flex: 1; display: flex; flex-direction: column; min-width: 0;">
                    <h4 style="margin: 0 0 10px 0; text-align: center; font-size: 16px;">Program Activity</h4>
                    <div style="width: 100%; height: 100%; overflow: hidden; border-radius: 8px; background: white;">
                        <iframe 
                            src="${activityHtmlPath}" 
                            style="width: 100%; height: 100%; border: none; transform: scale(0.85); transform-origin: top left; width: 117.65%; height: 117.65%;"
                            title="Program Activity UMAP">
                        </iframe>
                    </div>
                </div>
                <div class="umap-panel" style="flex: 1; display: flex; flex-direction: column; min-width: 0;">
                    <h4 style="margin: 0 0 10px 0; text-align: center; font-size: 16px;">Cell Types</h4>
                    <div style="width: 100%; height: 100%; overflow: hidden; border-radius: 8px; background: white;">
                        <iframe 
                            src="${cellTypeHtmlPath}" 
                            style="width: 100%; height: 100%; border: none; transform: scale(0.85); transform-origin: top left; width: 117.65%; height: 117.65%;"
                            title="Cell Type UMAP">
                        </iframe>
                    </div>
                </div>
            </div>
        `;
        
        modalTitle.textContent = title;
        modalSubtitle.textContent = 'Interactive UMAPs';
        
        // Make the modal content container larger
        const modalContent = modal.querySelector('.image-modal-content');
        if (modalContent) {
            modalContent.style.width = '95vw';
            modalContent.style.maxWidth = '95vw';
            modalContent.style.height = '95vh';
        }
        
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    openSingleUmapModal(htmlPath, title) {
        const modal = document.getElementById('image-modal');
        const modalTitle = document.getElementById('image-modal-title');
        const modalSubtitle = document.getElementById('image-modal-subtitle');
        const modalBody = modal.querySelector('.image-modal-body');
        
        // Add class for combined content
        modalBody.classList.add('combined-content');
        
        // Create single UMAP with proper scaling
        modalBody.innerHTML = `
            <div style="width: 100%; height: 80vh; max-width: 900px; margin: 0 auto; display: flex; flex-direction: column;">
                <div style="width: 100%; height: 100%; overflow: hidden; border-radius: 8px; background: white;">
                    <iframe 
                        src="${htmlPath}" 
                        style="width: 117.65%; height: 117.65%; border: none; transform: scale(0.85); transform-origin: top left;"
                        title="${title}">
                    </iframe>
                </div>
            </div>
        `;
        
        modalTitle.textContent = title;
        modalSubtitle.textContent = 'Interactive UMAP';
        
        // Make the modal content container larger
        const modalContent = modal.querySelector('.image-modal-content');
        if (modalContent) {
            modalContent.style.width = '95vw';
            modalContent.style.maxWidth = '95vw';
            modalContent.style.height = '95vh';
        }
        
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    openCombinedUmapModal(nodeName, title, subtitle) {
        const modal = document.getElementById('image-modal');
        const modalTitle = document.getElementById('image-modal-title');
        const modalSubtitle = document.getElementById('image-modal-subtitle');
        const modalBody = modal.querySelector('.image-modal-body');
        
        // Add class for combined content
        modalBody.classList.add('combined-content');
        
        // Get paths for both UMAPs from current node info
        const overviewFigures = this.currentNodeInfo?.overview_figures || {};
        const leidenUmapPath = overviewFigures['program_umap_leiden'];
        const interactivePath = `/api/interactive-plot/${nodeName}/umap_cell_type`;
        
        const leidenImageSrc = leidenUmapPath ? 
            `/api/images/${leidenUmapPath.replace('/mnt/vdd/hca_lung_atlas_tree/test_setup/assets/', '')}?compress=true&quality=85&max_width=800` : '';
        
        // Create side-by-side layout
        modalBody.innerHTML = `
            <div class="combined-umap-container">
                <div class="umap-panel">
                    <h4>Leiden Clusters</h4>
                    <img src="${leidenImageSrc}" alt="UMAP - Leiden Clusters" style="max-width: 100%; height: auto; border-radius: 8px;" />
                </div>
                <div class="umap-panel">
                    <h4>Cell Types (Interactive)</h4>
                    <iframe 
                        src="${interactivePath}" 
                        style="width: 100%; height: 70vh; border: none; border-radius: 8px;"
                        title="Interactive UMAP - Cell Types">
                    </iframe>
                </div>
            </div>
        `;
        
        modalTitle.textContent = title;
        modalSubtitle.textContent = subtitle + ' (Combined View)';
        
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    openProgramActivityUmapModal(imageSrc, title, subtitle) {
        const modal = document.getElementById('image-modal');
        const modalTitle = document.getElementById('image-modal-title');
        const modalSubtitle = document.getElementById('image-modal-subtitle');
        const modalBody = modal.querySelector('.image-modal-body');
        
        // Add class for combined content
        modalBody.classList.add('combined-content');
        
        // Get interactive path for current node
        const nodeName = this.currentNode;
        const interactivePath = `/api/interactive-plot/${nodeName}/umap_cell_type`;
        
        // Create side-by-side layout with program activity on left, interactive on right
        modalBody.innerHTML = `
            <div class="combined-umap-container">
                <div class="umap-panel">
                    <h4>Program Activity</h4>
                    <img src="${imageSrc}" alt="Program UMAP - Activity" style="max-width: 100%; height: auto; border-radius: 8px;" />
                </div>
                <div class="umap-panel">
                    <h4>Cell Types (Interactive)</h4>
                    <iframe 
                        src="${interactivePath}" 
                        style="width: 100%; height: 70vh; border: none; border-radius: 8px;"
                        title="Interactive UMAP - Cell Types">
                    </iframe>
                </div>
            </div>
        `;
        
        modalTitle.textContent = title;
        modalSubtitle.textContent = subtitle + ' (with Interactive Cell Types)';
        
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    openCellTypeUmapModal(imageSrc, title, subtitle) {
        const modal = document.getElementById('image-modal');
        const modalTitle = document.getElementById('image-modal-title');
        const modalSubtitle = document.getElementById('image-modal-subtitle');
        const modalBody = modal.querySelector('.image-modal-body');
        
        // Remove any previous classes
        modalBody.classList.remove('combined-content');
        
        // Get interactive path for current node
        const nodeName = this.currentNode;
        const interactivePath = `/api/interactive-plot/${nodeName}/umap_cell_type`;
        
        // Show just the interactive cell type UMAP
        modalBody.innerHTML = `
            <div style="width: 100%; height: 80vh; display: flex; justify-content: center; align-items: center;">
                <iframe 
                    src="${interactivePath}" 
                    style="width: 100%; height: 100%; border: none; border-radius: 8px;"
                    title="Interactive UMAP - Cell Types">
                </iframe>
            </div>
        `;
        
        modalTitle.textContent = title + ' (Interactive)';
        modalSubtitle.textContent = subtitle;
        
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    closeImageModal() {
        const modal = document.getElementById('image-modal');
        const modalBody = modal.querySelector('.image-modal-body');
        const modalContent = modal.querySelector('.image-modal-content');
        
        modal.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling
        
        // Clean up any iframes when closing
        const iframe = modalBody.querySelector('iframe');
        if (iframe) {
            // Reset to default image structure
            modalBody.innerHTML = `<img id="image-modal-img" src="" alt="" />`;
        }
        
        // Reset modal content sizing to default
        if (modalContent) {
            modalContent.style.width = '';
            modalContent.style.maxWidth = '';
            modalContent.style.height = '';
        }
        
        // Remove interactive and combined content classes
        modalBody.classList.remove('interactive-content');
        modalBody.classList.remove('combined-content');
    }

    createNodeInfoSection(nodeInfo) {
        const projectName = nodeInfo.project_name || 'Node Information';
        const cells = nodeInfo.cells || {};
        const genes = nodeInfo.genes || {};
        const programsSummary = nodeInfo.programs_summary || {};
        const overviewFigures = nodeInfo.overview_figures || {};
        
        return `
            <div class="program-card node-info-card">
                <div class="program-header">
                    <div class="program-header-content">
                        <div class="program-name-row">
                            <h3 class="program-name">
                                <i class="fas fa-info-circle" style="margin-right: 0.5rem;"></i>
                                Node Overview
                            </h3>
                            <div class="program-stats">
                            </div>
                        </div>
                        <div class="program-summary">${this.createDataOverviewInline(nodeInfo)}</div>
                    </div>
                    <i class="fas fa-chevron-down expand-icon expanded"></i>
                </div>
                <div class="program-content expanded">
                    ${this.currentNodeSummary ? this.createNodeSummaryContent(this.currentNodeSummary) : ''}
                    ${this.createRemainingNodeInfoSections(nodeInfo)}
                </div>
            </div>
        `;
    }

    createDataOverviewInline(nodeInfo) {
        // Use the full data overview content for the inline display
        return this.createNodeDataOverview(nodeInfo) || 'Cellular Programs Analysis';
    }

    createDataOverviewFirst(nodeInfo) {
        // Extract and show only the Data Overview section first
        const dataOverview = this.createNodeDataOverview(nodeInfo);
        if (dataOverview) {
            return `
                <div class="section">
                    <div class="section-header">
                        <h4>Data Overview</h4>
                        <i class="fas fa-chevron-right expand-icon"></i>
                    </div>
                    <div class="section-content">
                        ${dataOverview}
                    </div>
                </div>
            `;
        }
        return '';
    }

    createRemainingNodeInfoSections(nodeInfo) {
        // Program Activity Plots section removed - no longer needed
        return '';
    }

    createNodeSummaryContent(summaryData) {
        const figures = summaryData.figures || {};
        const programLabels = summaryData.program_labels || {};
        const programGeneCounts = summaryData.program_gene_counts || {};
        
        let content = '';
        
        // Add summary heatmaps first, in the specified order, without dropdown
        if (Object.keys(figures).length > 0) {
            content += `<div class="summary-heatmaps-section" style="margin: 2rem 0;">`;
            content += `<h4 style="text-align: center; margin-bottom: 1.5rem;">Summary Heatmaps</h4>`;
            content += `<div class="heatmap-display-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 2rem; justify-items: center;">`;
            
            // Define the desired order of heatmaps
            const heatmapOrder = [
                'cluster_by_cell_type_heatmap',
                'cell_type_by_program_activity_heatmap',
                'heatmap_celltype_leiden_composition',
                'leiden_cluster_by_program_activity_heatmap'
            ];
            
            heatmapOrder.forEach(figureName => {
                if (figures[figureName]) {
                    const displayName = figureName
                        .replace(/_/g, ' ')
                        .replace(/\b\w/g, l => l.toUpperCase());
                    
                    const htmlPath = figures[figureName];
                    const isHtmlFile = htmlPath && (htmlPath.endsWith('.html') || htmlPath.includes('/api/node-summary-html/'));
                    
                    if (isHtmlFile) {
                        // Render as iframe for HTML files (lazy-loaded - Node Overview is expanded by default)
                        content += `
                            <div class="heatmap-display-item" style="max-width: 650px; width: 100%;">
                                <div class="image-header" style="text-align: center; margin-bottom: 1rem;">
                                    <div class="image-title">${displayName}</div>
                                    <div class="image-subtitle">Node Summary</div>
                                </div>
                                <div style="display: flex; justify-content: center; position: relative; min-height: 550px;">
                                    <iframe data-src="${htmlPath}" 
                                            style="width:100%; height:550px; border:none; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1);"
                                            onerror="this.parentElement.innerHTML='<div style=&quot;text-align:center;padding:2rem;&quot;>No image found</div>'">
                                    </iframe>
                                    <div class="image-loading" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">
                                        <i class="fas fa-spinner fa-pulse"></i> Loading...
                                    </div>
                                </div>
                            </div>
                        `;
                    } else {
                        // Handle PNG files
                        content += `
                            <div class="heatmap-display-item" style="max-width: 650px; width: 100%;">
                                <div class="image-header" style="text-align: center; margin-bottom: 1rem;">
                                    <div class="image-title">${displayName}</div>
                                    <div class="image-subtitle">Node Summary</div>
                                </div>
                                <div class="image-container" 
                                     data-image-src="${htmlPath}" 
                                     data-image-title="${displayName}" 
                                     data-image-subtitle="Node Summary"
                                     style="display: flex; justify-content: center; cursor: pointer;">
                                    <img src="${htmlPath}" alt="${displayName}" 
                                         style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
                                         onerror="this.parentElement.innerHTML='<div style=&quot;text-align:center;padding:2rem;color:#999;&quot;>No image found</div>'">
                                </div>
                            </div>
                        `;
                    }
                }
            });
            
            content += `</div></div>`;
            
            // Add UMAPs section
            const nodeName = summaryData.node_name;
            const cellTypeUmapPngPath = `/api/node-summary-image/${nodeName}/umap_by_cell_type.png`;
            const cellTypeUmapHtmlPath = `/api/node-summary-html/${nodeName}/umap_by_cell_type.html`;
            const leidenUmapPngPath = `/api/node-summary-image/${nodeName}/umap_by_leiden.png`;
            const leidenUmapHtmlPath = `/api/node-summary-html/${nodeName}/umap_by_leiden.html`;
            
            content += `<div class="summary-umaps-section" style="margin: 2rem 0;">`;
            content += `<h4 style="text-align: center; margin-bottom: 1.5rem;">UMAPs</h4>`;
            content += `<div class="umap-display-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 2rem; justify-items: center;">`;
            
            // Add cell type UMAP
            content += `
                <div class="heatmap-display-item" style="max-width: 650px; width: 100%; margin: 0 auto;">
                    <div class="image-header" style="text-align: center; margin-bottom: 1rem;">
                        <div class="image-title">Cell Type UMAP</div>
                        <div class="image-subtitle">Node Summary</div>
                    </div>
                    <div class="image-container cell-type-umap-modal" 
                         data-umap-html-path="${cellTypeUmapHtmlPath}"
                         data-image-title="Cell Type UMAP"
                         style="display: flex; justify-content: center; cursor: pointer; position: relative;">
                        <img src="${cellTypeUmapPngPath}" alt="Cell Type UMAP" 
                             style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
                             onerror="this.parentElement.innerHTML='<div style=&quot;text-align:center;padding:2rem;color:#999;&quot;>No image found</div>'">
                    </div>
                </div>
            `;
            
            // Add leiden UMAP
            content += `
                <div class="heatmap-display-item" style="max-width: 650px; width: 100%; margin: 0 auto;">
                    <div class="image-header" style="text-align: center; margin-bottom: 1rem;">
                        <div class="image-title">Leiden Cluster UMAP</div>
                        <div class="image-subtitle">Node Summary</div>
                    </div>
                    <div class="image-container leiden-umap-modal" 
                         data-umap-html-path="${leidenUmapHtmlPath}"
                         data-image-title="Leiden Cluster UMAP"
                         style="display: flex; justify-content: center; cursor: pointer; position: relative;">
                        <img src="${leidenUmapPngPath}" alt="Leiden Cluster UMAP" 
                             style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
                             onerror="this.parentElement.innerHTML='<div style=&quot;text-align:center;padding:2rem;color:#999;&quot;>No image found</div>'">
                    </div>
                </div>
            `;
            
            content += `</div></div>`;
        }
        
        // Add combined UMAP comparison after heatmaps
        if (this.currentNodeInfo && this.currentNodeInfo.overview_figures && 
            this.currentNodeInfo.overview_figures.program_umap_cell_type && 
            this.currentNodeInfo.overview_figures.program_umap_leiden) {
            const nodeName = summaryData.node_name;
            const thumbnailPath = `/api/node-summary-image/${nodeName}/umap_cell_type.png?compress=true&quality=75&max_width=400`;
            
            content += `
                <div style="margin: 2rem 0; display: flex; justify-content: center;">
                    <div class="image-item" style="max-width: 800px; width: 100%;">
                        <div class="image-header" style="text-align: center;">
                            <div class="image-title">UMAP Comparison - Leiden vs Cell Type</div>
                            <div class="image-subtitle">combined_umap_comparison</div>
                        </div>
                        <div class="image-container combined-umap" data-node-name="${nodeName}" data-image-title="UMAP Comparison - Leiden vs Cell Type" data-image-subtitle="combined_umap_comparison" style="display: flex; justify-content: center; position: relative;">
                            <img src="${thumbnailPath}" alt="UMAP Comparison - Leiden vs Cell Type" loading="lazy"
                                 onerror="this.parentElement.innerHTML='<div class=&quot;image-loading&quot;>Image not available</div>'"
                                 onload="this.style.opacity=1" style="opacity:0;transition:opacity 0.3s;cursor:pointer; width: 100%; height: auto; max-width: 800px;">
                            <div class="combined-badge">
                                <i class="fas fa-mouse-pointer"></i>
                                Interactive
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Add program labels if available
        if (Object.keys(programLabels).length > 0) {
            content += '<div class="program-labels-section">';
            content += '<h4>Program Labels</h4>';
            content += '<div class="program-labels-grid">';
            
            // Sort program labels by program number
            const sortedLabels = Object.entries(programLabels).sort((a, b) => {
                return parseInt(a[0]) - parseInt(b[0]);
            });
            
            // Create grid items
            for (let i = 0; i < sortedLabels.length; i++) {
                const [programNum, label] = sortedLabels[i];
                const geneCount = programGeneCounts[programNum];
                const geneCountText = geneCount ? ` (${geneCount} genes)` : '';
                
                // Convert to 1-based indexing for display
                const programNum1Based = parseInt(programNum) + 1;
                
                content += `
                    <div class="program-label-item clickable-program-label" data-program="program_${programNum}">
                        <span class="program-label-num">Program ${programNum1Based}${geneCountText}:</span>
                        <span class="program-label-text" title="${label}">${label}</span>
                    </div>
                `;
            }
            
            content += '</div>';
            
            // Add program correlation heatmap if available
            if (this.currentNodeInfo && this.currentNodeInfo.overview_figures && this.currentNodeInfo.overview_figures.program_correlation_heatmap) {
                const correlationPath = this.currentNodeInfo.overview_figures.program_correlation_heatmap;
                // Clean the path similar to how other images are handled
                const cleanPath = correlationPath.replace('/mnt/vdd/hca_lung_atlas_tree/test_setup/assets/', '');
                const basePath = `/api/images/${cleanPath}`;
                
                content += `
                    <div style="margin: 2rem 0; display: flex; justify-content: center;">
                        <div class="image-item" style="max-width: 800px; width: 100%;">
                            <div class="image-header" style="text-align: center;">
                                <div class="image-title">Program Correlation Heatmap</div>
                                <div class="image-subtitle">program_correlation_heatmap</div>
                            </div>
                            <div class="image-container" data-image-src="${basePath}?compress=true&quality=95&max_width=2000" data-image-title="Program Correlation Heatmap" data-image-subtitle="program_correlation_heatmap" style="display: flex; justify-content: center;">
                                <img src="${basePath}?compress=true&quality=85&max_width=800" alt="Program Correlation Heatmap" loading="lazy"
                                     onerror="console.error('Failed to load correlation heatmap:', '${correlationPath}', 'cleaned:', '${cleanPath}'); this.parentElement.innerHTML='<div class=&quot;image-loading&quot;>Image not available</div>'"
                                     onload="this.style.opacity=1" style="opacity:0;transition:opacity 0.3s;cursor:pointer; width: 100%; height: auto; max-width: 800px;">
                            </div>
                        </div>
                    </div>
                `;
            }
            
            content += '</div>';
        }
        
        return content;
    }

    createNodeInfoSections(nodeInfo) {
        const sections = [];
        
        // Data Overview section
        const dataOverview = this.createNodeDataOverview(nodeInfo);
        if (dataOverview) {
            sections.push(`
                <div class="section">
                    <div class="section-header">
                        <h4>Data Overview</h4>
                        <i class="fas fa-chevron-right expand-icon"></i>
                    </div>
                    <div class="section-content">
                        ${dataOverview}
                    </div>
                </div>
            `);
        }
        
        // Programs Summary section
        const programsSummary = this.createProgramsSummarySection(nodeInfo.programs_summary);
        if (programsSummary) {
            sections.push(`
                <div class="section">
                    <div class="section-header">
                        <h4>Programs Summary</h4>
                        <i class="fas fa-chevron-right expand-icon"></i>
                    </div>
                    <div class="section-content">
                        ${programsSummary}
                    </div>
                </div>
            `);
        }
        
        // Overview Visualizations section
        const overviewViz = this.createOverviewVisualizationsSection(nodeInfo.overview_figures);
        if (overviewViz) {
            sections.push(`
                <div class="section">
                    <div class="section-header">
                        <h4>Overview Visualizations</h4>
                        <i class="fas fa-chevron-right expand-icon"></i>
                    </div>
                    <div class="section-content">
                        ${overviewViz}
                    </div>
                </div>
            `);
        }
        
        return sections.join('');
    }

    createNodeDataOverview(nodeInfo) {
        const cells = nodeInfo.cells || {};
        const genes = nodeInfo.genes || {};
        const programsSummary = nodeInfo.programs_summary || {};
        
        let content = '';
        
        if (cells.number || cells.prelabeled_clusters) {
            content += '<div class="data-section"><h5>Cells</h5>';
            if (cells.number) {
                content += `<p><strong>Count:</strong> ${cells.number.toLocaleString()}</p>`;
            }
            if (cells.prelabeled_clusters && cells.prelabeled_clusters.cell_type) {
                content += '<p><strong>Prelabeled Clusters:</strong></p><ul>';
                content += `<li>cell_type: ${cells.prelabeled_clusters.cell_type} unique values</li>`;
                content += '</ul>';
            }
            
            // Add cell type counts if available from node summary
            if (this.currentNodeSummary && this.currentNodeSummary.cell_type_counts) {
                const cellTypeCounts = this.currentNodeSummary.cell_type_counts;
                if (Object.keys(cellTypeCounts).length > 0) {
                    content += '<p><strong>Cell Type Distribution:</strong></p><ul>';
                    
                    // Calculate total cells
                    const totalCells = Object.values(cellTypeCounts).reduce((sum, count) => sum + count, 0);
                    
                    // Sort by count in descending order
                    const sortedCellTypes = Object.entries(cellTypeCounts)
                        .sort(([,a], [,b]) => b - a);
                    
                    // Group cell types < 1% into "Other"
                    const mainCellTypes = [];
                    let otherCount = 0;
                    
                    sortedCellTypes.forEach(([cellType, count]) => {
                        const percentage = (count / totalCells) * 100;
                        if (percentage >= 1.0) {
                            mainCellTypes.push([cellType, count]);
                        } else {
                            otherCount += count;
                        }
                    });
                    
                    // Display main cell types
                    mainCellTypes.forEach(([cellType, count]) => {
                        content += `<li>${cellType}: ${count.toLocaleString()}</li>`;
                    });
                    
                    // Display "Other" if there are any
                    if (otherCount > 0) {
                        content += `<li>Other: ${otherCount.toLocaleString()}</li>`;
                    }
                    
                    content += '</ul>';
                }
            }
            
            content += '</div>';
        }
        
        if (genes.number) {
            content += '<div class="data-section"><h5>Genes</h5>';
            if (genes.number) {
                content += `<p><strong>Count:</strong> ${genes.number.toLocaleString()}</p>`;
            }
            content += '</div>';
        }
        
        // Add Programs Summary as a separate box
        if (programsSummary && Object.keys(programsSummary).length > 0) {
            content += '<div class="data-section"><h5>Programs Summary</h5>';
            
            if (programsSummary.number_of_programs) {
                content += `<p><strong>Number of Programs:</strong> ${programsSummary.number_of_programs}</p>`;
            }
            
            if (programsSummary.total_unique_genes) {
                content += `<p><strong>Total Unique Genes:</strong> ${programsSummary.total_unique_genes.toLocaleString()}</p>`;
            }
            
            if (programsSummary.size_stats) {
                const stats = programsSummary.size_stats;
                
                if (stats.min !== undefined) {
                    content += `<p><strong>Min Size:</strong> ${stats.min}</p>`;
                }
                if (stats.max !== undefined) {
                    content += `<p><strong>Max Size:</strong> ${stats.max}</p>`;
                }
                if (stats.mean !== undefined) {
                    content += `<p><strong>Mean Size:</strong> ${stats.mean.toFixed(1)}</p>`;
                }
                if (stats.median !== undefined) {
                    content += `<p><strong>Median Size:</strong> ${stats.median}</p>`;
                }
            }
            
            if (programsSummary.program_sizes && programsSummary.program_sizes.length > 0) {
                const sizes = programsSummary.program_sizes.slice(0, 10); // Show first 10
                const remaining = programsSummary.program_sizes.length - 10;
                content += `<p><strong>Program Sizes:</strong> [${sizes.join(', ')}${remaining > 0 ? `... +${remaining} more` : ''}]</p>`;
            }
            
            content += '</div>';
        }
        
        return content;
    }

    createProgramsSummarySection(programsSummary) {
        if (!programsSummary || Object.keys(programsSummary).length === 0) {
            return '';
        }
        
        let content = '';
        
        if (programsSummary.number_of_programs) {
            content += `<p><strong>Number of Programs:</strong> ${programsSummary.number_of_programs}</p>`;
        }
        
        if (programsSummary.total_unique_genes) {
            content += `<p><strong>Total Unique Genes:</strong> ${programsSummary.total_unique_genes.toLocaleString()}</p>`;
        }
        
        if (programsSummary.size_stats) {
            const stats = programsSummary.size_stats;
            content += '<div class="stats-grid">';
            content += `<div class="stat-item"><strong>Min Size:</strong> ${stats.min}</div>`;
            content += `<div class="stat-item"><strong>Max Size:</strong> ${stats.max}</div>`;
            content += `<div class="stat-item"><strong>Mean Size:</strong> ${stats.mean.toFixed(1)}</div>`;
            content += `<div class="stat-item"><strong>Median Size:</strong> ${stats.median.toFixed(1)}</div>`;
            content += '</div>';
        }
        
        if (programsSummary.program_sizes && programsSummary.program_sizes.length > 0) {
            const sizes = programsSummary.program_sizes;
            const displaySizes = sizes.length > 10 ? sizes.slice(0, 10) : sizes;
            content += `<p><strong>Program Sizes:</strong> [${displaySizes.join(', ')}${sizes.length > 10 ? '...' : ''}]</p>`;
        }
        
        return content;
    }

    createOverviewVisualizationsSection(overviewFigures) {
        if (!overviewFigures || Object.keys(overviewFigures).length === 0) {
            return '';
        }
        
        const imageMapping = {
            'program_umap_cell_type': 'UMAP - Cell Type',
            'program_umap_leiden': 'UMAP - Leiden Clusters',
            'combined_umap_comparison': 'UMAP Comparison - Leiden vs Cell Type'
        };
        
        // Don't add combined UMAP here anymore - it will be in node summary section
        const enhancedFigures = { ...overviewFigures };
        
        return this.createImagesGrid(enhancedFigures, imageMapping, 'Overview');
    }

    async loadNodeSummary(nodeName, nodeData = null) {
        try {
            const response = await fetch(`/api/node/${nodeName}/summary`);
            if (response.ok) {
                const summaryData = await response.json();
                this.renderNodeSummary(summaryData);
                
                // Refresh the node info section to include the summary data
                if (nodeData && nodeData.node_info && Object.keys(nodeData.node_info).length > 0) {
                    const nodeInfoContainer = document.getElementById('node-info-container');
                    nodeInfoContainer.innerHTML = this.createNodeInfoSection(nodeData.node_info);
                    // Load iframes in Node Overview section since it's expanded by default
                    this.loadIframesInElement(nodeInfoContainer);
                }
            } else {
                // Node summary not available, hide the container
                const summaryContainer = document.getElementById('node-summary-container');
                if (summaryContainer) {
                    summaryContainer.style.display = 'none';
                }
            }
        } catch (error) {
            console.warn('Node summary not available:', error);
            const summaryContainer = document.getElementById('node-summary-container');
            if (summaryContainer) {
                summaryContainer.style.display = 'none';
            }
        }
    }

    renderNodeSummary(summaryData) {
        // Store the summary data for use in program cards and node info section
        this.currentNodeSummary = summaryData;
        
        // Hide the separate node summary container since we're now showing this in node overview
        let summaryContainer = document.getElementById('node-summary-container');
        if (summaryContainer) {
            summaryContainer.style.display = 'none';
        }
    }

    async loadCellClusters(nodeName) {
        try {
            const response = await fetch(`/api/node/${nodeName}/leiden-clusters`);
            if (response.ok) {
                const clusterData = await response.json();
                this.renderCellClusters(clusterData);
            } else {
                // Cell clusters not available, hide the container
                const clusterContainer = document.getElementById('cell-clusters-container');
                if (clusterContainer) {
                    clusterContainer.style.display = 'none';
                }
            }
        } catch (error) {
            console.warn('Cell clusters not available:', error);
            const clusterContainer = document.getElementById('cell-clusters-container');
            if (clusterContainer) {
                clusterContainer.style.display = 'none';
            }
        }
    }

    renderCellClusters(clusterData) {
        let clusterContainer = document.getElementById('cell-clusters-container');
        
        // Create container if it doesn't exist
        if (!clusterContainer) {
            clusterContainer = document.createElement('div');
            clusterContainer.id = 'cell-clusters-container';
            
            // Insert after node-info-container
            const nodeInfoContainer = document.getElementById('node-info-container');
            if (nodeInfoContainer && nodeInfoContainer.parentNode) {
                nodeInfoContainer.parentNode.insertBefore(clusterContainer, nodeInfoContainer.nextSibling);
            }
        }
        
        const { cluster_labels, cluster_summaries, cluster_cell_types, cluster_cell_counts } = clusterData;
        
        // If no clusters, hide container
        if (!cluster_labels || Object.keys(cluster_labels).length === 0) {
            clusterContainer.style.display = 'none';
            return;
        }
        
        clusterContainer.style.display = 'block';
        clusterContainer.innerHTML = this.createCellClustersContent(cluster_labels, cluster_summaries, cluster_cell_types, cluster_cell_counts);
    }

    createCellClustersContent(clusterLabels, clusterSummaries, clusterCellTypes, clusterCellCounts) {
        // Sort clusters numerically by cluster number
        const sortedClusters = Object.entries(clusterLabels).sort(([a], [b]) => {
            const numA = parseInt(a.replace('cluster_', ''));
            const numB = parseInt(b.replace('cluster_', ''));
            return numA - numB;
        });

        // Create cluster dropdown items
        let clusterDropdowns = '';
        sortedClusters.forEach(([clusterKey, label]) => {
            const clusterNum = clusterKey.replace('cluster_', '');
            const summary = clusterSummaries[clusterKey] || 'No description available.';
            const cellTypes = clusterCellTypes[clusterKey] || [];
            const cellCount = clusterCellCounts[clusterKey];
            
            // Create cell type composition HTML
            let cellTypeHTML = '';
            if (cellTypes && cellTypes.length > 0) {
                cellTypeHTML = `
                    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                        <h4 style="margin: 0 0 0.75rem 0; font-size: 0.95rem; font-weight: 600; color: var(--text-color);">Cell Type Composition</h4>
                        <div style="display: grid; gap: 0.5rem;">
                            ${cellTypes.map(ct => `
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: #f8f9fa; border-radius: 4px;">
                                    <span style="font-weight: 500; color: var(--text-color);">${ct.cell_type}</span>
                                    <span style="color: var(--primary-color); font-weight: 600;">${ct.percentage}%</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            // Add cell count if available
            let cellCountHTML = '';
            if (cellCount !== undefined && cellCount !== null) {
                cellCountHTML = `
                    <div style="margin-top: 0.75rem; padding: 0.5rem; background: #e3f2fd; border-radius: 4px; text-align: center;">
                        <span style="font-weight: 600; color: var(--primary-color);">Total Cells: ${cellCount.toLocaleString()}</span>
                    </div>
                `;
            }
            
            clusterDropdowns += `
                <div class="cluster-dropdown-item" style="margin-bottom: 0.5rem;">
                    <div class="cluster-dropdown-header" style="display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1rem; background: #f8f9fa; border: 1px solid var(--border-color); border-radius: 6px; cursor: pointer; transition: background-color 0.2s ease;">
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <span style="font-weight: 600; color: var(--primary-color); min-width: 2rem;">Cluster ${clusterNum}</span>
                            <span style="color: var(--text-color);">${label}</span>
                        </div>
                        <i class="fas fa-chevron-right cluster-expand-icon" style="color: var(--text-secondary); transition: transform 0.3s ease;"></i>
                    </div>
                    <div class="cluster-dropdown-content" style="display: none; padding: 1.5rem; background: white; border: 1px solid var(--border-color); border-top: none; border-radius: 0 0 6px 6px; margin-top: -6px;">
                        ${cellCountHTML}
                        ${cellTypeHTML}
                        <p style="line-height: 1.6; color: var(--text-color); white-space: pre-wrap; margin: ${cellTypeHTML || cellCountHTML ? '1rem 0 0 0' : '0'}; ${cellTypeHTML || cellCountHTML ? 'padding-top: 1rem; border-top: 1px solid var(--border-color);' : ''}">${summary}</p>
                    </div>
                </div>
            `;
        });

        return `
            <div class="program-card cell-clusters-card" style="margin-bottom: 2rem;">
                <div class="program-header">
                    <div class="program-header-content">
                        <div class="program-name-row">
                            <h3 class="program-name">
                                Cell Clusters
                            </h3>
                        </div>
                    </div>
                    <i class="fas fa-chevron-down expand-icon expanded"></i>
                </div>
                <div class="program-content expanded">
                    <div class="cluster-dropdowns-container">
                        ${clusterDropdowns}
                    </div>
                </div>
            </div>
        `;
    }

    createNodeSummarySection(summaryData) {
        const figures = summaryData.figures || {};
        const programLabels = summaryData.program_labels || {};
        const programGeneCounts = summaryData.program_gene_counts || {};
        
        let content = '<div class="node-summary-section">';
        
        // Add program labels first if available
        if (Object.keys(programLabels).length > 0) {
            content += '<div class="program-labels-section">';
            content += '<h3>Program Labels</h3>';
            content += '<div class="program-labels-grid">';
            
            // Sort program labels by program number
            const sortedLabels = Object.entries(programLabels).sort(([a], [b]) => {
                return parseInt(a) - parseInt(b);
            });
            
            // Arrange in 3 columns with numbers running down columns
            const numColumns = 3;
            const itemsPerColumn = Math.ceil(sortedLabels.length / numColumns);
            
            // Create columns
            for (let col = 0; col < numColumns; col++) {
                const startIdx = col * itemsPerColumn;
                const endIdx = Math.min(startIdx + itemsPerColumn, sortedLabels.length);
                
                for (let i = startIdx; i < endIdx; i++) {
                    const [programNum, label] = sortedLabels[i];
                    const geneCount = programGeneCounts[programNum];
                    const geneCountText = geneCount ? ` (${geneCount} genes)` : '';
                    
                    // Convert to 1-based indexing for display
                    const programNum1Based = parseInt(programNum) + 1;
                    
                    content += `
                        <div class="program-label-item clickable-program-label" data-program="program_${programNum}">
                            <span class="program-label-num">Program ${programNum1Based}${geneCountText}:</span>
                            <span class="program-label-text" title="${label}">${label}</span>
                        </div>
                    `;
                }
            }
            
            content += '</div></div>';
        }
        
        // Add figures section if available
        if (Object.keys(figures).length > 0) {
            content += '<div class="node-summary-figures">';
            content += '<h3>Node Summary Heatmaps</h3>';
            content += '<div class="heatmap-grid">';
            
            const figureMapping = {
                'cell_type_by_program_activity_heatmap': 'Cell Type by Program Activity',
                'cluster_by_cell_type_heatmap': 'Cluster by Cell Type',
                'leiden_cluster_by_program_activity_heatmap': 'Leiden Cluster by Program Activity'
            };
            
            Object.entries(figures).forEach(([key, imagePath]) => {
                const title = figureMapping[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                content += `
                    <div class="heatmap-item" 
                         data-image-src="${imagePath}" 
                         data-image-title="${title}"
                         data-image-subtitle="Node: ${summaryData.node_name}">
                        <img src="${imagePath}" alt="${title}" loading="lazy">
                        <div class="heatmap-title">${title}</div>
                    </div>
                `;
            });
            
            content += '</div></div>';
        }
        
        content += '</div>';
        return content;
    }

    showError(message) {
        document.getElementById('programs-loading').style.display = 'none';
        document.getElementById('programs-container').innerHTML = `
            <div class="error" style="text-align: center; padding: 2rem; color: var(--danger-color);">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>${message}</p>
            </div>
        `;
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.hcaApp = new HCAAtlasApp();
});
