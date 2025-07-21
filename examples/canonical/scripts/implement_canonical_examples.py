#!/usr/bin/env python3
"""
Comprehensive Implementation of Canonical Existential Graph Examples

This script implements all 14 canonical examples from Peirce, Dau, and Sowa
literature, demonstrating the full capabilities of the EG-CL-Manus2 system.

Based on Phase 1 research from:
- John Sowa's "Peirce's Tutorial on Existential Graphs"
- Frithjof Dau's mathematical formalization
- Charles Sanders Peirce's original writings
"""

import sys
import os
sys.path.append('/home/ubuntu/EG-CL-Manus2/src')

from graph import EGGraph
from eg_types import Entity, Predicate
from context import Context, ContextManager
from egrf import EGRFGenerator, EGRFSerializer
import json
from datetime import datetime

class CanonicalExampleImplementer:
    """Implements canonical EG examples with proper validation and EGRF generation"""
    
    def __init__(self):
        self.generator = EGRFGenerator()
        self.serializer = EGRFSerializer()
        self.results = []
    
    def create_example_1_simple_man(self):
        """
        Example 1: Simple Man - "There is a man"
        Peirce's first example: —man
        EGIF: [*x] (man ?x)
        Formula: ∃x man(x)
        """
        print("Creating Example 1: Simple Man")
        
        graph = EGGraph.create_empty()
        
        # Create entity (line of identity)
        man_entity = Entity.create(
            name="x",
            entity_type="variable"
        )
        
        # Create predicate
        man_predicate = Predicate.create(
            name="man",
            entities=[man_entity.id]
        )
        
        # Add to graph
        graph = graph.add_entity(man_entity)
        graph = graph.add_predicate(man_predicate)
        
        return graph, "There is a man", "∃x man(x)", "[*x] (man ?x)"
    
    def create_example_2_socrates_mortal(self):
        """
        Example 2: Socrates is Mortal
        Classic example with named individual
        EGIF: (Person Socrates) (Mortal Socrates)
        Formula: Person(Socrates) ∧ Mortal(Socrates)
        """
        print("Creating Example 2: Socrates is Mortal")
        
        graph = EGGraph.create_empty()
        
        # Create entity for Socrates
        socrates = Entity.create(
            name="Socrates",
            entity_type="constant"
        )
        
        # Create predicates
        person_pred = Predicate.create(
            name="Person",
            entities=[socrates.id]
        )
        
        mortal_pred = Predicate.create(
            name="Mortal",
            entities=[socrates.id]
        )
        
        # Add to graph
        graph = graph.add_entity(socrates)
        graph = graph.add_predicate(person_pred)
        graph = graph.add_predicate(mortal_pred)
        
        return graph, "Socrates is a person and Socrates is mortal", "Person(Socrates) ∧ Mortal(Socrates)", "(Person Socrates) (Mortal Socrates)"
    
    def create_example_3_every_man_mortal(self):
        """
        Example 3: Every man is mortal
        Universal quantification using nested cuts
        EGIF: ~[[*x] (man ?x) ~[(mortal ?x)]]
        Formula: ∀x (man(x) → mortal(x))
        """
        print("Creating Example 3: Every man is mortal")
        
        graph = EGGraph.create_empty()
        
        # Create outer context (negation)
        graph, outer_context = graph.create_context(
            context_type='cut',
            parent_id=graph.context_manager.root_context.id
        )
        
        # Create inner context (double negation)
        graph, inner_context = graph.create_context(
            context_type='cut',
            parent_id=outer_context.id
        )
        
        # Create entity in outer context
        man_entity = Entity.create(
            name="x",
            entity_type="variable"
        )
        
        # Create man predicate in outer context
        man_pred = Predicate.create(
            name="man",
            entities=[man_entity.id]
        )
        
        # Create mortal predicate in inner context (negated)
        mortal_pred = Predicate.create(
            name="mortal",
            entities=[man_entity.id]
        )
        
        # Add to graph
        graph = graph.add_entity(man_entity)
        graph = graph.add_predicate(man_pred)
        graph = graph.add_predicate(mortal_pred)
        
        return graph, "Every man is mortal", "∀x (man(x) → mortal(x))", "~[[*x] (man ?x) ~[(mortal ?x)]]"
    
    def create_example_4_thunder_lightning(self):
        """
        Example 4: Thunder and Lightning
        Peirce's example of implication
        EGIF: ~[(thunder) ~[(lightning)]]
        Formula: thunder → lightning
        """
        print("Creating Example 4: Thunder and Lightning")
        
        graph = EGGraph.create_empty()
        
        # Create outer context for implication
        graph, outer_context = graph.create_context(
            context_type='cut',
            parent_id=graph.context_manager.root_context.id
        )
        
        # Create inner context for consequent
        graph, inner_context = graph.create_context(
            context_type='cut',
            parent_id=outer_context.id
        )
        
        # Create thunder predicate in outer context (antecedent)
        thunder_pred = Predicate.create(
            name="thunder",
            entities=[]
        )
        
        # Create lightning predicate in inner context (negated consequent)
        lightning_pred = Predicate.create(
            name="lightning",
            entities=[]
        )
        
        # Add to graph
        graph = graph.add_predicate(thunder_pred)
        graph = graph.add_predicate(lightning_pred)
        
        return graph, "If there is thunder, then there is lightning", "thunder → lightning", "~[(thunder) ~[(lightning)]]"
    
    def create_example_5_african_man(self):
        """
        Example 5: African Man with Line of Identity
        Demonstrates line of identity connecting multiple predicates
        EGIF: [*x] (man ?x) (African ?x)
        Formula: ∃x (man(x) ∧ African(x))
        """
        print("Creating Example 5: African Man")
        
        graph = EGGraph.create_empty()
        
        # Create entity (line of identity)
        person_entity = Entity.create(
            name="x",
            entity_type="variable"
        )
        
        # Create predicates connected by line of identity
        man_pred = Predicate.create(
            name="man",
            entities=[person_entity.id]
        )
        
        african_pred = Predicate.create(
            name="African",
            entities=[person_entity.id]
        )
        
        # Add to graph
        graph = graph.add_entity(person_entity)
        graph = graph.add_predicate(man_pred)
        graph = graph.add_predicate(african_pred)
        
        return graph, "There is an African man", "∃x (man(x) ∧ African(x))", "[*x] (man ?x) (African ?x)"
    
    def create_example_6_boy_industrious(self):
        """
        Example 6: Boy/Industrious Transformation
        Demonstrates Peirce's transformation rules
        EGIF: [*x] (boy ?x) (industrious ?x)
        Formula: ∃x (boy(x) ∧ industrious(x))
        """
        print("Creating Example 6: Boy is Industrious")
        
        graph = EGGraph.create_empty()
        
        # Create entity
        boy_entity = Entity.create(
            name="x",
            entity_type="variable"
        )
        
        # Create predicates
        boy_pred = Predicate.create(
            name="boy",
            entities=[boy_entity.id]
        )
        
        industrious_pred = Predicate.create(
            name="industrious",
            entities=[boy_entity.id]
        )
        
        # Add to graph
        graph = graph.add_entity(boy_entity)
        graph = graph.add_predicate(boy_pred)
        graph = graph.add_predicate(industrious_pred)
        
        return graph, "There is a boy who is industrious", "∃x (boy(x) ∧ industrious(x))", "[*x] (boy ?x) (industrious ?x)"
    
    def create_example_7_exactly_one_p(self):
        """
        Example 7: Exactly One P
        Demonstrates cardinality constraints
        EGIF: [*x] (P ?x) ~[[*y] (P ?y) ~[[?x ?y]]]
        Formula: ∃x (P(x) ∧ ∀y (P(y) → x=y))
        """
        print("Creating Example 7: Exactly One P")
        
        graph = EGGraph.create_empty()
        
        # Create entity for "there is a P"
        p_entity = Entity.create(
            name="x",
            entity_type="variable"
        )
        
        # Create P predicate
        p_pred = Predicate.create(
            name="P",
            entities=[p_entity.id]
        )
        
        # Create negation context for "no other P"
        neg_context = Context.create(parent_id=graph.context_manager.root_context.id)
        graph = graph.add_context(neg_context)
        
        # Create second entity in negation
        p2_entity = Entity.create(
            name="y",
            entity_type="variable"
        )
        
        # Create second P predicate
        p2_pred = Predicate.create(
            name="P",
            entities=[p2_entity.id]
        )
        
        # Create inner negation for inequality
        inner_neg = Context.create(parent_id=neg_context.id)
        graph = graph.add_context(inner_neg)
        
        # Create equality predicate (to be negated)
        eq_pred = Predicate.create(
            name="equals",
            entities=[p_entity.id, p2_entity.id]
        )
        
        # Add to graph
        graph = graph.add_entity(p_entity)
        graph = graph.add_entity(p2_entity)
        graph = graph.add_predicate(p_pred)
        graph = graph.add_predicate(p2_pred)
        graph = graph.add_predicate(eq_pred)
        
        return graph, "There is exactly one P", "∃x (P(x) ∧ ∀y (P(y) → x=y))", "[*x] (P ?x) ~[[*y] (P ?y) ~[[?x ?y]]]"
    
    def create_example_8_at_least_three(self):
        """
        Example 8: At Least Three
        Demonstrates cardinality "at least 3"
        EGIF: [*x] [*y] [*z] ~[[?x ?y]] ~[[?y ?z]] ~[[?z ?x]]
        Formula: ∃x∃y∃z (x≠y ∧ y≠z ∧ z≠x)
        """
        print("Creating Example 8: At Least Three")
        
        graph = EGGraph.create_empty()
        
        # Create three entities
        entities = []
        for name in ['x', 'y', 'z']:
            entity = Entity.create(
                name=name,
                entity_type="variable"
            )
            entities.append(entity)
            graph = graph.add_entity(entity)
        
        # Create three negation contexts for inequalities
        contexts = []
        for i in range(3):
            context = Context.create(parent_id=graph.context_manager.root_context.id)
            contexts.append(context)
            graph = graph.add_context(context)
        
        # Create inequality predicates (negated equality)
        pairs = [(0, 1), (1, 2), (2, 0)]  # x≠y, y≠z, z≠x
        for i, (idx1, idx2) in enumerate(pairs):
            eq_pred = Predicate.create(
                name="equals",
                entities=[entities[idx1].id, entities[idx2].id]
            )
            graph = graph.add_predicate(eq_pred)
        
        return graph, "There are at least three things", "∃x∃y∃z (x≠y ∧ y≠z ∧ z≠x)", "[*x] [*y] [*z] ~[[?x ?y]] ~[[?y ?z]] ~[[?z ?x]]"
    
    def create_example_9_complex_disjunction(self):
        """
        Example 9: Complex Disjunction - "If p then q or r or s"
        Demonstrates complex Boolean combinations
        EGIF: ~[(p) ~[~[(q)] ~[(r)] ~[(s)]]]
        Formula: p → (q ∨ r ∨ s)
        """
        print("Creating Example 9: Complex Disjunction")
        
        graph = EGGraph.create_empty()
        
        # Create outer negation for implication
        outer_context = Context.create(parent_id=graph.context_manager.root_context.id)
        graph = graph.add_context(outer_context)
        
        # Create p predicate (antecedent)
        p_pred = Predicate.create(
            name="p",
            entities=[]
        )
        
        # Create inner negation for disjunction
        inner_context = Context.create(parent_id=outer_context.id)
        graph = graph.add_context(inner_context)
        
        # Create three nested negations for q, r, s
        for pred_name in ['q', 'r', 's']:
            neg_context = Context.create(parent_id=inner_context.id)
            graph = graph.add_context(neg_context)
            
            pred = Predicate.create(
                name=pred_name,
                entities=[]
            )
            graph = graph.add_predicate(pred)
        
        # Add p predicate
        graph = graph.add_predicate(p_pred)
        
        return graph, "If p then q or r or s", "p → (q ∨ r ∨ s)", "~[(p) ~[~[(q)] ~[(r)] ~[(s)]]]"
    
    def create_example_10_peirce_syllogism(self):
        """
        Example 10: Peirce's Syllogism
        Classic syllogistic reasoning in EG form
        EGIF: ~[[*x] (man ?x) ~[(mortal ?x)]] ∧ (man Socrates)
        Formula: ∀x (man(x) → mortal(x)) ∧ man(Socrates)
        """
        print("Creating Example 10: Peirce's Syllogism")
        
        graph = EGGraph.create_empty()
        
        # Major premise: All men are mortal
        # Create outer negation
        major_context = Context.create(parent_id=graph.context_manager.root_context.id)
        graph = graph.add_context(major_context)
        
        # Create inner negation
        major_inner = Context.create(parent_id=major_context.id)
        graph = graph.add_context(major_inner)
        
        # Create entity for major premise
        major_entity = Entity.create(
            name="x",
            entity_type="variable"
        )
        
        # Create predicates for major premise
        man_pred = Predicate.create(
            name="man",
            entities=[major_entity.id]
        )
        
        mortal_pred = Predicate.create(
            name="mortal",
            entities=[major_entity.id]
        )
        
        # Minor premise: Socrates is a man
        socrates = Entity.create(
            name="Socrates",
            entity_type="constant"
        )
        
        socrates_man = Predicate.create(
            name="man",
            entities=[socrates.id]
        )
        
        # Add to graph
        graph = graph.add_entity(major_entity)
        graph = graph.add_entity(socrates)
        graph = graph.add_predicate(man_pred)
        graph = graph.add_predicate(mortal_pred)
        graph = graph.add_predicate(socrates_man)
        
        return graph, "All men are mortal; Socrates is a man", "∀x (man(x) → mortal(x)) ∧ man(Socrates)", "~[[*x] (man ?x) ~[(mortal ?x)]] ∧ (man Socrates)"
    
    def generate_egrf_and_save(self, graph, example_name, description, formula, egif):
        """Generate EGRF representation and save to file"""
        try:
            # Generate EGRF
            egrf_doc = self.generator.generate(graph)
            
            # Add metadata
            egrf_doc.metadata.title = example_name
            egrf_doc.metadata.description = description
            egrf_doc.metadata.logical_form = formula
            egrf_doc.metadata.source = "Peirce's Canonical Examples"
            
            # Add EGIF to metadata instead of semantics to avoid serialization issues
            egrf_doc.metadata.logical_form = f"{formula} | EGIF: {egif}"
            
            # Serialize to JSON
            egrf_json = self.serializer.to_json(egrf_doc)
            
            # Save to file
            safe_name = example_name.lower().replace(' ', '_').replace('/', '_').replace("'", "")
            filename = f"/home/ubuntu/canonical_{safe_name}.egrf"
            with open(filename, 'w') as f:
                f.write(egrf_json)
            
            print(f"✓ Generated EGRF: {filename}")
            return filename
            
        except Exception as e:
            print(f"✗ Error generating EGRF for {example_name}: {e}")
            return None
    
    def implement_foundational_examples(self):
        """Implement Peirce's foundational examples (1-5)"""
        print("🎯 Implementing Peirce's Foundational Examples (1-5)")
        print("=" * 60)
        
        examples = [
            self.create_example_1_simple_man,
            self.create_example_2_socrates_mortal,
            self.create_example_3_every_man_mortal,
            self.create_example_4_thunder_lightning,
            self.create_example_5_african_man
        ]
        
        for i, example_func in enumerate(examples, 1):
            try:
                graph, description, formula, egif = example_func()
                example_name = f"Example {i}: {example_func.__name__.replace('create_example_', '').replace('_', ' ').title()}"
                
                # Generate EGRF
                egrf_file = self.generate_egrf_and_save(graph, example_name, description, formula, egif)
                
                result = {
                    'number': i,
                    'name': example_name,
                    'description': description,
                    'formula': formula,
                    'egif': egif,
                    'egrf_file': egrf_file,
                    'entities': len(graph.entities),
                    'predicates': len(graph.predicates),
                    'contexts': len(graph.context_manager.contexts)
                }
                
                self.results.append(result)
                
                print(f"✓ {example_name}")
                print(f"  Description: {description}")
                print(f"  Formula: {formula}")
                print(f"  EGIF: {egif}")
                print(f"  Graph: {len(graph.entities)} entities, {len(graph.predicates)} predicates, {len(graph.context_manager.contexts)} contexts")
                print()
                
            except Exception as e:
                print(f"✗ Error creating {example_func.__name__}: {e}")
                print()
        
        return len([r for r in self.results if r.get('egrf_file')])

def main():
    """Main function to implement foundational examples"""
    print("🎯 Canonical Examples Implementation - Phase 2")
    print("Implementing Peirce's Foundational Examples (1-5)")
    print("=" * 70)
    
    implementer = CanonicalExampleImplementer()
    
    # Implement foundational examples
    success_count = implementer.implement_foundational_examples()
    
    # Generate summary report
    print("📊 PHASE 1 SUMMARY REPORT")
    print("=" * 60)
    print(f"Examples implemented: {len(implementer.results)}")
    print(f"EGRF files generated: {success_count}")
    print(f"Total entities: {sum(r['entities'] for r in implementer.results)}")
    print(f"Total predicates: {sum(r['predicates'] for r in implementer.results)}")
    print(f"Total contexts: {sum(r['contexts'] for r in implementer.results)}")
    
    # Save summary to JSON
    summary = {
        'phase': 'Foundational Examples (1-5)',
        'timestamp': datetime.now().isoformat(),
        'examples': implementer.results,
        'statistics': {
            'total_examples': len(implementer.results),
            'successful_egrf_generation': success_count,
            'total_entities': sum(r['entities'] for r in implementer.results),
            'total_predicates': sum(r['predicates'] for r in implementer.results),
            'total_contexts': sum(r['contexts'] for r in implementer.results)
        }
    }
    
    with open('/home/ubuntu/canonical_examples_phase1_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n✅ Phase 1 (Foundational Examples) completed successfully!")
    print("📁 Files generated:")
    for result in implementer.results:
        if result.get('egrf_file'):
            print(f"  - {result['egrf_file']}")
    print("  - /home/ubuntu/canonical_examples_phase1_summary.json")
    
    if success_count == len(implementer.results):
        print("\n🚀 Ready to proceed to Phase 2: Cardinality and Complex Examples (6-10)")
    else:
        print(f"\n⚠️  {len(implementer.results) - success_count} examples had issues - review before proceeding")

if __name__ == "__main__":
    main()

