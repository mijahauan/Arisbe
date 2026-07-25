# Item 4 Phase 2: Formal Doubt Structure — Implementation Plan

**Status:** Pre-implementation specification (2026-07-25)  
**Scope:** Build unified `Doubt` class and wire into UoD architecture  
**Build method:** Subagent-driven development (6 tasks)

---

## Overview

Formalize erotetic structure of doubt and embed it in UoD state. A doubt is:
```
Doubt := (Presupposition, Erotetic_Core, Status, Lifecycle)

Where:
- Presupposition: EGI state that must hold for the Q to be well-posed
- Erotetic_Core: Set[EGI] of possible answers
- Status: "unresolved" | "partial" | "resolved"
- Lifecycle: (emerged_at_state, resolved_at_state, resolution_path)
```

Doubts live **in UoD state**, indexed by state_id and doubt_id, so inquiry trajectories are legible.

---

## Architecture

### New Module: `src/erotetic_doubt.py`

**Core class:**
```python
@dataclass
class Doubt:
    """Formal erotetic structure of a doubt/question."""
    
    # Erotetic structure (the question)
    id: str                              # Unique within UoD
    presupposition: EGI                  # What must hold for Q to be well-posed
    erotetic_core: FrozenSet[str]        # Set of EGI hashes (possible answers)
    current_answers: FrozenSet[str] = frozenset()  # Narrowed answers so far
    
    # Status in the lifecycle
    status: Literal["unresolved", "partial", "resolved"] = "unresolved"
    
    # Lifecycle tracking
    emerged_at_state_id: str             # When doubt first raised
    resolved_at_state_id: Optional[str] = None  # When resolved (if ever)
    resolution_path: List[str] = field(default_factory=list)  # States it passed through
    
    # Metadata
    kind: Literal["unknown_verdict", "thin_spot", "unwitnessed", "branch_point", "other"] = "other"
    warrant: float = 1.0                 # Confidence in the doubt itself (0–1)
    source: str = "unspecified"          # Where it came from
    
    # Methods
    def narrow_to(self, answers: Set[str]) -> "Doubt":
        """Narrow erotetic core to subset; update status if needed."""
        
    def resolve_to(self, answer: str) -> "Doubt":
        """Resolve to single answer; lock status to RESOLVED."""
        
    def deepen(self, new_answers: Set[str]) -> "Doubt":
        """Discover new possible answers; status → PARTIAL if was narrowed."""
        
    def reemergent_from(self, new_presupposition: EGI) -> "Doubt":
        """Abductive re-emergence: doubt recurs with refined presupposition."""
```

**Serialization (JSON-roundtrip):**
```python
def to_dict(self) -> dict
def from_dict(data: dict) -> "Doubt"
```

### Modified Module: `src/universe_of_discourse.py`

**Add to UniverseOfDiscourse dataclass:**
```python
@dataclass
class UniverseOfDiscourse:
    ...
    # NEW: Doubts embedded in this UoD's inquiry trajectory
    doubts_by_state: Dict[str, List[Doubt]] = field(default_factory=dict)
    
    # NEW: Global doubt registry (all doubts ever, with lifecycle)
    all_doubts: Dict[str, Doubt] = field(default_factory=dict)
    
    # Methods
    def record_doubt_at_state(self, state_id: str, doubt: Doubt) -> None:
        """Record that a doubt emerged at this state."""
        
    def resolve_doubt_at_state(self, doubt_id: str, state_id: str, answer: EGI) -> None:
        """Record resolution of a doubt at this state."""
        
    def doubt_lifecycle(self, doubt_id: str) -> List[Tuple[str, Doubt]]:
        """Trace the full lifecycle of a doubt through the DAG."""
        
    def doubts_at_state(self, state_id: str) -> List[Doubt]:
        """Get all active doubts at a given state."""
```

### Modified Module: `src/tomos_service.py`

**Persistence layer (new methods):**
```python
class TomosService:
    def save_doubts(self, uod_id: str, doubts_dict: Dict[str, Doubt]) -> None:
        """Save doubts to {uod_path}/doubts.jsonl (one per line)."""
        
    def load_doubts(self, uod_id: str) -> Dict[str, Doubt]:
        """Load doubts from {uod_path}/doubts.jsonl."""
        
    def load_uod_with_doubts(self, uod_id: str) -> UniverseOfDiscourse:
        """Load full UoD including doubts from persistent store."""
        
    def save_uod_with_doubts(self, uod: UniverseOfDiscourse) -> None:
        """Persist UoD + doubts to disk."""
```

**File structure:**
```
tomos/{uod_id}/
├── uod.meta.json              # existing
├── history/                   # existing
├── current.egi.json           # existing
├── layout_deltas.json         # existing
├── doubts.jsonl               # NEW: one doubt per line (JSON)
└── doubts_index.json          # NEW: (optional) global index {doubt_id → states}
```

---

## Tasks (6, TDD)

### Task 1: `Doubt` class + erotetic structure
**File:** `src/erotetic_doubt.py` (new)
**What:** Core dataclass, erotetic operations (narrow, resolve, deepen, reemergent), serialization
**Tests:** `tests/test_erotetic_doubt.py`
- Doubt lifecycle (emergence → partial → resolved)
- Narrowing and deepening
- Re-emergence (abductive cycle)
- JSON round-trip

### Task 2: Integrate `Doubt` into `UniverseOfDiscourse`
**File:** `src/universe_of_discourse.py` (modify)
**What:** Add `doubts_by_state`, `all_doubts`, and lifecycle methods
**Tests:** `tests/test_uod_with_doubts.py`
- Record doubt at state
- Resolve doubt at state
- Trace lifecycle through DAG
- Query doubts at state

### Task 3: Persistence layer in `TomosService`
**File:** `src/tomos_service.py` (modify)
**What:** Save/load doubts from disk (JSONL format)
**Tests:** Existing `test_tomos_service.py` + new doubts test cases
- Save doubts to `doubts.jsonl`
- Load doubts + reconstruct lifecycle
- Round-trip (save → load → same)

### Task 4: Wire doubts into `QueryDocket` (UNKNOWN verdicts)
**File:** `src/query_docket.py` (modify)
**What:** When registering a want from UNKNOWN, create and record a `Doubt`
**Tests:** `tests/test_query_docket_with_doubts.py`
- UNKNOWN verdict → Doubt(kind="unknown_verdict")
- Doubt presupposition = current M
- Erotetic core = the three-way partition from UNKNOWN

### Task 5: Wire doubts into `attention_brief` (thin spots)
**File:** `src/domain_oracle.py` (modify)
**What:** When attention_brief identifies a thin spot, create and record a `Doubt`
**Tests:** `tests/test_attention_with_doubts.py`
- Thin spot on R → Doubt(kind="thin_spot")
- Presupposition = current M
- Erotetic core = {R is rare, R is grounded-few-ways, ...}

### Task 6: Wire doubts into `branch_points` (modal gaps)
**File:** `src/modal_query.py` (modify) OR new `src/branch_point_doubt.py`
**What:** Formalize E3's branch-point questions (◇M but not □M) as doubts
**Tests:** `tests/test_branch_point_doubts.py`
- Branch point → Doubt(kind="branch_point")
- Presupposition = start position + legal continuations
- Erotetic core = reachable basins/futures

---

## Implementation Order

**Sequential (later tasks depend on earlier):**
1. Task 1 (Doubt class — foundation)
2. Task 2 (UoD integration — container)
3. Task 3 (Persistence — storage)
4–6. Tasks 4–6 (Wiring — can run in parallel after Task 3)

---

## Integration Points (Existing Code to Modify)

| Module | Current Pattern | New Pattern |
|--------|---|---|
| `query_docket.py` | Registers "wants" from UNKNOWN | Creates Doubt objects; records at state |
| `attention_brief` | Returns list of thin spots | Creates Doubt per spot; records at state |
| `modal_query.py` | Reads ◇/□ from DAG | Formalizes as branch-point Doubt |
| `tomos_service.py` | Saves/loads UoD (EGI+history) | Also saves/loads doubts |
| `universe_of_discourse.py` | Holds current_egi + history | Also holds doubts_by_state + all_doubts |

---

## Testing Strategy

**Per-task:** Unit tests for isolated functionality  
**Integration:** `test_corpus_polarity_discipline.py` extended to verify doubts don't violate §3.3  
**End-to-end:** Load a complete UoD (e.g., E3 or Swan), verify doubts are persisted and lifecycle is correct

---

## Success Criteria

- ✓ All 6 tasks pass their tests
- ✓ Existing corpus UoDs load without regression
- ✓ A new UoD can record doubts at each state
- ✓ Doubts persist to disk and round-trip correctly
- ✓ Doubt lifecycle is traceable through the DAG
- ✓ Core tests (152) still pass

---

## Notes

- **Backward compatibility:** Existing UoDs without doubts load cleanly (empty doubts_by_state)
- **No §3.3 violation:** Doubts are metadata, not EGI content; correspondence unaffected
- **Minimal coupling:** Doubt class is independent of layout, rendering, or rule application
- **Future work (Phase 3):** Corpus-wide doubt analysis (recurring doubts, resolution metrics, etc.)
