"""
EG Constraint Validator

Implements logical constraints for existential graph manipulation
following Peirce's rules for valid transformations.
"""

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtWidgets import QGraphicsItem


class EGConstraintValidator:
    """Validates existential graph constraints and transformations"""
    
    def __init__(self, scene):
        self.scene = scene
        
    def validate_node_move(self, node, new_position):
        """
        Validate if a node can be moved to a new position
        
        Args:
            node: GraphicsNode being moved
            new_position: QPointF of proposed new position
            
        Returns:
            tuple: (is_valid: bool, reason: str)
        """
        # Get node's variable bindings
        node_vars = self.get_node_variables(node)
        
        if not node_vars:
            # Nodes without variables can move freely on the sheet
            return True, "No variable constraints"
            
        # Find the contexts that bind these variables
        binding_contexts = self.find_binding_contexts(node_vars)
        
        # Check if new position is within at least one binding context
        for context in binding_contexts:
            if self.is_position_within_context(new_position, node, context):
                return True, "Within valid scope"
                
        # If node has variables but isn't in any binding context
        if binding_contexts:
            return False, f"Variables {node_vars} must stay within their binding scope"
        else:
            # Variables exist but no binding context found - this is complex
            # For now, allow it but this needs more sophisticated logic
            return True, "No binding context found (complex case)"
            
    def get_node_variables(self, node):
        """Extract variables from a node"""
        if not hasattr(node, 'node_data') or not node.node_data:
            return []
            
        if isinstance(node.node_data, dict):
            return node.node_data.get('args', [])
        elif hasattr(node.node_data, 'args'):
            return node.node_data.args
        else:
            return []
            
    def find_binding_contexts(self, variables):
        """Find contexts that bind the given variables"""
        binding_contexts = []
        
        for item in self.scene.items():
            if self.is_context_item(item):
                context_vars = self.get_context_variables(item)
                
                # Check if this context binds any of our variables
                if any(var in context_vars for var in variables):
                    binding_contexts.append(item)
                    
        return binding_contexts
        
    def is_context_item(self, item):
        """Check if an item represents a context (cut)"""
        # Look for elliptical contexts or items with context data
        from gui.widgets.graph_canvas import GraphicsContext
        
        if isinstance(item, GraphicsContext):
            return True
            
        # Check for elliptical items that might be contexts
        if hasattr(item, 'boundingRect') and hasattr(item, 'pen'):
            # Look for associated scope labels to identify contexts
            for child in item.childItems():
                if hasattr(child, 'toPlainText'):
                    text = child.toPlainText()
                    if 'scope' in text.lower():
                        return True
                        
        return False
        
    def get_context_variables(self, context):
        """Get variables bound by a context"""
        # Look for scope labels or context data
        variables = []
        
        # Check child items for scope labels
        for child in context.childItems():
            if hasattr(child, 'toPlainText'):
                text = child.toPlainText()
                if 'scope of' in text.lower():
                    # Extract variables from "scope of x, y" format
                    parts = text.lower().split('scope of')
                    if len(parts) > 1:
                        var_part = parts[1].strip()
                        variables.extend([v.strip() for v in var_part.split(',')])
                        
        # Also check for context data
        if hasattr(context, 'context_data') and context.context_data:
            if isinstance(context.context_data, dict):
                context_vars = context.context_data.get('variables', [])
                variables.extend(context_vars)
                
        return variables
        
    def is_position_within_context(self, position, node, context):
        """Check if a position is within a context boundary"""
        # Get context boundaries
        context_rect = context.boundingRect()
        context_pos = context.pos()
        
        # Transform to scene coordinates
        scene_rect = QRectF(
            context_pos.x() + context_rect.x(),
            context_pos.y() + context_rect.y(),
            context_rect.width(),
            context_rect.height()
        )
        
        # Get node dimensions
        node_rect = node.boundingRect()
        
        # Check if the center of the node at new position is within context
        node_center = QPointF(
            position.x() + node_rect.width() / 2,
            position.y() + node_rect.height() / 2
        )
        
        return scene_rect.contains(node_center)
        
    def validate_context_move(self, context, new_position):
        """
        Validate if a context can be moved to a new position
        
        Args:
            context: GraphicsContext being moved
            new_position: QPointF of proposed new position
            
        Returns:
            tuple: (is_valid: bool, reason: str)
        """
        # Contexts can generally be moved, but we need to check:
        # 1. They don't move outside their containing context
        # 2. They don't leave behind nodes that depend on them
        
        # For now, allow context moves but this needs more logic
        return True, "Context moves allowed (needs refinement)"
        
    def validate_ligature_modification(self, ligature, modification_type):
        """
        Validate ligature (line of identity) modifications
        
        Args:
            ligature: GraphicsLigature being modified
            modification_type: str ('move', 'delete', 'extend')
            
        Returns:
            tuple: (is_valid: bool, reason: str)
        """
        # Lines of identity have strict rules:
        # 1. They must connect predicates with the same variable
        # 2. They cannot be broken if they're the only connection
        # 3. They must stay within the scope of their variable
        
        if modification_type == 'delete':
            # Check if this is the only connection for a variable
            variable = self.get_ligature_variable(ligature)
            if variable:
                other_connections = self.find_other_ligatures_for_variable(ligature, variable)
                if not other_connections:
                    return False, f"Cannot delete the only connection for variable {variable}"
                    
        return True, "Ligature modification allowed"
        
    def get_ligature_variable(self, ligature):
        """Get the variable represented by a ligature"""
        if hasattr(ligature, 'ligature_data') and ligature.ligature_data:
            if isinstance(ligature.ligature_data, dict):
                return ligature.ligature_data.get('variable')
            elif hasattr(ligature.ligature_data, 'variable'):
                return ligature.ligature_data.variable
        return None
        
    def find_other_ligatures_for_variable(self, current_ligature, variable):
        """Find other ligatures that represent the same variable"""
        other_ligatures = []
        
        for item in self.scene.items():
            if item != current_ligature and hasattr(item, 'ligature_data'):
                item_var = self.get_ligature_variable(item)
                if item_var == variable:
                    other_ligatures.append(item)
                    
        return other_ligatures
        
    def suggest_valid_position(self, node, attempted_position):
        """
        Suggest a valid position near the attempted position
        
        Args:
            node: GraphicsNode being moved
            attempted_position: QPointF that was invalid
            
        Returns:
            QPointF: Suggested valid position
        """
        node_vars = self.get_node_variables(node)
        
        if not node_vars:
            return attempted_position  # No constraints
            
        # Find the nearest valid context
        binding_contexts = self.find_binding_contexts(node_vars)
        
        if not binding_contexts:
            return attempted_position  # No binding contexts
            
        # Find the closest context to the attempted position
        closest_context = None
        min_distance = float('inf')
        
        for context in binding_contexts:
            context_center = self.get_context_center(context)
            distance = self.distance(attempted_position, context_center)
            
            if distance < min_distance:
                min_distance = distance
                closest_context = context
                
        if closest_context:
            # Position the node near the center of the closest valid context
            return self.get_context_center(closest_context)
        else:
            return attempted_position
            
    def get_context_center(self, context):
        """Get the center point of a context"""
        rect = context.boundingRect()
        pos = context.pos()
        
        return QPointF(
            pos.x() + rect.x() + rect.width() / 2,
            pos.y() + rect.y() + rect.height() / 2
        )
        
    def distance(self, point1, point2):
        """Calculate distance between two points"""
        dx = point1.x() - point2.x()
        dy = point1.y() - point2.y()
        return (dx * dx + dy * dy) ** 0.5

