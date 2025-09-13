"""
Domain Model and Ontology Integration for EGI Transformation History

Supports multiple domain contexts within a single EGI, external ontology integration,
and semantic grounding for the Endoporeutic Game. Designed for extensibility to
major ontologies like Cyc, WordNet, SNOMED, Gene Ontology, DOLCE, BFO, SUMO.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Union, Tuple, Protocol
from datetime import datetime, timezone
from enum import Enum
from abc import ABC, abstractmethod
import uuid

from frozendict import frozendict
from egi_core_dau import ElementID, RelationName


class OntologyType(Enum):
    """Types of supported ontologies."""
    LOCAL = "local"           # Local domain model
    OWL = "owl"              # OWL ontologies
    CYC = "cyc"              # OpenCyc/ResearchCyc
    WORDNET = "wordnet"      # Princeton WordNet
    SNOMED = "snomed"        # SNOMED CT medical ontology
    GENE_ONTOLOGY = "go"     # Gene Ontology
    DOLCE = "dolce"          # DOLCE upper ontology
    BFO = "bfo"              # Basic Formal Ontology
    SUMO = "sumo"            # Suggested Upper Merged Ontology
    CUSTOM_API = "custom"    # Custom API-based ontology


class ConceptType(Enum):
    """Types of ontological concepts."""
    CLASS = "class"
    INDIVIDUAL = "individual"
    PROPERTY = "property"
    RELATION = "relation"
    AXIOM = "axiom"
    CONSTRAINT = "constraint"


@dataclass(frozen=True)
class OntologyReference:
    """Reference to an external ontology."""
    ontology_id: str
    ontology_type: OntologyType
    name: str
    description: str
    version: Optional[str] = None
    uri: Optional[str] = None
    api_endpoint: Optional[str] = None
    access_credentials: Optional[str] = None  # Encrypted/hashed
    metadata: frozendict[str, Any] = field(default_factory=lambda: frozendict())


@dataclass(frozen=True)
class ConceptMapping:
    """Mapping between EGI elements and ontological concepts."""
    egi_element_id: ElementID
    ontology_id: str
    concept_uri: str
    concept_type: ConceptType
    confidence: float  # 0.0 to 1.0
    mapping_source: str  # "manual", "automatic", "validated"
    natural_language: Optional[str]
    definition: Optional[str]
    synonyms: List[str] = field(default_factory=list)
    metadata: frozendict[str, Any] = field(default_factory=lambda: frozendict())


@dataclass(frozen=True)
class DomainContext:
    """A domain context within an EGI with its own ontological grounding."""
    context_id: str
    name: str
    description: str
    primary_ontology_id: str
    secondary_ontologies: List[str] = field(default_factory=list)
    
    # Elements that belong to this domain context
    scoped_elements: Set[ElementID] = field(default_factory=set)
    
    # Domain-specific concept mappings
    concept_mappings: Dict[ElementID, ConceptMapping] = field(default_factory=dict)
    
    # Natural language annotations for this domain
    natural_language_forms: Dict[str, str] = field(default_factory=dict)  # form_type -> text
    
    # Domain-specific constraints and rules
    domain_constraints: List[str] = field(default_factory=list)
    
    created_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: frozendict[str, Any] = field(default_factory=lambda: frozendict())


class OntologyConnector(Protocol):
    """Protocol for connecting to external ontologies."""
    
    def lookup_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """Look up a concept by ID."""
        ...
    
    def search_concepts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for concepts matching a query."""
        ...
    
    def get_concept_relations(self, concept_id: str) -> List[Dict[str, Any]]:
        """Get relations for a concept."""
        ...
    
    def validate_concept_uri(self, uri: str) -> bool:
        """Validate that a concept URI exists."""
        ...


@dataclass
class SemanticAnnotation:
    """Rich semantic annotation for EGI elements or subgraphs."""
    annotation_id: str
    target_elements: Set[ElementID]
    domain_context_id: str
    
    # Natural language representations
    natural_language: str
    
    # Provenance (required fields first)
    annotation_source: str  # "user", "automatic", "imported"
    
    # Optional fields with defaults
    paraphrase_variants: List[str] = field(default_factory=list)
    
    # Logical forms
    logical_form_clif: Optional[str] = None
    logical_form_fol: Optional[str] = None
    logical_form_description_logic: Optional[str] = None
    
    # Ontological grounding
    primary_concepts: List[ConceptMapping] = field(default_factory=list)
    
    # Pragmatic context
    discourse_function: Optional[str] = None  # "assertion", "question", "hypothesis"
    epistemic_status: Optional[str] = None    # "known", "believed", "assumed"
    
    confidence: float = 1.0
    created_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    metadata: Dict[str, Any] = field(default_factory=dict)


class DomainModelManager:
    """Manages multiple domain contexts and ontology integration for an EGI."""
    
    def __init__(self):
        self.ontology_references: Dict[str, OntologyReference] = {}
        self.domain_contexts: Dict[str, DomainContext] = {}
        self.semantic_annotations: Dict[str, SemanticAnnotation] = {}
        self.ontology_connectors: Dict[str, OntologyConnector] = {}
        
        # Global concept mappings (cross-domain)
        self.global_concept_mappings: Dict[ElementID, List[ConceptMapping]] = {}
        
        # Element to domain context mappings
        self.element_to_contexts: Dict[ElementID, Set[str]] = {}
    
    def register_ontology(self, ontology_ref: OntologyReference, connector: Optional[OntologyConnector] = None):
        """Register an external ontology for use."""
        self.ontology_references[ontology_ref.ontology_id] = ontology_ref
        if connector:
            self.ontology_connectors[ontology_ref.ontology_id] = connector
    
    def create_domain_context(self, 
                            name: str, 
                            description: str, 
                            primary_ontology_id: str,
                            secondary_ontologies: List[str] = None) -> str:
        """Create a new domain context."""
        context_id = str(uuid.uuid4())
        
        domain_context = DomainContext(
            context_id=context_id,
            name=name,
            description=description,
            primary_ontology_id=primary_ontology_id,
            secondary_ontologies=secondary_ontologies or []
        )
        
        self.domain_contexts[context_id] = domain_context
        return context_id
    
    def add_element_to_context(self, element_id: ElementID, context_id: str):
        """Add an EGI element to a domain context."""
        if context_id not in self.domain_contexts:
            raise ValueError(f"Domain context {context_id} not found")
        
        # Update domain context
        context = self.domain_contexts[context_id]
        updated_context = DomainContext(
            context_id=context.context_id,
            name=context.name,
            description=context.description,
            primary_ontology_id=context.primary_ontology_id,
            secondary_ontologies=context.secondary_ontologies,
            scoped_elements=context.scoped_elements | {element_id},
            concept_mappings=context.concept_mappings,
            natural_language_forms=context.natural_language_forms,
            domain_constraints=context.domain_constraints,
            created_timestamp=context.created_timestamp,
            metadata=context.metadata
        )
        self.domain_contexts[context_id] = updated_context
        
        # Update element to context mapping
        if element_id not in self.element_to_contexts:
            self.element_to_contexts[element_id] = set()
        self.element_to_contexts[element_id].add(context_id)
    
    def map_element_to_concept(self, 
                              element_id: ElementID,
                              ontology_id: str,
                              concept_uri: str,
                              concept_type: ConceptType,
                              confidence: float = 1.0,
                              natural_language: Optional[str] = None) -> ConceptMapping:
        """Map an EGI element to an ontological concept."""
        
        mapping = ConceptMapping(
            egi_element_id=element_id,
            ontology_id=ontology_id,
            concept_uri=concept_uri,
            concept_type=concept_type,
            confidence=confidence,
            mapping_source="manual",
            natural_language=natural_language,
            definition=None  # Could be filled from ontology lookup
        )
        
        # Add to global mappings
        if element_id not in self.global_concept_mappings:
            self.global_concept_mappings[element_id] = []
        self.global_concept_mappings[element_id].append(mapping)
        
        return mapping
    
    def create_semantic_annotation(self,
                                 target_elements: Set[ElementID],
                                 domain_context_id: str,
                                 natural_language: str,
                                 logical_forms: Dict[str, str] = None) -> str:
        """Create a rich semantic annotation for EGI elements."""
        
        annotation_id = str(uuid.uuid4())
        
        annotation = SemanticAnnotation(
            annotation_id=annotation_id,
            target_elements=target_elements,
            domain_context_id=domain_context_id,
            natural_language=natural_language,
            annotation_source="user",
            logical_form_clif=logical_forms.get("clif") if logical_forms else None,
            logical_form_fol=logical_forms.get("fol") if logical_forms else None,
            logical_form_description_logic=logical_forms.get("dl") if logical_forms else None
        )
        
        self.semantic_annotations[annotation_id] = annotation
        return annotation_id
    
    def get_element_contexts(self, element_id: ElementID) -> List[DomainContext]:
        """Get all domain contexts containing an element."""
        context_ids = self.element_to_contexts.get(element_id, set())
        return [self.domain_contexts[cid] for cid in context_ids if cid in self.domain_contexts]
    
    def get_element_concept_mappings(self, element_id: ElementID) -> List[ConceptMapping]:
        """Get all concept mappings for an element."""
        return self.global_concept_mappings.get(element_id, [])
    
    def export_domain_model_data(self) -> Dict[str, Any]:
        """Export domain model data for serialization."""
        return {
            "domain_contexts": {
                ctx_id: {
                    "context_id": ctx.context_id,
                    "name": ctx.name,
                    "description": ctx.description,
                    "ontology_references": [
                        {
                            "ontology_id": ref.ontology_id,
                            "ontology_type": ref.ontology_type.value,
                            "base_uri": ref.base_uri,
                            "version": ref.version,
                            "access_method": ref.access_method
                        } for ref in ctx.ontology_references
                    ],
                    "concept_mappings": {
                        elem_id: [
                            {
                                "concept_uri": mapping.concept_uri,
                                "ontology_id": mapping.ontology_id,
                                "mapping_type": mapping.mapping_type,
                                "confidence_score": mapping.confidence_score,
                                "justification": mapping.justification
                            } for mapping in mappings
                        ] for elem_id, mappings in ctx.concept_mappings.items()
                    },
                    "semantic_annotations": {
                        ann_id: {
                            "annotation_id": ann.annotation_id,
                            "target_elements": list(ann.target_elements),
                            "domain_context_id": ann.domain_context_id,
                            "natural_language": ann.natural_language,
                            "annotation_source": ann.annotation_source,
                            "logical_form_clif": ann.logical_form_clif,
                            "logical_form_fol": ann.logical_form_fol,
                            "logical_form_description_logic": ann.logical_form_description_logic
                        } for ann_id, ann in ctx.semantic_annotations.items()
                    }
                } for ctx_id, ctx in self.domain_contexts.items()
            },
            "global_concept_mappings": {
                elem_id: [
                    {
                        "concept_uri": mapping.concept_uri,
                        "ontology_id": mapping.ontology_id,
                        "mapping_type": mapping.mapping_type,
                        "confidence_score": mapping.confidence_score,
                        "justification": mapping.justification
                    } for mapping in mappings
                ] for elem_id, mappings in self.global_concept_mappings.items()
            },
            "element_to_contexts": {
                elem_id: list(contexts) for elem_id, contexts in self.element_to_contexts.items()
            }
        }
    
    def import_domain_model_data(self, data: Dict[str, Any]) -> None:
        """Import domain model data from serialization."""
        # Clear existing data
        self.domain_contexts.clear()
        self.global_concept_mappings.clear()
        self.element_to_contexts.clear()
        
        # Import domain contexts
        for ctx_id, ctx_data in data.get("domain_contexts", {}).items():
            # Reconstruct ontology references
            ontology_refs = []
            for ref_data in ctx_data.get("ontology_references", []):
                ontology_refs.append(OntologyReference(
                    ontology_id=ref_data["ontology_id"],
                    ontology_type=OntologyType(ref_data["ontology_type"]),
                    base_uri=ref_data["base_uri"],
                    version=ref_data["version"],
                    access_method=ref_data["access_method"]
                ))
            
            # Reconstruct concept mappings
            concept_mappings = {}
            for elem_id, mappings_data in ctx_data.get("concept_mappings", {}).items():
                concept_mappings[elem_id] = [
                    ConceptMapping(
                        concept_uri=mapping_data["concept_uri"],
                        ontology_id=mapping_data["ontology_id"],
                        mapping_type=mapping_data["mapping_type"],
                        confidence_score=mapping_data["confidence_score"],
                        justification=mapping_data["justification"]
                    ) for mapping_data in mappings_data
                ]
            
            # Reconstruct semantic annotations
            semantic_annotations = {}
            for ann_id, ann_data in ctx_data.get("semantic_annotations", {}).items():
                semantic_annotations[ann_id] = SemanticAnnotation(
                    annotation_id=ann_data["annotation_id"],
                    target_elements=set(ann_data["target_elements"]),
                    domain_context_id=ann_data["domain_context_id"],
                    natural_language=ann_data["natural_language"],
                    annotation_source=ann_data["annotation_source"],
                    logical_form_clif=ann_data["logical_form_clif"],
                    logical_form_fol=ann_data["logical_form_fol"],
                    logical_form_description_logic=ann_data["logical_form_description_logic"]
                )
            
            # Create domain context
            self.domain_contexts[ctx_id] = DomainContext(
                context_id=ctx_data["context_id"],
                name=ctx_data["name"],
                description=ctx_data["description"],
                ontology_references=ontology_refs,
                concept_mappings=concept_mappings,
                semantic_annotations=semantic_annotations
            )
        
        # Import global concept mappings
        for elem_id, mappings_data in data.get("global_concept_mappings", {}).items():
            self.global_concept_mappings[elem_id] = [
                ConceptMapping(
                    concept_uri=mapping_data["concept_uri"],
                    ontology_id=mapping_data["ontology_id"],
                    mapping_type=mapping_data["mapping_type"],
                    confidence_score=mapping_data["confidence_score"],
                    justification=mapping_data["justification"]
                ) for mapping_data in mappings_data
            ]
        
        # Import element to contexts mapping
        for elem_id, contexts_list in data.get("element_to_contexts", {}).items():
            self.element_to_contexts[elem_id] = set(contexts_list)
    
    def lookup_concept_in_ontology(self, ontology_id: str, concept_uri: str) -> Optional[Dict[str, Any]]:
        """Look up a concept in an external ontology."""
        if ontology_id not in self.ontology_connectors:
            return None
        
        connector = self.ontology_connectors[ontology_id]
        return connector.lookup_concept(concept_uri)
    
    def generate_natural_language_for_subgraph(self, 
                                             elements: Set[ElementID], 
                                             context_id: Optional[str] = None) -> str:
        """Generate natural language description for a subgraph."""
        # This would use the concept mappings and domain context
        # to generate appropriate natural language
        
        if not elements:
            return "Empty subgraph"
        
        # Get concept mappings for elements
        concept_descriptions = []
        for element_id in elements:
            mappings = self.get_element_concept_mappings(element_id)
            if mappings:
                # Use the highest confidence mapping
                best_mapping = max(mappings, key=lambda m: m.confidence)
                if best_mapping.natural_language:
                    concept_descriptions.append(best_mapping.natural_language)
        
        if concept_descriptions:
            return " and ".join(concept_descriptions)
        else:
            return f"Subgraph with {len(elements)} elements"
    
    def validate_domain_consistency(self, context_id: str) -> List[str]:
        """Validate consistency within a domain context."""
        issues = []
        
        if context_id not in self.domain_contexts:
            return ["Domain context not found"]
        
        context = self.domain_contexts[context_id]
        
        # Check if primary ontology is registered
        if context.primary_ontology_id not in self.ontology_references:
            issues.append(f"Primary ontology {context.primary_ontology_id} not registered")
        
        # Check secondary ontologies
        for ont_id in context.secondary_ontologies:
            if ont_id not in self.ontology_references:
                issues.append(f"Secondary ontology {ont_id} not registered")
        
        # Validate concept mappings if connectors available
        for element_id, mapping in context.concept_mappings.items():
            if mapping.ontology_id in self.ontology_connectors:
                connector = self.ontology_connectors[mapping.ontology_id]
                if not connector.validate_concept_uri(mapping.concept_uri):
                    issues.append(f"Invalid concept URI: {mapping.concept_uri}")
        
        return issues
    
    def export_domain_model_data(self) -> Dict[str, Any]:
        """Export domain model data for persistence."""
        return {
            "ontology_references": {
                oid: {
                    "ontology_id": ref.ontology_id,
                    "ontology_type": ref.ontology_type.value,
                    "name": ref.name,
                    "version": ref.version,
                    "uri": ref.uri,
                    "api_endpoint": ref.api_endpoint,
                    "description": ref.description,
                    "metadata": dict(ref.metadata)
                } for oid, ref in self.ontology_references.items()
            },
            "domain_contexts": {
                cid: {
                    "context_id": ctx.context_id,
                    "name": ctx.name,
                    "description": ctx.description,
                    "primary_ontology_id": ctx.primary_ontology_id,
                    "secondary_ontologies": ctx.secondary_ontologies,
                    "scoped_elements": list(ctx.scoped_elements),
                    "natural_language_forms": ctx.natural_language_forms,
                    "domain_constraints": ctx.domain_constraints,
                    "created_timestamp": ctx.created_timestamp.isoformat(),
                    "metadata": dict(ctx.metadata)
                } for cid, ctx in self.domain_contexts.items()
            },
            "semantic_annotations": {
                aid: {
                    "annotation_id": ann.annotation_id,
                    "target_elements": list(ann.target_elements),
                    "domain_context_id": ann.domain_context_id,
                    "natural_language": ann.natural_language,
                    "paraphrase_variants": ann.paraphrase_variants,
                    "logical_form_clif": ann.logical_form_clif,
                    "logical_form_fol": ann.logical_form_fol,
                    "logical_form_description_logic": ann.logical_form_description_logic,
                    "discourse_function": ann.discourse_function,
                    "epistemic_status": ann.epistemic_status,
                    "annotation_source": ann.annotation_source,
                    "confidence": ann.confidence,
                    "created_timestamp": ann.created_timestamp.isoformat(),
                    "metadata": ann.metadata
                } for aid, ann in self.semantic_annotations.items()
            }
        }


# Example ontology connectors for major systems
class WordNetConnector:
    """Connector for Princeton WordNet."""
    
    def __init__(self, wordnet_path: Optional[str] = None):
        self.wordnet_path = wordnet_path
        # Would initialize NLTK WordNet or similar
    
    def lookup_concept(self, synset_id: str) -> Optional[Dict[str, Any]]:
        # Implementation would use NLTK or similar
        pass
    
    def search_concepts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        pass


class CycConnector:
    """Connector for OpenCyc/ResearchCyc."""
    
    def __init__(self, cyc_endpoint: str, api_key: Optional[str] = None):
        self.cyc_endpoint = cyc_endpoint
        self.api_key = api_key
    
    def lookup_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        # Implementation would use Cyc API
        pass


class OWLConnector:
    """Connector for OWL ontologies."""
    
    def __init__(self, owl_file_path: str):
        self.owl_file_path = owl_file_path
        # Would use owlready2 or similar
    
    def lookup_concept(self, concept_uri: str) -> Optional[Dict[str, Any]]:
        # Implementation would parse OWL
        pass
