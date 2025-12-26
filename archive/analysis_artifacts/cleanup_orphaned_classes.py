#!/usr/bin/env python3
"""
Remove clearly orphaned classes and functions identified in the analysis.
"""

import os
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Clearly orphaned classes that can be safely removed
ORPHANED_CLASSES_TO_REMOVE = [
    ('src/diagram_annotations.py', 'AnnotationRenderer'),
    ('src/domain_ontology_model.py', 'CycConnector'),
    ('src/diagram_data_contract.py', 'DiagramDataContract'),
    ('src/egif_parsing_result.py', 'EGIFParsingResult'),
    ('src/gui/diagram_editor.py', 'EdgeElement'),
    ('src/gui/organon/exports_panel.py', 'ExportsPanel'),
    ('src/gui/organon/info_panel.py', 'GraphInfo'),
    ('src/historical_graph_model.py', 'HistoricalGraphRepository'),
    ('src/egi_transformation_history.py', 'HistoryViewer'),
]

# Files that are entirely orphaned (no active references)
ORPHANED_FILES_TO_REMOVE = [
    'src/diagram_annotations.py',
    'src/diagram_data_contract.py', 
    'src/egif_parsing_result.py',
    'src/domain_ontology_model.py',
    'src/historical_graph_model.py',
]

def remove_class_from_file(filepath: str, class_name: str):
    """Remove a specific class from a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find class definition
        class_start = None
        class_end = None
        indent_level = None
        
        for i, line in enumerate(lines):
            if line.strip().startswith(f'class {class_name}'):
                class_start = i
                # Determine indentation level
                indent_level = len(line) - len(line.lstrip())
                break
        
        if class_start is None:
            logger.warning(f"Class {class_name} not found in {filepath}")
            return False
        
        # Find end of class (next class or function at same or lower indent level)
        for i in range(class_start + 1, len(lines)):
            line = lines[i]
            if line.strip() == '':
                continue
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent_level and (line.strip().startswith('class ') or 
                                                   line.strip().startswith('def ') or
                                                   line.strip().startswith('if __name__')):
                class_end = i
                break
        
        if class_end is None:
            class_end = len(lines)
        
        # Remove the class
        new_lines = lines[:class_start] + lines[class_end:]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        logger.info(f"Removed class {class_name} from {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to remove class {class_name} from {filepath}: {e}")
        return False

def remove_orphaned_file(filepath: str):
    """Remove an entire orphaned file."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Removed orphaned file: {filepath}")
            return True
        else:
            logger.warning(f"File not found: {filepath}")
            return False
    except Exception as e:
        logger.error(f"Failed to remove file {filepath}: {e}")
        return False

def main():
    """Run the cleanup process."""
    logger.info("Starting orphaned class and file cleanup...")
    
    base_dir = Path(__file__).parent
    
    # Remove orphaned files entirely
    files_removed = 0
    for filepath in ORPHANED_FILES_TO_REMOVE:
        full_path = base_dir / filepath
        if remove_orphaned_file(str(full_path)):
            files_removed += 1
    
    # Remove specific orphaned classes
    classes_removed = 0
    for filepath, class_name in ORPHANED_CLASSES_TO_REMOVE:
        full_path = base_dir / filepath
        if full_path.exists() and remove_class_from_file(str(full_path), class_name):
            classes_removed += 1
    
    logger.info(f"Cleanup complete: {files_removed} files removed, {classes_removed} classes removed")
    
    # Check if any files are now empty and should be removed
    for filepath, _ in ORPHANED_CLASSES_TO_REMOVE:
        full_path = base_dir / filepath
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # If file only contains imports and comments, remove it
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                code_lines = [line for line in lines if not line.startswith('#') and 
                             not line.startswith('import') and not line.startswith('from')]
                
                if len(code_lines) <= 2:  # Only docstring or minimal content
                    remove_orphaned_file(str(full_path))
                    logger.info(f"Removed now-empty file: {filepath}")
                    
            except Exception as e:
                logger.warning(f"Could not check if {filepath} is empty: {e}")

if __name__ == "__main__":
    main()
