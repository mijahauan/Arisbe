#!/usr/bin/env node
/**
 * D3.js Force-Directed Layout with Containment Constraints
 * 
 * Custom forces:
 * 1. Link force - attracts connected elements (ligatures)
 * 2. Collision force - prevents overlap
 * 3. Containment force - keeps elements in parent area
 * 4. Exclusion force - pushes elements out of child cuts
 */

const d3 = require('d3-force');
const fs = require('fs');

// Read input JSON from stdin or file
const inputFile = process.argv[2];
if (!inputFile) {
    console.error('Usage: node d3_layout_bridge.js <input.json>');
    process.exit(1);
}

const input = JSON.parse(fs.readFileSync(inputFile, 'utf8'));

// Parse input
const { nodes, links, areas, hierarchy, iterations = 300 } = input;

// Build hierarchy levels (bottom-up)
function buildHierarchyLevels() {
    const levels = [];
    const visited = new Set();
    const allAreas = Object.keys(hierarchy);
    
    // Find leaf cuts (no children)
    let currentLevel = allAreas.filter(areaId => 
        hierarchy[areaId].children.length === 0 && 
        areaId !== findSheetId()
    );
    
    while (currentLevel.length > 0) {
        levels.push(currentLevel);
        currentLevel.forEach(id => visited.add(id));
        
        // Find parents of current level that have all children visited
        currentLevel = allAreas.filter(areaId => {
            if (visited.has(areaId)) return false;
            if (areaId === findSheetId()) return false;
            const children = hierarchy[areaId].children;
            return children.length > 0 && children.every(c => visited.has(c));
        });
    }
    
    // Add sheet as final level
    levels.push([findSheetId()]);
    
    return levels;
}

function findSheetId() {
    // Sheet has no parent or is the root
    for (const [areaId, info] of Object.entries(hierarchy)) {
        const isChild = Object.values(hierarchy).some(h => h.children.includes(areaId));
        if (!isChild) return areaId;
    }
    return Object.keys(hierarchy)[0]; // Fallback
}

// Convert to D3 format
const d3Nodes = nodes.map(n => ({
    id: n.id,
    type: n.type, // 'vertex' or 'edge_label' or 'cut'
    label: n.label || '',
    area_id: n.area_id,
    x: n.x || 50,  // Default deterministic position (will be overridden)
    y: n.y || 50,  // Default deterministic position (will be overridden)
    radius: n.type === 'vertex' ? 3 : 8,
    fixed: false // Will be set to true for sized cuts
}));

const d3Links = links.map(l => ({
    source: l.source,
    target: l.target,
    strength: 0.3
}));

// Track cut sizes (calculated bottom-up)
const cutSizes = {};

// Custom containment force - HARD constraint
// NOTE: This force works in LOCAL coordinates for each sub-simulation
function forceContainment(boundingBox) {
    let nodes;
    
    function force(alpha) {
        for (let node of nodes) {
            // Skip fixed nodes (child cut obstacles)
            if (node.fx !== undefined && node.fy !== undefined) continue;
            
            const radius = node.radius || 5;
            
            // HARD CLIPPING: Clamp node center to bounding box minus radius
            // This is NOT a soft force - it's a hard constraint
            if (node.x < boundingBox.x1 + radius) {
                node.x = boundingBox.x1 + radius;
                node.vx = 0; // Kill velocity at boundary
            } else if (node.x > boundingBox.x2 - radius) {
                node.x = boundingBox.x2 - radius;
                node.vx = 0;
            }
            
            if (node.y < boundingBox.y1 + radius) {
                node.y = boundingBox.y1 + radius;
                node.vy = 0;
            } else if (node.y > boundingBox.y2 - radius) {
                node.y = boundingBox.y2 - radius;
                node.vy = 0;
            }
        }
    }
    
    force.initialize = function(_) {
        nodes = _;
    };
    
    return force;
}

// No exclusion force needed - child cuts are fixed obstacles with collision

// BOTTOM-UP RECURSIVE SIMULATION
// Layout cuts from innermost to outermost, calculating sizes as we go

const hierarchyLevels = buildHierarchyLevels();
console.error(`Hierarchy levels: ${hierarchyLevels.map(l => l.length).join(' → ')}`);

// Process each level bottom-up
for (const levelAreas of hierarchyLevels) {
    for (const areaId of levelAreas) {
        console.error(`Laying out area: ${areaId.substring(0, 8)}`);
        
        // Get nodes in this area
        const areaNodes = d3Nodes.filter(n => n.area_id === areaId);
        
        // Add cut nodes for child cuts (with known sizes from previous levels)
        // Position them in a non-overlapping grid based on their actual sizes
        const childCutNodes = [];
        const childIds = hierarchy[areaId].children.filter(id => cutSizes[id]);
        
        if (childIds.length > 0) {
            // Calculate grid layout with proper spacing
            const cols = Math.ceil(Math.sqrt(childIds.length));
            
            // Find max dimensions for grid cell sizing
            let maxWidth = 0, maxHeight = 0;
            for (const childId of childIds) {
                maxWidth = Math.max(maxWidth, cutSizes[childId].width);
                maxHeight = Math.max(maxHeight, cutSizes[childId].height);
            }
            
            const cellWidth = maxWidth + 60;  // Add spacing between cuts
            const cellHeight = maxHeight + 60;
            
            for (let i = 0; i < childIds.length; i++) {
                const childId = childIds[i];
                
                const col = i % cols;
                const row = Math.floor(i / cols);
                
                // Center each cut in its grid cell
                const x = col * cellWidth + cellWidth / 2 + 50;
                const y = row * cellHeight + cellHeight / 2 + 50;
                
                const cutNode = {
                    id: childId,
                    type: 'cut',
                    area_id: areaId,
                    x: x,
                    y: y,
                    fx: x,  // FIXED position - cuts cannot move!
                    fy: y,  // FIXED position - cuts cannot move!
                    radius: Math.max(cutSizes[childId].width, cutSizes[childId].height) / 2 + 20,
                    width: cutSizes[childId].width,
                    height: cutSizes[childId].height,
                    isCut: true
                };
                childCutNodes.push(cutNode);
                areaNodes.push(cutNode);
            }
        }
        
        // Get links involving nodes in this area
        const areaLinks = d3Links.filter(l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            return areaNodes.some(n => n.id === sourceId) && 
                   areaNodes.some(n => n.id === targetId);
        });
        
        if (areaNodes.length === 0) {
            console.error(`  (empty area)`);
            continue;
        }
        
        // Estimate bounding box size for this simulation
        // Start with a reasonable initial size
        let estimatedWidth = 200;
        let estimatedHeight = 200;
        
        if (childCutNodes.length > 0) {
            // If we have child cuts, size must fit them
            const totalChildArea = childCutNodes.reduce((sum, c) => sum + c.width * c.height, 0);
            estimatedWidth = Math.sqrt(totalChildArea) * 1.5;
            estimatedHeight = estimatedWidth;
        }
        
        // Initialize nodes in DETERMINISTIC positions to ensure reproducible layouts
        // Circular arrangement for aesthetics and stability
        let freeNodes = areaNodes.filter(n => !n.fx && !n.fy);
        const centerX = estimatedWidth / 2;
        const centerY = estimatedHeight / 2;
        const radius = Math.min(estimatedWidth, estimatedHeight) / 4;
        
        for (let i = 0; i < freeNodes.length; i++) {
            const angle = (i / freeNodes.length) * 2 * Math.PI;
            freeNodes[i].x = centerX + radius * Math.cos(angle);
            freeNodes[i].y = centerY + radius * Math.sin(angle);
        }
        
        // Define LOCAL bounding box for containment
        const localBounds = {
            x1: 15,  // Padding from edges
            y1: 15,
            x2: estimatedWidth - 15,
            y2: estimatedHeight - 15
        };
        
        // Run simulation for this area only - in LOCAL coordinates
        const simulation = d3.forceSimulation(areaNodes)
            .force('link', d3.forceLink(areaLinks)
                .id(d => d.id)
                .distance(30)
                .strength(0.3))
            .force('charge', d3.forceManyBody()
                .strength(-100)
                .distanceMax(100))
            .force('collision', d3.forceCollide()
                .radius(d => {
                    if (d.type === 'cut' || d.isCut) {
                        // Use larger of width/height for cut collision
                        return Math.max(d.width, d.height) / 2 + 15;
                    }
                    return d.radius + 5;
                })
                .strength(1.0)  // MAXIMUM strength - cuts CANNOT overlap!
                .iterations(3)) // Multiple iterations per tick
            .force('containment', forceContainment(localBounds))
            .alphaDecay(0.01)
            .velocityDecay(0.4);
        
        // Run simulation synchronously
        for (let i = 0; i < iterations; i++) {
            simulation.tick();
        }
        
        // Calculate bounding box - GUARANTEED to contain all content
        if (areaNodes.length > 0) {
            const padding = 50; // Large padding for safety
            
            let minX = Infinity, maxX = -Infinity;
            let minY = Infinity, maxY = -Infinity;
            
            for (const n of areaNodes) {
                if (n.isCut || n.type === 'cut') {
                    // Child cut: use its KNOWN size (from previous level)
                    // This is GUARANTEED correct since we calculated it bottom-up
                    minX = Math.min(minX, n.x - n.width / 2);
                    maxX = Math.max(maxX, n.x + n.width / 2);
                    minY = Math.min(minY, n.y - n.height / 2);
                    maxY = Math.max(maxY, n.y + n.height / 2);
                } else {
                    // Regular node: use its radius
                    const r = n.radius || 5;
                    minX = Math.min(minX, n.x - r);
                    maxX = Math.max(maxX, n.x + r);
                    minY = Math.min(minY, n.y - r);
                    maxY = Math.max(maxY, n.y + r);
                }
            }
            
            // Calculate size with generous padding
            const width = (maxX - minX) + 2 * padding;
            const height = (maxY - minY) + 2 * padding;
            
            // Store size for use in parent area
            cutSizes[areaId] = { width, height };
            
            // Store area bounds in LOCAL coordinates (will be transformed later)
            areas[areaId] = {
                x: 0,  // Start at origin in local space
                y: 0,
                width: width,
                height: height
            };
            
            console.error(`  Sized: ${width.toFixed(0)}x${height.toFixed(0)}`);
        }
    }
}

// NO COORDINATE TRANSFORMATION!
// Everything stays in ALU (Abstract Layout Units) - local coordinates per area
// The renderer will handle hierarchy-based positioning

// Extract final positions (all in LOCAL coordinates)
const output = {
    nodes: d3Nodes.filter(n => !n.isCut && n.type !== 'cut').map(n => ({
        id: n.id,
        x: n.x,  // LOCAL to its area
        y: n.y,  // LOCAL to its area
        area_id: n.area_id
    })),
    areas: areas,  // Each area has x=0, y=0 in local space
    hierarchy: hierarchy  // Parent-child relationships for renderer
};

// Write to stdout
console.log(JSON.stringify(output, null, 2));
