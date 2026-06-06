"""
Workshop scratch store — a regime-1 holding pen for Ergasterion drafts.

The Ergasterion is where a user *plays*: composes new graphs, copies one in
from Organon and transforms it, backs up and branches.  None of that is
asserted — it is regime-1 work, drawn but not anchored in the corpus context.
A new graph only earns a place in the attested corpus (Organon) by being a
style-only reprojection of an already-attested graph, or by being *tested
through Agon*.  §3.3 attestation proves *correspondence*, not *truth*, so it is
necessary but not sufficient for assertion.

This store is therefore deliberately **separate from the corpus** (TomosService):
it holds fragments, incomplete attempts, and saved branches the user wants to
come back to, with **no §3.3 gate** (a draft need not even be in correspondence
yet) and no warrant.  It persists one transformation line (the active branch of
a session) per entry, reusing the same JSONL chain shape as the corpus history
so a saved draft round-trips back into a workshop session.

Files written under ``<root>/<scratch_id>/``:

    meta.json                  — {scratch_id, name, base_source, style_name,
                                  created, step_count}
    chain.jsonl                — initial-state header + one record per step
    states/<state_id>.egi.json — per-state EGI snapshots
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Ensure src/ is on path (when imported from web_api/services/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from egi_core_dau import RelationalGraphWithCuts
from egi_io import load_egi_json, save_egi_json
from tomos_service import ChainStep, TransformationChain


class ScratchStore:
    """A flat, file-backed store of workshop drafts (regime-1, un-attested)."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # ----- write -------------------------------------------------------- #

    def save(
        self,
        chain: TransformationChain,
        *,
        name: str,
        base_source: str,
        style_name: Optional[str] = None,
        scratch_id: Optional[str] = None,
    ) -> dict:
        """Persist a transformation line as a draft.  No §3.3 — it's a draft.

        Returns the entry's metadata dict.  Passing an existing ``scratch_id``
        overwrites that entry (save-in-place); otherwise a new id is minted.
        """
        scratch_id = scratch_id or f"scratch-{uuid.uuid4().hex[:8]}"
        entry_dir = self.root / scratch_id
        states_dir = entry_dir / "states"
        states_dir.mkdir(parents=True, exist_ok=True)

        for state_id, state_egi in chain.states.items():
            save_egi_json(state_egi, states_dir / f"{state_id}.egi.json")

        with open(entry_dir / "chain.jsonl", "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "initial",
                "initial_state_id": chain.initial_state_id,
            }) + "\n")
            for step in chain.steps:
                f.write(json.dumps({
                    "type": "step",
                    "step_id": step.step_id,
                    "rule_name": step.rule_name,
                    "from_state_id": step.from_state_id,
                    "to_state_id": step.to_state_id,
                    "parameters": step.parameters,
                    "timestamp": step.timestamp,
                    "user_annotation": step.user_annotation,
                }) + "\n")

        meta = {
            "scratch_id": scratch_id,
            "name": name or scratch_id,
            "base_source": base_source,
            "style_name": style_name,
            "created": datetime.now(timezone.utc).isoformat(),
            "step_count": len(chain.steps),
        }
        with open(entry_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        return meta

    # ----- read --------------------------------------------------------- #

    def list(self) -> List[dict]:
        """All saved drafts, newest first."""
        out: List[dict] = []
        for entry in self.root.iterdir():
            if not entry.is_dir():
                continue
            meta_path = entry / "meta.json"
            if not meta_path.exists():
                continue
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    out.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                continue
        out.sort(key=lambda m: m.get("created", ""), reverse=True)
        return out

    def load(self, scratch_id: str) -> Optional[Tuple[TransformationChain, dict]]:
        """Load a draft as ``(chain, meta)``; ``None`` if missing or broken."""
        entry_dir = self.root / scratch_id
        chain_jsonl = entry_dir / "chain.jsonl"
        states_dir = entry_dir / "states"
        meta_path = entry_dir / "meta.json"
        if not (chain_jsonl.exists() and states_dir.exists() and meta_path.exists()):
            return None

        initial_state_id: Optional[str] = None
        steps: List[ChainStep] = []
        with open(chain_jsonl, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if obj.get("type") == "initial":
                    initial_state_id = obj["initial_state_id"]
                elif obj.get("type") == "step":
                    steps.append(ChainStep(
                        step_id=obj["step_id"],
                        rule_name=obj["rule_name"],
                        from_state_id=obj["from_state_id"],
                        to_state_id=obj["to_state_id"],
                        parameters=obj.get("parameters", {}),
                        timestamp=obj["timestamp"],
                        user_annotation=obj.get("user_annotation"),
                    ))
        if initial_state_id is None:
            return None

        needed = {initial_state_id}
        for step in steps:
            needed.add(step.from_state_id)
            needed.add(step.to_state_id)
        states: Dict[str, RelationalGraphWithCuts] = {}
        for sid in needed:
            snap = states_dir / f"{sid}.egi.json"
            if not snap.exists():
                return None  # broken draft — refuse a partial load
            states[sid] = load_egi_json(snap)

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        return TransformationChain(
            initial_state_id=initial_state_id,
            steps=steps,
            states=states,
        ), meta

    def delete(self, scratch_id: str) -> bool:
        """Remove a draft.  Returns False if it wasn't there."""
        entry_dir = self.root / scratch_id
        if not entry_dir.exists():
            return False
        import shutil
        shutil.rmtree(entry_dir)
        return True
