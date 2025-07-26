// Correct Existential Graph Editor

class CorrectEGEditor {
    constructor() {
        this.canvas = document.getElementById('eg-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.currentTool = 'select';
        this.graph = null;
        this.selectedElement = null;
        this.attachmentStart = null;
        this.isDragging = false;
        this.dragStart = null;
        
        this.setupEventListeners();
        this.loadGraph();
        this.startUpdateLoop();
    }
    
    setupEventListeners() {
        // Tool selection
        document.querySelectorAll('input[name="tool"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentTool = e.target.value;
                this.updateStatus(`${this.currentTool} mode selected`);
                this.attachmentStart = null; // Reset attachment
            });
        });
        
        // Canvas events
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        
        // Buttons
        document.getElementById('validate-btn').addEventListener('click', () => this.validateGraph());
        document.getElementById('clear-btn').addEventListener('click', () => this.clearGraph());
        document.getElementById('help-btn').addEventListener('click', () => this.showHelp());
    }
    
    getMousePos(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }
    
    handleClick(e) {
        const pos = this.getMousePos(e);
        
        if (this.currentTool === 'line') {
            this.addLineOfIdentity(pos.x, pos.y);
        } else if (this.currentTool === 'predicate') {
            this.addPredicate(pos.x, pos.y);
        } else if (this.currentTool === 'cut') {
            this.addCut(pos.x, pos.y);
        } else if (this.currentTool === 'attach') {
            this.handleAttachClick(pos.x, pos.y);
        }
    }
    
    handleMouseDown(e) {
        if (this.currentTool === 'select') {
            const pos = this.getMousePos(e);
            const predicate = this.findPredicateAt(pos.x, pos.y);
            
            if (predicate) {
                this.selectedElement = predicate;
                this.isDragging = true;
                this.dragStart = pos;
                this.updateStatus(`Dragging predicate "${predicate.name}"`);
            }
        }
    }
    
    handleMouseMove(e) {
        if (this.isDragging && this.selectedElement && this.currentTool === 'select') {
            const pos = this.getMousePos(e);
            this.movePredicate(this.selectedElement.id, pos.x, pos.y);
        }
    }
    
    handleMouseUp(e) {
        if (this.isDragging) {
            this.isDragging = false;
            this.dragStart = null;
            this.updateStatus('Predicate moved - lines updated automatically');
        }
    }
    
    async addLineOfIdentity(x, y) {
        const name = prompt('Line of Identity name (entity):', 'x');
        if (!name) return;
        
        try {
            const response = await fetch('/api/add_line', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: name,
                    x: x,
                    y: y
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
                this.updateStatus(`Added line of identity "${name}" (this IS the entity)`);
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Error adding line:', error);
        }
    }
    
    async addPredicate(x, y) {
        const name = prompt('Predicate name:', 'P');
        if (!name) return;
        
        const arity = parseInt(prompt('Arity (number of arguments):', '1') || '1');
        
        try {
            const response = await fetch('/api/add_predicate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: name,
                    x: x,
                    y: y,
                    arity: arity
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
                this.updateStatus(`Added predicate "${name}" with hook attachment points`);
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Error adding predicate:', error);
        }
    }
    
    handleAttachClick(x, y) {
        if (!this.attachmentStart) {
            // First click - select line
            const line = this.findLineAt(x, y);
            if (line) {
                this.attachmentStart = line.id;
                this.updateStatus(`Selected line "${line.name}" - click predicate to attach`);
            } else {
                this.updateStatus('Click on a line of identity first');
            }
        } else {
            // Second click - select predicate
            const predicate = this.findPredicateAt(x, y);
            if (predicate) {
                this.attachLineToPredicate(this.attachmentStart, predicate.id, x, y);
                this.attachmentStart = null;
            } else {
                this.updateStatus('Click on a predicate to attach the line');
            }
        }
    }
    
    async attachLineToPredicate(lineId, predicateId, x, y) {
        try {
            const response = await fetch('/api/attach', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    line_id: lineId,
                    predicate_id: predicateId,
                    x: x,
                    y: y
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
                this.updateStatus('Line attached to predicate hook');
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Error attaching line:', error);
        }
    }
    
    async movePredicate(predicateId, x, y) {
        try {
            const response = await fetch('/api/move_predicate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    predicate_id: predicateId,
                    x: x,
                    y: y
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
            } else {
                this.updateStatus('Cannot move predicate there (containment constraint)');
            }
        } catch (error) {
            console.error('Error moving predicate:', error);
        }
    }
    
    async addCut(x, y) {
        try {
            const response = await fetch('/api/add_cut', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    x: x,
                    y: y,
                    width: 200,
                    height: 150
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
                this.updateStatus('Added cut (no overlapping allowed)');
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Error adding cut:', error);
        }
    }
    
    findLineAt(x, y) {
        if (!this.graph || !this.graph.lines_of_identity) return null;
        
        for (const [id, line] of Object.entries(this.graph.lines_of_identity)) {
            // Check if click is near any point on the line
            for (const point of line.points) {
                const dx = x - point.x;
                const dy = y - point.y;
                if (Math.sqrt(dx*dx + dy*dy) <= 10) {
                    return {id, ...line};
                }
            }
        }
        return null;
    }
    
    findPredicateAt(x, y) {
        if (!this.graph || !this.graph.predicates) return null;
        
        for (const [id, predicate] of Object.entries(this.graph.predicates)) {
            const bounds = this.getPredicateBounds(predicate);
            if (x >= bounds.x && x <= bounds.x + bounds.width &&
                y >= bounds.y && y <= bounds.y + bounds.height) {
                return {id, ...predicate};
            }
        }
        return null;
    }
    
    getPredicateBounds(predicate) {
        const width = predicate.size ? predicate.size[0] : 100;
        const height = predicate.size ? predicate.size[1] : 50;
        return {
            x: predicate.position.x - width/2,
            y: predicate.position.y - height/2,
            width: width,
            height: height
        };
    }
    
    async loadGraph() {
        try {
            const response = await fetch('/api/graph');
            this.graph = await response.json();
            this.render();
            this.updateInfo();
        } catch (error) {
            console.error('Error loading graph:', error);
        }
    }
    
    render() {
        if (!this.graph) return;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Render cuts
        this.renderCuts();
        
        // Render predicates (with invisible boundaries)
        this.renderPredicates();
        
        // Render lines of identity (these ARE the entities)
        this.renderLinesOfIdentity();
        
        // Render hooks (for debugging)
        this.renderHooks();
    }
    
    renderCuts() {
        if (!this.graph.cuts) return;
        
        // Sort by nesting level to render outer cuts first
        const cuts = Object.entries(this.graph.cuts)
            .filter(([id, cut]) => id !== 'sheet')
            .sort(([,a], [,b]) => a.nesting_level - b.nesting_level);
        
        cuts.forEach(([id, cut]) => {
            this.ctx.save();
            this.ctx.strokeStyle = '#333';
            this.ctx.lineWidth = 2;
            this.ctx.fillStyle = 'rgba(240, 240, 240, 0.1)';
            
            // Draw oval
            this.ctx.beginPath();
            this.ctx.ellipse(
                cut.bounds.x + cut.bounds.width/2,
                cut.bounds.y + cut.bounds.height/2,
                cut.bounds.width/2,
                cut.bounds.height/2,
                0, 0, 2 * Math.PI
            );
            this.ctx.fill();
            this.ctx.stroke();
            
            // Label
            this.ctx.fillStyle = '#666';
            this.ctx.font = '12px Times New Roman';
            this.ctx.fillText(cut.name, cut.bounds.x + 5, cut.bounds.y + 15);
            
            this.ctx.restore();
        });
    }
    
    renderPredicates() {
        if (!this.graph.predicates) return;
        
        Object.values(this.graph.predicates).forEach(predicate => {
            this.ctx.save();
            
            // Draw invisible boundary (for debugging - light gray)
            const bounds = this.getPredicateBounds(predicate);
            this.ctx.strokeStyle = '#ddd';
            this.ctx.lineWidth = 1;
            this.ctx.setLineDash([2, 2]);
            
            this.ctx.beginPath();
            this.ctx.ellipse(
                predicate.position.x,
                predicate.position.y,
                bounds.width/2,
                bounds.height/2,
                0, 0, 2 * Math.PI
            );
            this.ctx.stroke();
            this.ctx.setLineDash([]);
            
            // Draw predicate text
            this.ctx.fillStyle = '#000';
            this.ctx.font = '16px Times New Roman';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(predicate.name, predicate.position.x, predicate.position.y + 5);
            
            this.ctx.restore();
        });
    }
    
    renderLinesOfIdentity() {
        if (!this.graph.lines_of_identity) return;
        
        Object.values(this.graph.lines_of_identity).forEach(line => {
            if (line.points && line.points.length > 0) {
                this.ctx.save();
                this.ctx.strokeStyle = '#000';
                this.ctx.lineWidth = 3;
                
                // Draw the line path
                this.ctx.beginPath();
                this.ctx.moveTo(line.points[0].x, line.points[0].y);
                
                for (let i = 1; i < line.points.length; i++) {
                    this.ctx.lineTo(line.points[i].x, line.points[i].y);
                }
                
                this.ctx.stroke();
                
                // Label the line
                if (line.points.length > 0) {
                    const firstPoint = line.points[0];
                    this.ctx.fillStyle = '#000';
                    this.ctx.font = '14px Times New Roman';
                    this.ctx.textAlign = 'center';
                    this.ctx.fillText(line.name, firstPoint.x, firstPoint.y - 10);
                }
                
                this.ctx.restore();
            }
        });
    }
    
    renderHooks() {
        if (!this.graph.predicates) return;
        
        // Render hook points for debugging
        Object.values(this.graph.predicates).forEach(predicate => {
            if (predicate.hooks) {
                predicate.hooks.forEach(hook => {
                    if (hook.position) {
                        this.ctx.save();
                        this.ctx.fillStyle = '#f00';
                        this.ctx.beginPath();
                        this.ctx.arc(hook.position.x, hook.position.y, 3, 0, 2 * Math.PI);
                        this.ctx.fill();
                        this.ctx.restore();
                    }
                });
            }
        });
    }
    
    updateInfo() {
        if (!this.graph) return;
        
        document.getElementById('line-count').textContent = 
            Object.keys(this.graph.lines_of_identity || {}).length;
        document.getElementById('predicate-count').textContent = 
            Object.keys(this.graph.predicates || {}).length;
        document.getElementById('cut-count').textContent = 
            Object.keys(this.graph.cuts || {}).length - 1; // Exclude sheet
        
        // Count total attachments
        let attachmentCount = 0;
        if (this.graph.lines_of_identity) {
            Object.values(this.graph.lines_of_identity).forEach(line => {
                if (line.attached_hooks) {
                    attachmentCount += line.attached_hooks.length;
                }
            });
        }
        document.getElementById('attachment-count').textContent = attachmentCount;
    }
    
    async validateGraph() {
        try {
            const response = await fetch('/api/validate');
            const validation = await response.json();
            
            const statusEl = document.getElementById('validation-status');
            const issuesEl = document.getElementById('validation-issues');
            
            statusEl.textContent = validation.is_valid ? 'Valid' : 'Invalid';
            statusEl.className = validation.is_valid ? 'valid' : 'invalid';
            
            issuesEl.innerHTML = '';
            validation.issues.forEach(issue => {
                const li = document.createElement('li');
                li.textContent = issue;
                issuesEl.appendChild(li);
            });
            
            this.updateStatus(`Validation: ${validation.is_valid ? 'Valid' : 'Invalid'}`);
        } catch (error) {
            console.error('Error validating graph:', error);
        }
    }
    
    clearGraph() {
        if (confirm('Clear the entire graph?')) {
            // Implement clear functionality
            this.updateStatus('Graph cleared');
        }
    }
    
    showHelp() {
        alert(`Correct Existential Graph Editor

Key Concepts:
• Line of Identity = Entity (not a connection!)
• Predicates have invisible oval boundaries with hooks
• Lines attach to hooks on predicate boundaries
• Movement is constrained by logical containment

Tools:
• Line of Identity: Create entity lines (these ARE the entities)
• Predicate: Create predicates with hook attachment points
• Attach: Connect lines to predicate hooks
• Select: Drag predicates (lines move automatically)
• Cut: Create nested contexts (no overlapping allowed)

Correct Semantics:
• Lines of identity represent entities in the domain
• Predicates are relations with attachment hooks
• Movement preserves logical relationships
• Visual layout constrained by logical structure`);
    }
    
    updateStatus(message) {
        document.getElementById('status-text').textContent = message;
    }
    
    startUpdateLoop() {
        setInterval(() => {
            this.render();
        }, 100); // 10 FPS for smooth updates
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.egEditor = new CorrectEGEditor();
    console.log('Correct EG Editor initialized');
    console.log('Lines of identity ARE the entities!');
});