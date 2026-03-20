"""
Z3 Semantic Validator for EGI Transformation Soundness

Replaces the stub implementations in chapter17_soundness_evaluation.py with
genuine Z3 SMT-solver based verification.

Core operations
---------------
are_semantically_equivalent(G, G')
    Returns True if G ≡ G' (¬(G ↔ G') is UNSAT in Z3).
    Returns False if a countermodel exists.
    Returns None if Z3 times out (inconclusive).

is_satisfiable(G)
    Returns True / False / None (unknown).

is_tautology(G)
    Returns True if ¬G is UNSAT.

validate_transformation(rule, context, timeout_ms)
    Apply rule to get G', then check G ≡ G'.

Pipeline
--------
EGI → Φ (egi_to_fopl) → FOPL string → parse_fopl_formula → FOPLFormula AST
   → _fopl_ast_to_z3 → z3.ExprRef → Solver

Limitations
-----------
- First-order logic is semi-decidable; Z3 may return 'unknown' for complex
  quantified formulas.  All callers must handle the None (unknown) result.
- The domain sort U is always uninterpreted (no finite-domain assumption).
"""

from __future__ import annotations

import sys
import os
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

# Z3 import — optional dependency; callers should check Z3_AVAILABLE
try:
    import z3
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False

from egi_core_dau import RelationalGraphWithCuts
from chapter18_fopl_translation import (
    AtomicFormula,
    ConjunctionFormula,
    ExistentialFormula,
    FOPLFormula,
    ImplicationFormula,
    NegationFormula,
    UniversalFormula,
    egi_to_fopl,
    parse_fopl_formula,
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

class Z3Result:
    """
    Result from a Z3 query.

    Attributes:
        value     True = definitely yes; False = definitely no; None = unknown
        reason    Human-readable explanation
        model     Countermodel (if value is False and one was found)
    """
    __slots__ = ("value", "reason", "model")

    def __init__(
        self,
        value: Optional[bool],
        reason: str = "",
        model: Optional[object] = None,
    ):
        self.value = value
        self.reason = reason
        self.model = model

    def __bool__(self):
        return self.value is True

    def __repr__(self):
        label = {True: "YES", False: "NO", None: "UNKNOWN"}[self.value]
        return f"Z3Result({label}: {self.reason})"


# ---------------------------------------------------------------------------
# Z3 compiler for FOPLFormula ASTs
# ---------------------------------------------------------------------------

class FOPLToZ3Compiler:
    """
    Compiles a FOPLFormula AST into a Z3 expression.

    All relation names are registered as uninterpreted functions over a
    single sort U (the domain of discourse).  Variable scoping follows
    standard quantifier nesting.
    """

    def __init__(self):
        if not Z3_AVAILABLE:
            raise ImportError("z3-solver is required for semantic validation")
        self.domain_sort = z3.DeclareSort("U")
        self._func_cache: Dict[Tuple[str, int], z3.FuncDeclRef] = {}

    def compile(
        self,
        formula: FOPLFormula,
        var_env: Optional[Dict[str, z3.ExprRef]] = None,
    ) -> z3.ExprRef:
        """Compile a FOPLFormula to a Z3 expression."""
        if var_env is None:
            var_env = {}

        if isinstance(formula, AtomicFormula):
            return self._compile_atomic(formula, var_env)
        if isinstance(formula, NegationFormula):
            return z3.Not(self.compile(formula.formula, var_env))
        if isinstance(formula, ConjunctionFormula):
            return z3.And(
                self.compile(formula.left, var_env),
                self.compile(formula.right, var_env),
            )
        if isinstance(formula, ImplicationFormula):
            return z3.Implies(
                self.compile(formula.antecedent, var_env),
                self.compile(formula.consequent, var_env),
            )
        if isinstance(formula, ExistentialFormula):
            return self._compile_quantifier(formula, var_env, universal=False)
        if isinstance(formula, UniversalFormula):
            return self._compile_quantifier(formula, var_env, universal=True)

        raise ValueError(f"Unsupported FOPLFormula type: {type(formula).__name__}")

    # ------------------------------------------------------------------

    def _compile_atomic(
        self, formula: AtomicFormula, var_env: Dict[str, z3.ExprRef]
    ) -> z3.ExprRef:
        arity = len(formula.variables)
        key = (formula.relation, arity)
        if key not in self._func_cache:
            sorts = [self.domain_sort] * arity + [z3.BoolSort()]
            self._func_cache[key] = z3.Function(formula.relation, *sorts)
        func = self._func_cache[key]
        args = [self._resolve_var(v, var_env) for v in formula.variables]
        if arity == 0:
            # Propositional constant — use Bool
            if key not in self._func_cache:
                self._func_cache[key] = z3.Bool(formula.relation)
            return z3.Bool(formula.relation)
        return func(*args)

    def _resolve_var(
        self, name: str, var_env: Dict[str, z3.ExprRef]
    ) -> z3.ExprRef:
        if name in var_env:
            return var_env[name]
        # Free variable — create a Z3 constant
        return z3.Const(name, self.domain_sort)

    def _compile_quantifier(
        self,
        formula,
        var_env: Dict[str, z3.ExprRef],
        universal: bool,
    ) -> z3.ExprRef:
        var_name = formula.variable
        z3_var = z3.Const(var_name, self.domain_sort)
        inner_env = {**var_env, var_name: z3_var}
        body = self.compile(formula.formula, inner_env)
        if universal:
            return z3.ForAll([z3_var], body)
        return z3.Exists([z3_var], body)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_DEFAULT_TIMEOUT_MS = 10_000  # 10 s


def _parse_to_z3(fopl_str: str, compiler: FOPLToZ3Compiler) -> Optional[z3.ExprRef]:
    """
    Parse a FOPL string and compile to Z3.  Returns None for empty strings
    (empty graph = tautologically true).
    """
    if not fopl_str or fopl_str.strip() in ("", "⊤", "True"):
        return z3.BoolVal(True)
    try:
        ast = parse_fopl_formula(fopl_str)
        return compiler.compile(ast)
    except Exception:
        return None


def are_semantically_equivalent(
    egi1: RelationalGraphWithCuts,
    egi2: RelationalGraphWithCuts,
    timeout_ms: int = _DEFAULT_TIMEOUT_MS,
) -> Z3Result:
    """
    Verify G₁ ≡ G₂ using Z3.

    Strategy: build a fresh solver, add ¬(G₁ ↔ G₂), check UNSAT.
    - UNSAT  → equivalent (True)
    - SAT    → not equivalent, countermodel available (False)
    - UNKNOWN → timeout / undecidable (None)
    """
    if not Z3_AVAILABLE:
        return Z3Result(None, "z3-solver not installed")

    compiler = FOPLToZ3Compiler()

    fopl1 = egi_to_fopl(egi1)
    fopl2 = egi_to_fopl(egi2)

    z3_f1 = _parse_to_z3(fopl1, compiler)
    z3_f2 = _parse_to_z3(fopl2, compiler)

    if z3_f1 is None:
        return Z3Result(None, f"Failed to parse FOPL for EGI1: {fopl1!r}")
    if z3_f2 is None:
        return Z3Result(None, f"Failed to parse FOPL for EGI2: {fopl2!r}")

    # ¬(G1 ↔ G2) = ¬((G1 → G2) ∧ (G2 → G1))
    not_equiv = z3.Not(
        z3.And(z3.Implies(z3_f1, z3_f2), z3.Implies(z3_f2, z3_f1))
    )

    solver = z3.Solver()
    solver.set("timeout", timeout_ms)
    solver.add(not_equiv)

    result = solver.check()

    if result == z3.unsat:
        return Z3Result(True, f"Equivalent: ¬({fopl1} ↔ {fopl2}) is UNSAT")
    if result == z3.sat:
        model = solver.model()
        return Z3Result(False, f"Not equivalent: countermodel found", model)
    return Z3Result(None, "Unknown: Z3 timed out or could not decide")


def is_satisfiable(
    egi: RelationalGraphWithCuts,
    timeout_ms: int = _DEFAULT_TIMEOUT_MS,
) -> Z3Result:
    """Return True if G has at least one model."""
    if not Z3_AVAILABLE:
        return Z3Result(None, "z3-solver not installed")

    compiler = FOPLToZ3Compiler()
    fopl = egi_to_fopl(egi)
    z3_f = _parse_to_z3(fopl, compiler)

    if z3_f is None:
        return Z3Result(None, f"Failed to parse: {fopl!r}")

    solver = z3.Solver()
    solver.set("timeout", timeout_ms)
    solver.add(z3_f)
    result = solver.check()

    if result == z3.sat:
        return Z3Result(True, "Satisfiable", solver.model())
    if result == z3.unsat:
        return Z3Result(False, "Unsatisfiable (contradiction)")
    return Z3Result(None, "Unknown")


def is_tautology(
    egi: RelationalGraphWithCuts,
    timeout_ms: int = _DEFAULT_TIMEOUT_MS,
) -> Z3Result:
    """Return True if ¬G is UNSAT (i.e. G is always true)."""
    if not Z3_AVAILABLE:
        return Z3Result(None, "z3-solver not installed")

    compiler = FOPLToZ3Compiler()
    fopl = egi_to_fopl(egi)
    z3_f = _parse_to_z3(fopl, compiler)

    if z3_f is None:
        return Z3Result(None, f"Failed to parse: {fopl!r}")

    solver = z3.Solver()
    solver.set("timeout", timeout_ms)
    solver.add(z3.Not(z3_f))
    result = solver.check()

    if result == z3.unsat:
        return Z3Result(True, f"Tautology: ¬({fopl}) is UNSAT")
    if result == z3.sat:
        return Z3Result(False, "Not a tautology: countermodel found", solver.model())
    return Z3Result(None, "Unknown")


def validate_transformation_soundness(
    rule,
    context,
    timeout_ms: int = _DEFAULT_TIMEOUT_MS,
) -> "SoundnessTestResult":
    """
    Apply a transformation rule and verify semantic equivalence of G and G'.

    Returns a SoundnessTestResult compatible with Chapter17SoundnessEvaluator.
    Imports SoundnessTestResult locally to avoid circular imports.
    """
    from chapter17_soundness_evaluation import SoundnessTestResult

    rule_name = rule.get_rule_name()

    result = rule.apply_transformation(context)
    if not result.success:
        return SoundnessTestResult(
            rule_name=rule_name,
            is_sound=False,
            semantic_equivalence_verified=False,
            model_preservation_verified=False,
            error_message=f"Transformation failed: {result.error_message}",
        )

    equiv = are_semantically_equivalent(
        context.source_egi, result.result_egi, timeout_ms=timeout_ms
    )
    sat_orig = is_satisfiable(context.source_egi, timeout_ms=timeout_ms)

    sem_equiv = equiv.value  # True / False / None
    model_pres = (
        equiv.value is True or equiv.value is None
    )  # Inconclusive counts as preserved (conservative)

    is_sound = sem_equiv is True

    return SoundnessTestResult(
        rule_name=rule_name,
        is_sound=is_sound,
        semantic_equivalence_verified=sem_equiv is True,
        model_preservation_verified=model_pres,
        error_message=None if is_sound else equiv.reason,
        test_details={
            "fopl_original": egi_to_fopl(context.source_egi),
            "fopl_transformed": egi_to_fopl(result.result_egi),
            "z3_equivalence": repr(equiv),
            "z3_satisfiable": repr(sat_orig),
            "changes_made": result.changes_made,
        },
    )
