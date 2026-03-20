"""
Endoporeutic Game — interactive REPL / CLI

Launch::

    python src/game_repl.py [initial_egif] [--goal goal_egif]

If initial_egif is omitted you will be prompted.

Commands (case-insensitive)
---------------------------
status / s          Show current graph, whose turn, area polarity map
areas               List all areas with polarity + nesting depth
history / h         Print the move history as a text proof
help / ?            List available commands

Move commands (use rule abbreviations):
  era  <id...> in <area>     Erasure          (Skeptic, positive area)
  ins  <egif> in <area>      Insertion        (Proposer, negative area)
  it+  <id...> to <area>     Iteration        (Proposer, negative area)
  it-  <id...> in <area>     Deiteration      (Skeptic, positive area)
  dc+  in <area>             Double-cut intro (either player, any area)
  dc-  <outer_cut> in <area> Double-cut erase (either player, any area)
  concede / c                Current player concedes

Persistence:
  save <file>       Save proof history as JSON
  load <file>       (Re-)load a proof from JSON  [starts new session]

IDs can be abbreviated to their first 8 characters.
Type 'quit' or press Ctrl-D to exit.
"""

import cmd
import os
import sys


def _resolve_path():
    """Add src/ to sys.path when running as a script."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)


_resolve_path()

from egif_generator_dau import generate_egif
from endoporeutic_game import EndoporeuticGame, GameState, Player
from proof_serializer import ProofSerializer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _shorten(elem_id: str, length: int = 12) -> str:
    return elem_id[:length] if len(elem_id) > length else elem_id


def _resolve_id(partial: str, egi) -> str:
    """
    Resolve a possibly-abbreviated element ID to its full form.
    Matches by prefix against all known IDs.  Raises ValueError if ambiguous
    or not found.
    """
    all_ids = (
        {v.id for v in egi.V}
        | {e.id for e in egi.E}
        | {c.id for c in egi.Cut}
        | set(egi.area.keys())
    )
    candidates = [i for i in all_ids if i.startswith(partial)]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) == 0:
        raise ValueError(f"No element ID starts with {partial!r}")
    raise ValueError(
        f"Ambiguous ID prefix {partial!r}: matches {candidates}"
    )


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------

class GameREPL(cmd.Cmd):
    intro = (
        "\n=== Endoporeutic Game REPL ===\n"
        "Type 'help' for a command list, 'status' to see the current graph.\n"
    )
    prompt = "eg-game> "

    def __init__(self, initial_egif: str, goal_egif: str = None):
        super().__init__()
        self.game = EndoporeuticGame()
        self.state: GameState = self.game.new_game(initial_egif, goal_egif)
        self._print_status()

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def _print_status(self):
        print()
        print(self.game.status_text(self.state))
        print()

    def _print_error(self, msg: str):
        print(f"  [!] {msg}")

    def _print_ok(self, msg: str):
        print(f"  → {msg}")

    # ------------------------------------------------------------------
    # Status / info commands
    # ------------------------------------------------------------------

    def do_status(self, _):
        """Show current graph, whose turn, and area polarity map."""
        self._print_status()

    do_s = do_status

    def do_areas(self, _):
        """List all areas with polarity and element count."""
        egi = self.state.current_egi
        print()
        for area_id, contents in sorted(egi.area.items()):
            pol, depth = self.game._area_polarity(egi, area_id)
            pol_str = "+" if pol.value == "positive" else "−"
            mine = " ← your turn here" if self.game._is_players_area(self.state, area_id) else ""
            print(f"  [{pol_str}] d={depth}  {_shorten(area_id)!r}  ({len(contents)} items){mine}")
        print()

    def do_history(self, _):
        """Print the transformation history as a text proof."""
        print()
        print(ProofSerializer.to_text(self.state.history))
        print()

    do_h = do_history

    def do_help(self, arg):
        """List commands or explain a specific command."""
        if arg:
            super().do_help(arg)
        else:
            print(__doc__)

    # ------------------------------------------------------------------
    # Move commands — shared parser
    # ------------------------------------------------------------------

    def _parse_in(self, args: str):
        """
        Parse '<ids...> in <area>' or 'in <area>' for DC+.
        Returns (id_list, area_id) or ([], area_id).
        """
        parts = args.strip().split()
        if "in" not in parts:
            raise ValueError("Expected 'in <area_id>'")
        idx = parts.index("in")
        elem_parts = parts[:idx]
        area_parts = parts[idx + 1:]
        if not area_parts:
            raise ValueError("Expected area ID after 'in'")
        area_raw = area_parts[0]
        area_id = _resolve_id(area_raw, self.state.current_egi)
        elem_ids = []
        for raw in elem_parts:
            elem_ids.append(_resolve_id(raw, self.state.current_egi))
        return elem_ids, area_id

    def _parse_to(self, args: str):
        """Parse '<ids...> to <area>' for IT+."""
        parts = args.strip().split()
        if "to" not in parts:
            raise ValueError("Expected 'to <area_id>'")
        idx = parts.index("to")
        elem_parts = parts[:idx]
        area_parts = parts[idx + 1:]
        if not area_parts:
            raise ValueError("Expected area ID after 'to'")
        area_id = _resolve_id(area_parts[0], self.state.current_egi)
        elem_ids = [_resolve_id(r, self.state.current_egi) for r in elem_parts]
        return elem_ids, area_id

    def _apply(self, rule: str, selected: list, area: str, insert_egif: str = None):
        """Wrapper that applies a move and prints the result."""
        if self.state.is_over:
            self._print_error("Game is already over.")
            return
        state, msg = self.game.apply_move(
            self.state,
            rule_name=rule,
            selected_subgraph=frozenset(selected),
            target_area=area,
            insert_egif=insert_egif,
        )
        self._print_ok(msg)
        if state.is_over:
            print(f"\n  *** {state.outcome_reason} ***\n")
        else:
            self._print_status()

    # ------------------------------------------------------------------
    # Individual move commands
    # ------------------------------------------------------------------

    def do_era(self, args):
        """era <id...> in <area>   — Erasure (Skeptic)"""
        try:
            elem_ids, area_id = self._parse_in(args)
            self._apply("ERA", elem_ids, area_id)
        except ValueError as exc:
            self._print_error(str(exc))

    def do_ins(self, args):
        """ins <egif> in <area>   — Insertion (Proposer)
Examples:
  ins *x (Human x) in <area_id>
  ins ~[ (Mortal x) ] in <area_id>
The EGIF must not contain spaces around 'in'; wrap in quotes if needed."""
        # Strategy: split on ' in ' (with spaces) to separate EGIF from area
        parts = args.rsplit(" in ", 1)
        if len(parts) != 2:
            self._print_error("Usage: ins <egif> in <area_id>")
            return
        insert_egif = parts[0].strip()
        area_raw = parts[1].strip()
        try:
            area_id = _resolve_id(area_raw, self.state.current_egi)
            self._apply("INS", [], area_id, insert_egif=insert_egif)
        except ValueError as exc:
            self._print_error(str(exc))

    def do_itp(self, args):
        """it+ <id...> to <area>  — Iteration (Proposer)"""
        try:
            elem_ids, area_id = self._parse_to(args)
            self._apply("IT+", elem_ids, area_id)
        except ValueError as exc:
            self._print_error(str(exc))

    def do_itm(self, args):
        """it- <id...> in <area>  — Deiteration (Skeptic)"""
        try:
            elem_ids, area_id = self._parse_in(args)
            self._apply("IT-", elem_ids, area_id)
        except ValueError as exc:
            self._print_error(str(exc))

    def do_dcp(self, args):
        """dc+ in <area>  — Double-cut introduction (either player)"""
        try:
            _, area_id = self._parse_in("in " + args.strip())
            self._apply("DC+", [], area_id)
        except ValueError as exc:
            self._print_error(str(exc))

    def do_dcm(self, args):
        """dc- <outer_cut> in <area>  — Double-cut erasure (either player)"""
        try:
            elem_ids, area_id = self._parse_in(args)
            self._apply("DC-", elem_ids, area_id)
        except ValueError as exc:
            self._print_error(str(exc))

    def do_concede(self, _):
        """concede — Current player concedes the game."""
        if self.state.is_over:
            self._print_error("Game is already over.")
            return
        state, msg = self.game.concede(self.state)
        print(f"\n  *** {msg} ***\n")

    do_c = do_concede

    # ------------------------------------------------------------------
    # Aliases for rule names
    # ------------------------------------------------------------------

    def default(self, line: str):
        """Allow 'it+', 'it-', 'dc+', 'dc-' with special characters."""
        parts = line.strip().split(None, 1)
        if not parts:
            return
        cmd_word = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""
        dispatch = {
            "it+": self.do_itp,
            "it-": self.do_itm,
            "dc+": self.do_dcp,
            "dc-": self.do_dcm,
        }
        if cmd_word in dispatch:
            dispatch[cmd_word](rest)
        else:
            print(f"  Unknown command: {parts[0]!r}. Type 'help' for a list.")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def do_save(self, args):
        """save <file>  — Save the proof history as JSON."""
        path = args.strip()
        if not path:
            self._print_error("Usage: save <filename>")
            return
        try:
            json_str = ProofSerializer.to_json(self.state.history)
            with open(path, "w", encoding="utf-8") as f:
                f.write(json_str)
            self._print_ok(f"Saved to {path!r}")
        except Exception as exc:
            self._print_error(f"Save failed: {exc}")

    def do_load(self, args):
        """load <file>  — Load a proof from JSON (replaces current session)."""
        path = args.strip()
        if not path:
            self._print_error("Usage: load <filename>")
            return
        try:
            with open(path, encoding="utf-8") as f:
                json_str = f.read()
            history = ProofSerializer.from_json(json_str)
            # Reconstruct a minimal game state from the loaded history
            current_snap = history.get_current_state()
            self.state = GameState(
                initial_egi=history.states[history.root_state_id].egi,
                current_egi=current_snap.egi,
                current_player=Player.PROPOSER,
                move_number=current_snap.step_number,
                history=history,
                outcome=__import__("endoporeutic_game").GameOutcome.ONGOING,
                outcome_reason="",
            )
            self._print_ok(f"Loaded from {path!r}  ({current_snap.step_number} moves)")
            self._print_status()
        except Exception as exc:
            self._print_error(f"Load failed: {exc}")

    # ------------------------------------------------------------------
    # Exit
    # ------------------------------------------------------------------

    def do_quit(self, _):
        """quit — Exit the game REPL."""
        print("Goodbye.")
        return True

    def do_EOF(self, _):
        """Exit on Ctrl-D."""
        print()
        return True

    do_exit = do_quit


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Endoporeutic Game — interactive REPL for Existential Graphs"
    )
    parser.add_argument(
        "initial_egif",
        nargs="?",
        help="Starting EGIF expression (quoted)",
    )
    parser.add_argument(
        "--goal", "-g",
        metavar="EGIF",
        help="Goal EGIF — Proposer wins when this appears in the current graph",
    )
    parser.add_argument(
        "--load", "-l",
        metavar="FILE",
        help="Load a saved proof JSON instead of starting fresh",
    )
    args = parser.parse_args()

    if args.load:
        # Load from file
        with open(args.load, encoding="utf-8") as f:
            json_str = f.read()
        history = ProofSerializer.from_json(json_str)
        initial_egif = generate_egif(history.states[history.root_state_id].egi)
        repl = GameREPL(initial_egif, args.goal)
        repl.state.history = history
    else:
        if args.initial_egif:
            initial_egif = args.initial_egif
        else:
            print("Enter the starting EGIF expression (e.g. '*x (Human x)'):")
            initial_egif = input("EGIF> ").strip()
            if not initial_egif:
                initial_egif = "*x"  # trivial default

        repl = GameREPL(initial_egif, args.goal)

    repl.cmdloop()


if __name__ == "__main__":
    main()
