"""Quick test to debug clipboard issue."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from insertion_clipboard import get_insertion_clipboard
from egi_core_dau import RelationalGraphWithCuts, Vertex, ElementID
from frozendict import frozendict

# Get clipboard
clipboard = get_insertion_clipboard()
print(f"Clipboard instance: {id(clipboard)}")
print(f"Entries before: {len(clipboard.get_all_entries())}")

# Create minimal EGI
egi = RelationalGraphWithCuts(
    V=frozenset([Vertex("v1"), Vertex("v2")]),
    E=frozenset(),
    nu=frozendict(),
    sheet=ElementID("sheet"),
    Cut=frozenset(),
    area=frozendict({ElementID("sheet"): frozenset([ElementID("v1"), ElementID("v2")])}),
    rel=frozendict()
)

# Add entry
success, message, entry = clipboard.add_entry(
    subgraph_elements=frozenset([ElementID("v1"), ElementID("v2")]),
    source_egi=egi,
    name="Test Subgraph"
)

print(f"Add result: success={success}, message={message}")
print(f"Entries after add: {len(clipboard.get_all_entries())}")

# Get clipboard again (should be same singleton)
clipboard2 = get_insertion_clipboard()
print(f"Clipboard2 instance: {id(clipboard2)}")
print(f"Same instance? {clipboard is clipboard2}")
print(f"Entries from clipboard2: {len(clipboard2.get_all_entries())}")

for entry in clipboard2.get_all_entries():
    print(f"  - {entry.name}: {len(entry.subgraph_elements)} elements")
