#!/usr/bin/env python3
import sys, json
sys.path.insert(0, 'src')
from pathlib import Path
from entity_storage import EntityStorageManager
from definitive_three_pass_engine import DefinitiveThreePassEngine
from style_loader import StyleLoader

# Monkey patch to capture d3 payloads
import subprocess
original_run = subprocess.run

payloads_sent = []

def capture_run(args, **kwargs):
    if 'd3_layout_worker.js' in str(args):
        payload_json = kwargs.get('input', '')
        if payload_json:
            payloads_sent.append(json.loads(payload_json))
    return original_run(args, **kwargs)

subprocess.run = capture_run

# Run layout
storage = EntityStorageManager(Path('corpus/graphs'))
entity = storage.load_entity('dau_theorem_proving')
egi = entity.current_egi

engine = DefinitiveThreePassEngine()
style = StyleLoader().load_default_style()

output_dir = Path('test_outputs/definitive_corpus')
dto = engine.generate_layout(egi, style, str(output_dir / 'dau_theorem_proving'))

# Find payload for first cut (where *x lives)
print("D3 PAYLOADS SENT:")
print("=" * 60)

for i, payload in enumerate(payloads_sent):
    print(f"\nPayload {i+1}:")
    print(f"  Bounds: {payload['bounds']}")
    print(f"  Nodes: {[n['id'] for n in payload['nodes']]}")
    print(f"  Port nodes: {[p['id'] for p in payload['portNodes']]}")
    print(f"  Links: {len(payload['links'])}")
    for link in payload['links']:
        print(f"    {link['source']} → {link['target']}")
    
    # Check if this is the cut with *x
    node_ids = [n['id'] for n in payload['nodes']]
    if 'v_32eac115' in node_ids:  # *x
        print(f"\n  ⭐ THIS IS THE CUT WITH *x")
        print(f"  Bounds: x={payload['bounds']['x']:.1f}, y={payload['bounds']['y']:.1f}")
        print(f"  Looking for link: v_32eac115 → port_1_external")
        
        # Find the port position
        for port in payload['portNodes']:
            if port['id'] == 'port_1_external':
                print(f"  Port position (local): ({port['x']:.1f}, {port['y']:.1f})")
                print(f"  Port position (global): ({payload['bounds']['x'] + port['x']:.1f}, {payload['bounds']['y'] + port['y']:.1f})")
        
        has_link = any(l['source'] == 'v_32eac115' and 'port' in l['target'] 
                      for l in payload['links'])
        if has_link:
            print(f"  ✅ Port link found!")
        else:
            print(f"  ❌ Port link MISSING!")
