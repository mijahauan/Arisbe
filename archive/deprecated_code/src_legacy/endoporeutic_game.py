#!/usr/bin/env python3
"""
Endoporeutic Game Engine for the Agon module.
Implements Peirce's deductive game with automated umpire functions.
"""

import os

# Import core components
import sys
import tkinter as tk
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from egi_core_dau import ElementID, RelationalGraphWithCuts
from formal_transformation_rules import (
    AreaPolarity,
    DeiterationRule,
    DoubleCutErasureRule,
    DoubleCutInsertionRule,
    ErasureRule,
    FormalTransformationRule,
    InsertionRule,
    IterationRule,
    TransformationContext,
    TransformationResult,
)

# from interactive_transformer_with_history import InteractiveTransformerWithHistory


class GameOutcome(Enum):
    """Possible outcomes of a game inning."""

    CONTRADICTION = "contradiction"
    TAUTOLOGY = "tautology"
    CONTINGENT = "contingent"
    IN_PROGRESS = "in_progress"


class UmpireDecision(Enum):
    """Umpire decisions for game outcomes."""

    ARCHIVE_DISCARD = "archive_discard"
    ACCEPT_HYPOTHESIS = "accept_hypothesis"
    CONTINUE_GAME = "continue_game"


@dataclass
class GameMove:
    """A single move in the endoporeutic game."""

    move_id: str
    player: str
    transformation_rule: str
    source_egi: RelationalGraphWithCuts
    target_egi: RelationalGraphWithCuts
    context: TransformationContext
    timestamp: datetime
    valid: bool
    explanation: str


@dataclass
class GameInning:
    """A complete game inning from hypothesis to conclusion."""

    inning_id: str
    hypothesis: RelationalGraphWithCuts
    moves: List[GameMove]
    outcome: GameOutcome
    umpire_decision: UmpireDecision
    final_egi: Optional[RelationalGraphWithCuts]
    start_time: datetime
    end_time: Optional[datetime]
    explanation: str


@dataclass
class CompetingHypothesis:
    """A hypothesis in competition with others."""

    hypothesis_id: str
    name: str
    egi: RelationalGraphWithCuts
    context_id: str
    status: str  # "active", "validated", "refuted", "archived"
    evidence_score: float
    last_tested: datetime


class EndoporeuticGameEngine:
    """Engine for conducting the endoporeutic game with umpire functions."""

    def __init__(self, master):
        self.master = master

        # Game state
        self.current_inning: Optional[GameInning] = None
        self.game_history: List[GameInning] = []
        self.competing_hypotheses: Dict[str, CompetingHypothesis] = {}

        # Transformation engine (placeholder for now)
        # self.transformer = InteractiveTransformerWithHistory()

        # Available transformation rules
        self.transformation_rules = {
            "IT+": IterationRule(),
            "IT-": DeiterationRule(),
            "DC+": DoubleCutInsertionRule(),
            "DC-": DoubleCutErasureRule(),
            "INS": InsertionRule(),
            "ERA": ErasureRule(),
        }

        # UI components
        self.game_board = None
        self.umpire_panel = None
        self.hypothesis_manager = None

        self.setup_ui()

    def setup_ui(self):
        """Create the Agon interface."""
        # Main container
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Top toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        ttk.Label(toolbar, text="Endoporeutic Game", font=("Arial", 14, "bold")).pack(
            side=tk.LEFT
        )

        ttk.Button(toolbar, text="New Game", command=self.start_new_game).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(toolbar, text="Load Hypothesis", command=self.load_hypothesis).pack(
            side=tk.RIGHT, padx=5
        )

        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel - Game board
        self.setup_game_board(content_frame)

        # Right panel - Umpire and hypothesis management
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 0))

        self.setup_umpire_panel(right_panel)
        self.setup_hypothesis_manager(right_panel)

    def setup_game_board(self, parent):
        """Setup the main game board interface."""
        game_frame = ttk.LabelFrame(parent, text="Game Board")
        game_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Game canvas (simplified for now)
        canvas_frame = ttk.Frame(game_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.game_canvas = tk.Canvas(canvas_frame, bg="white", width=600, height=400)
        self.game_canvas.pack(fill=tk.BOTH, expand=True)

        # Transformation controls
        controls_frame = ttk.Frame(game_frame)
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        ttk.Label(controls_frame, text="Available Moves:").pack(side=tk.LEFT)

        # Transformation buttons
        for rule_name in self.transformation_rules.keys():
            btn = ttk.Button(
                controls_frame,
                text=rule_name,
                command=lambda r=rule_name: self.attempt_move(r),
            )
            btn.pack(side=tk.LEFT, padx=2)

        # Game status
        self.game_status_var = tk.StringVar()
        self.game_status_var.set("No active game")
        ttk.Label(controls_frame, textvariable=self.game_status_var).pack(side=tk.RIGHT)

    def setup_umpire_panel(self, parent):
        """Setup the umpire panel for automated decisions."""
        umpire_frame = ttk.LabelFrame(parent, text="Umpire")
        umpire_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5))

        # Umpire analysis display
        analysis_frame = ttk.Frame(umpire_frame)
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.umpire_text = tk.Text(analysis_frame, wrap=tk.WORD, width=30, height=15)
        umpire_scroll = ttk.Scrollbar(
            analysis_frame, orient=tk.VERTICAL, command=self.umpire_text.yview
        )
        self.umpire_text.configure(yscrollcommand=umpire_scroll.set)

        umpire_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.umpire_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Umpire decision buttons
        decision_frame = ttk.Frame(umpire_frame)
        decision_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        ttk.Button(
            decision_frame, text="Accept Move", command=self.umpire_accept_move
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            decision_frame, text="Reject Move", command=self.umpire_reject_move
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            decision_frame, text="End Inning", command=self.umpire_end_inning
        ).pack(side=tk.LEFT, padx=2)

    def setup_hypothesis_manager(self, parent):
        """Setup the competing hypothesis management panel."""
        hypothesis_frame = ttk.LabelFrame(parent, text="Hypothesis Manager")
        hypothesis_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Hypothesis list
        list_frame = ttk.Frame(hypothesis_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.hypothesis_tree = ttk.Treeview(
            list_frame, columns=("status", "score"), show="tree headings"
        )
        self.hypothesis_tree.heading("#0", text="Hypothesis")
        self.hypothesis_tree.heading("status", text="Status")
        self.hypothesis_tree.heading("score", text="Score")

        self.hypothesis_tree.column("#0", width=150)
        self.hypothesis_tree.column("status", width=80)
        self.hypothesis_tree.column("score", width=60)

        hyp_scroll = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.hypothesis_tree.yview
        )
        self.hypothesis_tree.configure(yscrollcommand=hyp_scroll.set)

        hyp_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.hypothesis_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Hypothesis actions
        hyp_actions = ttk.Frame(hypothesis_frame)
        hyp_actions.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        ttk.Button(
            hyp_actions, text="Test Selected", command=self.test_hypothesis
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(hyp_actions, text="Compare", command=self.compare_hypotheses).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(hyp_actions, text="Archive", command=self.archive_hypothesis).pack(
            side=tk.LEFT, padx=2
        )

    def start_new_game(self):
        """Start a new game inning."""
        if (
            self.current_inning
            and self.current_inning.outcome == GameOutcome.IN_PROGRESS
        ):
            if not messagebox.askyesno(
                "New Game", "End current game and start new one?"
            ):
                return

        # Create new inning
        inning_id = str(uuid.uuid4())

        # For now, start with empty EGI (sheet of assertion)
        from frozendict import frozendict

        from egi_core_dau import RelationalGraphWithCuts

        empty_egi = RelationalGraphWithCuts(
            V=frozenset(),
            E=frozenset(),
            nu=frozendict(),
            sheet="sheet",
            Cut=frozenset(),
            area=frozendict({"sheet": frozenset()}),
            rel=frozendict(),
        )

        self.current_inning = GameInning(
            inning_id=inning_id,
            hypothesis=empty_egi,
            moves=[],
            outcome=GameOutcome.IN_PROGRESS,
            umpire_decision=UmpireDecision.CONTINUE_GAME,
            final_egi=None,
            start_time=datetime.now(),
            end_time=None,
            explanation="",
        )

        self.game_status_var.set(f"Game {inning_id[:8]} - In Progress")
        self.update_umpire_analysis("New game started. Make your first move.")
        self.draw_current_egi()

    def load_hypothesis(self):
        """Load a hypothesis to test."""
        # TODO: Implement hypothesis loading from corpus
        messagebox.showinfo("Load Hypothesis", "Hypothesis loading not yet implemented")

    def attempt_move(self, rule_name: str):
        """Attempt to make a move using the specified transformation rule."""
        if (
            not self.current_inning
            or self.current_inning.outcome != GameOutcome.IN_PROGRESS
        ):
            messagebox.showwarning("No Game", "No active game. Start a new game first.")
            return

        # For now, show move attempt
        self.update_umpire_analysis(
            f"Attempting move: {rule_name}\n\nMove validation not yet fully implemented."
        )

    def umpire_accept_move(self):
        """Umpire accepts the current move."""
        if self.current_inning:
            self.update_umpire_analysis("Move accepted by umpire.")

    def umpire_reject_move(self):
        """Umpire rejects the current move."""
        if self.current_inning:
            self.update_umpire_analysis(
                "Move rejected by umpire. Invalid transformation."
            )

    def umpire_end_inning(self):
        """Umpire ends the current inning and evaluates outcome."""
        if not self.current_inning:
            return

        # Analyze final EGI for outcome
        outcome = self.analyze_egi_outcome(self.current_inning.hypothesis)
        decision = self.make_umpire_decision(outcome)

        self.current_inning.outcome = outcome
        self.current_inning.umpire_decision = decision
        self.current_inning.end_time = datetime.now()

        # Update display
        outcome_text = f"Game Outcome: {outcome.value.title()}\n"
        outcome_text += (
            f"Umpire Decision: {decision.value.replace('_', ' ').title()}\n\n"
        )

        if outcome == GameOutcome.CONTRADICTION:
            outcome_text += "The EGI contains a logical contradiction. "
            outcome_text += "This hypothesis is logically invalid and will be archived."
        elif outcome == GameOutcome.TAUTOLOGY:
            outcome_text += "The EGI is a tautology (always true). "
            outcome_text += "While logically valid, it provides no new information and will be archived."
        elif outcome == GameOutcome.CONTINGENT:
            outcome_text += "The EGI represents a contingent hypothesis. "
            outcome_text += "This is logically valid and informative. "
            outcome_text += (
                "You may proceed to empirical testing or propose a new hypothesis."
            )

        self.update_umpire_analysis(outcome_text)

        # Archive the inning
        self.game_history.append(self.current_inning)
        self.current_inning = None
        self.game_status_var.set("Game completed")

    def analyze_egi_outcome(self, egi: RelationalGraphWithCuts) -> GameOutcome:
        """Analyze an EGI to determine its logical outcome."""
        # Simplified analysis - in full implementation, this would use
        # sophisticated logical analysis

        # Check for obvious contradictions (e.g., P and not-P)
        # Check for tautologies (e.g., empty graph, or P or not-P)
        # Otherwise assume contingent

        # For now, return contingent as default
        return GameOutcome.CONTINGENT

    def make_umpire_decision(self, outcome: GameOutcome) -> UmpireDecision:
        """Make umpire decision based on game outcome."""
        if outcome in [GameOutcome.CONTRADICTION, GameOutcome.TAUTOLOGY]:
            return UmpireDecision.ARCHIVE_DISCARD
        elif outcome == GameOutcome.CONTINGENT:
            return UmpireDecision.ACCEPT_HYPOTHESIS
        else:
            return UmpireDecision.CONTINUE_GAME

    def update_umpire_analysis(self, text: str):
        """Update the umpire analysis display."""
        self.umpire_text.delete(1.0, tk.END)
        self.umpire_text.insert(1.0, text)

    def draw_current_egi(self):
        """Draw the current EGI state on the game board."""
        self.game_canvas.delete("all")

        if self.current_inning:
            # Simple visualization - just show that we have an EGI
            self.game_canvas.create_rectangle(50, 50, 550, 350, outline="blue", width=2)
            self.game_canvas.create_text(
                300, 200, text="Current EGI State", font=("Arial", 16)
            )

            # Show basic stats
            egi = self.current_inning.hypothesis
            stats_text = (
                f"Vertices: {len(egi.V)}, Edges: {len(egi.E)}, Cuts: {len(egi.Cut)}"
            )
            self.game_canvas.create_text(300, 230, text=stats_text, font=("Arial", 12))

    def test_hypothesis(self):
        """Test the selected hypothesis."""
        selection = self.hypothesis_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select a hypothesis to test")
            return

        # TODO: Implement hypothesis testing
        messagebox.showinfo("Test Hypothesis", "Hypothesis testing not yet implemented")

    def compare_hypotheses(self):
        """Compare multiple selected hypotheses."""
        selection = self.hypothesis_tree.selection()
        if len(selection) < 2:
            messagebox.showwarning(
                "Insufficient Selection", "Select at least 2 hypotheses to compare"
            )
            return

        # TODO: Implement hypothesis comparison
        messagebox.showinfo(
            "Compare Hypotheses", "Hypothesis comparison not yet implemented"
        )

    def archive_hypothesis(self):
        """Archive the selected hypothesis."""
        selection = self.hypothesis_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select a hypothesis to archive")
            return

        # TODO: Implement hypothesis archiving
        messagebox.showinfo(
            "Archive Hypothesis", "Hypothesis archiving not yet implemented"
        )

    def add_competing_hypothesis(self, name: str, egi: RelationalGraphWithCuts) -> str:
        """Add a new competing hypothesis."""
        hypothesis_id = str(uuid.uuid4())
        context_id = f"context_{hypothesis_id}"

        hypothesis = CompetingHypothesis(
            hypothesis_id=hypothesis_id,
            name=name,
            egi=egi,
            context_id=context_id,
            status="active",
            evidence_score=0.0,
            last_tested=datetime.now(),
        )

        self.competing_hypotheses[hypothesis_id] = hypothesis
        self.update_hypothesis_display()

        return hypothesis_id

    def update_hypothesis_display(self):
        """Update the hypothesis manager display."""
        # Clear existing items
        for item in self.hypothesis_tree.get_children():
            self.hypothesis_tree.delete(item)

        # Add current hypotheses
        for hypothesis in self.competing_hypotheses.values():
            self.hypothesis_tree.insert(
                "",
                "end",
                text=hypothesis.name,
                values=(hypothesis.status, f"{hypothesis.evidence_score:.2f}"),
            )


def main():
    """Run the endoporeutic game engine."""
    root = tk.Tk()
    root.title("Arisbe - Endoporeutic Game (Agon)")
    root.geometry("1200x800")

    app = EndoporeuticGameEngine(root)
    root.mainloop()


if __name__ == "__main__":
    main()
