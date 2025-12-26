#!/usr/bin/env python3
import sys, json
sys.path.insert(0, 'src')
from pathlib import Path
from entity_storage import EntityStorageManager
from definitive_three_pass_engine import DefinitiveThreePassEngine
from style_loader import StyleLoader

def debug_d3_payload(graph_name):
    storage = EntityStorageManager(Path('corpus/graphs'))
    entity = storage.load_entity(graph_name)
    egi = entity.current_egi
    
    engine = DefinitiveThreePassEngine()
    style = StyleLoader().load_default_style()
    
    # Monkey patch to capture payload
    original_layout_cut = engine._layout_cut
    engine._last_payload = None
    
    def capture_payload(egi, cut_id, hierarchy):
        result = original_layout_cut(egi, cut_id, hierarchy)
        if hasattr(engine, '_last_payload'):
            payload = engine._last_payload
            print(f"\n=== D3 PAYLOAD FOR CUT {cut_id} ===")
            print(f"Bounds: {payload['bounds']}")
            print(f"Nodes: {len(payload['nodes'])}")
            for node in payload['nodes']:
                print(f"  {node['id']} ({node['type']})")
            print(f"Ports: {len(payload['portNodes'])}")
            for port in payload['portNodes']:
                print(f"  {port['id']}: ({port['x']:.1f}, {port['y']:.1f})")
            print(f"Links: {len(payload['links'])}")
            for link in payload['links']:
                print(f"  {link['source']} → {link['target']}")
            print(f"Obstacles: {len(payload['obstacles'])}")
        return result
    
    def store_payload(egi, cut_id, hierarchy):
        bounds = engine.area_bounds[cut_id]
        payload = {
            'bounds': {'x': bounds.x, 'y': bounds.y, 'width': bounds.width, 'height': bounds.height},
            'nodes': [], 'links': [], 'obstacles': [], 'portNodes': []
        }
        
        # Add nodes
        for elem_id in egi.area[cut_id]:
            if elem_id.startswith('v_'):
                payload['nodes'].append({'id': elem_id, 'type': 'vertex'})
            elif elem_id.startswith('e_'):
                payload['nodes'].append({'id': elem_id, 'type': 'edge_label'})
        
        # Add obstacles
        for child in hierarchy[cut_id]['children']:
            cb = engine.area_bounds[child]
            payload['obstacles'].append({
                'id': child, 'x': cb.x - bounds.x + cb.width/2,
                'y': cb.y - bounds.y + cb.height/2, 'width': cb.width, 'height': cb.height
            })
        
        # Add port pairs
        child_ids = hierarchy[cut_id]['children']
        for port_id, port_node in engine.port_nodes.items():
            if port_node.cut_id == cut_id:
                port_x = port_node.position[0] - bounds.x
                port_y = port_node.position[1] - bounds.y
                if port_y < 5: port_y = 5
                elif port_y > bounds.height - 5: port_y = bounds.height - 5
                elif port_x < 5: port_x = 5
                elif port_x > bounds.width - 5: port_x = bounds.width - 5
                payload['portNodes'].append({'id': f'{port_id}_internal', 'x': port_x, 'y': port_y})
            elif port_node.cut_id in child_ids:
                port_x = port_node.position[0] - bounds.x
                port_y = port_node.position[1] - bounds.y
                payload['portNodes'].append({'id': f'{port_id}_external', 'x': port_x, 'y': port_y})
        
        # Add links
        node_ids = [n['id'] for n in payload['nodes']]
        for edge_id, vertices in egi.nu.items():
            for v_id in vertices:
                ligature_id = f"{v_id}_to_{edge_id}"
                if v_id in node_ids and edge_id in node_ids:
                    payload['links'].append({'source': v_id, 'target': edge_id})
                elif v_id in node_ids or edge_id in node_ids:
                    port = next((p for p in engine.port_nodes.values() 
                               if p.ligature_id == ligature_id), None)
                    if port:
                        if port.cut_id == cut_id:
                            port_id = f'{port.id}_internal'
                        elif port.cut_id in child_ids:
                            port_id = f'{port.id}_external'
                        else: continue
                        if v_id in node_ids:
                            payload['links'].append({'source': v_id, 'target': port_id})
                        elif edge_id in node_ids:
                            payload['links'].append({'source': port_id, 'target': edge_id})
        
        engine._last_payload = payload
        return capture_payload(egi, cut_id, hierarchy)
    
    engine._layout_cut = store_payload
    output_dir = Path('test_outputs/definitive_corpus')
    dto = engine.generate_layout(egi, style, str(output_dir / graph_name))

debug_d3_payload('dau_theorem_proving')
