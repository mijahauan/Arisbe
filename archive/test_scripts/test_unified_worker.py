#!/usr/bin/env python3
"""
Standalone test for the unified D3 worker.
Tests the worker independently of the full layout engine.
"""

import json
import subprocess
from pathlib import Path

# Simple test payload
test_payload = {
    "nodes": [
        {"id": "v1", "type": "vertex", "width": 20, "height": 20},
        {"id": "v2", "type": "vertex", "width": 20, "height": 20},
        {"id": "e1", "type": "predicate", "width": 60, "height": 30},
    ],
    "links": [
        {"source": "e1", "target": "v1"},
        {"source": "e1", "target": "v2"}
    ],
    "hierarchy": {
        "v1": "sheet",
        "v2": "sheet", 
        "e1": "sheet"
    },
    "style": {
        "cutPadding": 20,
        "margin": 50
    },
    "seed": "42"
}

print("Testing Unified D3 Worker...")
print("=" * 60)

worker_path = Path(__file__).parent / "src" / "unified_d3_worker.js"
print(f"Worker path: {worker_path}")
print(f"Worker exists: {worker_path.exists()}")

if not worker_path.exists():
    print("ERROR: Worker file not found!")
    exit(1)

print(f"\nTest payload:")
print(json.dumps(test_payload, indent=2))

# Run the worker
try:
    process = subprocess.Popen(
        ['node', str(worker_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = process.communicate(json.dumps(test_payload), timeout=5)
    
    print(f"\nWorker exit code: {process.returncode}")
    
    if stderr:
        print(f"\nWorker stderr:")
        print(stderr)
    
    if process.returncode == 0:
        print(f"\n✅ Worker executed successfully!")
        print(f"\nWorker output:")
        result = json.loads(stdout)
        print(json.dumps(result, indent=2))
        
        # Validate result structure
        assert "positions" in result, "Result missing 'positions'"
        assert "viewport" in result, "Result missing 'viewport'"
        assert len(result["positions"]) == 3, f"Expected 3 positions, got {len(result['positions'])}"
        
        print(f"\n✅ All validations passed!")
        print(f"   - Got {len(result['positions'])} node positions")
        print(f"   - Viewport: {result['viewport']}")
        
    else:
        print(f"\n❌ Worker failed with exit code {process.returncode}")
        
except subprocess.TimeoutExpired:
    process.kill()
    print("❌ Worker timed out!")
    exit(1)
except Exception as e:
    print(f"❌ Error running worker: {e}")
    exit(1)

print("\n" + "=" * 60)
print("Test complete!")
