# EGRF v3.0 Next Steps

## Introduction

This document outlines the next steps for the EGRF v3.0 implementation, providing a roadmap for future development. It includes specific tasks, priorities, and recommendations for continuing the work on EGRF v3.0.

## Immediate Next Steps

### 1. Fix EG-HG Parser

The EG-HG parser is not correctly handling nested structures, resulting in incomplete graph structures. This is the most immediate priority.

**Tasks:**
- Enhance the `parse_eg_hg_content` function to correctly parse nested structures.
- Add better error handling and validation.
- Add detailed logging to help diagnose parsing issues.
- Create targeted tests for the parser with different EG-HG structures.

**Example:**
```python
def parse_eg_hg_content(content):
    """Parse EG-HG content into a structured dictionary."""
    lines = content.strip().split('\n')
    result = {}
    current_section = None
    current_subsection = None
    indent_level = 0
    
    for line in lines:
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith('#'):
            continue
        
        # Calculate indent level
        current_indent = len(line) - len(line.lstrip())
        
        # Handle indentation changes
        if current_indent > indent_level:
            # Indentation increased
            indent_level = current_indent
        elif current_indent < indent_level:
            # Indentation decreased
            indent_level = current_indent
            if current_subsection:
                current_subsection = None
        
        # Remove leading/trailing whitespace
        line = line.strip()
        
        # Handle key-value pairs
        if ':' in line and not line.endswith(':'):
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if current_subsection:
                if current_section not in result:
                    result[current_section] = {}
                if current_subsection not in result[current_section]:
                    result[current_section][current_subsection] = []
                
                # Add to current subsection
                item = result[current_section][current_subsection][-1]
                item[key] = value
            elif current_section:
                if current_section not in result:
                    result[current_section] = {}
                result[current_section][key] = value
            else:
                result[key] = value
        
        # Handle section headers
        elif line.endswith(':'):
            section = line[:-1].strip()
            if section in ['contexts', 'predicates', 'entities', 'connections']:
                current_section = 'graph'
                current_subsection = section
                if current_section not in result:
                    result[current_section] = {}
                if current_subsection not in result[current_section]:
                    result[current_section][current_subsection] = []
            else:
                current_section = section
                current_subsection = None
                if current_section not in result:
                    result[current_section] = {}
        
        # Handle list items
        elif line.startswith('-'):
            item = {}
            line = line[1:].strip()
            
            # Handle inline key-value pairs
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                item[key] = value
            
            if current_subsection:
                if current_section not in result:
                    result[current_section] = {}
                if current_subsection not in result[current_section]:
                    result[current_section][current_subsection] = []
                result[current_section][current_subsection].append(item)
    
    return result
```

### 2. Complete EG-HG to EGRF Converter

The converter is only generating the sheet element, missing predicates, entities, and cuts defined in the EG-HG files.

**Tasks:**
- Update the converter to properly handle all elements from the parsed data.
- Ensure proper handling of containment relationships.
- Add support for connections and ligatures.
- Add validation of the generated EGRF.

**Example:**
```python
def convert(self, eg_hg_data):
    """Convert EG-HG data to EGRF v3.0."""
    # Initialize EGRF data
    egrf_data = {
        "metadata": {
            "version": "3.0.0",
            "format": "egrf",
            "id": eg_hg_data.get("id", "unknown"),
            "description": eg_hg_data.get("description", "")
        },
        "elements": {},
        "containment": {},
        "connections": [],
        "ligatures": [],
        "layout_constraints": []
    }
    
    # Process contexts
    self._process_contexts(eg_hg_data, egrf_data)
    
    # Process predicates
    self._process_predicates(eg_hg_data, egrf_data)
    
    # Process entities
    self._process_entities(eg_hg_data, egrf_data)
    
    # Process connections
    self._process_connections(eg_hg_data, egrf_data)
    
    # Generate layout constraints
    self._generate_layout_constraints(egrf_data)
    
    return egrf_data
```

### 3. Enhance Corpus Validation

The corpus validation system needs to be enhanced to provide more detailed feedback.

**Tasks:**
- Add more detailed validation of EGRF structure.
- Add validation of containment relationships.
- Add validation of connections and ligatures.
- Add validation of layout constraints.

**Example:**
```python
def validate_egrf_structure(egrf_data):
    """Validate the structure of an EGRF v3.0 document."""
    messages = []
    
    # Check metadata
    if "metadata" not in egrf_data:
        messages.append("Missing metadata section")
        return False, messages
    
    metadata = egrf_data["metadata"]
    if "version" not in metadata or metadata["version"] != "3.0.0":
        messages.append(f"Invalid version: {metadata.get('version', 'missing')}")
        return False, messages
    
    if "format" not in metadata or metadata["format"] != "egrf":
        messages.append(f"Invalid format: {metadata.get('format', 'missing')}")
        return False, messages
    
    # Check elements
    if "elements" not in egrf_data:
        messages.append("Missing elements section")
        return False, messages
    
    elements = egrf_data["elements"]
    if not elements:
        messages.append("Empty elements section")
        return False, messages
    
    # Check containment
    if "containment" not in egrf_data:
        messages.append("Missing containment section")
        return False, messages
    
    # Check each element
    for element_id, element in elements.items():
        if "element_type" not in element:
            messages.append(f"Element {element_id} missing element_type")
            return False, messages
        
        element_type = element["element_type"]
        if element_type not in ["context", "predicate", "entity"]:
            messages.append(f"Invalid element_type for {element_id}: {element_type}")
            return False, messages
        
        if "logical_properties" not in element:
            messages.append(f"Element {element_id} missing logical_properties")
            return False, messages
        
        logical_properties = element["logical_properties"]
        
        if element_type == "context":
            if "context_type" not in logical_properties:
                messages.append(f"Context {element_id} missing context_type")
                return False, messages
            
            context_type = logical_properties["context_type"]
            if context_type not in ["sheet", "cut", "sheet_of_assertion"]:
                messages.append(f"Invalid context_type for {element_id}: {context_type}")
                return False, messages
        
        elif element_type == "predicate":
            if "arity" not in logical_properties:
                messages.append(f"Predicate {element_id} missing arity")
                return False, messages
        
        elif element_type == "entity":
            if "entity_type" not in logical_properties:
                messages.append(f"Entity {element_id} missing entity_type")
                return False, messages
            
            entity_type = logical_properties["entity_type"]
            if entity_type not in ["constant", "variable"]:
                messages.append(f"Invalid entity_type for {element_id}: {entity_type}")
                return False, messages
    
    # Validate containment relationships
    containment = egrf_data["containment"]
    for element_id, container_id in containment.items():
        if element_id not in elements:
            messages.append(f"Containment references non-existent element: {element_id}")
            return False, messages
        
        if container_id not in elements and container_id != "none":
            messages.append(f"Containment references non-existent container: {container_id}")
            return False, messages
    
    # Validate connections
    connections = egrf_data.get("connections", [])
    for connection in connections:
        if "entity_id" not in connection:
            messages.append("Connection missing entity_id")
            return False, messages
        
        if "predicate_id" not in connection:
            messages.append("Connection missing predicate_id")
            return False, messages
        
        entity_id = connection["entity_id"]
        predicate_id = connection["predicate_id"]
        
        if entity_id not in elements:
            messages.append(f"Connection references non-existent entity: {entity_id}")
            return False, messages
        
        if predicate_id not in elements:
            messages.append(f"Connection references non-existent predicate: {predicate_id}")
            return False, messages
    
    # Validate ligatures
    ligatures = egrf_data.get("ligatures", [])
    for ligature in ligatures:
        if "entity1_id" not in ligature:
            messages.append("Ligature missing entity1_id")
            return False, messages
        
        if "entity2_id" not in ligature:
            messages.append("Ligature missing entity2_id")
            return False, messages
        
        entity1_id = ligature["entity1_id"]
        entity2_id = ligature["entity2_id"]
        
        if entity1_id not in elements:
            messages.append(f"Ligature references non-existent entity: {entity1_id}")
            return False, messages
        
        if entity2_id not in elements:
            messages.append(f"Ligature references non-existent entity: {entity2_id}")
            return False, messages
    
    return True, messages
```

## Medium-Term Tasks

### 1. Expand the Corpus

The corpus should be expanded with more examples from Peirce's original works, scholarly interpretations, and canonical forms.

**Tasks:**
- Add more examples from Peirce's Collected Papers.
- Add more examples from Roberts, Sowa, and Dau.
- Add more canonical forms.
- Add examples specifically designed for the Endoporeutic Game.

**Example:**
```python
def add_example_to_corpus(corpus_dir, category, example_id, metadata, clif, eg_hg, egrf):
    """Add a new example to the corpus."""
    # Create category directory if it doesn't exist
    category_dir = os.path.join(corpus_dir, category)
    os.makedirs(category_dir, exist_ok=True)
    
    # Write files
    with open(os.path.join(category_dir, f"{example_id}.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    with open(os.path.join(category_dir, f"{example_id}.clif"), "w") as f:
        f.write(clif)
    
    with open(os.path.join(category_dir, f"{example_id}.eg-hg"), "w") as f:
        f.write(eg_hg)
    
    with open(os.path.join(category_dir, f"{example_id}.egrf"), "w") as f:
        json.dump(egrf, f, indent=2)
    
    # Update corpus index
    index_path = os.path.join(corpus_dir, "corpus_index.json")
    with open(index_path, "r") as f:
        corpus_index = json.load(f)
    
    if category not in corpus_index:
        corpus_index[category] = []
    
    # Add example to index
    corpus_index[category].append({
        "id": example_id,
        "title": metadata["title"],
        "source": metadata["source"]["work"] if "source" in metadata and "work" in metadata["source"] else "Unknown",
        "pattern": metadata["pattern"],
        "description": metadata["description"]
    })
    
    # Write updated index
    with open(index_path, "w") as f:
        json.dump(corpus_index, f, indent=2)
```

### 2. Implement Platform Adapters

Adapters for specific GUI platforms should be implemented to demonstrate the platform independence of EGRF v3.0.

**Tasks:**
- Implement a web-based adapter using HTML/CSS/JavaScript.
- Implement a desktop adapter using a cross-platform GUI toolkit.
- Implement a mobile adapter for touch interfaces.
- Create a common interface for all adapters.

**Example:**
```python
class PlatformAdapter:
    """Base class for platform adapters."""
    
    def __init__(self):
        """Initialize the platform adapter."""
        pass
    
    def render(self, egrf_data):
        """Render the EGRF data on the platform."""
        raise NotImplementedError("Subclasses must implement render()")
    
    def handle_user_interaction(self, event):
        """Handle user interaction events."""
        raise NotImplementedError("Subclasses must implement handle_user_interaction()")
    
    def update(self, egrf_data):
        """Update the rendering with new EGRF data."""
        raise NotImplementedError("Subclasses must implement update()")
    
    def export(self, format):
        """Export the rendering to the specified format."""
        raise NotImplementedError("Subclasses must implement export()")


class WebAdapter(PlatformAdapter):
    """Web-based adapter using HTML/CSS/JavaScript."""
    
    def __init__(self):
        """Initialize the web adapter."""
        super().__init__()
        self.html = ""
        self.css = ""
        self.js = ""
    
    def render(self, egrf_data):
        """Render the EGRF data as HTML/CSS/JavaScript."""
        # Generate HTML
        html = "<div class='egrf-container'>\n"
        
        # Render contexts
        for element_id, element in egrf_data["elements"].items():
            if element["element_type"] == "context":
                context_type = element["logical_properties"]["context_type"]
                html += f"  <div id='{element_id}' class='egrf-context egrf-{context_type}'>\n"
                
                # Add name if available
                if "visual_properties" in element and "name" in element["visual_properties"]:
                    name = element["visual_properties"]["name"]
                    html += f"    <div class='egrf-context-name'>{name}</div>\n"
                
                html += "  </div>\n"
        
        # Render predicates
        for element_id, element in egrf_data["elements"].items():
            if element["element_type"] == "predicate":
                html += f"  <div id='{element_id}' class='egrf-predicate'>\n"
                
                # Add name if available
                if "visual_properties" in element and "name" in element["visual_properties"]:
                    name = element["visual_properties"]["name"]
                    html += f"    <div class='egrf-predicate-name'>{name}</div>\n"
                
                html += "  </div>\n"
        
        # Render entities
        for element_id, element in egrf_data["elements"].items():
            if element["element_type"] == "entity":
                html += f"  <div id='{element_id}' class='egrf-entity'>\n"
                
                # Add name if available
                if "visual_properties" in element and "name" in element["visual_properties"]:
                    name = element["visual_properties"]["name"]
                    html += f"    <div class='egrf-entity-name'>{name}</div>\n"
                
                html += "  </div>\n"
        
        html += "</div>"
        
        # Generate CSS
        css = """
        .egrf-container {
            position: relative;
            width: 100%;
            height: 100%;
        }
        
        .egrf-context {
            position: absolute;
            border: 1px solid black;
            border-radius: 10px;
            padding: 10px;
        }
        
        .egrf-sheet_of_assertion {
            background-color: #f0f0f0;
        }
        
        .egrf-cut {
            background-color: #e0e0e0;
            border: 2px solid black;
        }
        
        .egrf-predicate {
            position: absolute;
            border: 1px solid blue;
            border-radius: 5px;
            padding: 5px;
            background-color: #e0e0ff;
        }
        
        .egrf-entity {
            position: absolute;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: black;
        }
        
        .egrf-context-name, .egrf-predicate-name, .egrf-entity-name {
            font-family: Arial, sans-serif;
            font-size: 12px;
        }
        """
        
        # Generate JavaScript
        js = """
        document.addEventListener('DOMContentLoaded', function() {
            // Apply layout constraints
            applyLayoutConstraints();
            
            // Add event listeners for user interaction
            addEventListeners();
        });
        
        function applyLayoutConstraints() {
            // Apply layout constraints based on EGRF data
            // ...
        }
        
        function addEventListeners() {
            // Add event listeners for user interaction
            // ...
        }
        """
        
        self.html = html
        self.css = css
        self.js = js
        
        return {
            "html": html,
            "css": css,
            "js": js
        }
    
    def handle_user_interaction(self, event):
        """Handle user interaction events."""
        # Handle user interaction events
        # ...
        pass
    
    def update(self, egrf_data):
        """Update the rendering with new EGRF data."""
        # Update the rendering with new EGRF data
        # ...
        pass
    
    def export(self, format):
        """Export the rendering to the specified format."""
        if format == "html":
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                {self.css}
                </style>
            </head>
            <body>
                {self.html}
                <script>
                {self.js}
                </script>
            </body>
            </html>
            """
        else:
            raise ValueError(f"Unsupported export format: {format}")
```

### 3. Develop User Interaction

User interaction with the EGRF v3.0 system needs to be implemented to demonstrate the usability of the system.

**Tasks:**
- Implement drag-and-drop functionality for moving elements.
- Implement resizing functionality for contexts.
- Implement adding and removing elements.
- Implement connecting entities to predicates.
- Implement creating and editing ligatures.

**Example:**
```javascript
// Add event listeners for user interaction
function addEventListeners() {
    // Add event listeners for dragging elements
    document.querySelectorAll('.egrf-context, .egrf-predicate, .egrf-entity').forEach(element => {
        element.addEventListener('mousedown', startDrag);
    });
    
    // Add event listeners for resizing contexts
    document.querySelectorAll('.egrf-context').forEach(element => {
        const resizer = document.createElement('div');
        resizer.className = 'egrf-resizer';
        element.appendChild(resizer);
        resizer.addEventListener('mousedown', startResize);
    });
    
    // Add event listeners for connecting entities to predicates
    document.querySelectorAll('.egrf-entity').forEach(entity => {
        entity.addEventListener('dblclick', startConnection);
    });
}

// Start dragging an element
function startDrag(event) {
    const element = event.target;
    const startX = event.clientX;
    const startY = event.clientY;
    const startLeft = parseInt(window.getComputedStyle(element).left);
    const startTop = parseInt(window.getComputedStyle(element).top);
    
    // Add event listeners for dragging
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDrag);
    
    // Prevent default behavior
    event.preventDefault();
    
    // Drag the element
    function drag(event) {
        const dx = event.clientX - startX;
        const dy = event.clientY - startY;
        
        // Calculate new position
        const newLeft = startLeft + dx;
        const newTop = startTop + dy;
        
        // Check if the new position is valid
        if (isValidPosition(element, newLeft, newTop)) {
            // Update position
            element.style.left = newLeft + 'px';
            element.style.top = newTop + 'px';
            
            // Update connections
            updateConnections(element);
        }
    }
    
    // Stop dragging
    function stopDrag() {
        // Remove event listeners
        document.removeEventListener('mousemove', drag);
        document.removeEventListener('mouseup', stopDrag);
        
        // Save the new position
        savePosition(element);
    }
}

// Check if the new position is valid
function isValidPosition(element, left, top) {
    // Get the container
    const container = getContainer(element);
    
    // Get the container bounds
    const containerBounds = container.getBoundingClientRect();
    
    // Get the element bounds
    const elementBounds = element.getBoundingClientRect();
    
    // Check if the element is within the container
    return (
        left >= 0 &&
        top >= 0 &&
        left + elementBounds.width <= containerBounds.width &&
        top + elementBounds.height <= containerBounds.height
    );
}

// Get the container of an element
function getContainer(element) {
    // Get the element ID
    const elementId = element.id;
    
    // Get the container ID from the EGRF data
    const containerId = egrfData.containment[elementId];
    
    // Return the container element
    return document.getElementById(containerId);
}

// Update connections when an element is moved
function updateConnections(element) {
    // Get the element ID
    const elementId = element.id;
    
    // Update connections for predicates
    if (element.classList.contains('egrf-predicate')) {
        // Find connections where this predicate is involved
        egrfData.connections.forEach(connection => {
            if (connection.predicate_id === elementId) {
                // Update the connection
                updateConnection(connection);
            }
        });
    }
    
    // Update connections for entities
    if (element.classList.contains('egrf-entity')) {
        // Find connections where this entity is involved
        egrfData.connections.forEach(connection => {
            if (connection.entity_id === elementId) {
                // Update the connection
                updateConnection(connection);
            }
        });
        
        // Find ligatures where this entity is involved
        egrfData.ligatures.forEach(ligature => {
            if (ligature.entity1_id === elementId || ligature.entity2_id === elementId) {
                // Update the ligature
                updateLigature(ligature);
            }
        });
    }
}

// Update a connection
function updateConnection(connection) {
    // Get the entity and predicate elements
    const entity = document.getElementById(connection.entity_id);
    const predicate = document.getElementById(connection.predicate_id);
    
    // Get the entity and predicate positions
    const entityPos = {
        x: parseInt(window.getComputedStyle(entity).left) + entity.offsetWidth / 2,
        y: parseInt(window.getComputedStyle(entity).top) + entity.offsetHeight / 2
    };
    
    const predicatePos = {
        x: parseInt(window.getComputedStyle(predicate).left) + predicate.offsetWidth / 2,
        y: parseInt(window.getComputedStyle(predicate).top) + predicate.offsetHeight / 2
    };
    
    // Create or update the connection line
    let connectionLine = document.getElementById(`connection-${connection.entity_id}-${connection.predicate_id}`);
    
    if (!connectionLine) {
        connectionLine = document.createElement('div');
        connectionLine.id = `connection-${connection.entity_id}-${connection.predicate_id}`;
        connectionLine.className = 'egrf-connection';
        document.querySelector('.egrf-container').appendChild(connectionLine);
    }
    
    // Calculate the line position and length
    const dx = predicatePos.x - entityPos.x;
    const dy = predicatePos.y - entityPos.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    const angle = Math.atan2(dy, dx) * 180 / Math.PI;
    
    // Update the line style
    connectionLine.style.width = length + 'px';
    connectionLine.style.left = entityPos.x + 'px';
    connectionLine.style.top = entityPos.y + 'px';
    connectionLine.style.transform = `rotate(${angle}deg)`;
}

// Update a ligature
function updateLigature(ligature) {
    // Get the entity elements
    const entity1 = document.getElementById(ligature.entity1_id);
    const entity2 = document.getElementById(ligature.entity2_id);
    
    // Get the entity positions
    const entity1Pos = {
        x: parseInt(window.getComputedStyle(entity1).left) + entity1.offsetWidth / 2,
        y: parseInt(window.getComputedStyle(entity1).top) + entity1.offsetHeight / 2
    };
    
    const entity2Pos = {
        x: parseInt(window.getComputedStyle(entity2).left) + entity2.offsetWidth / 2,
        y: parseInt(window.getComputedStyle(entity2).top) + entity2.offsetHeight / 2
    };
    
    // Create or update the ligature line
    let ligatureLine = document.getElementById(`ligature-${ligature.entity1_id}-${ligature.entity2_id}`);
    
    if (!ligatureLine) {
        ligatureLine = document.createElement('div');
        ligatureLine.id = `ligature-${ligature.entity1_id}-${ligature.entity2_id}`;
        ligatureLine.className = 'egrf-ligature';
        document.querySelector('.egrf-container').appendChild(ligatureLine);
    }
    
    // Calculate the line position and length
    const dx = entity2Pos.x - entity1Pos.x;
    const dy = entity2Pos.y - entity1Pos.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    const angle = Math.atan2(dy, dx) * 180 / Math.PI;
    
    // Update the line style
    ligatureLine.style.width = length + 'px';
    ligatureLine.style.left = entity1Pos.x + 'px';
    ligatureLine.style.top = entity1Pos.y + 'px';
    ligatureLine.style.transform = `rotate(${angle}deg)`;
}

// Save the position of an element
function savePosition(element) {
    // Get the element ID
    const elementId = element.id;
    
    // Get the element position
    const left = parseInt(window.getComputedStyle(element).left);
    const top = parseInt(window.getComputedStyle(element).top);
    
    // Update the layout constraints
    egrfData.layout_constraints.forEach(constraint => {
        if (constraint.element_id === elementId && constraint.constraint_type === 'position') {
            // Update the position
            constraint.x = left;
            constraint.y = top;
            constraint.x_unit = 'absolute';
            constraint.y_unit = 'absolute';
        }
    });
    
    // Save the updated EGRF data
    saveEgrfData();
}

// Save the EGRF data
function saveEgrfData() {
    // Send the updated EGRF data to the server
    fetch('/api/save-egrf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(egrfData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('EGRF data saved:', data);
    })
    .catch(error => {
        console.error('Error saving EGRF data:', error);
    });
}
```

## Long-Term Tasks

### 1. Implement Automatic Layout

More sophisticated automatic layout algorithms should be developed to improve the visualization of Existential Graphs.

**Tasks:**
- Implement a force-directed layout algorithm.
- Implement a hierarchical layout algorithm.
- Implement a constraint-based layout algorithm.
- Implement a hybrid layout algorithm.

**Example:**
```python
class ForceDirectedLayout:
    """Force-directed layout algorithm for Existential Graphs."""
    
    def __init__(self, egrf_data):
        """Initialize the force-directed layout algorithm."""
        self.egrf_data = egrf_data
        self.elements = {}
        self.forces = {}
        self.positions = {}
        self.velocities = {}
        
        # Initialize elements
        for element_id, element in egrf_data["elements"].items():
            self.elements[element_id] = element
            self.forces[element_id] = {"x": 0, "y": 0}
            self.positions[element_id] = {"x": 0, "y": 0}
            self.velocities[element_id] = {"x": 0, "y": 0}
        
        # Initialize positions
        self._initialize_positions()
    
    def _initialize_positions(self):
        """Initialize element positions."""
        # Get the root element
        root_id = None
        for element_id, element in self.elements.items():
            if element["element_type"] == "context" and element["logical_properties"].get("is_root", False):
                root_id = element_id
                break
        
        if not root_id:
            # No root element found, use the first context
            for element_id, element in self.elements.items():
                if element["element_type"] == "context":
                    root_id = element_id
                    break
        
        # Set the root element position
        self.positions[root_id] = {"x": 0, "y": 0}
        
        # Set positions for other elements
        for element_id in self.elements:
            if element_id != root_id:
                # Set random initial position
                self.positions[element_id] = {
                    "x": random.uniform(-100, 100),
                    "y": random.uniform(-100, 100)
                }
    
    def _calculate_forces(self):
        """Calculate forces for each element."""
        # Reset forces
        for element_id in self.forces:
            self.forces[element_id] = {"x": 0, "y": 0}
        
        # Calculate repulsive forces
        for element1_id in self.elements:
            for element2_id in self.elements:
                if element1_id != element2_id:
                    self._calculate_repulsive_force(element1_id, element2_id)
        
        # Calculate attractive forces
        for element1_id, container_id in self.egrf_data["containment"].items():
            if container_id != "none":
                self._calculate_attractive_force(element1_id, container_id)
        
        # Calculate connection forces
        for connection in self.egrf_data.get("connections", []):
            entity_id = connection["entity_id"]
            predicate_id = connection["predicate_id"]
            self._calculate_connection_force(entity_id, predicate_id)
        
        # Calculate ligature forces
        for ligature in self.egrf_data.get("ligatures", []):
            entity1_id = ligature["entity1_id"]
            entity2_id = ligature["entity2_id"]
            self._calculate_ligature_force(entity1_id, entity2_id)
    
    def _calculate_repulsive_force(self, element1_id, element2_id):
        """Calculate repulsive force between two elements."""
        # Get positions
        pos1 = self.positions[element1_id]
        pos2 = self.positions[element2_id]
        
        # Calculate distance
        dx = pos2["x"] - pos1["x"]
        dy = pos2["y"] - pos1["y"]
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Avoid division by zero
        if distance < 0.1:
            distance = 0.1
        
        # Calculate force
        force = 1000 / (distance * distance)
        
        # Calculate force components
        fx = force * dx / distance
        fy = force * dy / distance
        
        # Apply force
        self.forces[element1_id]["x"] -= fx
        self.forces[element1_id]["y"] -= fy
        self.forces[element2_id]["x"] += fx
        self.forces[element2_id]["y"] += fy
    
    def _calculate_attractive_force(self, element_id, container_id):
        """Calculate attractive force between an element and its container."""
        # Get positions
        pos1 = self.positions[element_id]
        pos2 = self.positions[container_id]
        
        # Calculate distance
        dx = pos2["x"] - pos1["x"]
        dy = pos2["y"] - pos1["y"]
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Avoid division by zero
        if distance < 0.1:
            distance = 0.1
        
        # Calculate force
        force = 0.01 * distance
        
        # Calculate force components
        fx = force * dx / distance
        fy = force * dy / distance
        
        # Apply force
        self.forces[element_id]["x"] += fx
        self.forces[element_id]["y"] += fy
    
    def _calculate_connection_force(self, entity_id, predicate_id):
        """Calculate force between a connected entity and predicate."""
        # Get positions
        pos1 = self.positions[entity_id]
        pos2 = self.positions[predicate_id]
        
        # Calculate distance
        dx = pos2["x"] - pos1["x"]
        dy = pos2["y"] - pos1["y"]
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Avoid division by zero
        if distance < 0.1:
            distance = 0.1
        
        # Calculate force
        force = 0.05 * distance
        
        # Calculate force components
        fx = force * dx / distance
        fy = force * dy / distance
        
        # Apply force
        self.forces[entity_id]["x"] += fx
        self.forces[entity_id]["y"] += fy
        self.forces[predicate_id]["x"] -= fx
        self.forces[predicate_id]["y"] -= fy
    
    def _calculate_ligature_force(self, entity1_id, entity2_id):
        """Calculate force between two entities connected by a ligature."""
        # Get positions
        pos1 = self.positions[entity1_id]
        pos2 = self.positions[entity2_id]
        
        # Calculate distance
        dx = pos2["x"] - pos1["x"]
        dy = pos2["y"] - pos1["y"]
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Avoid division by zero
        if distance < 0.1:
            distance = 0.1
        
        # Calculate force
        force = 0.05 * distance
        
        # Calculate force components
        fx = force * dx / distance
        fy = force * dy / distance
        
        # Apply force
        self.forces[entity1_id]["x"] += fx
        self.forces[entity1_id]["y"] += fy
        self.forces[entity2_id]["x"] -= fx
        self.forces[entity2_id]["y"] -= fy
    
    def _update_positions(self, damping=0.9, time_step=0.1):
        """Update element positions based on forces."""
        for element_id in self.elements:
            # Update velocity
            self.velocities[element_id]["x"] = damping * self.velocities[element_id]["x"] + time_step * self.forces[element_id]["x"]
            self.velocities[element_id]["y"] = damping * self.velocities[element_id]["y"] + time_step * self.forces[element_id]["y"]
            
            # Update position
            self.positions[element_id]["x"] += time_step * self.velocities[element_id]["x"]
            self.positions[element_id]["y"] += time_step * self.velocities[element_id]["y"]
    
    def layout(self, iterations=100):
        """Run the layout algorithm."""
        for _ in range(iterations):
            self._calculate_forces()
            self._update_positions()
        
        # Update layout constraints
        for element_id, position in self.positions.items():
            # Find existing position constraint
            position_constraint = None
            for constraint in self.egrf_data.get("layout_constraints", []):
                if constraint["element_id"] == element_id and constraint["constraint_type"] == "position":
                    position_constraint = constraint
                    break
            
            # Create new position constraint if not found
            if not position_constraint:
                position_constraint = {
                    "element_id": element_id,
                    "constraint_type": "position",
                    "x": 0,
                    "y": 0,
                    "x_unit": "absolute",
                    "y_unit": "absolute"
                }
                self.egrf_data.setdefault("layout_constraints", []).append(position_constraint)
            
            # Update position
            position_constraint["x"] = position["x"]
            position_constraint["y"] = position["y"]
            position_constraint["x_unit"] = "absolute"
            position_constraint["y_unit"] = "absolute"
        
        return self.egrf_data
```

### 2. Enhance Constraint Solving

The constraint solving system should be enhanced for better performance and more flexibility.

**Tasks:**
- Implement a more efficient constraint solver.
- Add support for more complex constraints.
- Add support for constraint priorities.
- Add support for constraint relaxation.

**Example:**
```python
class ConstraintSolver:
    """Constraint solver for layout constraints."""
    
    def __init__(self, layout_context):
        """Initialize the constraint solver."""
        self.layout_context = layout_context
        self.elements = layout_context.elements
        self.constraints = layout_context.constraints
        self.positions = {}
        self.sizes = {}
        
        # Initialize positions and sizes
        for element_id, element in self.elements.items():
            self.positions[element_id] = {"x": 0, "y": 0}
            self.sizes[element_id] = {"width": 0, "height": 0}
    
    def solve(self):
        """Solve the constraints."""
        # Sort constraints by priority
        sorted_constraints = sorted(self.constraints, key=lambda c: c.priority)
        
        # Apply constraints in order of priority
        for constraint in sorted_constraints:
            self._apply_constraint(constraint)
        
        # Return the solved positions and sizes
        return self.positions, self.sizes
    
    def _apply_constraint(self, constraint):
        """Apply a constraint."""
        if isinstance(constraint, SizeConstraint):
            self._apply_size_constraint(constraint)
        elif isinstance(constraint, PositionConstraint):
            self._apply_position_constraint(constraint)
        elif isinstance(constraint, SpacingConstraint):
            self._apply_spacing_constraint(constraint)
        elif isinstance(constraint, AlignmentConstraint):
            self._apply_alignment_constraint(constraint)
        elif isinstance(constraint, ContainmentConstraint):
            self._apply_containment_constraint(constraint)
    
    def _apply_size_constraint(self, constraint):
        """Apply a size constraint."""
        element_id = constraint.element_id
        
        # Get current size
        current_width = self.sizes[element_id]["width"]
        current_height = self.sizes[element_id]["height"]
        
        # Calculate new size
        new_width = constraint.width
        new_height = constraint.height
        
        # Apply min/max constraints
        if constraint.min_width is not None:
            new_width = max(new_width, constraint.min_width)
        if constraint.max_width is not None:
            new_width = min(new_width, constraint.max_width)
        if constraint.min_height is not None:
            new_height = max(new_height, constraint.min_height)
        if constraint.max_height is not None:
            new_height = min(new_height, constraint.max_height)
        
        # Apply auto-sizing
        if constraint.auto_size:
            # Get contained elements
            contained_elements = []
            for element_id2, element in self.elements.items():
                if element.container == element_id:
                    contained_elements.append(element_id2)
            
            # Calculate size based on contained elements
            if contained_elements:
                max_x = 0
                max_y = 0
                for element_id2 in contained_elements:
                    pos = self.positions[element_id2]
                    size = self.sizes[element_id2]
                    max_x = max(max_x, pos["x"] + size["width"])
                    max_y = max(max_y, pos["y"] + size["height"])
                
                # Add padding
                padding = 20
                new_width = max(new_width, max_x + padding)
                new_height = max(new_height, max_y + padding)
        
        # Update size
        self.sizes[element_id]["width"] = new_width
        self.sizes[element_id]["height"] = new_height
    
    def _apply_position_constraint(self, constraint):
        """Apply a position constraint."""
        element_id = constraint.element_id
        container_id = constraint.container
        
        # Get container size
        container_width = self.sizes[container_id]["width"]
        container_height = self.sizes[container_id]["height"]
        
        # Calculate position
        x = constraint.x
        y = constraint.y
        
        # Convert units
        if constraint.x_unit == "relative":
            x = x * container_width
        elif constraint.x_unit == "percentage":
            x = x * container_width / 100
        
        if constraint.y_unit == "relative":
            y = y * container_height
        elif constraint.y_unit == "percentage":
            y = y * container_height / 100
        
        # Update position
        self.positions[element_id]["x"] = x
        self.positions[element_id]["y"] = y
    
    def _apply_spacing_constraint(self, constraint):
        """Apply a spacing constraint."""
        element_id = constraint.element_id
        reference_id = constraint.reference_id
        
        # Get element position and size
        element_pos = self.positions[element_id]
        element_size = self.sizes[element_id]
        
        if reference_id:
            # Get reference position and size
            reference_pos = self.positions[reference_id]
            reference_size = self.sizes[reference_id]
            
            # Calculate spacing
            if constraint.edge == "left":
                spacing = element_pos["x"] - (reference_pos["x"] + reference_size["width"])
            elif constraint.edge == "right":
                spacing = reference_pos["x"] - (element_pos["x"] + element_size["width"])
            elif constraint.edge == "top":
                spacing = element_pos["y"] - (reference_pos["y"] + reference_size["height"])
            elif constraint.edge == "bottom":
                spacing = reference_pos["y"] - (element_pos["y"] + element_size["height"])
            else:
                # Calculate center-to-center distance
                dx = element_pos["x"] + element_size["width"] / 2 - (reference_pos["x"] + reference_size["width"] / 2)
                dy = element_pos["y"] + element_size["height"] / 2 - (reference_pos["y"] + reference_size["height"] / 2)
                spacing = math.sqrt(dx * dx + dy * dy)
            
            # Apply min/max constraints
            if spacing < constraint.min_spacing:
                # Adjust position to maintain minimum spacing
                if constraint.edge == "left":
                    element_pos["x"] = reference_pos["x"] + reference_size["width"] + constraint.min_spacing
                elif constraint.edge == "right":
                    element_pos["x"] = reference_pos["x"] - element_size["width"] - constraint.min_spacing
                elif constraint.edge == "top":
                    element_pos["y"] = reference_pos["y"] + reference_size["height"] + constraint.min_spacing
                elif constraint.edge == "bottom":
                    element_pos["y"] = reference_pos["y"] - element_size["height"] - constraint.min_spacing
                else:
                    # Adjust position to maintain minimum spacing
                    if dx != 0 or dy != 0:
                        scale = constraint.min_spacing / spacing
                        element_pos["x"] = reference_pos["x"] + reference_size["width"] / 2 + dx * scale - element_size["width"] / 2
                        element_pos["y"] = reference_pos["y"] + reference_size["height"] / 2 + dy * scale - element_size["height"] / 2
            
            if constraint.max_spacing is not None and spacing > constraint.max_spacing:
                # Adjust position to maintain maximum spacing
                if constraint.edge == "left":
                    element_pos["x"] = reference_pos["x"] + reference_size["width"] + constraint.max_spacing
                elif constraint.edge == "right":
                    element_pos["x"] = reference_pos["x"] - element_size["width"] - constraint.max_spacing
                elif constraint.edge == "top":
                    element_pos["y"] = reference_pos["y"] + reference_size["height"] + constraint.max_spacing
                elif constraint.edge == "bottom":
                    element_pos["y"] = reference_pos["y"] - element_size["height"] - constraint.max_spacing
                else:
                    # Adjust position to maintain maximum spacing
                    if dx != 0 or dy != 0:
                        scale = constraint.max_spacing / spacing
                        element_pos["x"] = reference_pos["x"] + reference_size["width"] / 2 + dx * scale - element_size["width"] / 2
                        element_pos["y"] = reference_pos["y"] + reference_size["height"] / 2 + dy * scale - element_size["height"] / 2
        else:
            # Reference is container
            container_id = self.elements[element_id].container
            
            # Get container position and size
            container_pos = self.positions[container_id]
            container_size = self.sizes[container_id]
            
            # Calculate spacing
            if constraint.edge == "left":
                spacing = element_pos["x"] - container_pos["x"]
            elif constraint.edge == "right":
                spacing = container_pos["x"] + container_size["width"] - (element_pos["x"] + element_size["width"])
            elif constraint.edge == "top":
                spacing = element_pos["y"] - container_pos["y"]
            elif constraint.edge == "bottom":
                spacing = container_pos["y"] + container_size["height"] - (element_pos["y"] + element_size["height"])
            else:
                # Use minimum of all edges
                spacing = min(
                    element_pos["x"] - container_pos["x"],
                    container_pos["x"] + container_size["width"] - (element_pos["x"] + element_size["width"]),
                    element_pos["y"] - container_pos["y"],
                    container_pos["y"] + container_size["height"] - (element_pos["y"] + element_size["height"])
                )
            
            # Apply min/max constraints
            if spacing < constraint.min_spacing:
                # Adjust position to maintain minimum spacing
                if constraint.edge == "left":
                    element_pos["x"] = container_pos["x"] + constraint.min_spacing
                elif constraint.edge == "right":
                    element_pos["x"] = container_pos["x"] + container_size["width"] - element_size["width"] - constraint.min_spacing
                elif constraint.edge == "top":
                    element_pos["y"] = container_pos["y"] + constraint.min_spacing
                elif constraint.edge == "bottom":
                    element_pos["y"] = container_pos["y"] + container_size["height"] - element_size["height"] - constraint.min_spacing
                else:
                    # Adjust position to maintain minimum spacing on all edges
                    element_pos["x"] = max(element_pos["x"], container_pos["x"] + constraint.min_spacing)
                    element_pos["x"] = min(element_pos["x"], container_pos["x"] + container_size["width"] - element_size["width"] - constraint.min_spacing)
                    element_pos["y"] = max(element_pos["y"], container_pos["y"] + constraint.min_spacing)
                    element_pos["y"] = min(element_pos["y"], container_pos["y"] + container_size["height"] - element_size["height"] - constraint.min_spacing)
            
            if constraint.max_spacing is not None and spacing > constraint.max_spacing:
                # Adjust position to maintain maximum spacing
                if constraint.edge == "left":
                    element_pos["x"] = container_pos["x"] + constraint.max_spacing
                elif constraint.edge == "right":
                    element_pos["x"] = container_pos["x"] + container_size["width"] - element_size["width"] - constraint.max_spacing
                elif constraint.edge == "top":
                    element_pos["y"] = container_pos["y"] + constraint.max_spacing
                elif constraint.edge == "bottom":
                    element_pos["y"] = container_pos["y"] + container_size["height"] - element_size["height"] - constraint.max_spacing
                else:
                    # Adjust position to maintain maximum spacing on all edges
                    element_pos["x"] = max(element_pos["x"], container_pos["x"] + constraint.max_spacing)
                    element_pos["x"] = min(element_pos["x"], container_pos["x"] + container_size["width"] - element_size["width"] - constraint.max_spacing)
                    element_pos["y"] = max(element_pos["y"], container_pos["y"] + constraint.max_spacing)
                    element_pos["y"] = min(element_pos["y"], container_pos["y"] + container_size["height"] - element_size["height"] - constraint.max_spacing)
    
    def _apply_alignment_constraint(self, constraint):
        """Apply an alignment constraint."""
        element_id = constraint.element_id
        reference_id = constraint.reference_id
        
        # Get element position and size
        element_pos = self.positions[element_id]
        element_size = self.sizes[element_id]
        
        # Get reference position and size
        reference_pos = self.positions[reference_id]
        reference_size = self.sizes[reference_id]
        
        # Apply alignment
        if constraint.alignment == "left":
            element_pos["x"] = reference_pos["x"]
        elif constraint.alignment == "right":
            element_pos["x"] = reference_pos["x"] + reference_size["width"] - element_size["width"]
        elif constraint.alignment == "top":
            element_pos["y"] = reference_pos["y"]
        elif constraint.alignment == "bottom":
            element_pos["y"] = reference_pos["y"] + reference_size["height"] - element_size["height"]
        elif constraint.alignment == "center_x":
            element_pos["x"] = reference_pos["x"] + reference_size["width"] / 2 - element_size["width"] / 2
        elif constraint.alignment == "center_y":
            element_pos["y"] = reference_pos["y"] + reference_size["height"] / 2 - element_size["height"] / 2
        elif constraint.alignment == "center":
            element_pos["x"] = reference_pos["x"] + reference_size["width"] / 2 - element_size["width"] / 2
            element_pos["y"] = reference_pos["y"] + reference_size["height"] / 2 - element_size["height"] / 2
    
    def _apply_containment_constraint(self, constraint):
        """Apply a containment constraint."""
        element_id = constraint.element_id
        container_id = constraint.container
        
        # Get element position and size
        element_pos = self.positions[element_id]
        element_size = self.sizes[element_id]
        
        # Get container position and size
        container_pos = self.positions[container_id]
        container_size = self.sizes[container_id]
        
        # Apply containment
        element_pos["x"] = max(element_pos["x"], container_pos["x"] + constraint.padding)
        element_pos["x"] = min(element_pos["x"], container_pos["x"] + container_size["width"] - element_size["width"] - constraint.padding)
        element_pos["y"] = max(element_pos["y"], container_pos["y"] + constraint.padding)
        element_pos["y"] = min(element_pos["y"], container_pos["y"] + container_size["height"] - element_size["height"] - constraint.padding)
```

### 3. Implement Visualization

Better visualization of Existential Graphs should be implemented to improve the user experience.

**Tasks:**
- Implement a web-based visualization.
- Implement a desktop visualization.
- Implement a mobile visualization.
- Implement export to various formats (SVG, PNG, PDF).

**Example:**
```python
class EgrfVisualizer:
    """Visualize EGRF data."""
    
    def __init__(self, egrf_data):
        """Initialize the visualizer."""
        self.egrf_data = egrf_data
        self.elements = egrf_data["elements"]
        self.containment = egrf_data["containment"]
        self.connections = egrf_data.get("connections", [])
        self.ligatures = egrf_data.get("ligatures", [])
        self.layout_constraints = egrf_data.get("layout_constraints", [])
        
        # Initialize positions and sizes
        self.positions = {}
        self.sizes = {}
        
        # Apply layout constraints
        self._apply_layout_constraints()
    
    def _apply_layout_constraints(self):
        """Apply layout constraints."""
        # Initialize positions and sizes
        for element_id in self.elements:
            self.positions[element_id] = {"x": 0, "y": 0}
            self.sizes[element_id] = {"width": 100, "height": 50}
        
        # Apply size constraints
        for constraint in self.layout_constraints:
            if constraint["constraint_type"] == "size":
                element_id = constraint["element_id"]
                self.sizes[element_id]["width"] = constraint.get("width", 100)
                self.sizes[element_id]["height"] = constraint.get("height", 50)
        
        # Apply position constraints
        for constraint in self.layout_constraints:
            if constraint["constraint_type"] == "position":
                element_id = constraint["element_id"]
                self.positions[element_id]["x"] = constraint.get("x", 0)
                self.positions[element_id]["y"] = constraint.get("y", 0)
    
    def to_svg(self):
        """Convert EGRF data to SVG."""
        # Create SVG
        svg = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        svg += '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">\n'
        
        # Draw contexts
        for element_id, element in self.elements.items():
            if element["element_type"] == "context":
                svg += self._context_to_svg(element_id, element)
        
        # Draw predicates
        for element_id, element in self.elements.items():
            if element["element_type"] == "predicate":
                svg += self._predicate_to_svg(element_id, element)
        
        # Draw entities
        for element_id, element in self.elements.items():
            if element["element_type"] == "entity":
                svg += self._entity_to_svg(element_id, element)
        
        # Draw connections
        for connection in self.connections:
            svg += self._connection_to_svg(connection)
        
        # Draw ligatures
        for ligature in self.ligatures:
            svg += self._ligature_to_svg(ligature)
        
        svg += '</svg>'
        
        return svg
    
    def _context_to_svg(self, element_id, element):
        """Convert a context to SVG."""
        # Get position and size
        pos = self.positions[element_id]
        size = self.sizes[element_id]
        
        # Get context type
        context_type = element["logical_properties"]["context_type"]
        
        # Set style based on context type
        if context_type == "sheet_of_assertion" or context_type == "sheet":
            fill = "#f0f0f0"
            stroke = "#000000"
            stroke_width = 1
        else:  # cut
            fill = "#e0e0e0"
            stroke = "#000000"
            stroke_width = 2
        
        # Create SVG
        svg = f'<rect id="{element_id}" x="{pos["x"]}" y="{pos["y"]}" width="{size["width"]}" height="{size["height"]}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" rx="10" ry="10" />\n'
        
        # Add name if available
        if "visual_properties" in element and "name" in element["visual_properties"]:
            name = element["visual_properties"]["name"]
            svg += f'<text x="{pos["x"] + 10}" y="{pos["y"] + 20}" font-family="Arial" font-size="12">{name}</text>\n'
        
        return svg
    
    def _predicate_to_svg(self, element_id, element):
        """Convert a predicate to SVG."""
        # Get position and size
        pos = self.positions[element_id]
        size = self.sizes[element_id]
        
        # Create SVG
        svg = f'<rect id="{element_id}" x="{pos["x"]}" y="{pos["y"]}" width="{size["width"]}" height="{size["height"]}" fill="#e0e0ff" stroke="#0000ff" stroke-width="1" rx="5" ry="5" />\n'
        
        # Add name if available
        if "visual_properties" in element and "name" in element["visual_properties"]:
            name = element["visual_properties"]["name"]
            svg += f'<text x="{pos["x"] + size["width"] / 2}" y="{pos["y"] + size["height"] / 2}" font-family="Arial" font-size="12" text-anchor="middle" dominant-baseline="middle">{name}</text>\n'
        
        return svg
    
    def _entity_to_svg(self, element_id, element):
        """Convert an entity to SVG."""
        # Get position and size
        pos = self.positions[element_id]
        size = self.sizes[element_id]
        
        # Create SVG
        svg = f'<circle id="{element_id}" cx="{pos["x"] + size["width"] / 2}" cy="{pos["y"] + size["height"] / 2}" r="{min(size["width"], size["height"]) / 2}" fill="#000000" />\n'
        
        # Add name if available
        if "visual_properties" in element and "name" in element["visual_properties"]:
            name = element["visual_properties"]["name"]
            svg += f'<text x="{pos["x"] + size["width"] / 2}" y="{pos["y"] + size["height"] + 15}" font-family="Arial" font-size="12" text-anchor="middle">{name}</text>\n'
        
        return svg
    
    def _connection_to_svg(self, connection):
        """Convert a connection to SVG."""
        # Get entity and predicate
        entity_id = connection["entity_id"]
        predicate_id = connection["predicate_id"]
        
        # Get positions and sizes
        entity_pos = self.positions[entity_id]
        entity_size = self.sizes[entity_id]
        predicate_pos = self.positions[predicate_id]
        predicate_size = self.sizes[predicate_id]
        
        # Calculate connection points
        entity_x = entity_pos["x"] + entity_size["width"] / 2
        entity_y = entity_pos["y"] + entity_size["height"] / 2
        predicate_x = predicate_pos["x"] + predicate_size["width"] / 2
        predicate_y = predicate_pos["y"] + predicate_size["height"] / 2
        
        # Create SVG
        svg = f'<line x1="{entity_x}" y1="{entity_y}" x2="{predicate_x}" y2="{predicate_y}" stroke="#000000" stroke-width="1" />\n'
        
        return svg
    
    def _ligature_to_svg(self, ligature):
        """Convert a ligature to SVG."""
        # Get entities
        entity1_id = ligature["entity1_id"]
        entity2_id = ligature["entity2_id"]
        
        # Get positions and sizes
        entity1_pos = self.positions[entity1_id]
        entity1_size = self.sizes[entity1_id]
        entity2_pos = self.positions[entity2_id]
        entity2_size = self.sizes[entity2_id]
        
        # Calculate connection points
        entity1_x = entity1_pos["x"] + entity1_size["width"] / 2
        entity1_y = entity1_pos["y"] + entity1_size["height"] / 2
        entity2_x = entity2_pos["x"] + entity2_size["width"] / 2
        entity2_y = entity2_pos["y"] + entity2_size["height"] / 2
        
        # Create SVG
        svg = f'<line x1="{entity1_x}" y1="{entity1_y}" x2="{entity2_x}" y2="{entity2_y}" stroke="#000000" stroke-width="2" stroke-dasharray="5,5" />\n'
        
        return svg
    
    def to_png(self, width=800, height=600):
        """Convert EGRF data to PNG."""
        # Generate SVG
        svg_data = self.to_svg()
        
        # Convert SVG to PNG
        import cairosvg
        png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'), output_width=width, output_height=height)
        
        return png_data
    
    def to_pdf(self, width=800, height=600):
        """Convert EGRF data to PDF."""
        # Generate SVG
        svg_data = self.to_svg()
        
        # Convert SVG to PDF
        import cairosvg
        pdf_data = cairosvg.svg2pdf(bytestring=svg_data.encode('utf-8'), output_width=width, output_height=height)
        
        return pdf_data
```

## Conclusion

This document outlines the next steps for the EGRF v3.0 implementation, providing a roadmap for future development. By following these steps, the EGRF v3.0 implementation can be completed and enhanced to provide a robust platform for working with Peirce's Existential Graphs.

