#!/usr/bin/env python3
import json
import re
from pathlib import Path

CANONICAL_DIR = Path(__file__).resolve().parents[1] / "corpus" / "corpus" / "canonical"

AUTHOR_HIGH_PAT = re.compile(r"(sowa|roberts|stanford|dau)", re.I)
DIFF_HARD_PAT = re.compile(r"(nested|complex|ternary)", re.I)
DIFF_EASY_PAT = re.compile(r"(cat_on_mat|simple|starting)", re.I)

TOPIC_TAGS_BY_KEYWORD = {
    "cat_on_mat": ["relation", "ground", "basic"],
    "nested": ["quantifiers", "nesting", "scope"],
    "quantifier": ["quantifiers", "scope"],
    "ternary": ["arity-3", "relations"],
    "sibling": ["shared-variable", "cuts"],
    "domain_modeling": ["typing", "roles"],
    "complex_scope": ["scope", "cuts"],
    "theorem_proving": ["reasoning", "derivation"],
    "disjunction": ["boolean", "disjunction"],
}

def infer_authority_level(name: str) -> str:
    return "high" if AUTHOR_HIGH_PAT.search(name) else "medium"

def infer_difficulty(name: str) -> str:
    if DIFF_HARD_PAT.search(name):
        return "hard"
    if DIFF_EASY_PAT.search(name):
        return "easy"
    return "medium"

def infer_topic_tags(name: str) -> list[str]:
    tags = set()
    for key, tag_list in TOPIC_TAGS_BY_KEYWORD.items():
        if key in name:
            tags.update(tag_list)
    # generic tags if none matched
    if not tags:
        tags.update(["relations", "quantifiers"])  # safe baseline
    return sorted(tags)


def main() -> None:
    if not CANONICAL_DIR.exists():
        print(f"Canonical dir not found: {CANONICAL_DIR}")
        return
    updated = 0
    for p in sorted(CANONICAL_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Skip unreadable {p.name}: {e}")
            continue
        name = p.stem
        changed = False
        if "authority_level" not in data:
            data["authority_level"] = infer_authority_level(name)
            changed = True
        if "difficulty" not in data:
            data["difficulty"] = infer_difficulty(name)
            changed = True
        if "provenance_notes" not in data:
            src = data.get("source") or {}
            author = src.get("author") or ""
            work = src.get("work") or ""
            if author or work:
                data["provenance_notes"] = f"Derived from {author} {work}".strip()
            else:
                data["provenance_notes"] = "Curated exemplar for Arisbe canonical corpus"
            changed = True
        if "topic_tags" not in data:
            data["topic_tags"] = infer_topic_tags(name)
            changed = True
        if changed:
            p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            updated += 1
    print(f"Updated {updated} JSON files in {CANONICAL_DIR}")

if __name__ == "__main__":
    main()
