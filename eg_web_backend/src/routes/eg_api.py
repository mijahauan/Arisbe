"""
Existential Graph API Routes
Provides REST API endpoints for EG-HG operations
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any, List, Optional
import uuid
import traceback

# Import our EG-HG system
from src.eg_system.eg_types import NodeId, EdgeId, ContextId, LigatureId
from src.eg_system.graph import EGGraph
from src.eg_system.clif_parser import CLIFParser
from src.eg_system.clif_generator import CLIFGenerator
from src.eg_system.transformations import TransformationEngine, TransformationType
from src.eg_system.game_engine import EndoporeuticGameEngine, GameState, Player
from src.eg_system.bullpen import GraphCompositionTool
from src.eg_system.lookahead import LookAheadEngine
from src.eg_system.exploration import GraphExplorer

# Create blueprint
eg_api = Blueprint('eg_api', __name__)

# Global instances (in production, these would be session-based)
_graphs: Dict[str, EGGraph] = {}
_games: Dict[str, EndoporeuticGameEngine] = {}
_transformation_engine = TransformationEngine()
_clif_parser = CLIFParser()
_clif_generator = CLIFGenerator()

def _serialize_graph(graph: EGGraph) -> Dict[str, Any]:
    """Serialize EGGraph to JSON-compatible format"""
    return {
        'contexts': [
            {
                'id': str(ctx_id),
                'parent_id': str(ctx.parent_context) if ctx.parent_context else None,
                'depth': ctx.depth,
                'polarity': 'positive' if ctx.is_positive else 'negative',
                'items': [str(item_id) for item_id in ctx.contained_items]
            }
            for ctx_id, ctx in graph.context_manager.contexts.items()
        ],
        'nodes': [
            {
                'id': str(node_id),
                'predicate': node.properties.get('name', 'Unnamed'),
                'arity': node.properties.get('arity', 0),
                'node_type': node.node_type
            }
            for node_id, node in graph.nodes.items()
        ],
        'edges': [
            {
                'id': str(edge_id),
                'edge_type': edge.edge_type,
                'nodes': [str(node_id) for node_id in edge.nodes]
            }
            for edge_id, edge in graph.edges.items()
        ],
        'ligatures': [
            {
                'id': str(lig_id),
                'nodes': [str(node_id) for node_id in ligature.nodes],
                'edges': [str(edge_id) for edge_id in ligature.edges]
            }
            for lig_id, ligature in graph.ligatures.items()
        ]
    }

def _deserialize_graph(data: Dict[str, Any]) -> EGGraph:
    """Deserialize JSON data to EGGraph"""
    # This is a simplified version - in production would need full reconstruction
    graph = EGGraph()
    # Implementation would reconstruct the graph from the serialized data
    return graph

@eg_api.route('/graphs', methods=['POST'])
def create_graph():
    """Create a new empty graph"""
    try:
        graph_id = str(uuid.uuid4())
        graph = EGGraph.create_empty()
        _graphs[graph_id] = graph
        
        return jsonify({
            'success': True,
            'graph_id': graph_id,
            'graph': _serialize_graph(graph)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@eg_api.route('/graphs/<graph_id>', methods=['GET'])
def get_graph(graph_id: str):
    """Get a graph by ID"""
    try:
        if graph_id not in _graphs:
            return jsonify({'success': False, 'error': 'Graph not found'}), 404
        
        graph = _graphs[graph_id]
        return jsonify({
            'success': True,
            'graph_id': graph_id,
            'graph': _serialize_graph(graph)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@eg_api.route('/graphs/<graph_id>/clif', methods=['POST'])
def parse_clif(graph_id: str):
    """Parse CLIF text and update graph"""
    try:
        data = request.get_json()
        clif_text = data.get('clif_text', '')
        
        if not clif_text:
            return jsonify({'success': False, 'error': 'No CLIF text provided'}), 400
        
        # Parse CLIF and create new graph
        graph = _clif_parser.parse(clif_text)
        _graphs[graph_id] = graph
        
        return jsonify({
            'success': True,
            'graph_id': graph_id,
            'graph': _serialize_graph(graph)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@eg_api.route('/graphs/<graph_id>/clif', methods=['GET'])
def generate_clif(graph_id: str):
    """Generate CLIF text from graph"""
    try:
        if graph_id not in _graphs:
            return jsonify({'success': False, 'error': 'Graph not found'}), 404
        
        graph = _graphs[graph_id]
        clif_text = _clif_generator.generate(graph)
        
        return jsonify({
            'success': True,
            'graph_id': graph_id,
            'clif_text': clif_text
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@eg_api.route('/graphs/<graph_id>/transformations', methods=['GET'])
def get_legal_transformations(graph_id: str):
    """Get legal transformations for a graph"""
    try:
        if graph_id not in _graphs:
            return jsonify({'success': False, 'error': 'Graph not found'}), 404
        
        graph = _graphs[graph_id]
        legal_transformations = _transformation_engine.get_legal_transformations(graph)
        
        # Convert to serializable format
        serialized_transformations = {}
        for trans_type, target_sets in legal_transformations.items():
            serialized_transformations[trans_type.value] = [
                [str(item_id) for item_id in target_set]
                for target_set in target_sets
            ]
        
        return jsonify({
            'success': True,
            'graph_id': graph_id,
            'legal_transformations': serialized_transformations
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@eg_api.route('/graphs/<graph_id>/transform', methods=['POST'])
def apply_transformation(graph_id: str):
    """Apply a transformation to a graph"""
    try:
        if graph_id not in _graphs:
            return jsonify({'success': False, 'error': 'Graph not found'}), 404
        
        data = request.get_json()
        transformation_type = data.get('transformation_type')
        target_items = data.get('target_items', [])
        
        # Convert string IDs back to proper types
        target_item_ids = []
        for item_id_str in target_items:
            # This is simplified - would need proper type detection
            target_item_ids.append(uuid.UUID(item_id_str))
        
        graph = _graphs[graph_id]
        trans_type = TransformationType(transformation_type)
        
        result = _transformation_engine.apply_transformation(
            graph, trans_type, set(target_item_ids)
        )
        
        if result.success:
            _graphs[graph_id] = result.new_graph
            
        return jsonify({
            'success': result.success,
            'graph_id': graph_id,
            'graph': _serialize_graph(result.new_graph) if result.success else None,
            'error': result.error_message if not result.success else None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@eg_api.route('/games', methods=['POST'])
def create_game():
    """Create a new endoporeutic game"""
    try:
        data = request.get_json()
        domain_model_name = data.get('domain_model_name', 'default')
        
        game_id = str(uuid.uuid4())
        game_engine = EndoporeuticGameEngine()
        _games[game_id] = game_engine
        
        return jsonify({
            'success': True,
            'game_id': game_id,
            'state': game_engine.get_current_state().value
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@eg_api.route('/games/<game_id>/start', methods=['POST'])
def start_game(game_id: str):
    """Start a game inning with a thesis"""
    try:
        if game_id not in _games:
            return jsonify({'success': False, 'error': 'Game not found'}), 404
        
        data = request.get_json()
        thesis_graph_id = data.get('thesis_graph_id')
        
        if thesis_graph_id not in _graphs:
            return jsonify({'success': False, 'error': 'Thesis graph not found'}), 404
        
        game_engine = _games[game_id]
        thesis_graph = _graphs[thesis_graph_id]
        
        result = game_engine.start_inning(thesis_graph)
        
        return jsonify({
            'success': result.success,
            'game_id': game_id,
            'state': game_engine.get_current_state().value,
            'current_player': game_engine.get_current_player().value,
            'error': result.error_message if not result.success else None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@eg_api.route('/bullpen', methods=['POST'])
def create_bullpen_graph():
    """Create a graph using the Bullpen composition tool"""
    try:
        data = request.get_json()
        template_name = data.get('template_name')
        
        bullpen = GraphCompositionTool()
        
        if template_name:
            graph, validation = bullpen.create_from_template(template_name, {})
        else:
            graph = bullpen.create_blank_sheet()
        
        graph_id = str(uuid.uuid4())
        _graphs[graph_id] = graph
        
        return jsonify({
            'success': True,
            'graph_id': graph_id,
            'graph': _serialize_graph(graph)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@eg_api.route('/lookahead/<graph_id>', methods=['POST'])
def preview_transformation(graph_id: str):
    """Preview a transformation without applying it"""
    try:
        if graph_id not in _graphs:
            return jsonify({'success': False, 'error': 'Graph not found'}), 404
        
        data = request.get_json()
        transformation_type = data.get('transformation_type')
        target_items = data.get('target_items', [])
        
        graph = _graphs[graph_id]
        lookahead = LookAheadEngine()
        
        preview = lookahead.preview_transformation(
            graph, 
            TransformationType(transformation_type),
            [uuid.UUID(item_id) for item_id in target_items]
        )
        
        return jsonify({
            'success': True,
            'graph_id': graph_id,
            'preview': {
                'success': preview.success,
                'result_graph': _serialize_graph(preview.result_graph) if preview.success else None,
                'error': preview.error_message if not preview.success else None,
                'confidence': preview.confidence
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@eg_api.route('/exploration/<graph_id>', methods=['POST'])
def explore_graph(graph_id: str):
    """Explore graph with different scope and focus options"""
    try:
        if graph_id not in _graphs:
            return jsonify({'success': False, 'error': 'Graph not found'}), 404
        
        data = request.get_json()
        scope_type = data.get('scope_type', 'area_only')
        focus_item_id = data.get('focus_item_id')
        
        graph = _graphs[graph_id]
        explorer = GraphExplorer()
        
        if focus_item_id:
            focus_id = uuid.UUID(focus_item_id)
            view = explorer.focus_on_item(graph, focus_id, scope_type)
        else:
            view = explorer.get_full_view(graph)
        
        return jsonify({
            'success': True,
            'graph_id': graph_id,
            'view': {
                'scope_type': view.scope_type,
                'focus_item': str(view.focus_item) if view.focus_item else None,
                'visible_items': [str(item_id) for item_id in view.visible_items],
                'context_hierarchy': [str(ctx_id) for ctx_id in view.context_hierarchy]
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@eg_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'graphs_count': len(_graphs),
        'games_count': len(_games)
    })

