#!/usr/bin/env node
/**
 * D3-Force Layout Worker for Pass 2
 * 
 * Receives JSON payload with:
 * - bounds: container dimensions
 * - nodes: content to position
 * - obstacles: child cuts to avoid
 * - portNodes: pinned ports on boundary
 * - links: connections
 * 
 * Returns: Final positions for all nodes
 */

const d3 = require('d3-force');
const fs = require('fs');

// Read input from stdin
let inputData = '';
process.stdin.on('data', chunk => {
    inputData += chunk;
});

process.stdin.on('end', () => {
    try {
        const payload = JSON.parse(inputData);
        const result = layoutContent(payload);
        console.log(JSON.stringify(result));
    } catch (error) {
        console.error('Error:', error.message);
        process.exit(1);
    }
});

function layoutContent(payload) {
    const { bounds, nodes, links, obstacles, portNodes, seed } = payload;
    
    // Seeded random number generator for deterministic layouts
    let randomSeed = seed !== undefined ? seed : Date.now();
    function seededRandom() {
        const x = Math.sin(randomSeed++) * 10000;
        return x - Math.floor(x);
    }
    
    // Build simulation nodes
    const simNodes = [];
    
    // SIMPLE INITIAL POSITIONING: Start all nodes at center
    // Let collision forces spread them out naturally
    const centerX = bounds.width / 2;
    const centerY = bounds.height / 2;
    
    // Add simNodes for all regular nodes
    for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];
        let x = centerX;
        let y = centerY;
        
        // Small jitter to break symmetry (gives collision force a direction)
        const jitter = 5;
        x += (seededRandom() - 0.5) * jitter;
        y += (seededRandom() - 0.5) * jitter;
        
        const simNode = {
            id: node.id,
            type: node.type,
            label: node.label,
            width: node.width,
            height: node.height,
            x: x,
            y: y
        };
        
        // If pinned, mark as fixed for D3 (fx/fy)
        if (node.pinned) {
            simNode.fx = x;
            simNode.fy = y;
        }
        
        simNodes.push(simNode);
    }
    
    // Add pinned port nodes
    for (const port of portNodes) {
        simNodes.push({
            id: port.id,
            type: 'port',
            fx: port.x,  // Fixed position
            fy: port.y,
            x: port.x,   // Also set x/y for distance calculations
            y: port.y
        });
    }
    
    // Add obstacle nodes (fixed)
    for (const obs of obstacles) {
        simNodes.push({
            id: obs.id,
            type: 'obstacle',
            fx: obs.x,
            fy: obs.y,
            width: obs.width,
            height: obs.height
        });
    }
    
    // Build simulation links
    const simLinks = links.map(link => ({
        source: link.source,
        target: link.target
    }));
    
    // ============================================================================
    // FOUR FORCES: ONE JOB EACH
    // ============================================================================
    // 1. forceLink: Attraction between connected elements
    // 2. forceCollide: Repulsion (handles ALL collisions including obstacles)
    // 3. forceCenter: Weak centering to prevent drift
    // 4. forceContainment: Boundary walls only (no obstacle logic - collision handles that)
    // ============================================================================
    
    const simulation = d3.forceSimulation(simNodes)
        // FORCE 1: Attraction - keep connected elements together
        .force('link', d3.forceLink(simLinks)
            .id(d => d.id)
            .distance(25)
            .strength(1.5)
        )
        // FORCE 2: Repulsion - ALL collisions (nodes AND obstacles)
        .force('collision', d3.forceCollide()
            .radius(d => {
                // Obstacles treated as large circles
                if (d.type === 'obstacle') return Math.max(d.width, d.height) / 2 + 5;
                if (d.type === 'port') return 3;
                // Content elements
                if (d.width && d.height) return Math.max(d.width, d.height) / 2 + 5;
                return d.type === 'vertex' ? 15 : 30;
            })
            .strength(1.0)
            .iterations(3)  // More iterations for stronger collision resolution
        )
        // FORCE 3: Centering - weak, prevents drift
        .force('center', d3.forceCenter(bounds.width / 2, bounds.height / 2)
            .strength(0.05)  // Very weak - just prevents escape
        )
        // FORCE 4: Walls - outer boundary only
        .force('containment', forceContainment(bounds));
    
    // Run simulation to equilibrium
    simulation.stop();
    for (let i = 0; i < 500; ++i) {
        simulation.tick();
    }
    
    // Extract final positions (containment force has already enforced all constraints)
    const positions = {};
    for (const node of simNodes) {
        // Include all nodes except obstacles and ports
        if (node.type !== 'obstacle' && node.type !== 'port') {
            positions[node.id] = {
                x: node.x,
                y: node.y
            };
        }
    }
    
    return positions;
}

/**
 * Simple Containment Force - Outer Boundary Only
 * 
 * ONE JOB: Keep nodes inside the virtual box boundaries.
 * Does NOT handle obstacle collisions - forceCollide does that.
 * 
 * Applied every tick to enforce the unbreakable rule: nodes cannot escape the box.
 */
function forceContainment(bounds) {
    let nodes;
    
    function force(alpha) {
        for (const node of nodes) {
            // Skip pinned nodes
            if (node.fx !== undefined || node.fy !== undefined) continue;
            
            // Skip obstacles
            if (node.type === 'obstacle' || node.type === 'port') continue;
            
            // Get node half-dimensions
            let halfWidth, halfHeight;
            if (node.width && node.height) {
                halfWidth = node.width / 2;
                halfHeight = node.height / 2;
            } else {
                const radius = node.type === 'vertex' ? 15 : 30;
                halfWidth = halfHeight = radius;
            }
            
            // Clamp to bounds and zero velocity at walls
            if (node.x - halfWidth < 0) {
                node.x = halfWidth;
                node.vx = 0;
            } else if (node.x + halfWidth > bounds.width) {
                node.x = bounds.width - halfWidth;
                node.vx = 0;
            }
            
            if (node.y - halfHeight < 0) {
                node.y = halfHeight;
                node.vy = 0;
            } else if (node.y + halfHeight > bounds.height) {
                node.y = bounds.height - halfHeight;
                node.vy = 0;
            }
        }
    }
    
    force.initialize = function(_) {
        nodes = _;
    };
    
    return force;
}
