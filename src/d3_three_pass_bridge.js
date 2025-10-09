#!/usr/bin/env node
/**
 * D3.js Layout Bridge for Three-Pass Architecture
 * 
 * Handles two types of layouts:
 * 1. Macro-layout: Position cuts relative to each other
 * 2. Micro-layout: Position content within a cut (with pinned port nodes)
 */

const d3 = require('d3-force');

// Read input from stdin
let inputData = '';
process.stdin.setEncoding('utf8');

process.stdin.on('data', (chunk) => {
    inputData += chunk;
});

process.stdin.on('end', () => {
    try {
        const input = JSON.parse(inputData);
        
        if (input.type === 'macro_layout') {
            executeMacroLayout(input);
        } else if (input.type === 'micro_layout') {
            executeMicroLayout(input);
        } else {
            throw new Error(`Unknown layout type: ${input.type}`);
        }
    } catch (error) {
        console.error('Error:', error.message);
        process.exit(1);
    }
});

/**
 * Macro-layout: Position cuts as nodes in force simulation
 */
function executeMacroLayout(input) {
    const { graph, config } = input;
    const { nodes, edges } = graph;
    const { width, height, iterations } = config;
    
    // Convert edges to d3 links
    const links = edges.map(e => ({
        source: e.source,
        target: e.target,
        ligature_id: e.ligature_id
    }));
    
    // Initialize simulation
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links)
            .id(d => d.id)
            .distance(150)
            .strength(0.7))
        .force('charge', d3.forceManyBody()
            .strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide()
            .radius(d => {
                // Cut nodes need more space than sheet
                return d.type === 'cut' ? 80 : 50;
            })
            .strength(0.9))
        .stop();
    
    // Run simulation synchronously
    for (let i = 0; i < iterations; i++) {
        simulation.tick();
    }
    
    // Estimate cut sizes based on content count
    nodes.forEach(node => {
        const baseSize = 100;
        const contentFactor = Math.sqrt(node.content_count || 1);
        node.width = baseSize + contentFactor * 30;
        node.height = baseSize + contentFactor * 20;
    });
    
    // Output result
    const result = {
        nodes: nodes.map(n => ({
            id: n.id,
            x: n.x,
            y: n.y,
            width: n.width || 150,
            height: n.height || 100
        })),
        edges: edges
    };
    
    console.log(JSON.stringify(result, null, 2));
}

/**
 * Micro-layout: Position content within a cut with constrained forces
 */
function executeMicroLayout(input) {
    const { graph, config } = input;
    const { nodes, edges } = graph;
    const { width, height, iterations, containment } = config;
    
    // Convert edges to d3 links
    const links = edges.map(e => ({
        source: e.source,
        target: e.target
    }));
    
    // Initialize simulation with containment
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links)
            .id(d => d.id)
            .distance(d => {
                // Ports pull content towards boundaries
                const isPortLink = d.source.type === 'port' || d.target.type === 'port';
                return isPortLink ? 40 : 30;  // Short distance for tight layout
            })
            .strength(d => {
                // Strong attraction for ligatures, but weaker to ports to avoid pulling into obstacles
                const isPortLink = d.source.type === 'port' || d.target.type === 'port';
                return isPortLink ? 0.3 : 1.0;  // Weak port links, strong internal links
            }))
        .force('charge', d3.forceManyBody()
            .strength(-30))  // Very weak general repulsion - let links dominate
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide()
            .radius(d => {
                if (d.type === 'vertex') return 10;  // Slightly larger
                if (d.type === 'edge_label') return 30;  // Slightly larger
                if (d.type === 'port') return 5;
                if (d.type === 'child_cut' || d.type === 'obstacle') {
                    // Child cuts / obstacles are large - ADD PADDING for exclusion zone
                    const baseRadius = Math.max(d.width || 100, d.height || 80) / 2;
                    return baseRadius + 15;  // Add 15px padding for safety
                }
                return 10;
            })
            .strength(3.0)  // MAXIMUM collision to enforce exclusion
            .iterations(5))  // Many collision iterations per tick
        .stop();
    
    // Add MANDATORY containment force - runs every tick
    if (containment) {
        simulation.force('containment', () => {
            // Extra margin for vertex labels rendered above
            const margin = 25;
            nodes.forEach(node => {
                // Don't constrain pinned nodes (ports, obstacles)
                if (node.fx !== undefined || node.fy !== undefined) return;
                if (node.type === 'obstacle' || node.type === 'child_cut') return;
                
                // HARD constrain to boundary - ABSOLUTE enforcement
                node.x = Math.max(margin, Math.min(width - margin, node.x));
                node.y = Math.max(margin, Math.min(height - margin, node.y));
                
                // Extra enforcement: push velocity to zero if at boundary
                if (node.x <= margin || node.x >= width - margin) {
                    node.vx = 0;
                }
                if (node.y <= margin || node.y >= height - margin) {
                    node.vy = 0;
                }
            });
        });
    }
    
    // Run simulation synchronously
    for (let i = 0; i < iterations; i++) {
        simulation.tick();
    }
    
    // Calculate actual bounding box with proper element sizes
    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;
    
    nodes.forEach(node => {
        if (node.type === 'port') return; // Don't include ports in bbox
        
        // Account for element extents
        let nodeRadius = 5;
        if (node.type === 'vertex') {
            nodeRadius = 15; // Vertex + label space
        } else if (node.type === 'edge_label') {
            // Estimate text width
            const textWidth = (node.label || '').length * 8 + 10;
            nodeRadius = textWidth / 2;
        } else if (node.type === 'child_cut') {
            // Child cuts are large rectangles
            nodeRadius = Math.max(node.width || 100, node.height || 80) / 2;
        }
        
        minX = Math.min(minX, node.x - nodeRadius);
        minY = Math.min(minY, node.y - nodeRadius);
        maxX = Math.max(maxX, node.x + nodeRadius);
        maxY = Math.max(maxY, node.y + nodeRadius);
    });
    
    const padding = 30; // Extra padding for safety
    const bbox = {
        x: minX - padding,
        y: minY - padding,
        width: (maxX - minX) + 2 * padding,
        height: (maxY - minY) + 2 * padding
    };
    
    // Output result
    const result = {
        nodes: nodes.map(n => ({
            id: n.id,
            type: n.type,
            x: n.x,
            y: n.y,
            label: n.label
        })),
        bbox: bbox
    };
    
    console.log(JSON.stringify(result, null, 2));
}
