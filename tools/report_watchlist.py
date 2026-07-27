"""Watchlist report — the PW1/PW2 disposal instrument (V2b-lite; spec:
docs/superpowers/specs/2026-07-27-journal-watchlist-aperture.md).

Reads a finished run's final M (the last ``vault_v0_seg<N>`` UoD via
``TomosService``) plus the author's watchlist and prints the per-GROUP
per-DECADE table of per-entry mention RATES (mentions ÷ entries-in-decade,
joining ``mentions`` × ``entry_date``) and the O1 coverage observable
(fraction of entries carrying ≥1 hit, per decade).

Custody: rates are per-decade, not raw counts, because entry density varies
by decade — a raw count would read as a life-shape signal that is really a
diary-habit signal. Output is numbers and GROUP names only (group names are
the author's own headers); terms are printed only under ``--terms`` (local
reading), and entry ids never. This tool reads the gitignored side-store —
it writes nothing.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from probe_feed import _model_signature       # noqa: E402
from tomos_service import TomosService         # noqa: E402
from vault_world import _const, load_watchlist  # noqa: E402

_SEG_RE = re.compile(r"vault_v0_seg(\d+)$")


def _latest_segment_id(service: TomosService):
    """The highest-numbered ``vault_v0_seg<N>`` — the run's final M carries
    every earlier segment forward, so the last segment IS the run's state."""
    best = None
    for entry in service.list_uods():
        uid = entry.get("uod_id") or entry.get("id") or ""
        m = _SEG_RE.fullmatch(uid)
        if m and (best is None or int(m.group(1)) > best[0]):
            best = (int(m.group(1)), uid)
    return best[1] if best else None


def _decade(month: str):
    year = (month or "")[:4]
    return f"{int(year) // 10 * 10}s" if year.isdigit() else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs-dir", default="runs/run13",
                     help="the run's TomosService root (gitignored side-store)")
    ap.add_argument("--root", default="/Users/mjh/Documents/Vorago",
                     help="vault root, used only to locate the default watchlist")
    ap.add_argument("--watchlist", default=None,
                     help="watchlist path (default: <root>/Arisbe/Watchlist.md)")
    ap.add_argument("--uod", default=None,
                     help="explicit UoD id (default: the latest vault_v0_seg<N>)")
    ap.add_argument("--terms", action="store_true",
                     help="also print per-term rows — terms are withheld by "
                          "default so a captured table stays group-level")
    args = ap.parse_args(argv)

    wl_path = Path(args.watchlist) if args.watchlist else (
        Path(args.root) / "Arisbe" / "Watchlist.md")
    wl = load_watchlist(wl_path)
    if not wl.is_open:
        print("watchlist: closed (no file or no terms) - nothing to report")
        return 1

    service = TomosService(Path(args.runs_dir))
    uod_id = args.uod or _latest_segment_id(service)
    if uod_id is None:
        print("no vault_v0_seg* UoD found in the runs dir")
        return 1
    uod = service.load_uod(uod_id)
    if uod is None:
        print("uod not loadable")
        return 1

    atoms, _cuts = _model_signature(uod.current_egi)
    entry_decade: dict = {}
    mentions = []                       # (entry_id, emitted term)
    for rel, labels in atoms:
        if rel == "entry_date" and len(labels) >= 2:
            d = _decade(labels[1])
            if d:
                entry_decade[labels[0]] = d
        elif rel == "mentions" and len(labels) >= 2:
            mentions.append((labels[0], labels[1]))

    entries_in = Counter(entry_decade.values())
    decades = sorted(entries_in)

    # The join key mirrors emission: atoms carry _const(term); group
    # membership is a report-time classification, so a term two groups share
    # is credited to both (the atom itself is group-blind).
    term_groups: defaultdict = defaultdict(list)
    for group, terms in wl.groups.items():
        for term in terms:
            term_groups[_const(term).lower()].append((group, term))

    group_dec: Counter = Counter()      # (group, decade) -> mention count
    term_dec: Counter = Counter()       # (group, term, decade) -> mention count
    hit_entries: defaultdict = defaultdict(set)   # decade -> entries with ≥1 hit
    unlisted = 0                        # M-term no longer on the watchlist
    undated = 0                         # mention whose entry has no date in M
    for eid, term in mentions:
        dec = entry_decade.get(eid)
        if dec is None:
            undated += 1                # counted, never silently dropped
            continue
        homes = term_groups.get(term.lower())
        if not homes:
            unlisted += 1               # watchlist edited since the run ran
            continue
        hit_entries[dec].add(eid)
        for group, spelled in homes:
            group_dec[(group, dec)] += 1
            term_dec[(group, spelled, dec)] += 1

    name_w = max([len(g) for g in wl.groups] + [len("coverage (O1)")],
                 default=12) + 4
    col_w = max([len(d) for d in decades] + [7]) + 2

    def _row(label: str, cells) -> str:
        return label.ljust(name_w) + "".join(c.rjust(col_w) for c in cells)

    print(f"watchlist report — {uod_id}  "
          f"(rates = mentions ÷ entries-in-decade)")
    print(_row("decade", decades))
    print(_row("entries", [str(entries_in[d]) for d in decades]))
    for group in wl.groups:
        print(_row(group, [
            f"{group_dec[(group, d)] / entries_in[d]:.3f}" for d in decades]))
        if args.terms:
            for term in wl.groups[group]:
                print(_row(f"  - {term}", [
                    f"{term_dec[(group, term, d)] / entries_in[d]:.3f}"
                    for d in decades]))
    print(_row("coverage (O1)", [
        f"{len(hit_entries[d]) / entries_in[d]:.3f}" for d in decades]))
    if unlisted:
        print(f"unlisted_mentions: {unlisted}  "
              "(in M but no longer on the watchlist)")
    if undated:
        print(f"undated_mentions: {undated}  (entry_date absent from M)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
