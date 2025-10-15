# Arisbe Tomos Restructure Plan

## Overview
Restructure the tomos to align with the new persistence model and provide high-quality educational/canonical examples for Arisbe users.

## Current Issues
1. **Low-quality entries**: Test graphs, auto-harvested fragments, generic placeholders
2. **Missing attribution**: No proper citations or source references
3. **Persistence model mismatch**: Inconsistent metadata, missing EGDF/exports
4. **Poor organization**: No educational progression or clear categorization

## Proposed Structure

### Categories
- **canonical/** - Foundational examples from key sources
- **educational/** - Learning progression from simple to complex
- **historical/** - Important graphs from EG literature
- **examples/** - Well-documented use cases

### Entry Requirements
Each retained entry must have:
- Proper source attribution and citation
- Complete metadata (title, description, difficulty, concepts)
- Valid EGI structure matching current system
- EGDF representation for visual rendering
- Educational context and learning objectives

## Retention Criteria

### KEEP - High Value Entries
- **Peirce examples**: Classic EG demonstrations (with proper CP citations)
- **Dau examples**: Modern formalism illustrations (with page references)
- **Sowa examples**: Conceptual graph connections (with publication data)
- **Educational progressions**: Simple → complex learning sequences

### REMOVE - Low Value Entries
- Generic test entries (`test`, `graph_new_1`)
- Auto-harvested fragments without context
- Duplicate or near-duplicate examples
- Entries with unclear provenance

## New Persistence Model Compliance

### Required Structure
```
tomos/graphs/{category}/{entry_id}/
├── {entry_id}.json           # Complete metadata
├── {entry_id}.egi.json       # EGI structure
├── EGDF/                     # Visual representations
│   └── *.egdf.json
├── EXPORTS/                  # Generated formats
│   ├── *.egif
│   ├── *.cgif
│   └── *.clif
└── README.md                 # Entry documentation
```

### Metadata Schema
```json
{
  "id": "entry_identifier",
  "title": "Human-readable title",
  "description": "Educational context and purpose",
  "category": "canonical|educational|historical|examples",
  "difficulty": "beginner|intermediate|advanced",
  "concepts": ["iteration", "double_cut", "quantification"],
  "source": {
    "author": "Author Name",
    "title": "Publication Title", 
    "citation": "Full bibliographic citation",
    "page": "Page reference if applicable",
    "url": "Online source if available"
  },
  "educational": {
    "prerequisites": ["concept1", "concept2"],
    "learning_objectives": ["objective1", "objective2"],
    "suggested_transformations": ["IT+", "DC-"]
  },
  "created": "ISO timestamp",
  "updated": "ISO timestamp"
}
```

## Implementation Plan

### Phase 1: Audit and Categorize
1. Review all 50+ current entries
2. Identify high-value entries for retention
3. Mark low-value entries for removal
4. Research proper attributions for retained entries

### Phase 2: Clean and Restructure  
1. Remove identified low-value entries
2. Migrate retained entries to new structure
3. Add complete metadata and attribution
4. Validate EGI structures against current system

### Phase 3: Educational Enhancement
1. Create learning progressions
2. Add educational metadata
3. Generate missing EGDF representations
4. Create entry documentation

### Phase 4: Quality Assurance
1. Test all entries in Arisbe
2. Verify transformations work correctly
3. Validate educational progressions
4. Update tomos documentation

## Success Criteria
- Tomos reduced to ~15-20 high-quality entries
- All entries have complete attribution
- 100% compliance with new persistence model
- Clear educational progression paths
- All entries tested and working in Arisbe
