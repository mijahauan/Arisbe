#!/usr/bin/env node

/**
 * Unified D3 Layout Worker - DEFINITIVE SIMPLE VERSION
 * 
 * THREE FORCES, ZERO CONFLICTS:
 * 1. Link (attraction)
 * 2. Collision (repulsion)
 * 3. Walls (containment)
 * 
 * NO competing forces, NO post-processing complexity
 * Just a dumb physics engine that finds the lowest energy state
 * 
 * Author: Final simplification
 * Date: 2025-10-12
 */

const d3 = require('d3-force');

// Read input from stdin
let inputData = '';
process.stdin.on('data', chunk => { inputData += chunk; });
process.stdin.on('end', () => {
    try {
        const payload = JSON.parse(inputData);
        const result = layoutSingleCut(payload);
        console.log(JSON.stringify(result));
    } catch (error) {
        console.error(`D3 Worker ERROR: ${error.message}`);
        console.error(error.stack);
        process.exit(1);
    }
});

/**
 * Layout a single cut's contents - SHELL-AND-CORE MODEL
 * 
 * TWO SIMULATIONS, ZERO CONFLICTS:
 * 1. SHELL: Layout obstacles (child cuts) - arrange large boxes
 * 2. CORE: Layout content - with obstacles as fixed no-go zones
 * 
 * This eliminates the force-fighting problem entirely.
 */
function layoutSingleCut(payload) {
    const { content, obstacles, links, bounds, seed } = payload;
    
    // Seeded random for determinism
    let randomSeed = seed !== undefined ? seed : Date.now();
    function seededRandom() {
        const x = Math.sin(randomSeed++) * 10000;
        return x - Math.floor(x);
    }
    
    const centerX = bounds.width / 2;
    const centerY = bounds.height / 2;
    const margin = 30;
    
    // ========================================================================
    // PHASE 1: SHELL - Layout obstacles (child cuts) only
    // ========================================================================
    
    let obstaclePositions = {};
    
    if (obstacles.length > 0) {
        console.error(`  SHELL: Laying out ${obstacles.length} child cuts...`);
        
        const shellNodes = obstacles.map(obst => ({
            id: obst.id,
            width: obst.width,
            height: obst.height,
            x: centerX + (seededRandom() - 0.5) * 60,
            y: centerY + (seededRandom() - 0.5) * 60
        }));
        
        const shellSim = d3.forceSimulation(shellNodes)
            .force('collision', d3.forceCollide()
                .radius(d => Math.sqrt(d.width * d.width + d.height * d.height) / 2 + 10)
                .strength(1.0)
                .iterations(5)
            )
            .force('center', d3.forceCenter(centerX, centerY).strength(0.05))
            .force('walls', forceWalls(bounds, margin));
        
        shellSim.stop();
        for (let i = 0; i < 200; ++i) shellSim.tick();
        
        // Store obstacle positions
        for (const node of shellNodes) {
            obstaclePositions[node.id] = { x: node.x, y: node.y };
        }
        
        console.error(`  SHELL: Complete`);
    }
    
    // ========================================================================
    // PHASE 2: CORE - Layout content with obstacles as no-go zones
    // ========================================================================
    
    console.error(`  CORE: Laying out ${content.length} content elements...`);
    
    const coreNodes = content.map(node => ({
        id: node.id,
        type: node.type,
        label: node.label,
        width: node.width || 30,
        height: node.height || 30,
        x: centerX + (seededRandom() - 0.5) * 80,
        y: centerY + (seededRandom() - 0.5) * 80,
        fx: node.fx,
        fy: node.fy
    }));
    
    // Build fixed obstacle representations
    const fixedObstacles = obstacles.map(obst => ({
        ...obstaclePositions[obst.id],
        width: obst.width,
        height: obst.height
    }));
    
    const coreLinks = links.map(link => ({
        source: link.source,
        target: link.target
    }));
    
    const coreSim = d3.forceSimulation(coreNodes)
        .force('link', d3.forceLink(coreLinks)
            .id(d => d.id)
            .distance(40)
            .strength(0.5)
        )
        .force('collision', d3.forceCollide()
            .radius(d => Math.sqrt(d.width * d.width + d.height * d.height) / 2 + 5)
            .strength(0.8)
            .iterations(3)
        )
        .force('walls', forceWalls(bounds, margin))
        .force('obstacleAvoidance', forceObstacleAvoidance(fixedObstacles));
    
    coreSim.stop();
    for (let i = 0; i < 300; ++i) coreSim.tick();
    
    console.error(`  CORE: Complete`);
    
    // ========================================================================
    // COMBINE RESULTS
    // ========================================================================
    
    const positions = {};
    
    // Add obstacle positions
    for (const [id, pos] of Object.entries(obstaclePositions)) {
        positions[id] = pos;
    }
    
    // Add content positions
    for (const node of coreNodes) {
        positions[node.id] = { x: node.x, y: node.y };
    }
    
    // Calculate bbox including all elements
    const allNodes = [...obstacles.map(o => ({
        ...obstaclePositions[o.id],
        width: o.width,
        height: o.height
    })), ...coreNodes];
    
    const bbox = calculateTightBbox(allNodes);
    
    return { positions, bbox };
}

/**
 * Simple Wall Force - Clamp to boundaries
 */
function forceWalls(bounds, margin) {
    let nodes;
    
    const minX = margin;
    const minY = margin;
    const maxX = bounds.width - margin;
    const maxY = bounds.height - margin;
    
    function force() {
        for (const node of nodes) {
            if (node.fx !== undefined) continue;
            
            const hw = node.width / 2;
            const hh = node.height / 2;
            
            if (node.x - hw < minX) node.x = minX + hw;
            if (node.x + hw > maxX) node.x = maxX - hw;
            if (node.y - hh < minY) node.y = minY + hh;
            if (node.y + hh > maxY) node.y = maxY - hh;
        }
    }
    
    force.initialize = function(_) {
        nodes = _;
    };
    
    return force;
}

/**
 * Obstacle Avoidance Force - GENTLE REPULSION FROM NO-GO ZONES
 * 
 * Fixed obstacles act as repelling forces, not instant ejection.
 * This works WITH the other forces, not against them.
 */
function forceObstacleAvoidance(fixedObstacles) {
    let nodes;
    
    function force(alpha) {
        for (const node of nodes) {
            if (node.fx !== undefined) continue;
            
            for (const obstacle of fixedObstacles) {
                // Calculate distance from node center to obstacle center
                const dx = node.x - obstacle.x;
                const dy = node.y - obstacle.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                if (dist < 1) continue;  // Avoid division by zero
                
                // Calculate minimum safe distance (sum of half-sizes)
                const nodeRadius = Math.sqrt(node.width * node.width + node.height * node.height) / 2;
                const obstRadius = Math.sqrt(obstacle.width * obstacle.width + obstacle.height * obstacle.height) / 2;
                const minDist = nodeRadius + obstRadius + 10;  // 10px buffer
                
                // If too close, apply repulsive force
                if (dist < minDist) {
                    const strength = 0.5 * alpha;  // Gentle, continuous force
                    const force = strength * (minDist - dist) / dist;
                    
                    node.vx += dx * force;
                    node.vy += dy * force;
                }
            }
        }
    }
    
    force.initialize = function(_) {
        nodes = _;
    };
    
    return force;
}

/**
 * Calculate tight bbox - Include all elements (content + obstacles)
 * 
 * The parent bbox must encompass child cuts (obstacles) so they nest visually.
 */
function calculateTightBbox(nodes) {
    let min_x = Infinity;
    let min_y = Infinity;
    let max_x = -Infinity;
    let max_y = -Infinity;
    
    for (const node of nodes) {
        const hw = (node.width || 30) / 2;
        const hh = (node.height || 30) / 2;
        
        min_x = Math.min(min_x, node.x - hw);
        min_y = Math.min(min_y, node.y - hh);
        max_x = Math.max(max_x, node.x + hw);
        max_y = Math.max(max_y, node.y + hh);
    }
    
    // Add padding
    const padding = 25;
    min_x -= padding;
    min_y -= padding;
    max_x += padding;
    max_y += padding;
    
    return { min_x, min_y, max_x, max_y };
}
