// Authentic Existential Graph Editor

class AuthenticEGEditor {
    constructor() {
        this.canvas = document.getElementById('eg-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.currentTool = 'select';
        this.graph = null;
        this.selectedElement = null;
        this.ligatureStart = null;
        
        this.setupEventListeners();
        this.loadGraph();
        this.loadExamples();
        this.startUpdateLoop();
    }
    
    setupEventListeners() {
        // Tool selection
        document.querySelectorAll('input[name="tool"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentTool = e.target.value;
                this.updateStatus(`${this.currentTool} mode selected`);
            });
        });
        
        // Canvas events
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        this.canvas.addEventListener('contextmenu', (e) => this.handleRightClick(e));
        
        // Buttons
        document.getElementById('validate-btn').addEventListener('click', () => this.validateGraph());
        document.getElementById('clear-btn').addEventListener('click', () => this.clearGraph());
        document.getElementById('help-btn').addEventListener('click', () => this.showHelp());
        
        // Example selector
        document.getElementById('example-selector').addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadExample(e.target.value);
            }
        });
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
        
        if (this.currentTool === 'entity') {
            this.addEntity(pos.x, pos.y);
        } else if (this.currentTool === 'predicate') {
            this.addPredicate(pos.x, pos.y);
        } else if (this.currentTool === 'cut') {
            this.addCut(pos.x, pos.y);
        } else if (this.currentTool === 'ligature') {
            this.handleLigatureClick(pos.x, pos.y);
        } else if (this.currentTool === 'select') {
            this.selectElement(pos.x, pos.y);
        }
    }
    
    handleRightClick(e) {
        e.preventDefault();
        // Context menu functionality
    }
    
    async addEntity(x, y) {
        const name = prompt('Entity name:', 'x');
        if (!name) return;
        
        try {
            const response = await fetch('/api/add_element', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    type: 'entity',
                    x: x,
                    y: y,
                    name: name
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
                this.updateStatus(`Added entity "${name}"`);
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Error adding entity:', error);
        }
    }
    
    async addPredicate(x, y) {
        const name = prompt('Predicate name:', 'P');
        if (!name) return;
        
        const arity = parseInt(prompt('Arity (number of arguments):', '1') || '1');
        
        try {
            const response = await fetch('/api/add_element', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    type: 'predicate',
                    x: x,
                    y: y,
                    name: name,
                    arity: arity
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
                this.updateStatus(`Added predicate "${name}"`);
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Error adding predicate:', error);
        }
    }
    
    async addCut(x, y) {
        try {
            const response = await fetch('/api/add_element', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    type: 'cut',
                    x: x,
                    y: y,
                    width: 200,
                    height: 150
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
                this.updateStatus('Added cut');
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Error adding cut:', error);
        }
    }
    
    handleLigatureClick(x, y) {
        const entity = this.findEntityAt(x, y);
        if (!entity) {
            this.updateStatus('Click on an entity to create ligature');
            return;
        }
        
        if (!this.ligatureStart) {
            this.ligatureStart = entity.id;
            this.updateStatus(`Selected entity "${entity.name}" - click another entity to connect`);
        } else {
            this.addLigature(this.ligatureStart, entity.id);
            this.ligatureStart = null;
        }
    }
    
    async addLigature(entity1_id, entity2_id) {
        try {
            const response = await fetch('/api/add_ligature', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    entity1_id: entity1_id,
                    entity2_id: entity2_id
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
                this.updateStatus('Added ligature (line of identity)');
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Error adding ligature:', error);
        }
    }
    
    findEntityAt(x, y) {
        if (!this.graph || !this.graph.entities) return null;
        
        for (const [id, entity] of Object.entries(this.graph.entities)) {
            const dx = x - entity.position.x;
            const dy = y - entity.position.y;
            if (Math.sqrt(dx*dx + dy*dy) <= 10) { // 10px radius
                return {id, ...entity};
            }
        }
        return null;
    }
    
    selectElement(x, y) {
        // Find element at position
        const entity = this.findEntityAt(x, y);
        if (entity) {
            this.selectedElement = {type: 'entity', ...entity};
            this.updateStatus(`Selected entity "${entity.name}"`);
            return;
        }
        
        // Check predicates
        if (this.graph && this.graph.predicates) {
            for (const [id, predicate] of Object.entries(this.graph.predicates)) {
                const bounds = this.getPredicateBounds(predicate);
                if (x >= bounds.x && x <= bounds.x + bounds.width &&
                    y >= bounds.y && y <= bounds.y + bounds.height) {
                    this.selectedElement = {type: 'predicate', id, ...predicate};
                    this.updateStatus(`Selected predicate "${predicate.name}"`);
                    return;
                }
            }
        }
        
        this.selectedElement = null;
        this.updateStatus('No element selected');
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
    
    async loadExamples() {
        try {
            const response = await fetch('/api/examples');
            const data = await response.json();
            
            const selector = document.getElementById('example-selector');
            data.examples.forEach(example => {
                const option = document.createElement('option');
                option.value = example.id;
                option.textContent = example.title;
                selector.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading examples:', error);
        }
    }
    
    async loadExample(exampleId) {
        try {
            const response = await fetch('/api/load_example', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({example_id: exampleId})
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
                this.updateStatus(`Loaded example: ${exampleId}`);
            } else {
                alert('Error loading example: ' + result.error);
            }
        } catch (error) {
            console.error('Error loading example:', error);
        }
    }
    
    render() {
        if (!this.graph) return;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Render cuts (contexts)
        this.renderCuts();
        
        // Render ligatures (lines of identity)
        this.renderLigatures();
        
        // Render predicates
        this.renderPredicates();
        
        // Render entities
        this.renderEntities();
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
    
    renderLigatures() {
        if (!this.graph.ligatures || !this.graph.entities) return;
        
        Object.values(this.graph.ligatures).forEach(ligature => {
            const entity1 = this.graph.entities[ligature.entity1_id];
            const entity2 = this.graph.entities[ligature.entity2_id];
            
            if (entity1 && entity2) {
                this.ctx.save();
                this.ctx.strokeStyle = '#000';
                this.ctx.lineWidth = 2;
                
                this.ctx.beginPath();
                this.ctx.moveTo(entity1.position.x, entity1.position.y);
                this.ctx.lineTo(entity2.position.x, entity2.position.y);
                this.ctx.stroke();
                
                this.ctx.restore();
            }
        });
    }
    
    renderPredicates() {
        if (!this.graph.predicates) return;
        
        Object.values(this.graph.predicates).forEach(predicate => {
            const bounds = this.getPredicateBounds(predicate);
            
            this.ctx.save();
            
            // Draw oval
            this.ctx.strokeStyle = '#000';
            this.ctx.lineWidth = 1;
            this.ctx.fillStyle = '#fff';
            
            this.ctx.beginPath();
            this.ctx.ellipse(
                predicate.position.x,
                predicate.position.y,
                bounds.width/2,
                bounds.height/2,
                0, 0, 2 * Math.PI
            );
            this.ctx.fill();
            this.ctx.stroke();
            
            // Label
            this.ctx.fillStyle = '#000';
            this.ctx.font = '14px Times New Roman';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(predicate.name, predicate.position.x, predicate.position.y + 5);
            
            this.ctx.restore();
        });
    }
    
    renderEntities() {
        if (!this.graph.entities) return;
        
        Object.values(this.graph.entities).forEach(entity => {
            this.ctx.save();
            
            // Draw small circle (10px diameter as per corpus)
            this.ctx.strokeStyle = '#000';
            this.ctx.lineWidth = 2;
            this.ctx.fillStyle = '#fff';
            
            this.ctx.beginPath();
            this.ctx.arc(entity.position.x, entity.position.y, 5, 0, 2 * Math.PI);
            this.ctx.fill();
            this.ctx.stroke();
            
            // Label
            this.ctx.fillStyle = '#000';
            this.ctx.font = '12px Times New Roman';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(entity.name, entity.position.x, entity.position.y - 10);
            
            this.ctx.restore();
        });
    }
    
    updateInfo() {
        if (!this.graph) return;
        
        document.getElementById('entity-count').textContent = 
            Object.keys(this.graph.entities || {}).length;
        document.getElementById('predicate-count').textContent = 
            Object.keys(this.graph.predicates || {}).length;
        document.getElementById('cut-count').textContent = 
            Object.keys(this.graph.cuts || {}).length - 1; // Exclude sheet
        document.getElementById('ligature-count').textContent = 
            Object.keys(this.graph.ligatures || {}).length;
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
        alert(`Authentic Existential Graph Editor

Tools:
• Entity: Small points (10px) representing individuals
• Predicate: Ovals with text labels for relations
• Cut: Oval contexts for negation (cannot overlap!)
• Ligature: Lines of identity connecting entities
• Select: Select and inspect elements

Visual Conventions:
• Based on corpus examples from Peirce, Sowa, Roberts, Dau
• Entities are small circles with variable names
• Predicates are ovals with concept names
• Cuts are nested ovals (no overlapping allowed)
• Ligatures are lines connecting entities

Examples:
• Load corpus examples from the dropdown
• Includes Peirce's classic man-mortal implication
• All examples follow authentic EG semantics`);
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
    window.egEditor = new AuthenticEGEditor();
    console.log('Authentic EG Editor initialized');
});