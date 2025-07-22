# EGRF v3.0 Architectural Transition

## Breaking Changes from v1.0

### Removed Features
- Absolute pixel coordinates
- Fixed canvas sizes
- Physical layout specifications

### New Features  
- Logical containment hierarchy
- Platform-independent constraints
- Auto-sizing from content
- User movement validation
- Cross-platform layout engines

## Migration Guide

v1.0 EGRF files are NOT compatible with v3.0. This is an intentional
architectural clean break to enable superior design.

## Version History
- v1.0.0: Absolute coordinate system (archived)
- v3.0.0: Logical containment system (current development)

## Rollback Strategy
If needed, v1.0 implementation is preserved in:
- Tag: v1.0.0
- Branch: archive/egrf-v1.0-absolute-coordinates
