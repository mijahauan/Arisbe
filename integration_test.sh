# Test EGRF module imports
#cd /path/to/your/EG-CL-Manus2
python -c "from src.egrf import EGRFGenerator; print('✓ EGRF imports working')"

# Run EGRF-specific tests
#python -m pytest tests/test_egrf_generator.py -v

# Run full test suite to ensure no regressions
#python -m pytest tests/ -v

# Test EGRF generation with existing data
python -c "
from src.graph import EGGraph
from src.eg_types import Entity, Predicate
from src.egrf import EGRFGenerator, EGRFSerializer

# Create test graph
eg_graph = EGGraph.create_empty()
socrates = Entity.create(name='Socrates', entity_type='constant')
eg_graph = eg_graph.add_entity(socrates)
person_pred = Predicate.create(name='Person', entities=[socrates.id])
eg_graph = eg_graph.add_predicate(person_pred)

# Generate EGRF
generator = EGRFGenerator()
egrf_doc = generator.generate(eg_graph)
print(f'✓ Generated EGRF with {len(egrf_doc.entities)} entities, {len(egrf_doc.predicates)} predicates')

# Test serialization
json_str = EGRFSerializer.to_json(egrf_doc)
print(f'✓ Serialized to {len(json_str)} characters')
"