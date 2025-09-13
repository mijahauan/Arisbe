"""
Level polarity adjustment system for EG transformations.
Handles re-assignment of nesting levels when subgraphs are moved between contexts.
"""

from typing import Dict, List, Optional, Set, Tuple, FrozenSet
from dataclasses import dataclass
from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from frozendict import frozendict
import dataclasses


@dataclass
class PolarityAdjustment:
    """Represents a polarity adjustment for transformation operations."""
    source_depth: int
    target_depth: int
    depth_change: int
    requires_adjustment: bool


class LevelPolarityAdjuster:
    """
    Handles level polarity adjustments for transformation operations.
    
    Key principles:
    - INS and IT+ require polarity adjustment when moving subgraphs
    - DC- adjusts subgraphs 2 levels closer to level 0 (depth -= 2)
    - DC+ adjusts subgraphs 2 levels further from level 0 (depth += 2)
    - ERA and IT- do not require adjustments (removal operations)
    """
    
    def __init__(self):
        pass
    
    def calculate_adjustment(self, rule_name: str, source_context_depth: int, 
                           target_context_depth: int) -> PolarityAdjustment:
        """
        Calculate the polarity adjustment needed for a transformation.
        
        Args:
            rule_name: The transformation rule being applied
            source_context_depth: Nesting depth of source context
            target_context_depth: Nesting depth of target context
            
        Returns:
            PolarityAdjustment describing the required changes
        """
        
        # Rules that don't require adjustment
        if rule_name in ["ERA", "IT-"]:
            return PolarityAdjustment(
                source_depth=source_context_depth,
                target_depth=target_context_depth,
                depth_change=0,
                requires_adjustment=False
            )
        
        # Calculate depth change based on rule
        if rule_name == "DC-":
            # DC- moves content 2 levels closer to level 0
            depth_change = -2
        elif rule_name == "DC+":
            # DC+ moves content 2 levels further from level 0
            depth_change = +2
        elif rule_name in ["INS", "IT+"]:
            # INS and IT+ adjust based on context difference
            depth_change = target_context_depth - source_context_depth
        else:
            # Unknown rule, no adjustment
            depth_change = 0
        
        return PolarityAdjustment(
            source_depth=source_context_depth,
            target_depth=target_context_depth,
            depth_change=depth_change,
            requires_adjustment=depth_change != 0
        )
    
    def adjust_subgraph_polarity(self, subgraph_egi: RelationalGraphWithCuts, 
                               adjustment: PolarityAdjustment) -> RelationalGraphWithCuts:
        """
        Apply polarity adjustment to a subgraph EGI.
        
        Args:
            subgraph_egi: The subgraph to adjust
            adjustment: The polarity adjustment to apply
            
        Returns:
            New EGI with adjusted polarity levels
        """
        
        if not adjustment.requires_adjustment:
            return subgraph_egi
        
        # Create new area mapping with adjusted cut nesting
        new_area_mapping = dict(subgraph_egi.area)
        
        # For each cut in the subgraph, we need to adjust its relative nesting
        # This is complex because we need to maintain the internal structure
        # while adjusting the overall nesting level
        
        # For now, implement a simplified version that handles basic cases
        # Full implementation would require sophisticated cut restructuring
        
        if adjustment.depth_change == -2:
            # DC- case: remove outer double cut if present
            return self._remove_outer_double_cut(subgraph_egi)
        elif adjustment.depth_change == +2:
            # DC+ case: add outer double cut
            return self._add_outer_double_cut(subgraph_egi)
        else:
            # General case: adjust all cut levels by depth_change
            return self._adjust_cut_levels(subgraph_egi, adjustment.depth_change)
    
    def _remove_outer_double_cut(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        """
        Remove outer double cut structure (DC- operation).
        
        This handles the case where ~[ ~[ content ] ] becomes content.
        """
        
        # Find the outermost cuts
        outer_cuts = []
        for cut in egi.Cut:
            # Check if this cut is contained by any other cut
            is_contained = False
            for other_cut in egi.Cut:
                if cut.id != other_cut.id:
                    other_contents = egi.area.get(other_cut.id, frozenset())
                    if cut.id in other_contents:
                        is_contained = True
                        break
            
            if not is_contained:
                outer_cuts.append(cut)
        
        # If we have exactly 2 outer cuts (double cut), remove them
        if len(outer_cuts) == 2:
            # Find the innermost content
            innermost_content = set()
            for cut in egi.Cut:
                cut_contents = egi.area.get(cut.id, frozenset())
                # If this cut contains no other cuts, its contents are innermost
                has_nested_cuts = any(other_cut.id in cut_contents for other_cut in egi.Cut if other_cut.id != cut.id)
                if not has_nested_cuts:
                    innermost_content.update(cut_contents)
            
            # Create new EGI with content moved to sheet
            new_area_mapping = {egi.sheet: frozenset(innermost_content)}
            new_cuts = frozenset()  # Remove all cuts
            
            return RelationalGraphWithCuts(
                V=egi.V,
                E=egi.E,
                nu=egi.nu,
                sheet=egi.sheet,
                Cut=new_cuts,
                area=frozendict(new_area_mapping),
                rel=egi.rel,
                alphabet=egi.alphabet,
                rho=getattr(egi, 'rho', frozendict()),
                _vertex_map=getattr(egi, '_vertex_map', frozendict()),
                _edge_map=getattr(egi, '_edge_map', frozendict()),
                _cut_map=frozendict()
            )
        
        # If not a proper double cut, return unchanged
        return egi
    
    def _add_outer_double_cut(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        """
        Add outer double cut structure (DC+ operation).
        
        This handles the case where content becomes ~[ ~[ content ] ].
        """
        
        # Create two new cuts
        outer_cut_id = ElementID("dc_outer")
        inner_cut_id = ElementID("dc_inner")
        
        outer_cut = Cut(outer_cut_id)
        inner_cut = Cut(inner_cut_id)
        
        # Get current sheet contents
        sheet_contents = egi.area.get(egi.sheet, frozenset())
        
        # Create new area mapping
        new_area_mapping = {
            egi.sheet: frozenset([outer_cut_id]),  # Sheet contains outer cut
            outer_cut_id: frozenset([inner_cut_id]),  # Outer cut contains inner cut
            inner_cut_id: sheet_contents  # Inner cut contains original content
        }
        
        # Add existing cut areas
        for area_id, contents in egi.area.items():
            if area_id != egi.sheet:
                new_area_mapping[area_id] = contents
        
        # Create new cut set
        new_cuts = egi.Cut | {outer_cut, inner_cut}
        
        return RelationalGraphWithCuts(
            V=egi.V,
            E=egi.E,
            nu=egi.nu,
            sheet=egi.sheet,
            Cut=new_cuts,
            area=frozendict(new_area_mapping),
            rel=egi.rel,
            alphabet=egi.alphabet,
            rho=getattr(egi, 'rho', frozendict()),
            _vertex_map=getattr(egi, '_vertex_map', frozendict()),
            _edge_map=getattr(egi, '_edge_map', frozendict()),
            _cut_map=frozendict({
                **getattr(egi, '_cut_map', {}),
                outer_cut_id: outer_cut,
                inner_cut_id: inner_cut
            })
        )
    
    def _adjust_cut_levels(self, egi: RelationalGraphWithCuts, depth_change: int) -> RelationalGraphWithCuts:
        """
        Adjust all cut levels by the specified depth change.
        
        This is a simplified implementation for general level adjustments.
        """
        
        # For now, return unchanged - full implementation would require
        # sophisticated cut restructuring based on depth_change
        # This is a complex operation that needs careful handling of:
        # 1. Relative cut nesting relationships
        # 2. Preservation of logical structure
        # 3. Proper area containment mappings
        
        return egi
    
    def calculate_nesting_depth(self, area_id: ElementID, egi: RelationalGraphWithCuts) -> int:
        """Calculate the nesting depth of an area within the EGI."""
        depth = 0
        for cut in egi.Cut:
            cut_contents = egi.area.get(cut.id, frozenset())
            if area_id in cut_contents:
                depth += 1
        return depth
    
    def get_polarity(self, depth: int) -> str:
        """Get polarity (positive/negative) based on nesting depth."""
        return "positive" if depth % 2 == 0 else "negative"


def test_polarity_adjustment():
    """Test the level polarity adjustment system."""
    print("=== Testing Level Polarity Adjustment System ===")
    
    adjuster = LevelPolarityAdjuster()
    
    # Test 1: DC- adjustment calculation
    print("\n--- Test 1: DC- Adjustment ---")
    dc_minus_adj = adjuster.calculate_adjustment("DC-", source_context_depth=2, target_context_depth=0)
    print(f"DC- adjustment: depth_change={dc_minus_adj.depth_change}, requires_adjustment={dc_minus_adj.requires_adjustment}")
    
    # Test 2: DC+ adjustment calculation
    print("\n--- Test 2: DC+ Adjustment ---")
    dc_plus_adj = adjuster.calculate_adjustment("DC+", source_context_depth=0, target_context_depth=2)
    print(f"DC+ adjustment: depth_change={dc_plus_adj.depth_change}, requires_adjustment={dc_plus_adj.requires_adjustment}")
    
    # Test 3: INS adjustment calculation
    print("\n--- Test 3: INS Adjustment ---")
    ins_adj = adjuster.calculate_adjustment("INS", source_context_depth=0, target_context_depth=1)
    print(f"INS adjustment: depth_change={ins_adj.depth_change}, requires_adjustment={ins_adj.requires_adjustment}")
    
    # Test 4: ERA no adjustment
    print("\n--- Test 4: ERA No Adjustment ---")
    era_adj = adjuster.calculate_adjustment("ERA", source_context_depth=1, target_context_depth=0)
    print(f"ERA adjustment: depth_change={era_adj.depth_change}, requires_adjustment={era_adj.requires_adjustment}")
    
    # Test 5: Simple double cut creation
    print("\n--- Test 5: Double Cut Creation ---")
    from egif_parser_dau import parse_egif
    from egif_generator_dau import generate_egif
    
    try:
        simple_egi = parse_egif('(Human "Socrates")')
        dc_plus_adj = adjuster.calculate_adjustment("DC+", 0, 2)
        adjusted_egi = adjuster.adjust_subgraph_polarity(simple_egi, dc_plus_adj)
        result_egif = generate_egif(adjusted_egi)
        print(f"Original: (Human \"Socrates\")")
        print(f"After DC+: {result_egif}")
    except Exception as e:
        print(f"Error in double cut creation test: {e}")


if __name__ == "__main__":
    test_polarity_adjustment()
