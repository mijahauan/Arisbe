"""
Integrated Export Manager

This module provides a unified export system that integrates with the core Dau
formalism manager to provide validated, comprehensive export functionality
for all supported linear forms and formats.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import logging
from datetime import datetime

# Core formalism integration
from .core_dau_formalism import CoreDauFormalismManager, LinearFormat, get_dau_formalism_manager
from .dau_chapters_integration import get_dau_chapters_manager
from .egi_core_dau import RelationalGraphWithCuts
from .integration_interfaces import ExportManager as ExportManagerProtocol


class ExportFormat(Enum):
    """Supported export formats."""
    EGIF = "egif"
    CGIF = "cgif"
    CLIF = "clif"
    FOPL = "fopl"
    JSON = "json"
    XML = "xml"
    SVG = "svg"
    TIKZ = "tikz"


class ExportQuality(Enum):
    """Export quality levels."""
    DRAFT = "draft"
    STANDARD = "standard"
    PUBLICATION = "publication"
    ARCHIVAL = "archival"


@dataclass
class ExportConfiguration:
    """Configuration for export operations."""
    format: ExportFormat
    quality: ExportQuality = ExportQuality.STANDARD
    include_metadata: bool = True
    include_validation: bool = True
    validate_before_export: bool = True
    pretty_print: bool = True
    include_comments: bool = False
    chapter_compliance_check: bool = False
    custom_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    content: Optional[str] = None
    file_path: Optional[Path] = None
    format: Optional[ExportFormat] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    export_timestamp: Optional[str] = None


class LinearFormExporter:
    """Handles export to linear forms (EGIF, CGIF, CLIF, FOPL)."""
    
    def __init__(self, core_manager: CoreDauFormalismManager):
        self.core_manager = core_manager
        self.logger = logging.getLogger(__name__)
    
    def export(self, egi: RelationalGraphWithCuts, config: ExportConfiguration) -> ExportResult:
        """Export EGI to linear form."""
        try:
            # Map export format to linear format
            linear_format_map = {
                ExportFormat.EGIF: LinearFormat.EGIF,
                ExportFormat.CGIF: LinearFormat.CGIF,
                ExportFormat.CLIF: LinearFormat.CLIF,
                ExportFormat.FOPL: LinearFormat.FOPL
            }
            
            linear_format = linear_format_map.get(config.format)
            if not linear_format:
                raise ValueError(f"Unsupported linear format: {config.format}")
            
            # Validate if requested
            validation_results = {}
            if config.validate_before_export:
                validation_results = self.core_manager.validate_egi(egi)
                if not validation_results.get("overall_valid", False):
                    if config.quality == ExportQuality.PUBLICATION:
                        return ExportResult(
                            success=False,
                            format=config.format,
                            errors=[f"EGI validation failed: {validation_results.get('errors', [])}"],
                            validation_results=validation_results
                        )
            
            # Generate linear form
            content = self.core_manager.generate_linear_form(egi, linear_format)
            
            # Add metadata and comments if requested
            if config.include_metadata or config.include_comments:
                content = self._add_metadata_comments(content, egi, config, validation_results)
            
            return ExportResult(
                success=True,
                content=content,
                format=config.format,
                metadata=self._generate_export_metadata(egi, config),
                validation_results=validation_results,
                export_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"Linear form export failed: {e}")
            return ExportResult(
                success=False,
                format=config.format,
                errors=[str(e)]
            )
    
    def _add_metadata_comments(self, content: str, egi: RelationalGraphWithCuts, 
                              config: ExportConfiguration, validation_results: Dict[str, Any]) -> str:
        """Add metadata and comments to exported content."""
        lines = []
        
        if config.include_comments:
            lines.append(f"# Exported from Arisbe EGI System")
            lines.append(f"# Export timestamp: {datetime.now().isoformat()}")
            lines.append(f"# Format: {config.format.value.upper()}")
            lines.append(f"# Quality: {config.quality.value}")
            
            if validation_results:
                lines.append(f"# Validation status: {'VALID' if validation_results.get('overall_valid') else 'INVALID'}")
            
            lines.append("")
        
        lines.append(content)
        return "\n".join(lines)
    
    def _generate_export_metadata(self, egi: RelationalGraphWithCuts, config: ExportConfiguration) -> Dict[str, Any]:
        """Generate metadata for export."""
        return {
            "export_format": config.format.value,
            "export_quality": config.quality.value,
            "export_timestamp": datetime.now().isoformat(),
            "egi_statistics": {
                "vertex_count": len(egi.V) if hasattr(egi, 'V') else 0,
                "edge_count": len(egi.E) if hasattr(egi, 'E') else 0,
                "cut_count": len(egi.Cut) if hasattr(egi, 'Cut') else 0,
                "area_count": len(egi.area) if hasattr(egi, 'area') else 0
            }
        }


class StructuredDataExporter:
    """Handles export to structured data formats (JSON, XML)."""
    
    def __init__(self, core_manager: CoreDauFormalismManager):
        self.core_manager = core_manager
        self.logger = logging.getLogger(__name__)
    
    def export(self, egi: RelationalGraphWithCuts, config: ExportConfiguration) -> ExportResult:
        """Export EGI to structured data format."""
        try:
            if config.format == ExportFormat.JSON:
                return self._export_json(egi, config)
            elif config.format == ExportFormat.XML:
                return self._export_xml(egi, config)
            else:
                raise ValueError(f"Unsupported structured format: {config.format}")
                
        except Exception as e:
            self.logger.error(f"Structured data export failed: {e}")
            return ExportResult(
                success=False,
                format=config.format,
                errors=[str(e)]
            )
    
    def _export_json(self, egi: RelationalGraphWithCuts, config: ExportConfiguration) -> ExportResult:
        """Export EGI to JSON format."""
        # Build JSON structure
        egi_data = {
            "format": "EGI_JSON",
            "version": "1.0",
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
                    "connected_vertices": list(egi.nu.get(e.id, ()))
                }
                for e in egi.E
            ],
            "cuts": [
                {
                    "id": c.id,
                    "contents": list(egi.area.get(c.id, set()))
                }
                for c in egi.Cut
            ],
            "areas": {
                area_id: list(contents)
                for area_id, contents in egi.area.items()
            },
            "sheet": egi.sheet
        }
        
        # Add metadata if requested
        if config.include_metadata:
            egi_data["metadata"] = self._generate_export_metadata(egi, config)
        
        # Serialize to JSON
        content = json.dumps(egi_data, indent=2 if config.pretty_print else None)
        
        return ExportResult(
            success=True,
            content=content,
            format=config.format,
            metadata=egi_data.get("metadata", {}),
            export_timestamp=datetime.now().isoformat()
        )
    
    def _export_xml(self, egi: RelationalGraphWithCuts, config: ExportConfiguration) -> ExportResult:
        """Export EGI to XML format."""
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<egi format="EGI_XML" version="1.0">')
        
        # Vertices
        lines.append('  <vertices>')
        for vertex in egi.V:
            lines.append(f'    <vertex id="{vertex.id}" label="{vertex.label}" is_generic="{vertex.is_generic}"/>')
        lines.append('  </vertices>')
        
        # Edges
        lines.append('  <edges>')
        for edge in egi.E:
            relation = egi.rel.get(edge.id, "")
            connected = ",".join(egi.nu.get(edge.id, ()))
            lines.append(f'    <edge id="{edge.id}" relation="{relation}" connected_vertices="{connected}"/>')
        lines.append('  </edges>')
        
        lines.append('</egi>')
        content = "\n".join(lines)
        
        return ExportResult(
            success=True,
            content=content,
            format=config.format,
            export_timestamp=datetime.now().isoformat()
        )
    
    def _generate_export_metadata(self, egi: RelationalGraphWithCuts, config: ExportConfiguration) -> Dict[str, Any]:
        """Generate metadata for structured export."""
        return {
            "export_timestamp": datetime.now().isoformat(),
            "export_format": config.format.value,
            "statistics": {
                "vertex_count": len(egi.V),
                "edge_count": len(egi.E),
                "cut_count": len(egi.Cut),
                "area_count": len(egi.area)
            }
        }


class IntegratedExportManager(ExportManagerProtocol):
    """
    Integrated export manager that provides unified, validated export functionality
    for all supported formats using the core Dau formalism system.
    """
    
    def __init__(self, core_manager: CoreDauFormalismManager = None):
        self.logger = logging.getLogger(__name__)
        
        # Core formalism integration
        self.core_manager = core_manager or get_dau_formalism_manager()
        self.chapters_manager = get_dau_chapters_manager()
        
        # Initialize exporters
        self.linear_exporter = LinearFormExporter(self.core_manager)
        self.structured_exporter = StructuredDataExporter(self.core_manager)
        
        # Export history
        self.export_history: List[ExportResult] = []
        self.max_history_size = 100
        
        self.logger.info("IntegratedExportManager initialized with core formalism integration")
    
    # ========================================================================
    # Main Export Interface
    # ========================================================================
    
    def export_egi(self, egi: RelationalGraphWithCuts, format_type: ExportFormat,
                   output_path: Optional[Path] = None, config: Optional[ExportConfiguration] = None) -> ExportResult:
        """Export EGI in specified format."""
        try:
            # Use provided config or create default
            if config is None:
                config = ExportConfiguration(format=format_type)
            
            # Select appropriate exporter
            if format_type in [ExportFormat.EGIF, ExportFormat.CGIF, ExportFormat.CLIF, ExportFormat.FOPL]:
                result = self.linear_exporter.export(egi, config)
            elif format_type in [ExportFormat.JSON, ExportFormat.XML]:
                result = self.structured_exporter.export(egi, config)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
            
            # Write to file if path provided and export succeeded
            if result.success and output_path and result.content:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(result.content, encoding="utf-8")
                result.file_path = output_path
                self.logger.info(f"Exported EGI to {output_path}")
            
            # Add to history
            self._add_to_history(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            error_result = ExportResult(
                success=False,
                format=format_type,
                errors=[str(e)]
            )
            self._add_to_history(error_result)
            return error_result
    
    def export_multiple_formats(self, egi: RelationalGraphWithCuts, formats: List[ExportFormat],
                               output_dir: Optional[Path] = None) -> Dict[ExportFormat, ExportResult]:
        """Export EGI to multiple formats."""
        results = {}
        
        for format_type in formats:
            try:
                output_path = None
                if output_dir:
                    filename = f"egi_export.{format_type.value}"
                    output_path = output_dir / filename
                
                result = self.export_egi(egi, format_type, output_path)
                results[format_type] = result
                
            except Exception as e:
                self.logger.error(f"Failed to export {format_type.value}: {e}")
                results[format_type] = ExportResult(
                    success=False,
                    format=format_type,
                    errors=[str(e)]
                )
        
        return results
    
    # ========================================================================
    # ExportManager Protocol Implementation
    # ========================================================================
    
    def export_to_egif(self, egi: RelationalGraphWithCuts, file_path: Path) -> bool:
        """Export EGI to EGIF format."""
        result = self.export_egi(egi, ExportFormat.EGIF, file_path)
        return result.success
    
    def export_to_cgif(self, egi: RelationalGraphWithCuts, file_path: Path) -> bool:
        """Export EGI to CGIF format."""
        result = self.export_egi(egi, ExportFormat.CGIF, file_path)
        return result.success
    
    def export_to_clif(self, egi: RelationalGraphWithCuts, file_path: Path) -> bool:
        """Export EGI to CLIF format."""
        result = self.export_egi(egi, ExportFormat.CLIF, file_path)
        return result.success
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return [fmt.value for fmt in ExportFormat]
    
    # ========================================================================
    # Export Management and Utilities
    # ========================================================================
    
    def get_export_history(self, limit: Optional[int] = None) -> List[ExportResult]:
        """Get export history."""
        if limit:
            return self.export_history[-limit:]
        return self.export_history.copy()
    
    def clear_export_history(self):
        """Clear export history."""
        self.export_history.clear()
        self.logger.info("Export history cleared")
    
    def get_export_statistics(self) -> Dict[str, Any]:
        """Get export statistics."""
        if not self.export_history:
            return {"total_exports": 0}
        
        successful = sum(1 for result in self.export_history if result.success)
        failed = len(self.export_history) - successful
        
        format_counts = {}
        for result in self.export_history:
            if result.format:
                format_counts[result.format.value] = format_counts.get(result.format.value, 0) + 1
        
        return {
            "total_exports": len(self.export_history),
            "successful_exports": successful,
            "failed_exports": failed,
            "success_rate": successful / len(self.export_history) if self.export_history else 0,
            "format_distribution": format_counts
        }
    
    def _add_to_history(self, result: ExportResult):
        """Add export result to history."""
        self.export_history.append(result)
        
        # Trim history if too large
        if len(self.export_history) > self.max_history_size:
            self.export_history = self.export_history[-self.max_history_size:]


# ============================================================================
# Global Instance Management
# ============================================================================

_global_export_manager: Optional[IntegratedExportManager] = None

def get_integrated_export_manager() -> IntegratedExportManager:
    """Get the global integrated export manager instance."""
    global _global_export_manager
    if _global_export_manager is None:
        _global_export_manager = IntegratedExportManager()
    return _global_export_manager

def reset_export_manager():
    """Reset global export manager (for testing)."""
    global _global_export_manager
    _global_export_manager = None
