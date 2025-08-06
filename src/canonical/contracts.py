"""
Canonical API Contract Enforcement

This module provides runtime validation and contract enforcement for the canonical core.
All canonical operations are protected by these contracts to ensure API stability.
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from functools import wraps
import inspect
from dataclasses import dataclass

# Import canonical types
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
from egdf_parser import EGDFDocument

T = TypeVar('T')

@dataclass
class ContractViolation(Exception):
    """Exception raised when a canonical contract is violated."""
    contract_name: str
    violation_type: str
    details: str
    
    def __str__(self) -> str:
        return f"Contract '{self.contract_name}' violated: {self.violation_type} - {self.details}"

class CanonicalContractValidator:
    """Validates canonical API contracts at runtime."""
    
    @staticmethod
    def validate_egi_structure(egi: RelationalGraphWithCuts, contract_name: str = "EGI Structure") -> None:
        """Validate that an EGI structure is well-formed."""
        if not isinstance(egi, RelationalGraphWithCuts):
            raise ContractViolation(
                contract_name, 
                "Type Error", 
                f"Expected RelationalGraphWithCuts, got {type(egi)}"
            )
        
        # Validate vertex set (Dau's Component 1)
        if not hasattr(egi, 'V') or not hasattr(egi.V, '__iter__'):
            raise ContractViolation(
                contract_name,
                "Structure Error",
                "EGI must have vertex set 'V' (Dau Component 1)"
            )
        
        # Validate edge set (Dau's Component 2)
        if not hasattr(egi, 'E') or not hasattr(egi.E, '__iter__'):
            raise ContractViolation(
                contract_name,
                "Structure Error", 
                "EGI must have edge set 'E' (Dau Component 2)"
            )
        
        # Validate cut set (Dau's Component 5)
        if not hasattr(egi, 'Cut') or not hasattr(egi.Cut, '__iter__'):
            raise ContractViolation(
                contract_name,
                "Structure Error",
                "EGI must have cut set 'Cut' (Dau Component 5)"
            )
        
        # Validate nu mapping (Dau's Component 3)
        if not hasattr(egi, 'nu') or not hasattr(egi.nu, '__getitem__'):
            raise ContractViolation(
                contract_name,
                "Structure Error",
                "EGI must have nu mapping 'nu' (Dau Component 3)"
            )
        
        # Validate sheet (Dau's Component 4)
        if not hasattr(egi, 'sheet'):
            raise ContractViolation(
                contract_name,
                "Structure Error",
                "EGI must have sheet 'sheet' (Dau Component 4)"
            )
        
        # Validate area mapping (Dau's Component 6)
        if not hasattr(egi, 'area') or not hasattr(egi.area, '__getitem__'):
            raise ContractViolation(
                contract_name,
                "Structure Error",
                "EGI must have area mapping 'area' (Dau Component 6)"
            )
        
        # Validate rel mapping (Dau's Component 7)
        if not hasattr(egi, 'rel') or not hasattr(egi.rel, '__getitem__'):
            raise ContractViolation(
                contract_name,
                "Structure Error",
                "EGI must have rel mapping 'rel' (Dau Component 7)"
            )
    
    @staticmethod
    def validate_egdf_document(egdf_doc: EGDFDocument, contract_name: str = "EGDF Document") -> None:
        """Validate that an EGDF document is well-formed."""
        if not isinstance(egdf_doc, EGDFDocument):
            raise ContractViolation(
                contract_name,
                "Type Error",
                f"Expected EGDFDocument, got {type(egdf_doc)}"
            )
        
        # Validate required fields
        required_fields = ['format', 'canonical_egi', 'visual_layout']
        for field in required_fields:
            if not hasattr(egdf_doc, field):
                raise ContractViolation(
                    contract_name,
                    "Structure Error",
                    f"EGDF document missing required field: {field}"
                )
    
    @staticmethod
    def validate_round_trip_integrity(
        original_egi: RelationalGraphWithCuts, 
        reconstructed_egi: RelationalGraphWithCuts,
        contract_name: str = "Round-trip Integrity"
    ) -> None:
        """Validate that round-trip preserves EGI structure."""
        # Validate both are well-formed EGIs
        CanonicalContractValidator.validate_egi_structure(original_egi, f"{contract_name} (Original)")
        CanonicalContractValidator.validate_egi_structure(reconstructed_egi, f"{contract_name} (Reconstructed)")
        
        # Validate structural preservation
        if len(original_egi.V) != len(reconstructed_egi.V):
            raise ContractViolation(
                contract_name,
                "Structure Mismatch",
                f"Vertex count changed: {len(original_egi.V)} → {len(reconstructed_egi.V)}"
            )
        
        if len(original_egi.E) != len(reconstructed_egi.E):
            raise ContractViolation(
                contract_name,
                "Structure Mismatch", 
                f"Edge count changed: {len(original_egi.E)} → {len(reconstructed_egi.E)}"
            )
        
        if len(original_egi.Cut) != len(reconstructed_egi.Cut):
            raise ContractViolation(
                contract_name,
                "Structure Mismatch",
                f"Cut count changed: {len(original_egi.Cut)} → {len(reconstructed_egi.Cut)}"
            )
        
        # Validate nu mapping preservation (critical for argument order)
        if original_egi.nu != reconstructed_egi.nu:
            raise ContractViolation(
                contract_name,
                "Semantic Mismatch",
                "Nu mapping (argument order) not preserved in round-trip"
            )

def enforce_canonical_contract(
    input_types: Optional[Dict[str, Type]] = None,
    output_type: Optional[Type] = None,
    validate_round_trip: bool = False,
    contract_name: Optional[str] = None
):
    """Decorator to enforce canonical API contracts."""
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Get contract name from function if not provided
        actual_contract_name = contract_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Get function signature for parameter mapping
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate input types
            if input_types:
                for param_name, expected_type in input_types.items():
                    if param_name in bound_args.arguments:
                        value = bound_args.arguments[param_name]
                        if value is not None and not isinstance(value, expected_type):
                            raise ContractViolation(
                                actual_contract_name,
                                "Input Type Error",
                                f"Parameter '{param_name}' expected {expected_type}, got {type(value)}"
                            )
            
            # Validate specific input contracts
            for param_name, value in bound_args.arguments.items():
                if isinstance(value, RelationalGraphWithCuts):
                    CanonicalContractValidator.validate_egi_structure(value, f"{actual_contract_name} (Input {param_name})")
                elif isinstance(value, EGDFDocument):
                    CanonicalContractValidator.validate_egdf_document(value, f"{actual_contract_name} (Input {param_name})")
            
            # Execute function
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                raise ContractViolation(
                    actual_contract_name,
                    "Execution Error",
                    f"Function execution failed: {str(e)}"
                )
            
            # Validate output type
            if output_type and result is not None:
                if not isinstance(result, output_type):
                    raise ContractViolation(
                        actual_contract_name,
                        "Output Type Error", 
                        f"Expected {output_type}, got {type(result)}"
                    )
            
            # Validate specific output contracts
            if isinstance(result, RelationalGraphWithCuts):
                CanonicalContractValidator.validate_egi_structure(result, f"{actual_contract_name} (Output)")
            elif isinstance(result, EGDFDocument):
                CanonicalContractValidator.validate_egdf_document(result, f"{actual_contract_name} (Output)")
            
            # Validate round-trip integrity if requested
            if validate_round_trip and len(args) > 0:
                if isinstance(args[0], RelationalGraphWithCuts) and isinstance(result, RelationalGraphWithCuts):
                    CanonicalContractValidator.validate_round_trip_integrity(
                        args[0], result, f"{actual_contract_name} (Round-trip)"
                    )
            
            return result
        
        # Add contract metadata to function
        wrapper.__canonical_contract__ = {
            'name': actual_contract_name,
            'input_types': input_types or {},
            'output_type': output_type,
            'validate_round_trip': validate_round_trip
        }
        
        return wrapper
    
    return decorator

class CanonicalContractEnforcer:
    """Central enforcer for canonical contracts."""
    
    _active_contracts: Dict[str, Dict[str, Any]] = {}
    _violation_log: List[ContractViolation] = []
    
    @classmethod
    def register_contract(cls, func: Callable, contract_info: Dict[str, Any]) -> None:
        """Register a canonical contract."""
        contract_name = contract_info['name']
        cls._active_contracts[contract_name] = contract_info
        print(f"✅ Registered canonical contract: {contract_name}")
    
    @classmethod
    def log_violation(cls, violation: ContractViolation) -> None:
        """Log a contract violation."""
        cls._violation_log.append(violation)
        print(f"❌ Contract violation: {violation}")
    
    @classmethod
    def get_contract_status(cls) -> Dict[str, Any]:
        """Get status of all canonical contracts."""
        return {
            'active_contracts': len(cls._active_contracts),
            'contract_names': list(cls._active_contracts.keys()),
            'total_violations': len(cls._violation_log),
            'recent_violations': cls._violation_log[-5:] if cls._violation_log else []
        }
    
    @classmethod
    def validate_all_contracts(cls) -> bool:
        """Validate that all registered contracts are functioning."""
        try:
            for contract_name, contract_info in cls._active_contracts.items():
                print(f"✅ Contract '{contract_name}' is active")
            return True
        except Exception as e:
            print(f"❌ Contract validation failed: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    print("🎯 CANONICAL CONTRACT ENFORCEMENT")
    print("=" * 50)
    
    # Test contract validation
    try:
        from egi_core_dau import RelationalGraphWithCuts
        
        # Create a test EGI
        test_egi = RelationalGraphWithCuts()
        CanonicalContractValidator.validate_egi_structure(test_egi)
        print("✅ EGI structure validation passed")
        
    except ContractViolation as e:
        print(f"❌ Contract validation failed: {e}")
    
    print(f"Contract status: {CanonicalContractEnforcer.get_contract_status()}")
