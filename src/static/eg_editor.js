// Existential Graph Editor - Interactive Functionality

class EGEditor {
    constructor() {
        this.canvas = document.getElementById('eg-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.currentTool = 'select';
        this.elements = [];
        this.selectedElement = null;
        this.isDragging = false;
        this.dragStart = null;
        this.educationalMode = true;
        
        this.setupEventListeners();
        this.loadElements();
        this.startFeedbackUpdates();
    }
    
    setupEventListeners() {
        // Tool selection
        document.querySelectorAll('input[name="tool"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentTool = e.target.value;
                this.updateCanvasCursor();
                this.updateStatus(`${this.currentTool} mode selected`);
            });
        });
        
        // Canvas events
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('dblclick', (e) => this.handleDoubleClick(e));
        this.canvas.addEventListener('contextmenu', (e) => this.handleRightClick(e));
        
        // Button events
        document.getElementById('validate-btn').addEventListener('click', () => this.validateGraph());
        document.getElementById('clear-btn').addEventListener('click', () => this.clearGraph());
        document.getElementById('help-btn').addEventListener('click', () => this.showHelp());
        
        // Educational mode toggle
        document.getElementById('educational-mode').addEventListener('change', (e) => {
            this.educationalMode = e.target.checked;
            this.toggleEducationalMode(this.educationalMode);
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }
    
    updateCanvasCursor() {
        this.canvas.className = `${this.currentTool}-mode`;
    }
    
    getMousePos(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }
    
    handleMouseDown(e) {
        const pos = this.getMousePos(e);
        
        if (this.currentTool === 'select') {
            const element = this.findElementAt(pos.x, pos.y);
            if (element) {
                this.selectedElement = element;
                this.isDragging = true;
                this.dragStart = pos;
                this.selectElement(element.id);
            } else {
                this.selectedElement = null;
            }
        } else {
            this.createElement(this.currentTool, pos.x, pos.y);
        }
        
        this.render();
    }
    
    handleMouseMove(e) {
        const pos = this.getMousePos(e);
        
        if (this.isDragging && this.selectedElement) {
            const dx = pos.x - this.dragStart.x;
            const dy = pos.y - this.dragStart.y;
            
            this.moveElement(this.selectedElement.id, dx, dy);
            this.dragStart = pos;
        }
        
        // Update status with position
        const element = this.findElementAt(pos.x, pos.y);
        if (element) {
            this.updateStatus(`${element.type}: ${element.label} at (${Math.round(pos.x)}, ${Math.round(pos.y)})`);
        } else {
            this.updateStatus(`Position: (${Math.round(pos.x)}, ${Math.round(pos.y)}) - Tool: ${this.currentTool}`);
        }
    }
    
    handleMouseUp(e) {
        this.isDragging = false;
        this.dragStart = null;
    }
    
    handleDoubleClick(e) {
        const pos = this.getMousePos(e);
        const element = this.findElementAt(pos.x, pos.y);
        
        if (element) {
            const newLabel = prompt(`Edit ${element.type} label:`, element.label);
            if (newLabel && newLabel !== element.label) {
                this.editElement(element.id, newLabel);
            }
        }
    }
    
    handleRightClick(e) {
        e.preventDefault();
        const pos = this.getMousePos(e);
        const element = this.findElementAt(pos.x, pos.y);
        
        if (element) {
            this.showElementContextMenu(element, e.clientX, e.clientY);
        } else {
            this.showCanvasContextMenu(pos.x, pos.y, e.clientX, e.clientY);
        }
    }
    
    handleKeyDown(e) {
        if (e.ctrlKey && e.key === 'a') {
            e.preventDefault();
            this.selectAll();
        } else if (e.key === 'Delete' && this.selectedElement) {
            this.deleteElement(this.selectedElement.id);
        } else if (e.key === 'F1') {
            e.preventDefault();
            this.showHelp();
        }
    }
    
    findElementAt(x, y) {
        // Find element at position (simple bounding box check)
        for (let element of this.elements) {
            const bounds = element.bounds;
            if (x >= bounds.x && x <= bounds.x + bounds.width &&
                y >= bounds.y && y <= bounds.y + bounds.height) {
                return element;
            }
        }
        return null;
    }
    
    async createElement(type, x, y) {
        try {
            const response = await fetch('/api/input', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    action: 'create_element',
                    element_type: type,
                    x: x,
                    y: y
                })
            });
            
            const result = await response.json();
            if (result.success) {
                await this.loadElements();
                this.render();
            }
        } catch (error) {
            console.error('Error creating element:', error);
        }
    }
    
    async moveElement(elementId, dx, dy) {
        try {
            const response = await fetch('/api/input', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    action: 'move_element',
                    element_id: elementId,
                    dx: dx,
                    dy: dy
                })
            });
            
            const result = await response.json();
            if (result.success) {
                await this.loadElements();
                this.render();
            }
        } catch (error) {
            console.error('Error moving element:', error);
        }
    }
    
    async selectElement(elementId) {
        try {
            const response = await fetch('/api/input', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    action: 'select_element',
                    element_id: elementId
                })
            });
            
            const result = await response.json();
            if (result.success) {
                // Element selection feedback handled by server
            }
        } catch (error) {
            console.error('Error selecting element:', error);
        }
    }
    
    async deleteElement(elementId) {
        try {
            const response = await fetch('/api/input', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    action: 'delete_element',
                    element_id: elementId
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.selectedElement = null;
                await this.loadElements();
                this.render();
            }
        } catch (error) {
            console.error('Error deleting element:', error);
        }
    }
    
    async editElement(elementId, newLabel) {
        try {
            const response = await fetch('/api/input', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    action: 'edit_element',
                    element_id: elementId,
                    new_label: newLabel
                })
            });
            
            const result = await response.json();
            if (result.success) {
                await this.loadElements();
                this.render();
            }
        } catch (error) {
            console.error('Error editing element:', error);
        }
    }
    
    async loadElements() {
        try {
            const response = await fetch('/api/elements');
            const data = await response.json();
            this.elements = data.elements;
        } catch (error) {
            console.error('Error loading elements:', error);
        }
    }
    
    render() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Render elements following authentic EG conventions
        for (let element of this.elements) {
            this.renderElement(element);
        }
    }
    
    renderElement(element) {
        const bounds = element.bounds;
        const isSelected = this.selectedElement && this.selectedElement.id === element.id;
        
        this.ctx.save();
        
        if (element.type === 'entity') {
            // Render as small circle (line of identity endpoint)
            this.ctx.beginPath();
            this.ctx.arc(bounds.x + bounds.width/2, bounds.y + bounds.height/2, 
                        Math.min(bounds.width, bounds.height)/2, 0, 2 * Math.PI);
            this.ctx.fillStyle = '#ffffff';
            this.ctx.fill();
            this.ctx.strokeStyle = isSelected ? '#0066cc' : '#333333';
            this.ctx.lineWidth = isSelected ? 3 : 2;
            this.ctx.stroke();
            
            // Add label
            this.ctx.fillStyle = '#000000';
            this.ctx.font = '12px Times New Roman';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(element.label, bounds.x + bounds.width/2, bounds.y + bounds.height + 15);
            
        } else if (element.type === 'predicate') {
            // Render as text label (concept name)
            this.ctx.fillStyle = '#000000';
            this.ctx.font = '14px Times New Roman';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(element.label, bounds.x + bounds.width/2, bounds.y + bounds.height/2 + 5);
            
            // Add selection indicator
            if (isSelected) {
                this.ctx.strokeStyle = '#0066cc';
                this.ctx.lineWidth = 2;
                this.ctx.strokeRect(bounds.x - 5, bounds.y - 5, bounds.width + 10, bounds.height + 10);
            }
            
        } else if (element.type === 'cut') {
            // Render as oval enclosure (Peirce's cut)
            this.ctx.beginPath();
            this.ctx.ellipse(bounds.x + bounds.width/2, bounds.y + bounds.height/2,
                           bounds.width/2, bounds.height/2, 0, 0, 2 * Math.PI);
            this.ctx.strokeStyle = isSelected ? '#0066cc' : '#333333';
            this.ctx.lineWidth = isSelected ? 3 : 2;
            this.ctx.stroke();
            
            // Add negation symbol
            this.ctx.fillStyle = '#333333';
            this.ctx.font = 'bold 16px Times New Roman';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('¬', bounds.x + bounds.width/2, bounds.y + 20);
        }
        
        this.ctx.restore();
    }
    
    async validateGraph() {
        try {
            const response = await fetch('/api/validate');
            const validation = await response.json();
            
            let message = `Graph Validation:\n`;
            message += `Entities: ${validation.entity_count}\n`;
            message += `Predicates: ${validation.predicate_count}\n`;
            message += `Cuts: ${validation.cut_count}\n\n`;
            message += validation.messages.join('\n');
            
            alert(message);
        } catch (error) {
            console.error('Error validating graph:', error);
        }
    }
    
    async clearGraph() {
        if (confirm('Clear all elements from the canvas?')) {
            try {
                const response = await fetch('/api/clear');
                const result = await response.json();
                
                if (result.success) {
                    this.selectedElement = null;
                    await this.loadElements();
                    this.render();
                }
            } catch (error) {
                console.error('Error clearing graph:', error);
            }
        }
    }
    
    showHelp() {
        const helpText = `Existential Graph Editor - Help

Tools:
• Select: Click to select, drag to move elements
• Entity: Click to create entities (lines of identity)
• Predicate: Click to create predicates (concept names)
• Cut: Click to create cuts (negation ovals)

Mouse Actions:
• Left click: Select/create elements
• Right click: Context menu
• Double click: Edit element label
• Drag: Move selected elements

Keyboard Shortcuts:
• Ctrl+A: Select all
• Delete: Delete selected element
• F1: Show this help

Visual Conventions:
This editor follows authentic existential graph notation:
• Entities are small circles (line of identity endpoints)
• Predicates are simple text labels (concept names)
• Cuts are oval enclosures (negation)
• Clean, minimal style matching Peirce's original notation

Educational Features:
• Enable "Educational Mode" for learning guidance
• Feedback panel shows explanations and tips
• Based on Sowa, Roberts, and Dau's reference materials`;
        
        alert(helpText);
    }
    
    async toggleEducationalMode(enabled) {
        try {
            const response = await fetch('/api/educational', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({enabled: enabled})
            });
            
            const result = await response.json();
            this.educationalMode = result.enabled;
        } catch (error) {
            console.error('Error toggling educational mode:', error);
        }
    }
    
    async updateFeedback() {
        if (!this.educationalMode) return;
        
        try {
            const response = await fetch('/api/educational');
            const data = await response.json();
            
            const feedbackContent = document.getElementById('feedback-content');
            feedbackContent.innerHTML = '';
            
            data.messages.forEach(message => {
                const p = document.createElement('p');
                p.textContent = message;
                feedbackContent.appendChild(p);
            });
            
            // Auto-scroll to bottom
            feedbackContent.scrollTop = feedbackContent.scrollHeight;
        } catch (error) {
            console.error('Error updating feedback:', error);
        }
    }
    
    startFeedbackUpdates() {
        // Update feedback every 2 seconds
        setInterval(() => this.updateFeedback(), 2000);
    }
    
    updateStatus(message) {
        document.getElementById('status-text').textContent = message;
    }
    
    showElementContextMenu(element, x, y) {
        // Simple context menu (could be enhanced with proper UI)
        const action = prompt(`Actions for ${element.type} "${element.label}":
1. Edit label
2. Delete element
3. Explain element

Enter choice (1-3):`, '1');
        
        if (action === '1') {
            const newLabel = prompt(`Edit ${element.type} label:`, element.label);
            if (newLabel && newLabel !== element.label) {
                this.editElement(element.id, newLabel);
            }
        } else if (action === '2') {
            if (confirm(`Delete ${element.type} "${element.label}"?`)) {
                this.deleteElement(element.id);
            }
        } else if (action === '3') {
            this.explainElement(element);
        }
    }
    
    showCanvasContextMenu(x, y, clientX, clientY) {
        const action = prompt(`Create element at (${Math.round(x)}, ${Math.round(y)}):
1. Entity
2. Predicate  
3. Cut

Enter choice (1-3):`, '1');
        
        if (action === '1') {
            this.createElement('entity', x, y);
        } else if (action === '2') {
            this.createElement('predicate', x, y);
        } else if (action === '3') {
            this.createElement('cut', x, y);
        }
    }
    
    explainElement(element) {
        const explanations = {
            'entity': 'Entities represent individuals or objects in the domain of discourse. In Peirce\'s notation, they appear as endpoints of lines of identity.',
            'predicate': 'Predicates express properties or relationships. They appear as concept names (text labels) that can be applied to entities.',
            'cut': 'Cuts represent negation in existential graphs. They are oval enclosures - if the cut is true, its contents are false.'
        };
        
        const explanation = explanations[element.type] || 'Unknown element type.';
        alert(`About ${element.type}: ${element.label}\n\n${explanation}`);
    }
    
    selectAll() {
        // Simple select all - just highlight all elements
        this.updateStatus(`Selected all ${this.elements.length} elements`);
    }
}

// Initialize the editor when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const editor = new EGEditor();
    
    // Initial render
    editor.render();
    
    console.log('Existential Graph Editor initialized');
    console.log('Following authentic visual conventions from Peirce, Sowa, Roberts, and Dau');
});