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
    
    // Add content nodes with smart initial positions
    // Strategy: Place near port nodes if available, avoiding obstacles
    for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];
        let x, y;
        
        // Check if this node has a user-defined pinned position
        if (node.pinned && node.x !== undefined && node.y !== undefined) {
            // User override - use exact position and mark as fixed
            x = node.x;
            y = node.y;
        } else if (node.x !== undefined && node.y !== undefined) {
            // Graphviz hint position (use as starting point, not fixed)
            x = node.x;
            y = node.y;
        } else if (portNodes.length > 0) {
            // Place near the first port node (likely connection point)
            const port = portNodes[0];
            // Offset from port to avoid exact overlap (use seeded random for determinism)
            const offsetAngle = seed !== undefined ? 
                (i / nodes.length) * 2 * Math.PI : 
                seededRandom() * 2 * Math.PI;
            const offsetDist = 40;
            x = port.x + offsetDist * Math.cos(offsetAngle);
            y = port.y + offsetDist * Math.sin(offsetAngle);
        } else {
            // No ports - spread in circle (deterministic if seed provided)
            const angle = seed !== undefined ? 
                (i / nodes.length) * 2 * Math.PI : 
                seededRandom() * 2 * Math.PI;
            const radius = Math.min(bounds.width, bounds.height) * 0.2;
            x = bounds.width / 2 + radius * Math.cos(angle);
            y = bounds.height / 2 + radius * Math.sin(angle);
        }
        
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
    
    // Build map of which nodes are connected to ports
    // These nodes need special handling - they MUST be able to reach port boundaries
    const nodesConnectedToPorts = new Set();
    for (const link of simLinks) {
        const srcType = typeof link.source === 'string' ? null : link.source.type;
        const tgtType = typeof link.target === 'string' ? null : link.target.type;
        const srcId = typeof link.source === 'string' ? link.source : link.source.id;
        const tgtId = typeof link.target === 'string' ? link.target : link.target.id;
        
        // Check if either end is a port (by ID pattern or type)
        const srcIsPort = srcId.includes('port') || srcType === 'port';
        const tgtIsPort = tgtId.includes('port') || tgtType === 'port';
        
        if (srcIsPort) {
            nodesConnectedToPorts.add(tgtId);
        }
        if (tgtIsPort) {
            nodesConnectedToPorts.add(srcId);
        }
    }
    
    // Calculate node degrees (connection counts)
    const nodeDegrees = new Map();
    for (const node of simNodes) {
        nodeDegrees.set(node.id, 0);
    }
    for (const link of simLinks) {
        const srcId = typeof link.source === 'object' ? link.source.id : link.source;
        const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
        nodeDegrees.set(srcId, (nodeDegrees.get(srcId) || 0) + 1);
        nodeDegrees.set(tgtId, (nodeDegrees.get(tgtId) || 0) + 1);
    }
    
    // Create simulation
    // Adaptive link distance: sheets need more space than tight cuts
    const linkDistance = obstacles.length > 0 ? 30 : 50;  // More space on sheets
    
    const simulation = d3.forceSimulation(simNodes)
        .force('link', d3.forceLink(simLinks)
            .id(d => d.id)
            .distance(d => {
                // Port links should have minimal distance - elements right at ports
                const isPortLink = d.source.type === 'port' || d.target.type === 'port';
                return isPortLink ? 5 : linkDistance;  // Port links very short!
            })
            .strength(d => {
                const isPortLink = d.source.type === 'port' || d.target.type === 'port';
                if (isPortLink) {
                    // Port links MUST dominate obstacle repulsion!
                    // Topological correctness requires elements stay near their ports
                    return 50.0;  // Extremely strong - must overcome obstacle repulsion
                }
                return 4.0;  // Normal links
            }))
        .force('charge', d3.forceManyBody()
            .strength(-50));  // Weaker repulsion for tighter packing (was -100)
    
    // NOTE: No d3.forceCenter! We use adaptive forceX/forceY instead for fine control
    
    // NOTE: No obstacle repulsion during simulation!
    // Port-linked elements must be free to reach ports (which are on obstacle boundaries).
    // Final hard ejection will handle any elements that stray into obstacle interiors.
    
    // Adaptive centering based on context:
    // Port-connected nodes: NO centering - port forces dominate
    // Cuts WITH obstacles: Strong centering (0.6) works because obstacles prevent clustering
    // Sheets WITHOUT obstacles: Weak/no centering - let links determine spacing
    const hasObstacles = obstacles.length > 0;
    
    simulation
        .force('x', d3.forceX(bounds.width / 2)
            .strength(d => {
                // NO centering for port-connected nodes - ports determine position!
                if (nodesConnectedToPorts.has(d.id)) {
                    return 0;
                }
                // Only apply adaptive centering if no ports (nested cut interiors)
                if (payload.portNodes.length > 0) {
                    return 0.05;  // Very weak centering when ports present
                }
                const degree = nodeDegrees.get(d.id) || 0;
                if (hasObstacles) {
                    // Strong centering OK with obstacles
                    return degree >= 2 ? 0.6 : 0.08;
                } else {
                    // Weak centering without obstacles (sheet context)
                    return degree >= 2 ? 0.15 : 0.05;
                }
            }))
        .force('y', d3.forceY(bounds.height / 2)
            .strength(d => {
                // NO centering for port-connected nodes
                if (nodesConnectedToPorts.has(d.id)) {
                    return 0;
                }
                // Weak centering when ports present
                if (payload.portNodes.length > 0) {
                    return 0.05;
                }
                return hasObstacles ? 0.08 : 0.05;
            }));
    
    simulation
        .force('collision', d3.forceCollide()
            .radius(d => {
                // Use actual dimensions for spatial/logical correspondence
                if (d.width !== undefined && d.height !== undefined) {
                    // Use max dimension / 2 as radius, plus generous safety margin
                    // The margin ensures spatial/logical clarity
                    return Math.max(d.width, d.height) / 2 + 5;
                }
                // Fallback for nodes without dimensions
                if (d.type === 'vertex') return 12;
                if (d.type === 'edge_label') return 25;
                if (d.type === 'port') return 5;
                if (d.type === 'obstacle') return 0;
                return 10;
            })
            .strength(0.8)  // Stronger collision enforcement
            .iterations(3));
    
    // Run simulation - apply containment AFTER each tick for absolute enforcement
    simulation.stop();
    for (let i = 0; i < 500; ++i) {
        simulation.tick();
        // ABSOLUTE CONTAINMENT: Apply after velocity integration
        applyAbsoluteContainment(simNodes, bounds, obstacles, nodesConnectedToPorts);
    }
    
    // FINAL HARD CLAMP: Ensure containment after simulation completes
    // This is the absolute guarantee - no element escapes its area
    for (const node of simNodes) {
        if (node.fx !== undefined || node.fy !== undefined) continue;
        if (node.type === 'obstacle' || node.type === 'port') continue;
        
        // Use actual dimensions for spatial/logical correspondence
        let halfWidth, halfHeight;
        const safetyMargin = 5;  // Moderate margin - allows proximity when needed
        if (node.width !== undefined && node.height !== undefined) {
            halfWidth = node.width / 2 + safetyMargin;
            halfHeight = node.height / 2 + safetyMargin;
        } else {
            const radius = node.type === 'vertex' ? 15 : (node.type === 'edge_label' ? 30 : 10);
            halfWidth = halfHeight = radius;
        }
        
        // Clamp to bounds using actual dimensions
        node.x = Math.max(halfWidth, Math.min(bounds.width - halfWidth, node.x));
        node.y = Math.max(halfHeight, Math.min(bounds.height - halfHeight, node.y));
        
        // Eject from obstacles
        // All nodes must stay out of obstacle interiors (child cuts)
        for (const obs of obstacles) {
            const obsLeft = obs.x - obs.width / 2;
            const obsRight = obs.x + obs.width / 2;
            const obsTop = obs.y - obs.height / 2;
            const obsBottom = obs.y + obs.height / 2;
            
            if (node.x + halfWidth > obsLeft && node.x - halfWidth < obsRight &&
                node.y + halfHeight > obsTop && node.y - halfHeight < obsBottom) {
                
                // Node is inside obstacle - must eject to valid space
                const distLeft = node.x - obsLeft;
                const distRight = obsRight - node.x;
                const distTop = node.y - obsTop;
                const distBottom = obsBottom - node.y;
                
                // Try each direction and check if it's valid (within bounds)
                const candidates = [
                    {dir: 'left', x: obsLeft - halfWidth - 1, y: node.y, valid: obsLeft - halfWidth - 1 >= halfWidth},
                    {dir: 'right', x: obsRight + halfWidth + 1, y: node.y, valid: obsRight + halfWidth + 1 <= bounds.width - halfWidth},
                    {dir: 'top', x: node.x, y: obsTop - halfHeight - 1, valid: obsTop - halfHeight - 1 >= halfHeight},
                    {dir: 'bottom', x: node.x, y: obsBottom + halfHeight + 1, valid: obsBottom + halfHeight + 1 <= bounds.height - halfHeight}
                ];
                
                // Sort by distance, prefer valid positions
                const minDist = Math.min(distLeft, distRight, distTop, distBottom);
                let ejected = false;
                
                // Try closest valid direction first
                for (const c of candidates) {
                    const dist = c.dir === 'left' ? distLeft : 
                                c.dir === 'right' ? distRight :
                                c.dir === 'top' ? distTop : distBottom;
                    
                    if (dist === minDist && c.valid) {
                        node.x = c.x;
                        node.y = c.y;
                        ejected = true;
                        break;
                    }
                }
                
                // If closest isn't valid, use any valid direction
                if (!ejected) {
                    for (const c of candidates) {
                        if (c.valid) {
                            node.x = c.x;
                            node.y = c.y;
                            ejected = true;
                            break;
                        }
                    }
                }
                
                // Final clamp (should be no-op if ejection worked)
                node.x = Math.max(halfWidth, Math.min(bounds.width - halfWidth, node.x));
                node.y = Math.max(halfHeight, Math.min(bounds.height - halfHeight, node.y));
            }
        }
    }
    
    const positions = {};
    for (const node of simNodes) {
        // Include all nodes except obstacles (pinned nodes should be returned!)
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
 * Apply absolute containment - runs AFTER velocity integration on each tick.
 * This ensures no force can override spatial/logical correspondence.
 */
function applyAbsoluteContainment(nodes, bounds, obstacles, nodesConnectedToPorts) {
    for (const node of nodes) {
        if (node.fx !== undefined || node.fy !== undefined) continue;
        if (node.type === 'obstacle' || node.type === 'port') continue;
        
        // Use actual dimensions for spatial/logical correspondence
        let halfWidth, halfHeight;
        const safetyMargin = 5;  // Moderate margin - allows proximity when needed
        if (node.width !== undefined && node.height !== undefined) {
            halfWidth = node.width / 2 + safetyMargin;
            halfHeight = node.height / 2 + safetyMargin;
        } else {
            const radius = node.type === 'vertex' ? 15 : (node.type === 'edge_label' ? 30 : 10);
            halfWidth = halfHeight = radius;
        }
        
        // 1. Clamp to bounds
        const oldX = node.x;
        node.x = Math.max(halfWidth, Math.min(bounds.width - halfWidth, node.x));
        node.y = Math.max(halfHeight, Math.min(bounds.height - halfHeight, node.y));
        
        // 2. Eject from obstacles
        // All nodes must stay out of obstacle interiors (cuts)
        for (const obs of obstacles) {
            const obsLeft = obs.x - obs.width / 2;
            const obsRight = obs.x + obs.width / 2;
            const obsTop = obs.y - obs.height / 2;
            const obsBottom = obs.y + obs.height / 2;
            
            if (node.x + halfWidth > obsLeft && node.x - halfWidth < obsRight &&
                node.y + halfHeight > obsTop && node.y - halfHeight < obsBottom) {
                
                // Node overlaps obstacle - eject to nearest edge
                const distLeft = node.x - obsLeft;
                const distRight = obsRight - node.x;
                const distTop = node.y - obsTop;
                const distBottom = obsBottom - node.y;
                
                const minDist = Math.min(distLeft, distRight, distTop, distBottom);
                
                if (minDist === distLeft) {
                    node.x = obsLeft - halfWidth - 1;
                } else if (minDist === distRight) {
                    node.x = obsRight + halfWidth + 1;
                } else if (minDist === distTop) {
                    node.y = obsTop - halfHeight - 1;
                } else {
                    node.y = obsBottom + halfHeight + 1;
                }
            }
        }
    }
}

/**
 * Custom containment force - IRREVOCABLY binds nodes to container.
 * 
 * This is the key innovation: on every tick, clamp node positions
 * to stay within the container bounds AND outside obstacle zones.
 * 
 * CRITICAL: No force can override this. Elements MUST stay in their area.
 */
function forceContainment(bounds, obstacles) {
    let nodes;
    
    function force(alpha) {
        for (let i = 0; i < nodes.length; i++) {
            const node = nodes[i];
            
            if (node.fx !== undefined || node.fy !== undefined) {
                continue;  // Skip pinned nodes
            }
            
            if (node.type === 'obstacle' || node.type === 'port') {
                continue;  // Skip obstacles and ports
            }
            
            // Determine node dimensions - use actual size for spatial/logical correspondence
            let halfWidth, halfHeight;
            const safetyMargin = 3;  // Breathing room for spatial/logical clarity
            if (node.width !== undefined && node.height !== undefined) {
                halfWidth = node.width / 2 + safetyMargin;
                halfHeight = node.height / 2 + safetyMargin;
            } else {
                // Fallback for nodes without dimensions
                const radius = node.type === 'vertex' ? 15 : (node.type === 'edge_label' ? 30 : 10);
                halfWidth = halfHeight = radius;
            }
            
            // 1. Clamp to container bounds
            // CRITICAL: Also zero velocity to prevent drift back into forbidden zones
            if (node.x - halfWidth < 0) {
                node.x = halfWidth;
                node.vx = 0;  // Stop horizontal movement
            } else if (node.x + halfWidth > bounds.width) {
                node.x = bounds.width - halfWidth;
                node.vx = 0;  // Stop horizontal movement
            }
            
            if (node.y - halfHeight < 0) {
                node.y = halfHeight;
                node.vy = 0;  // Stop vertical movement
            } else if (node.y + halfHeight > bounds.height) {
                node.y = bounds.height - halfHeight;
                node.vy = 0;  // Stop vertical movement
            }
            
            // 2. HARD EXCLUSION: Eject from obstacle zones
            for (const obs of obstacles) {
                const obsLeft = obs.x - obs.width / 2;
                const obsRight = obs.x + obs.width / 2;
                const obsTop = obs.y - obs.height / 2;
                const obsBottom = obs.y + obs.height / 2;
                
                // Check if node overlaps obstacle (with actual dimensions)
                if (node.x + halfWidth > obsLeft && 
                    node.x - halfWidth < obsRight &&
                    node.y + halfHeight > obsTop && 
                    node.y - halfHeight < obsBottom) {
                    
                    // Node is inside obstacle - eject to nearest edge
                    const distLeft = node.x - obsLeft;
                    const distRight = obsRight - node.x;
                    const distTop = node.y - obsTop;
                    const distBottom = obsBottom - node.y;
                    
                    const minDist = Math.min(distLeft, distRight, distTop, distBottom);
                    
                    // Eject and STOP movement toward obstacle
                    if (minDist === distLeft && distLeft > 0) {
                        node.x = obsLeft - halfWidth - 1;  // Push left (using actual width)
                        node.vx = 0;  // Stop horizontal drift
                    } else if (minDist === distRight && distRight > 0) {
                        node.x = obsRight + halfWidth + 1;  // Push right (using actual width)
                        node.vx = 0;  // Stop horizontal drift
                    } else if (minDist === distTop && distTop > 0) {
                        node.y = obsTop - halfHeight - 1;  // Push up (using actual height)
                        node.vy = 0;  // Stop vertical drift
                    } else if (minDist === distBottom && distBottom > 0) {
                        node.y = obsBottom + halfHeight + 1;  // Push down (using actual height)
                        node.vy = 0;  // Stop vertical drift
                    }
                }
            }
        }
    }
    
    force.initialize = function(_) {
        nodes = _;
    };
    
    return force;
}
