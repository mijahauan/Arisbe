"""
EGI export module for Ergasterion.

Provides functionality to export drawing editor content to various formats
including EGI, EGIF, CGIF, and CLIF with proper validation and formatting.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, create_vertex, create_edge, create_cut
from egif_generator_dau import EGIFGenerator
from drawing_to_egi_adapter import drawing_to_relational_graph
from frozendict import frozendict


class ExportFormat(Enum):
    """Supported export formats."""
    EGI_JSON = "egi_json"
    EGIF = "egif"
    CGIF = "cgif"
    CLIF = "clif"
    DRAWING_SCHEMA = "drawing_schema"


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    content: Optional[str] = None
    file_path: Optional[Path] = None
    format: Optional[ExportFormat] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class EGIExporter:
    """Handles export of drawing editor content to various formats."""
    
    def __init__(self):
        self.validation_enabled = True
        self.include_metadata = True
    
    def export_drawing_schema(self, drawing_schema: Dict, 
                            format: ExportFormat, 
                            output_path: Optional[Path] = None) -> ExportResult:
        """Export drawing schema to specified format."""
        try:
            # First convert to EGI
            egi_result = self._convert_to_egi(drawing_schema)
            if not egi_result.success:
                return egi_result
            
            egi = egi_result.egi
            
            # Then export to target format
            if format == ExportFormat.EGI_JSON:
                return self._export_egi_json(egi, drawing_schema, output_path)
            elif format == ExportFormat.EGIF:
                return self._export_egif(egi, drawing_schema, output_path)
            elif format == ExportFormat.CGIF:
                return self._export_cgif(egi, drawing_schema, output_path)
            elif format == ExportFormat.CLIF:
                return self._export_clif(egi, drawing_schema, output_path)
            elif format == ExportFormat.DRAWING_SCHEMA:
                return self._export_drawing_schema(drawing_schema, output_path)
            else:
                return ExportResult(
                    success=False,
                    errors=[f"Unsupported export format: {format}"]
                )
        
        except Exception as e:
            return ExportResult(
                success=False,
                errors=[f"Export failed: {str(e)}"]
            )
    
    def _convert_to_egi(self, drawing_schema: Dict) -> 'EGIConversionResult':
        """Convert drawing schema to EGI structure."""
        try:
            # Use the existing drawing_to_egi_adapter
            egi = drawing_to_relational_graph(drawing_schema)
            
            # Validate if enabled
            errors = []
            warnings = []
            
            if self.validation_enabled:
                validation_errors = self._validate_egi(egi)
                if validation_errors:
                    errors.extend(validation_errors)
            
            return EGIConversionResult(
                success=len(errors) == 0,
                egi=egi,
                errors=errors,
                warnings=warnings
            )
        
        except Exception as e:
            return EGIConversionResult(
                success=False,
                errors=[f"EGI conversion failed: {str(e)}"]
            )
    
    def _validate_egi(self, egi: RelationalGraphWithCuts) -> List[str]:
        """Validate EGI structure."""
        errors = []
        
        try:
            # The EGI constructor already validates Dau constraints
            # Additional validation can be added here
            
            # Check for empty graph
            if not egi.V and not egi.E and not egi.Cut:
                errors.append("Graph is empty")
            
            # Check for orphaned vertices (not connected to any edge)
            connected_vertices = set()
            for edge_id, vertex_sequence in egi.nu.items():
                connected_vertices.update(vertex_sequence)
            
            orphaned = set(v.id for v in egi.V) - connected_vertices
            if orphaned:
                errors.append(f"Orphaned vertices found: {', '.join(orphaned)}")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def _export_egi_json(self, egi: RelationalGraphWithCuts, 
                        drawing_schema: Dict, 
                        output_path: Optional[Path]) -> ExportResult:
        """Export to EGI JSON format."""
        try:
            # Create comprehensive EGI representation
            egi_data = {
                "format": "egi_json",
                "version": "1.0",
                "egi": {
                    "vertices": [
                        {
                            "id": v.id,
                            "label": v.label,
                            "is_generic": v.is_generic
                        }
                        for v in egi.V
                    ],
                    "edges": [
                        {
                            "id": e.id,
                            "relation": egi.rel.get(e.id, ""),
                            "vertex_sequence": egi.nu.get(e.id, [])
                        }
                        for e in egi.E
                    ],
                    "cuts": [
                        {
                            "id": c.id,
                            "area_contents": list(egi.area.get(c.id, []))
                        }
                        for c in egi.Cut
                    ],
                    "sheet": egi.sheet,
                    "area_mapping": dict(egi.area)
                }
            }
            
            if self.include_metadata:
                egi_data["metadata"] = {
                    "source": "ergasterion_composer",
                    "drawing_schema": drawing_schema.get("workshop_metadata", {}),
                    "export_timestamp": self._get_timestamp()
                }
            
            content = json.dumps(egi_data, indent=2)
            
            if output_path:
                output_path.write_text(content, encoding='utf-8')
                return ExportResult(
                    success=True,
                    content=content,
                    file_path=output_path,
                    format=ExportFormat.EGI_JSON
                )
            else:
                return ExportResult(
                    success=True,
                    content=content,
                    format=ExportFormat.EGI_JSON
                )
        
        except Exception as e:
            return ExportResult(
                success=False,
                errors=[f"EGI JSON export failed: {str(e)}"]
            )
    
    def _export_egif(self, egi: RelationalGraphWithCuts, 
                    drawing_schema: Dict, 
                    output_path: Optional[Path]) -> ExportResult:
        """Export to EGIF format."""
        try:
            generator = EGIFGenerator(egi)
            egif_content = generator.generate()
            
            # Add metadata as comments if enabled
            if self.include_metadata:
                metadata_lines = [
                    f"# Generated by Ergasterion Composer/Editor",
                    f"# Export timestamp: {self._get_timestamp()}"
                ]
                
                # Add source information if available
                corpus_meta = drawing_schema.get("corpus_metadata")
                if corpus_meta:
                    metadata_lines.extend([
                        f"# Source: {corpus_meta.get('title', 'Unknown')}",
                        f"# Category: {corpus_meta.get('category', 'Unknown')}"
                    ])
                
                content = "\n".join(metadata_lines) + "\n\n" + egif_content
            else:
                content = egif_content
            
            if output_path:
                output_path.write_text(content, encoding='utf-8')
                return ExportResult(
                    success=True,
                    content=content,
                    file_path=output_path,
                    format=ExportFormat.EGIF
                )
            else:
                return ExportResult(
                    success=True,
                    content=content,
                    format=ExportFormat.EGIF
                )
        
        except Exception as e:
            return ExportResult(
                success=False,
                errors=[f"EGIF export failed: {str(e)}"]
            )
    
    def _export_cgif(self, egi: RelationalGraphWithCuts, 
                    drawing_schema: Dict, 
                    output_path: Optional[Path]) -> ExportResult:
        """Export to CGIF format."""
        try:
            # Would use CGIF generator when available
            # For now, return a placeholder
            content = "# CGIF export not yet implemented\n# Use EGIF export instead"
            
            return ExportResult(
                success=False,
                errors=["CGIF export not yet implemented"],
                warnings=["Use EGIF export instead"]
            )
        
        except Exception as e:
            return ExportResult(
                success=False,
                errors=[f"CGIF export failed: {str(e)}"]
            )
    
    def _export_clif(self, egi: RelationalGraphWithCuts, 
                    drawing_schema: Dict, 
                    output_path: Optional[Path]) -> ExportResult:
        """Export to CLIF format."""
        try:
            # Would use CLIF generator when available
            # For now, return a placeholder
            content = "# CLIF export not yet implemented\n# Use EGIF export instead"
            
            return ExportResult(
                success=False,
                errors=["CLIF export not yet implemented"],
                warnings=["Use EGIF export instead"]
            )
        
        except Exception as e:
            return ExportResult(
                success=False,
                errors=[f"CLIF export failed: {str(e)}"]
            )
    
    def _export_drawing_schema(self, drawing_schema: Dict, 
                              output_path: Optional[Path]) -> ExportResult:
        """Export drawing schema as JSON."""
        try:
            if self.include_metadata:
                schema_with_meta = dict(drawing_schema)
                schema_with_meta["export_metadata"] = {
                    "format": "drawing_schema",
                    "version": "1.0",
                    "exported_by": "ergasterion_composer",
                    "export_timestamp": self._get_timestamp()
                }
                content = json.dumps(schema_with_meta, indent=2)
            else:
                content = json.dumps(drawing_schema, indent=2)
            
            if output_path:
                output_path.write_text(content, encoding='utf-8')
                return ExportResult(
                    success=True,
                    content=content,
                    file_path=output_path,
                    format=ExportFormat.DRAWING_SCHEMA
                )
            else:
                return ExportResult(
                    success=True,
                    content=content,
                    format=ExportFormat.DRAWING_SCHEMA
                )
        
        except Exception as e:
            return ExportResult(
                success=False,
                errors=[f"Drawing schema export failed: {str(e)}"]
            )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for metadata."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_supported_formats(self) -> List[ExportFormat]:
        """Get list of supported export formats."""
        return [
            ExportFormat.EGI_JSON,
            ExportFormat.EGIF,
            ExportFormat.DRAWING_SCHEMA
            # CGIF and CLIF would be added when implemented
        ]
    
    def validate_drawing_schema(self, drawing_schema: Dict) -> List[str]:
        """Validate drawing schema before export."""
        errors = []
        
        # Check required fields
        required_fields = ["sheet_id", "cuts", "vertices", "predicates", "ligatures"]
        for field in required_fields:
            if field not in drawing_schema:
                errors.append(f"Missing required field: {field}")
        
        # Check data types
        if "cuts" in drawing_schema and not isinstance(drawing_schema["cuts"], list):
            errors.append("Field 'cuts' must be a list")
        
        if "vertices" in drawing_schema and not isinstance(drawing_schema["vertices"], list):
            errors.append("Field 'vertices' must be a list")
        
        if "predicates" in drawing_schema and not isinstance(drawing_schema["predicates"], list):
            errors.append("Field 'predicates' must be a list")
        
        if "ligatures" in drawing_schema and not isinstance(drawing_schema["ligatures"], list):
            errors.append("Field 'ligatures' must be a list")
        
        return errors


@dataclass
class EGIConversionResult:
    """Result of converting drawing schema to EGI."""
    success: bool
    egi: Optional[RelationalGraphWithCuts] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ExportManager:
    """High-level export management for Ergasterion."""
    
    def __init__(self):
        self.exporter = EGIExporter()
        self.default_output_dir = Path("exports")
        self.default_output_dir.mkdir(exist_ok=True)
    
    def export_with_dialog(self, drawing_schema: Dict, 
                          suggested_name: str = "graph") -> ExportResult:
        """Export with file dialog (placeholder for GUI integration)."""
        # This would integrate with Qt file dialog in the actual GUI
        # For now, export to default location
        
        output_path = self.default_output_dir / f"{suggested_name}.egif"
        return self.exporter.export_drawing_schema(
            drawing_schema, 
            ExportFormat.EGIF, 
            output_path
        )
    
    def quick_export_egif(self, drawing_schema: Dict, name: str = None) -> ExportResult:
        """Quick export to EGIF format."""
        if name is None:
            name = f"graph_{self._get_timestamp_short()}"
        
        output_path = self.default_output_dir / f"{name}.egif"
        return self.exporter.export_drawing_schema(
            drawing_schema,
            ExportFormat.EGIF,
            output_path
        )
    
    def export_to_string(self, drawing_schema: Dict, 
                        format: ExportFormat) -> ExportResult:
        """Export to string without saving to file."""
        return self.exporter.export_drawing_schema(drawing_schema, format, None)
    
    def _get_timestamp_short(self) -> str:
        """Get short timestamp for filenames."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")


# Global export manager instance
_export_manager = None

def get_export_manager() -> ExportManager:
    """Get the global export manager instance."""
    global _export_manager
    if _export_manager is None:
        _export_manager = ExportManager()
    return _export_manager

