"""
EGIF Educational Features - Phase 2 Enhancement

This module provides enhanced educational features for EGIF, including:
- Visual mapping between EGIF syntax and existential graph concepts
- Interactive learning modules
- Concept progression tracking
- Detailed explanations of Peirce's notation
- Dau's mathematical extensions educational content

The goal is to make existential graphs more accessible to learners while
maintaining mathematical rigor.

Author: Manus AI
Date: January 2025
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import re

from egif_parser import EGIFParseResult, parse_egif
from egif_advanced_constructs import parse_advanced_egif, FunctionSymbol, CoreferencePattern, ScrollPattern
from egif_generator_simple import SimpleEGIFGenerator, SimpleEGIFGenerationResult


class ConceptLevel(Enum):
    """Educational concept difficulty levels."""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4
    
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
    
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented
    
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented
    
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented
    
    @property
    def name_str(self):
        """Get the string name of the level."""
        names = {1: "beginner", 2: "intermediate", 3: "advanced", 4: "expert"}
        return names[self.value]


class EGConcept(Enum):
    """Core existential graph concepts for educational mapping."""
    SHEET_OF_ASSERTION = "sheet_of_assertion"
    RELATION = "relation"
    ENTITY = "entity"
    DEFINING_LABEL = "defining_label"
    BOUND_LABEL = "bound_label"
    CUT = "cut"
    DOUBLE_CUT = "double_cut"
    LIGATURE = "ligature"
    SCROLL = "scroll"
    FUNCTION_SYMBOL = "function_symbol"
    COREFERENCE = "coreference"
    QUANTIFICATION = "quantification"


@dataclass
class ConceptExplanation:
    """Detailed explanation of an EG concept."""
    concept: EGConcept
    level: ConceptLevel
    title: str
    description: str
    peirce_notation: str
    egif_syntax: str
    examples: List[str]
    common_mistakes: List[str]
    related_concepts: List[EGConcept]
    
    def get_formatted_explanation(self) -> str:
        """Get a formatted explanation for display."""
        lines = []
        lines.append(f"📚 {self.title} ({self.level.name_str.title()})")
        lines.append("=" * 50)
        lines.append(f"\n{self.description}")
        lines.append(f"\n🎨 Peirce's Notation: {self.peirce_notation}")
        lines.append(f"💻 EGIF Syntax: {self.egif_syntax}")
        
        if self.examples:
            lines.append("\n📝 Examples:")
            for example in self.examples:
                lines.append(f"  • {example}")
        
        if self.common_mistakes:
            lines.append("\n⚠️  Common Mistakes:")
            for mistake in self.common_mistakes:
                lines.append(f"  • {mistake}")
        
        if self.related_concepts:
            concept_names = [c.value.replace('_', ' ').title() for c in self.related_concepts]
            lines.append(f"\n🔗 Related Concepts: {', '.join(concept_names)}")
        
        return "\n".join(lines)


@dataclass
class VisualMapping:
    """Visual mapping between EGIF and graphical EG representation."""
    egif_fragment: str
    graphical_description: str
    ascii_diagram: str
    concept_highlights: List[EGConcept]
    educational_notes: List[str]
    
    def get_visual_display(self) -> str:
        """Get formatted visual mapping display."""
        lines = []
        lines.append(f"🔄 EGIF ↔ Graphical Mapping")
        lines.append("-" * 40)
        lines.append(f"EGIF: {self.egif_fragment}")
        lines.append(f"Graph: {self.graphical_description}")
        lines.append("\nASCII Diagram:")
        lines.append(self.ascii_diagram)
        
        if self.concept_highlights:
            concept_names = [c.value.replace('_', ' ').title() for c in self.concept_highlights]
            lines.append(f"\n🎯 Key Concepts: {', '.join(concept_names)}")
        
        if self.educational_notes:
            lines.append("\n📖 Educational Notes:")
            for note in self.educational_notes:
                lines.append(f"  • {note}")
        
        return "\n".join(lines)


class EGIFEducationalSystem:
    """
    Comprehensive educational system for EGIF and existential graphs.
    
    Provides concept explanations, visual mappings, interactive learning,
    and progress tracking for students learning existential graphs.
    """
    
    def __init__(self):
        """Initialize the educational system."""
        self.concept_explanations = self._initialize_concept_explanations()
        self.visual_mappings = self._initialize_visual_mappings()
        self.learning_paths = self._initialize_learning_paths()
        
    def _initialize_concept_explanations(self) -> Dict[EGConcept, ConceptExplanation]:
        """Initialize comprehensive concept explanations."""
        explanations = {}
        
        # Sheet of Assertion
        explanations[EGConcept.SHEET_OF_ASSERTION] = ConceptExplanation(
            concept=EGConcept.SHEET_OF_ASSERTION,
            level=ConceptLevel.BEGINNER,
            title="Sheet of Assertion",
            description="The fundamental canvas where existential graphs are drawn. Represents the universe of discourse and what we assert to be true.",
            peirce_notation="Empty sheet or sheet with graphs drawn on it",
            egif_syntax="Implicit context containing all top-level assertions",
            examples=[
                "(Person *john) - Asserts that john is a person",
                "(Loves john mary) - Asserts that john loves mary"
            ],
            common_mistakes=[
                "Forgetting that the sheet itself represents assertion",
                "Confusing the sheet with a cut (negation)"
            ],
            related_concepts=[EGConcept.CUT, EGConcept.RELATION]
        )
        
        # Relations
        explanations[EGConcept.RELATION] = ConceptExplanation(
            concept=EGConcept.RELATION,
            level=ConceptLevel.BEGINNER,
            title="Relations",
            description="Predicates that express relationships between entities. In Peirce's notation, these are typically oval shapes with lines (pegs) connecting to entities.",
            peirce_notation="Oval with relation name and pegs extending to entities",
            egif_syntax="(RelationName entity1 entity2 ...)",
            examples=[
                "(Person *x) - x is a person",
                "(Loves *john *mary) - john loves mary",
                "(Between *a *b *c) - a is between b and c"
            ],
            common_mistakes=[
                "Forgetting parentheses around relations",
                "Mixing up argument order",
                "Using spaces in relation names without quotes"
            ],
            related_concepts=[EGConcept.ENTITY, EGConcept.DEFINING_LABEL, EGConcept.BOUND_LABEL]
        )
        
        # Entities and Labels
        explanations[EGConcept.DEFINING_LABEL] = ConceptExplanation(
            concept=EGConcept.DEFINING_LABEL,
            level=ConceptLevel.BEGINNER,
            title="Defining Labels (Lines of Identity)",
            description="The first occurrence of an entity in a graph, marked with * in EGIF. Corresponds to Peirce's 'lines of identity' that introduce new entities into the discourse.",
            peirce_notation="Line of identity extending from a relation peg",
            egif_syntax="*variableName",
            examples=[
                "(Person *john) - First mention of john",
                "(Loves *x *y) - First mention of both x and y",
                "(Function *input -> *output) - Defining both input and output"
            ],
            common_mistakes=[
                "Using * on subsequent mentions of the same entity",
                "Forgetting * on first mentions",
                "Using * with constants like numbers"
            ],
            related_concepts=[EGConcept.BOUND_LABEL, EGConcept.ENTITY, EGConcept.QUANTIFICATION]
        )
        
        explanations[EGConcept.BOUND_LABEL] = ConceptExplanation(
            concept=EGConcept.BOUND_LABEL,
            level=ConceptLevel.BEGINNER,
            title="Bound Labels",
            description="References to previously defined entities, without the * marker. Represents the continuation of a line of identity in Peirce's notation.",
            peirce_notation="Continuation of an existing line of identity",
            egif_syntax="variableName (without *)",
            examples=[
                "(Person *x) (Mortal x) - x is bound in the second relation",
                "(Loves john mary) - Both john and mary are bound references"
            ],
            common_mistakes=[
                "Using * on bound references",
                "Referencing undefined variables",
                "Inconsistent variable naming"
            ],
            related_concepts=[EGConcept.DEFINING_LABEL, EGConcept.COREFERENCE]
        )
        
        # Cuts and Negation
        explanations[EGConcept.CUT] = ConceptExplanation(
            concept=EGConcept.CUT,
            level=ConceptLevel.INTERMEDIATE,
            title="Cut (Negation)",
            description="Peirce's fundamental operation for negation. A cut is an oval enclosure that negates whatever is inside it. Essential for expressing logical negation.",
            peirce_notation="Oval enclosure around the negated content",
            egif_syntax="~[content]",
            examples=[
                "~[(Person x)] - x is not a person",
                "~[~[(Mortal x)]] - Double negation: x is mortal",
                "(Person *x) ~[(Mortal x)] - x is a person but not mortal"
            ],
            common_mistakes=[
                "Using ! or NOT instead of ~[]",
                "Forgetting brackets after ~",
                "Confusing cuts with parentheses"
            ],
            related_concepts=[EGConcept.DOUBLE_CUT, EGConcept.SHEET_OF_ASSERTION]
        )
        
        explanations[EGConcept.DOUBLE_CUT] = ConceptExplanation(
            concept=EGConcept.DOUBLE_CUT,
            level=ConceptLevel.INTERMEDIATE,
            title="Double Cut",
            description="Two nested cuts that cancel each other out, equivalent to assertion. Fundamental to Peirce's transformation rules.",
            peirce_notation="Two nested oval enclosures",
            egif_syntax="~[~[content]]",
            examples=[
                "~[~[(Person x)]] - Equivalent to (Person x)",
                "~[~[~[(Mortal x)]]] - Equivalent to ~[(Mortal x)]"
            ],
            common_mistakes=[
                "Not recognizing double cuts as assertions",
                "Incorrectly applying transformation rules"
            ],
            related_concepts=[EGConcept.CUT, EGConcept.SHEET_OF_ASSERTION]
        )
        
        # Advanced Constructs
        explanations[EGConcept.SCROLL] = ConceptExplanation(
            concept=EGConcept.SCROLL,
            level=ConceptLevel.ADVANCED,
            title="Scroll (Conditional)",
            description="Peirce's notation for conditionals, represented as a scroll-like shape. Expresses 'if-then' relationships between graphs.",
            peirce_notation="Scroll shape with antecedent and consequent",
            egif_syntax="[If condition [Then consequence]]",
            examples=[
                "[If (Person *x) [Then (Mortal x)]] - If x is a person, then x is mortal",
                "[Iff (Human *x) [Then (Rational x)]] - x is human if and only if x is rational"
            ],
            common_mistakes=[
                "Confusing scrolls with cuts",
                "Incorrect nesting of conditions",
                "Missing Then keyword"
            ],
            related_concepts=[EGConcept.CUT, EGConcept.COREFERENCE]
        )
        
        explanations[EGConcept.FUNCTION_SYMBOL] = ConceptExplanation(
            concept=EGConcept.FUNCTION_SYMBOL,
            level=ConceptLevel.EXPERT,
            title="Function Symbols (Dau's Extension)",
            description="Mathematical functions in existential graphs, following Dau's formalization. Extends Peirce's system with computational elements.",
            peirce_notation="Special relation with designated result peg",
            egif_syntax="(functionName args -> *result)",
            examples=[
                "(add 2 3 -> *sum) - sum is the result of adding 2 and 3",
                "(sqrt *x -> *y) - y is the square root of x"
            ],
            common_mistakes=[
                "Forgetting the -> operator",
                "Using * on input arguments unnecessarily",
                "Confusing functions with relations"
            ],
            related_concepts=[EGConcept.RELATION, EGConcept.DEFINING_LABEL]
        )
        
        return explanations
    
    def _initialize_visual_mappings(self) -> List[VisualMapping]:
        """Initialize visual mappings between EGIF and graphical notation."""
        mappings = []
        
        # Simple relation mapping
        mappings.append(VisualMapping(
            egif_fragment="(Person *john)",
            graphical_description="Oval labeled 'Person' with a line extending to 'john'",
            ascii_diagram="""
    ┌─────────┐
    │ Person  │──── john
    └─────────┘
            """,
            concept_highlights=[EGConcept.RELATION, EGConcept.DEFINING_LABEL],
            educational_notes=[
                "The oval represents the relation 'Person'",
                "The line (peg) connects to the entity 'john'",
                "The * in EGIF indicates this is john's first appearance"
            ]
        ))
        
        # Cut (negation) mapping
        mappings.append(VisualMapping(
            egif_fragment="~[(Person john)]",
            graphical_description="Oval enclosure (cut) around the Person-john relation",
            ascii_diagram="""
    ╭─────────────────────╮
    │  ┌─────────┐        │
    │  │ Person  │──john  │  ← Cut (negation)
    │  └─────────┘        │
    ╰─────────────────────╯
            """,
            concept_highlights=[EGConcept.CUT, EGConcept.RELATION],
            educational_notes=[
                "The outer oval is a 'cut' that negates the content",
                "This expresses 'john is NOT a person'",
                "Cuts are Peirce's fundamental negation operator"
            ]
        ))
        
        # Coreference mapping
        mappings.append(VisualMapping(
            egif_fragment="(Person *x) (Mortal x)",
            graphical_description="Two relations connected by the same line of identity",
            ascii_diagram="""
    ┌─────────┐     ┌─────────┐
    │ Person  │──x──│ Mortal  │
    └─────────┘     └─────────┘
            """,
            concept_highlights=[EGConcept.DEFINING_LABEL, EGConcept.BOUND_LABEL, EGConcept.COREFERENCE],
            educational_notes=[
                "The same line of identity (x) connects both relations",
                "First use (*x) defines the entity, second use (x) references it",
                "This expresses 'x is a person AND x is mortal'"
            ]
        ))
        
        # Function symbol mapping
        mappings.append(VisualMapping(
            egif_fragment="(add 2 3 -> *sum)",
            graphical_description="Function relation with input pegs and designated output peg",
            ascii_diagram="""
         2 ──┐
             │  ┌─────────┐
         3 ──┼──│   add   │──── sum
             │  └─────────┘
             └── (inputs)    (output)
            """,
            concept_highlights=[EGConcept.FUNCTION_SYMBOL, EGConcept.DEFINING_LABEL],
            educational_notes=[
                "Function symbols have designated input and output pegs",
                "The -> operator indicates the result variable",
                "This is Dau's extension to Peirce's original system"
            ]
        ))
        
        return mappings
    
    def _initialize_learning_paths(self) -> Dict[ConceptLevel, List[EGConcept]]:
        """Initialize structured learning paths by difficulty level."""
        return {
            ConceptLevel.BEGINNER: [
                EGConcept.SHEET_OF_ASSERTION,
                EGConcept.RELATION,
                EGConcept.ENTITY,
                EGConcept.DEFINING_LABEL,
                EGConcept.BOUND_LABEL
            ],
            ConceptLevel.INTERMEDIATE: [
                EGConcept.CUT,
                EGConcept.DOUBLE_CUT,
                EGConcept.COREFERENCE,
                EGConcept.LIGATURE
            ],
            ConceptLevel.ADVANCED: [
                EGConcept.SCROLL,
                EGConcept.QUANTIFICATION
            ],
            ConceptLevel.EXPERT: [
                EGConcept.FUNCTION_SYMBOL
            ]
        }
    
    def explain_concept(self, concept: EGConcept) -> str:
        """Get detailed explanation of a concept."""
        explanation = self.concept_explanations.get(concept)
        if explanation:
            return explanation.get_formatted_explanation()
        else:
            return f"No explanation available for concept: {concept.value}"
    
    def get_visual_mapping(self, egif_fragment: str) -> Optional[VisualMapping]:
        """Get visual mapping for an EGIF fragment."""
        for mapping in self.visual_mappings:
            if egif_fragment.strip() == mapping.egif_fragment.strip():
                return mapping
        return None
    
    def analyze_egif_for_concepts(self, egif_source: str) -> List[Tuple[EGConcept, str]]:
        """Analyze EGIF source and identify educational concepts present."""
        concepts_found = []
        
        # Parse the EGIF
        try:
            result = parse_advanced_egif(egif_source, educational_mode=True)
        except:
            # Fall back to basic parsing
            result = parse_egif(egif_source, educational_mode=True)
        
        # Identify concepts based on parse result
        if result.entities:
            concepts_found.append((EGConcept.ENTITY, "Entities found in the graph"))
            
            # Check for defining vs bound labels
            defining_labels = [e for e in result.entities if '*' in egif_source and e.name in egif_source]
            if defining_labels:
                concepts_found.append((EGConcept.DEFINING_LABEL, "Defining labels (*) introduce new entities"))
            
            bound_labels = [e for e in result.entities if e.name in egif_source.replace('*', '')]
            if bound_labels:
                concepts_found.append((EGConcept.BOUND_LABEL, "Bound labels reference existing entities"))
        
        if result.predicates:
            concepts_found.append((EGConcept.RELATION, "Relations express relationships between entities"))
        
        # Check for cuts (negation)
        if '~[' in egif_source:
            concepts_found.append((EGConcept.CUT, "Cuts (~[]) represent negation"))
            
            # Check for double cuts
            if '~[~[' in egif_source:
                concepts_found.append((EGConcept.DOUBLE_CUT, "Double cuts cancel out to assertion"))
        
        # Check for scrolls
        if '[If' in egif_source and '[Then' in egif_source:
            concepts_found.append((EGConcept.SCROLL, "Scrolls express conditional relationships"))
        
        # Check for function symbols
        if '->' in egif_source:
            concepts_found.append((EGConcept.FUNCTION_SYMBOL, "Function symbols (Dau's extension) perform computations"))
        
        # Check for coreference
        if len(result.entities) > 0 and len(result.predicates) > 1:
            # Simple heuristic: if entities appear in multiple predicates
            entity_usage = {}
            for pred in result.predicates:
                for entity_id in pred.entities:
                    entity = next((e for e in result.entities if e.id == entity_id), None)
                    if entity and entity.name:
                        entity_usage[entity.name] = entity_usage.get(entity.name, 0) + 1
            
            if any(count > 1 for count in entity_usage.values()):
                concepts_found.append((EGConcept.COREFERENCE, "Entities appear in multiple relations (coreference)"))
        
        return concepts_found
    
    def generate_educational_report(self, egif_source: str) -> str:
        """Generate comprehensive educational report for EGIF source."""
        lines = []
        lines.append("📚 EGIF Educational Analysis Report")
        lines.append("=" * 60)
        lines.append(f"\nSource: {egif_source}")
        
        # Analyze concepts
        concepts = self.analyze_egif_for_concepts(egif_source)
        
        if concepts:
            lines.append(f"\n🎯 Concepts Identified ({len(concepts)}):")
            for concept, description in concepts:
                lines.append(f"  • {concept.value.replace('_', ' ').title()}: {description}")
        
        # Get visual mapping if available
        visual_mapping = self.get_visual_mapping(egif_source)
        if visual_mapping:
            lines.append(f"\n{visual_mapping.get_visual_display()}")
        
        # Provide concept explanations
        if concepts:
            lines.append(f"\n📖 Detailed Concept Explanations:")
            for concept, _ in concepts[:3]:  # Show first 3 concepts
                explanation = self.concept_explanations.get(concept)
                if explanation:
                    lines.append(f"\n{explanation.get_formatted_explanation()}")
                    lines.append("")
        
        # Learning recommendations
        concept_levels = [self.concept_explanations[c].level for c, _ in concepts 
                         if c in self.concept_explanations]
        if concept_levels:
            max_level = max(concept_levels)
            lines.append(f"\n🎓 Learning Level: {max_level.name_str.title()}")
            
            # Suggest next concepts to learn
            current_concepts = {c for c, _ in concepts}
            next_concepts = []
            
            for level in [ConceptLevel.BEGINNER, ConceptLevel.INTERMEDIATE, 
                         ConceptLevel.ADVANCED, ConceptLevel.EXPERT]:
                path_concepts = self.learning_paths.get(level, [])
                for concept in path_concepts:
                    if concept not in current_concepts:
                        next_concepts.append(concept)
                        if len(next_concepts) >= 3:
                            break
                if next_concepts:
                    break
            
            if next_concepts:
                lines.append(f"\n🚀 Suggested Next Concepts:")
                for concept in next_concepts:
                    lines.append(f"  • {concept.value.replace('_', ' ').title()}")
        
        return "\n".join(lines)
    
    def get_learning_path(self, level: ConceptLevel) -> List[str]:
        """Get structured learning path for a given level."""
        concepts = self.learning_paths.get(level, [])
        return [concept.value.replace('_', ' ').title() for concept in concepts]
    
    def interactive_concept_explorer(self, concept: EGConcept) -> str:
        """Provide interactive exploration of a concept."""
        explanation = self.concept_explanations.get(concept)
        if not explanation:
            return f"Concept {concept.value} not found."
        
        lines = []
        lines.append(f"🔍 Interactive Concept Explorer")
        lines.append(f"{explanation.get_formatted_explanation()}")
        
        # Find related visual mappings
        related_mappings = [m for m in self.visual_mappings 
                          if concept in m.concept_highlights]
        
        if related_mappings:
            lines.append(f"\n🎨 Visual Examples:")
            for mapping in related_mappings[:2]:  # Show first 2
                lines.append(f"\n{mapping.get_visual_display()}")
        
        # Suggest practice exercises
        lines.append(f"\n💪 Practice Exercises:")
        if concept == EGConcept.DEFINING_LABEL:
            lines.append("  1. Write EGIF for: 'John is a person'")
            lines.append("  2. Identify the defining label in: (Loves *alice bob)")
            lines.append("  3. Convert to EGIF: 'There exists someone who is happy'")
        elif concept == EGConcept.CUT:
            lines.append("  1. Write EGIF for: 'John is not tall'")
            lines.append("  2. Simplify: ~[~[(Person x)]]")
            lines.append("  3. Express: 'If not (x is mortal) then x is immortal'")
        elif concept == EGConcept.FUNCTION_SYMBOL:
            lines.append("  1. Write EGIF for: 'y is the sum of 5 and 3'")
            lines.append("  2. Express: 'z is the square root of x'")
            lines.append("  3. Chain functions: 'w is the square of the sum of a and b'")
        
        return "\n".join(lines)


# Convenience functions
def explain_egif(egif_source: str) -> str:
    """Generate educational explanation for EGIF source."""
    system = EGIFEducationalSystem()
    return system.generate_educational_report(egif_source)


def explore_concept(concept_name: str) -> str:
    """Explore a specific EG concept interactively."""
    system = EGIFEducationalSystem()
    
    # Find concept by name
    concept = None
    for eg_concept in EGConcept:
        if eg_concept.value.replace('_', ' ').lower() == concept_name.lower():
            concept = eg_concept
            break
    
    if concept:
        return system.interactive_concept_explorer(concept)
    else:
        available = [c.value.replace('_', ' ').title() for c in EGConcept]
        return f"Concept '{concept_name}' not found. Available concepts: {', '.join(available)}"


# Example usage and testing
if __name__ == "__main__":
    print("EGIF Educational Features Test")
    print("=" * 50)
    
    # Test educational analysis
    test_cases = [
        "(Person *john)",
        "(Person *x) (Mortal x)",
        "~[(Person john)]",
        "[If (Person *x) [Then (Mortal x)]]",
        "(add 2 3 -> *sum)",
    ]
    
    system = EGIFEducationalSystem()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case}")
        print("-" * 60)
        
        # Generate educational report
        report = system.generate_educational_report(test_case)
        print(report)
        
        if i < len(test_cases):  # Don't print separator after last case
            print("\n" + "=" * 80)
    
    print("\n" + "=" * 80)
    print("Interactive Concept Explorer Example")
    print("=" * 80)
    
    # Test concept exploration
    concept_demo = system.interactive_concept_explorer(EGConcept.DEFINING_LABEL)
    print(concept_demo)
    
    print("\n" + "=" * 80)
    print("EGIF Educational Features Phase 2 implementation complete!")
    print("Provides comprehensive educational support for learning existential graphs.")

