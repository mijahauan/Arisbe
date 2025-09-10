{{ ... }}
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
{{ ... }}

class TransformationEngine:
    """
    Primary interface for all EG operations with transformation rule governance.
    
    Now supports history callbacks to record all transformations in the
    historical graph model for complete provenance tracking.
    """
    
    def __init__(self, spatial_tracker: RTreeCutTracker, 
                 history_callback: Optional[Callable[[OperationRequest, OperationResult], None]] = None):
        self.spatial_tracker = spatial_tracker
        self.history_callback = history_callback
        
        # Initialize transformation rules
        self.rules = {
            TransformationRuleType.INSERTION: InsertionRule(),
            TransformationRuleType.ERASURE: ErasureRule(),
            # Additional rules would be added here
        }
        
        # Operation mapping
        self.operation_to_rule = {
            OperationType.ADD_VERTEX: TransformationRuleType.INSERTION,
            OperationType.ADD_EDGE: TransformationRuleType.INSERTION,
            OperationType.ADD_CUT: TransformationRuleType.INSERTION,
            OperationType.REMOVE_VERTEX: TransformationRuleType.ERASURE,
            OperationType.REMOVE_EDGE: TransformationRuleType.ERASURE,
            OperationType.REMOVE_CUT: TransformationRuleType.ERASURE,
        }
    
    def apply_operation(self, graph: RelationalGraphWithCuts, 
                       operation: OperationRequest) -> OperationResult:
        """
        Apply an operation with transformation rule validation and history recording.
        """
        # Get appropriate transformation rule
        rule_type = self.operation_to_rule.get(operation.operation_type)
        if not rule_type:
            result = OperationResult(
                success=False,
                error_message=f"No transformation rule for operation: {operation.operation_type}",
                operation_request=operation
            )
            self._record_in_history(operation, result)
            return result
        
        rule = self.rules[rule_type]
        
        # Create transformation context
        context = self._create_transformation_context(graph, operation)
        
        # Validate operation
        validation = rule.validate(graph, context)
        if not validation.is_valid:
            result = OperationResult(
                success=False,
                error_message=validation.error_message,
                validation_suggestions=validation.suggestions,
                operation_request=operation
            )
            self._record_in_history(operation, result)
            return result
        
        # Apply transformation
        transformation_result = rule.apply(graph, context)
        
        # Update spatial representation if successful
        operation_result = OperationResult(
            success=transformation_result.success,
            modified_graph=transformation_result.modified_graph,
            spatial_updates=transformation_result.spatial_updates,
            error_message=transformation_result.error_message,
            operation_request=operation
        )
        
        if transformation_result.success and transformation_result.spatial_updates:
            self._apply_spatial_updates(transformation_result.spatial_updates)
        
        # Record in history
        self._record_in_history(operation, operation_result)
        
        return operation_result
    
    def _record_in_history(self, operation: OperationRequest, result: OperationResult):
        """Record the operation and result in history if callback is provided."""
        if self.history_callback:
            self.history_callback(operation, result)
    
    def apply_operation_sequence(self, graph: RelationalGraphWithCuts,
                               operations: List[OperationRequest]) -> List[OperationResult]:
        """
        Apply a sequence of operations with history tracking for each step.
        """
        results = []
        current_graph = graph
        
        for operation in operations:
            result = self.apply_operation(current_graph, operation)
            results.append(result)
            
            # Update graph for next operation if successful
            if result.success and result.modified_graph:
                current_graph = result.modified_graph
        
        return results
    
    def replay_transformation_sequence(self, initial_graph: RelationalGraphWithCuts,
                                     sequence: CompositionSequence) -> OperationResult:
        """
        Replay a transformation sequence from the historical model.
        """
        current_graph = initial_graph
        
        for step in sequence.steps:
            result = self.apply_operation(current_graph, step.operation)
            
            if not result.success:
                return OperationResult(
                    success=False,
                    error_message=f"Replay failed at step: {step.step_description}. {result.error_message}",
                    operation_request=step.operation
                )
            
            if result.modified_graph:
                current_graph = result.modified_graph
        
        return OperationResult(
            success=True,
            modified_graph=current_graph,
            operation_request=None  # This is a composite operation
        )
{{ ... }}
