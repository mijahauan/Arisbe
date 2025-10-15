# Arisbe Codebase Coherence Analysis

## Executive Summary
- **Total Issues Found**: 2710
- **Inconsistencies**: 5
- **Redundancies**: 0
- **Orphaned Code**: 2705

## Inconsistencies
### Naming Inconsistency (MEDIUM)
**Description**: Inconsistent naming prefixes in transformation functions
**Suggested Fix**: Standardize on common prefix pattern for transformation functions
**Locations**: 129 files affected

### Naming Inconsistency (MEDIUM)
**Description**: Inconsistent naming prefixes in polarity functions
**Suggested Fix**: Standardize on common prefix pattern for polarity functions
**Locations**: 8 files affected

### Naming Inconsistency (MEDIUM)
**Description**: Inconsistent naming prefixes in validation functions
**Suggested Fix**: Standardize on common prefix pattern for validation functions
**Locations**: 6 files affected

### Interface Incompatibility (HIGH)
**Description**: Incompatible parameter patterns in polarity functions
**Suggested Fix**: Standardize polarity function interfaces
**Locations**: 8 files affected

### Interface Incompatibility (HIGH)
**Description**: Incompatible parameter patterns in transformation functions
**Suggested Fix**: Standardize transformation function interfaces
**Locations**: 129 files affected

## Disconnected/Orphaned Code
### dau_theorem_correspondence_tests.DauTheorem (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_theorem_correspondence_tests.py:33
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_theorem_correspondence_tests.DauTheoremCorrespondenceTests.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_theorem_correspondence_tests.py:66
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_theorem_correspondence_tests.DauTheoremCorrespondenceTests.run_all_theorem_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_theorem_correspondence_tests.py:75
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_theorem_correspondence_tests.DauTheoremCorrespondenceTests._create_equivalent_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_theorem_correspondence_tests.py:576
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_theorem_correspondence_tests.DauTheoremCorrespondenceTests._compute_nesting_levels (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_theorem_correspondence_tests.py:623
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### dau_theorem_correspondence_tests.DauTheoremCorrespondenceTests._validate_nesting_preservation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_theorem_correspondence_tests.py:640
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### dau_theorem_correspondence_tests.DauTheoremCorrespondenceTests._print_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_theorem_correspondence_tests.py:649
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_theorem_correspondence_tests.run_dau_theorem_correspondence_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_theorem_correspondence_tests.py:690
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusCategory (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:19
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusItem.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:41
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:49
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager._load_tomos_index (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:54
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager._scan_directory (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager._process_file (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:76
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager._determine_category (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:117
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager._parse_metadata (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:132
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager._clean_content (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:147
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager.get_items_by_category (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:157
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager.get_item (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:161
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager.search_items (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:165
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager.parse_item_to_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:178
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager.get_drawing_schema_for_item (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:201
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager.get_categories (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:252
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusManager.get_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:259
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusIntegration.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:286
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusIntegration.get_corpus_list_for_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:289
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusIntegration.load_item_for_editor (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:307
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### corpus_integration.CorpusIntegration.get_related_items (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:321
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_transformer_with_history.InteractiveTransformerWithHistory.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_transformer_with_history.py:54
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_transformer_with_history.InteractiveTransformerWithHistory.create_new_session (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_transformer_with_history.py:69
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### interactive_transformer_with_history.InteractiveTransformerWithHistory.load_session (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_transformer_with_history.py:134
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### interactive_transformer_with_history.InteractiveTransformerWithHistory.undo_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_transformer_with_history.py:250
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### interactive_transformer_with_history.InteractiveTransformerWithHistory.create_exploration_branch (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_transformer_with_history.py:293
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_transformer_with_history.InteractiveTransformerWithHistory.get_transformation_narrative (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_transformer_with_history.py:304
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### interactive_transformer_with_history.InteractiveTransformerWithHistory.export_proof (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_transformer_with_history.py:329
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### interactive_transformer_with_history.InteractiveTransformerWithHistory.save_session (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_transformer_with_history.py:357
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_transformer_with_history.InteractiveTransformerWithHistory.get_session_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_transformer_with_history.py:377
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_transformer_with_history.InteractiveTransformerWithHistory._update_history_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_transformer_with_history.py:399
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_transformer_with_history.InteractiveTransformerWithHistory._auto_save_session (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_transformer_with_history.py:419
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_transformer_with_history.InteractiveTransformerWithHistory._create_analysis_from_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_transformer_with_history.py:433
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_transformer_with_history.InteractiveTransformerWithHistory.get_available_sessions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_transformer_with_history.py:446
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.Point2D (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.Point2D.__str__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:25
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.ValidationMode (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:29
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:38
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator.create_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:57
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator.create_predicate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:86
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator.create_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:117
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator.update_vertex_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:155
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator.update_predicate_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:164
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator.update_cut_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:173
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator.get_all_elements_in_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:184
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator.get_element_count (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:188
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator.clear_all (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:197
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator.load_egi_data (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:209
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator.load_egi_dto (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:302
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator._render_loaded_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:327
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_coordinator.DiagramCoordinator.get_current_drawing_schema (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_coordinator.py:385
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFTokenType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFLexer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:63
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFLexer.tokenize (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:68
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFLexer._skip_whitespace (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:124
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFLexer._read_string (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:130
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFLexer._read_comment (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:148
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFLexer._check_sequence_marker (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:163
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFLexer._read_sequence_marker (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:168
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFLexer._check_at_every (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:174
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFLexer._read_at_every (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:179
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFLexer._read_numeral (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:185
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFLexer._read_identifier (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:199
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFParseNode.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:220
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFParser.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:230
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFParser.parse (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:240
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFParser._advance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:256
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFParser._expect (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:262
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFParser._parse_cg (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:270
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFParser._parse_concept (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:287
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFParser._parse_relation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:385
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFParser._parse_reference (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:412
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFParser._convert_to_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:449
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_parser_dau.CGIFParser._finalize_alphabet_and_rho (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:533
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.HistoryEvent.to_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:52
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.GraphHistory.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:88
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.GraphHistory.add_event (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:98
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.GraphHistory.create_transformation_event (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:111
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### historical_graph_model.GraphHistory.create_checkpoint (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:128
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.GraphHistory.create_branch (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:141
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.GraphHistory.switch_branch (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:166
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.GraphHistory.get_events_to_replay (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:178
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.GraphHistory.get_transformation_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:194
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### historical_graph_model.GraphHistory.get_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:213
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.GraphHistory.export_history (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:229
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.HistoricalGraph.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:264
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.HistoricalGraph.create_checkpoint (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:300
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.HistoricalGraph.replay_to_event (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:309
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### historical_graph_model.HistoricalGraph.get_transformation_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:337
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### historical_graph_model.HistoricalGraph.branch_from_event (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:341
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.HistoricalGraph.merge_from_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:345
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.HistoricalGraph.export_with_history (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:366
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.HistoricalGraph._serialize_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:385
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.HistoricalGraphRepository (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:424
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### historical_graph_model.HistoricalGraphRepository.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:432
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.HistoricalGraphRepository.store_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:435
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.HistoricalGraphRepository.load_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:440
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.HistoricalGraphRepository.find_graphs_by_provenance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:444
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### historical_graph_model.HistoricalGraphRepository.get_transformation_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/historical_graph_model.py:457
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### dau_diagram_correspondence.DiagramElementType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_diagram_correspondence.py:25
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_diagram_correspondence.DauDiagramCorrespondence.validate_diagram_constraints (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_diagram_correspondence.py:106
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_diagram_correspondence.DauDiagramCorrespondence._validate_nary_relation_constraint (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_diagram_correspondence.py:116
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_diagram_correspondence.DauDiagramCorrespondence._validate_dominating_nodes_constraint (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_diagram_correspondence.py:145
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_diagram_correspondence.DauDiagramCorrespondence._is_dominated_by (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_diagram_correspondence.py:167
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_diagram_correspondence.DauDiagramCorrespondence._cut_contains_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_diagram_correspondence.py:196
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### dau_diagram_correspondence.DauDiagramCorrespondence.diagram_to_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_diagram_correspondence.py:223
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_diagram_correspondence.DauDiagramCorrespondence.egi_to_diagram (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_diagram_correspondence.py:301
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_diagram_correspondence.DauDiagramCorrespondence._find_containing_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_diagram_correspondence.py:361
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_diagram_correspondence.DauDiagramCorrespondence.calculate_graph_aware_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_diagram_correspondence.py:368
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_diagram_correspondence.DauDiagramCorrespondence._build_connection_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_diagram_correspondence.py:408
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_diagram_correspondence.DauDiagramCorrespondence._build_element_chain (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_diagram_correspondence.py:428
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_egif_transformer.InteractiveEGIFTransformer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:31
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_egif_transformer.InteractiveEGIFTransformer._discover_corpus_files (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:38
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_egif_transformer.InteractiveEGIFTransformer.analyze_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:67
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_egif_transformer.InteractiveEGIFTransformer.display_graph_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:202
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_egif_transformer.InteractiveEGIFTransformer.display_analysis (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:233
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_egif_transformer.InteractiveEGIFTransformer.display_yaml_structure (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:265
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_egif_transformer.InteractiveEGIFTransformer.get_user_choice (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:313
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_egif_transformer.InteractiveEGIFTransformer.select_transformation_rule (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:338
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### interactive_egif_transformer.InteractiveEGIFTransformer.select_target_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:356
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### interactive_egif_transformer.InteractiveEGIFTransformer.get_subgraph_specification (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:387
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### interactive_egif_transformer.InteractiveEGIFTransformer.get_valid_iteration_destinations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:678
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_egif_transformer.InteractiveEGIFTransformer.is_area_nested_within (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:703
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### interactive_egif_transformer.InteractiveEGIFTransformer.run_interactive_session (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:726
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### interactive_egif_transformer.InteractiveEGIFTransformer.continue_transformation_session (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/interactive_egif_transformer.py:819
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### formal_transformation_rules.FormalTransformationRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:47
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### formal_transformation_rules.FormalTransformationRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:52
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### formal_transformation_rules.FormalTransformationRule.is_closed_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:61
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.FormalTransformationRule.calculate_area_polarity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:75
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Connect to hierarchical_index.py

### formal_transformation_rules.DoubleCutInsertionRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:116
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### formal_transformation_rules.DoubleCutInsertionRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:119
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.DoubleCutErasureRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:216
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### formal_transformation_rules.DoubleCutErasureRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:219
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.InsertionRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:311
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### formal_transformation_rules.InsertionRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:314
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system

### formal_transformation_rules.ErasureRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:431
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### formal_transformation_rules.ErasureRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:434
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system

### formal_transformation_rules.IterationRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:535
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### formal_transformation_rules.IterationRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:538
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.DeiterationRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:640
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### formal_transformation_rules.DeiterationRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:643
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.DeiterationRule._check_deiteration_with_isomorphism_engine (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:654
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.DeiterationRule._basic_deiteration_validation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:671
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.DeiterationRule._get_nesting_hierarchy (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:692
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### formal_transformation_rules.DeiterationRule._contains_identical_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:714
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.DeiterationRule._is_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:799
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.DeiterationRule._is_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:803
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.DeiterationRule._is_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:807
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.DeiterationRule._get_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:811
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.DeiterationRule._get_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:818
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.DeiterationRule._get_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:825
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.DeiterationRule._sequences_structurally_equivalent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:832
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.DeiterationRule._cut_contents_structurally_equivalent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:850
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.HeavyDotInsertionRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:901
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### formal_transformation_rules.HeavyDotInsertionRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:904
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system

### formal_transformation_rules.FormalTransformationEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:966
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_transformation_rules.FormalTransformationEngine.get_available_rules (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:1007
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### formal_transformation_rules.FormalTransformationEngine.describe_rule (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:1011
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### clif_generator_dau.CLIFGenerator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:22
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator.generate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:29
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator.generate_clif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:48
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator._assign_vertex_labels (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:53
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator.assign_in_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:61
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator._edge_key (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:157
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator._vertex_key (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:89
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator._get_next_variable_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:113
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator._get_area_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:125
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator._generate_area_expression (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:151
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator._generate_atomic_formula (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:188
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator._generate_cut_expression (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:222
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator._get_free_variables (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:231
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator._is_variable_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:250
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator._constant_name_for_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:266
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator._format_constant (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:290
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator._is_simple_identifier (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:296
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.CLIFGenerator.generate_with_quantification (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:308
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_generator_dau.generate_clif_with_quantification (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:336
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_history.StateSnapshot.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:62
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_history.EGITransformationHistory.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:142
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_history.EGITransformationHistory._add_initial_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:165
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_history.EGITransformationHistory.add_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:200
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_transformation_history.EGITransformationHistory.get_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:273
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_history.EGITransformationHistory.get_current_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:277
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_history.EGITransformationHistory.get_transformation_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:281
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_transformation_history.EGITransformationHistory.rollback_to_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:324
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_history.EGITransformationHistory.create_exploration_branch (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:352
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_history.EGITransformationHistory.get_history_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:366
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_transformation_history.EGITransformationHistory._generate_sequence_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:386
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_transformation_history.EGITransformationHistory.export_history_data (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:404
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_history.HistoryViewer (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:442
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_transformation_history.HistoryViewer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:445
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_history.HistoryViewer.get_state_diff (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:448
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_history.HistoryViewer.get_transformation_tree (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_history.py:467
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### single_object_ligature_detector.SingleObjectLigatureDetector.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### single_object_ligature_detector.SingleObjectLigatureDetector.is_single_object_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### single_object_ligature_detector.SingleObjectLigatureDetector.separate_into_single_object_components (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py:47
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### single_object_ligature_detector.SingleObjectLigatureDetector._analyze_ligature_impl (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py:55
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### single_object_ligature_detector.SingleObjectLigatureDetector._find_ligature_identity_edges (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py:104
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### single_object_ligature_detector.SingleObjectLigatureDetector._get_element_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py:133
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### single_object_ligature_detector.SingleObjectLigatureDetector._find_ligature_cycles (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py:140
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### single_object_ligature_detector.SingleObjectLigatureDetector.dfs_cycle_detection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py:158
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### single_object_ligature_detector.SingleObjectLigatureDetector._check_condition_1 (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py:182
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### single_object_ligature_detector.SingleObjectLigatureDetector._check_condition_2 (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py:204
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### single_object_ligature_detector.SingleObjectLigatureDetector._check_condition_3 (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py:239
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### single_object_ligature_detector.SingleObjectLigatureDetector._is_context_deeper (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py:258
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### single_object_ligature_detector.SingleObjectLigatureDetector._get_parent_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py:275
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:84
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.create_toolbar (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:112
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.create_diagram_panel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:155
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.create_control_panel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:189
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.create_status_bar (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:238
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.setup_connections (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:255
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.load_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:266
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.update_diagram_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:287
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.update_egi_info (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:313
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.synchronize_formats (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:321
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.start_transformation_wizard (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:353
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_gui_integration.Chapter21DiagramWidget.on_mode_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:397
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_gui_integration.Chapter21DiagramWidget.on_format_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:416
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_gui_integration.Chapter21DiagramWidget.on_egi_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:436
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_gui_integration.Chapter21DiagramWidget.on_format_display_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:441
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_gui_integration.Chapter21DiagramWidget.zoom_in (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:446
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.zoom_out (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:450
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21DiagramWidget.fit_to_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:454
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21ArisbeIntegration (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:459
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21ArisbeIntegration.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:467
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21ArisbeIntegration.add_diagram_support_to_organon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:471
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21ArisbeIntegration.add_diagram_support_to_ergasterion (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:483
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21ArisbeIntegration.add_diagram_support_to_agon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:494
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_gui_integration.Chapter21ArisbeIntegration.get_diagram_widget (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_gui_integration.py:505
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### syntactic_equivalence_checker.SyntacticEquivalenceChecker.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:30
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### syntactic_equivalence_checker.SyntacticEquivalenceChecker.check_equivalence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:34
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### syntactic_equivalence_checker.SyntacticEquivalenceChecker._check_structural_differences (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:77
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### syntactic_equivalence_checker.SyntacticEquivalenceChecker._check_transformation_equivalence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:104
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### syntactic_equivalence_checker.SyntacticEquivalenceChecker._is_double_cut_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:125
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### syntactic_equivalence_checker.SyntacticEquivalenceChecker._has_double_cut_pattern (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:139
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### syntactic_equivalence_checker.SyntacticEquivalenceChecker._would_match_after_double_cut_removal (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:162
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### syntactic_equivalence_checker.SyntacticEquivalenceChecker._is_iteration_transformation_with_isomorphism (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:177
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### syntactic_equivalence_checker.SyntacticEquivalenceChecker._has_rigorous_iteration_pattern (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:191
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### syntactic_equivalence_checker.SyntacticEquivalenceChecker._is_ligature_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:228
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### syntactic_equivalence_checker.SyntacticEquivalenceChecker._has_valid_ligature_rearrangement (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:250
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### syntactic_equivalence_checker.SyntacticEquivalenceChecker._has_valid_ligature_extension (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:264
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### syntactic_equivalence_checker.SyntacticEquivalenceChecker._count_identity_edges (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:285
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### syntactic_equivalence_checker.SyntacticEquivalenceChecker._get_all_element_ids (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:289
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### syntactic_equivalence_checker.SyntacticEquivalenceChecker._element_exists_in_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py:297
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequence.length (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:70
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequence.total_compression_ratio (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:74
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequence.get_storage_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:80
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequenceValidator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:105
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequenceValidator.validate_proof_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:120
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### proof_sequence_validator.ProofSequenceValidator._execute_proof_step (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:225
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequenceValidator.check_syntactic_equivalence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:321
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequenceValidator.construct_proof_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:370
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### proof_sequence_validator.ProofSequenceValidator._egi_to_notation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:422
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequenceValidator.get_available_rules (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:430
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### proof_sequence_validator.ProofSequenceValidator.validate_rule_sequence_syntax (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:438
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### proof_sequence_validator.ProofSequenceValidator.save_proof_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:453
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequenceValidator.load_proof_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:478
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequenceValidator._reconstruct_proof_sequence_from_history (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:498
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### proof_sequence_validator.ProofSequenceValidator.get_proof_sequence_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:554
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequenceValidator.replay_proof_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:583
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequenceValidator.branch_proof_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:598
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequenceValidator.export_proof_sequence_formats (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:618
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequenceValidator.get_all_sequence_ids (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:638
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### proof_sequence_validator.ProofSequenceValidator.delete_proof_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/proof_sequence_validator.py:644
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_transformation_interface.EGIFTransformationInterface.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_transformation_interface.py:41
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_transformation_interface.EGIFTransformationInterface.load_corpus_egif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_transformation_interface.py:45
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_transformation_interface.EGIFTransformationInterface.parse_egif_to_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_transformation_interface.py:56
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_transformation_interface.EGIFTransformationInterface.generate_egif_from_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_transformation_interface.py:60
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_transformation_interface.EGIFTransformationInterface.identify_target_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_transformation_interface.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Integrate with formal_transformation_rules.py

### egif_transformation_interface.EGIFTransformationInterface._calculate_area_polarity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_transformation_interface.py:107
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Connect to hierarchical_index.py

### egif_transformation_interface.EGIFTransformationInterface._manual_depth_calculation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_transformation_interface.py:128
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### egif_transformation_interface.EGIFTransformationInterface.create_insertion_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_transformation_interface.py:151
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:23
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator.generate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:36
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator.generate_cgif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:57
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._identify_type_relations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:62
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._assign_vertex_labels (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:73
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator.assign_in_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:81
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._edge_key (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:87
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._vertex_key (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:329
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._get_next_variable_label (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:140
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._is_constant_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:153
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._get_constant_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:163
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._format_constant (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:171
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._is_simple_identifier (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:182
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._validate_edge_arity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:186
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._get_area_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:196
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._compute_vertex_def_contexts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:223
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator.ancestors (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:234
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator.lca (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:245
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._generate_area_expression (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:280
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._typed_key (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:298
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._rel_key (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:344
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._generate_typed_concept (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:372
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._generate_untyped_concept (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:392
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._generate_relation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:406
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cgif_generator_dau.CGIFGenerator._generate_cut_expression (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:445
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGIGraphOperations.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:23
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGIGraphOperations.add_vertex_graph_to_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:27
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGIGraphOperations.add_predicate_graph_to_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGIGraphOperations.create_negation_in_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:50
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGIGraphOperations.bind_vertex_to_predicate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:57
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGIGraphOperations.conjoin_graphs_in_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:100
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGIGraphOperations.move_graph_between_areas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:146
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGIGraphOperations.validate_graph_operation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:177
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGIGraphOperations.get_area_graph_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:204
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGISystemController.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:235
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGISystemController.register_presentation_adapter (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:244
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGISystemController.add_vertex_to_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:248
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGISystemController.add_predicate_to_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:255
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGISystemController.bind_vertex_to_predicate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:262
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGISystemController.create_negation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:269
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGISystemController.conjoin_graphs (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:276
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGISystemController.get_complete_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:283
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGISystemController._generate_linear_replica (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:295
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGISystemController.validate_system_consistency (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:334
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGISystemController._update_presentation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:343
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_graph_operations.EGISystemController.get_system_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_graph_operations.py:351
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:15
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator.generate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:25
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator.generate_egif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:40
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._assign_vertex_labels (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:45
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._compute_vertex_def_contexts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:56
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator.ancestors (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:67
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator.lca (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:78
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._assign_labels_preserving_nu_order (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:128
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._edge_key (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:139
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._vertex_key (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:171
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._assign_labels_recursive (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:202
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._generate_context_content (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:262
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._iso_key (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:283
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._edge_out_key (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:304
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._generate_relation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:327
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._generate_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:348
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._is_defining_occurrence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:357
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._is_constant_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:362
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_generator_dau.EGIFGenerator._constant_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:375
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:31
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager.save_history_json (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:43
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager.load_history_json (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:63
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager.save_history_yaml (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:73
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager.load_history_yaml (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:100
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager.save_history_compressed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:113
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager.load_history_compressed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:132
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager.save_incremental_checkpoint (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:143
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### history_persistence.HistoryPersistenceManager.export_proof_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:182
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### history_persistence.HistoryPersistenceManager._serialize_history_to_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:221
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager._serialize_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:275
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager._serialize_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:290
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### history_persistence.HistoryPersistenceManager._serialize_provenance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:311
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager._serialize_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:326
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### history_persistence.HistoryPersistenceManager._serialize_result (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:335
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### history_persistence.HistoryPersistenceManager._deserialize_history_from_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:344
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager._add_yaml_annotations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:423
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager._remove_yaml_annotations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:437
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager._json_serializer (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:448
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager.get_storage_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:457
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager._deserialize_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:476
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager._deserialize_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:496
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### history_persistence.HistoryPersistenceManager._deserialize_provenance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:529
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### history_persistence.HistoryPersistenceManager._deserialize_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:542
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### history_persistence.HistoryPersistenceManager._deserialize_result (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:554
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### history_persistence.HistoryPersistenceManager._deserialize_branch (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/history_persistence.py:570
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_core_dau.Vertex.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:98
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts._build_hierarchical_index (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:128
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts._validate_dau_constraints (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:165
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts._validate_area_constraints (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:206
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts._has_area_cycle (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:236
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### egi_core_dau.RelationalGraphWithCuts._validate_alphabet_and_rho (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:254
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:285
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:291
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:297
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_relation_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:303
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_incident_vertices (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:309
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:317
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:321
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_full_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:328
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_nesting_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:349
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### egi_core_dau.RelationalGraphWithCuts.is_evenly_enclosed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:360
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.is_oddly_enclosed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:364
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.is_positive_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:368
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system

### egi_core_dau.RelationalGraphWithCuts.is_negative_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:374
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system

### egi_core_dau.RelationalGraphWithCuts.get_hooks (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:380
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_vertex_at_hook (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:387
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_vertex_hooks (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:396
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.is_branching_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:405
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_branch_count (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:409
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.replace_vertex_on_hook (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:413
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_identity_edges (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:443
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_ligature_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:447
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_identity_edge_as_set (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:462
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_ligatures (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:473
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_vertex_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:503
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.is_vertex_isolated (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:513
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.get_isolated_vertices (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:520
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.has_dominating_nodes (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:528
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts._context_dominates (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:539
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.with_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:555
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.with_vertex_in_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:559
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.with_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:585
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.change_identity_edge_orientation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:692
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_core_dau.RelationalGraphWithCuts.add_vertex_to_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:712
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.remove_vertex_from_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:744
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.with_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:793
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.with_vertex_moved_to_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:821
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts.without_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:856
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts._without_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:867
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts._without_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:889
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.RelationalGraphWithCuts._without_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:913
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.Alphabet.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:984
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.Alphabet.get_fresh_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:988
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.Alphabet.reserve_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:1004
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_core_dau.AlphabetDAU.with_defaults (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:1019
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.ContextPolarity (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:24
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Connect to hierarchical_index.py

### dau_semantic_evaluation_engine.RelationalStructure.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:41
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.Valuation.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:56
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.Valuation.is_total_for (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:60
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.Valuation.is_partial_for_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.Valuation.extend (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:77
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.Valuation.restrict_to (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:86
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.Valuation._get_vertices_above_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:95
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.Valuation._get_vertices_at_or_below_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:113
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:152
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine.evaluate_classical (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:155
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine.evaluate_endoporeutic (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:196
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine._evaluate_classical_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:232
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine._evaluate_endoporeutic_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:275
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine._check_edge_conditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:320
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine._generate_valuation_extensions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:357
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine._get_context_vertices (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:373
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine._get_context_edges (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:379
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine._get_context_cuts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:385
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine._get_edge_by_id (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:391
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine._get_edge_relation_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:398
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine._get_incident_vertices (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:402
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_engine.SemanticEvaluationEngine.verify_evaluation_equivalence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_engine.py:406
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.ElementPosition.to_qpointf (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.ElementPosition.from_qpointf (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:24
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.ElementSize.to_qrectf (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:34
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.VertexElement.to_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:47
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.PredicateElement.to_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:76
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.CutElement.to_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:105
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.DiagramState.to_drawing_schema (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:137
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.DiagramState.add_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:193
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.DiagramState.add_predicate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:200
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.DiagramState.add_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:208
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.DiagramState.update_element_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:216
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.DiagramState.update_cut_size (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:229
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.DiagramState.get_element_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:236
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.DiagramDataContract (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:247
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.DiagramDataContract.normalize_drawing_schema (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:256
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.DiagramDataContract.to_egi_format (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:261
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_data_contract.DiagramDataContract.create_empty_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_data_contract.py:266
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_sequences.SequenceValidationResult (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:34
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_sequences.TransformationSequenceEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:83
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_sequences.TransformationSequenceEngine.create_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:89
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_sequences.TransformationSequenceEngine.add_transformation_step (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:108
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_sequences.TransformationSequenceEngine._validate_and_execute_step (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:151
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_sequences.TransformationSequenceEngine._validate_step_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:187
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_sequences.TransformationSequenceEngine._simulate_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:228
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_sequences.TransformationSequenceEngine._is_sound_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:622
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_sequences.TransformationSequenceEngine._is_constructive_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:632
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_sequences.TransformationSequenceEngine._is_odd_nesting_level (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:645
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Connect to hierarchical_index.py

### chapter21_transformation_sequences.TransformationSequenceEngine._validate_logical_equivalence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:673
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_sequences.TransformationSequenceEngine._elements_in_positive_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:691
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Connect to hierarchical_index.py

### chapter21_transformation_sequences.TransformationSequenceEngine._elements_in_negative_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:703
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Connect to hierarchical_index.py

### chapter21_transformation_sequences.TransformationSequenceEngine._elements_can_be_iterated (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:713
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_sequences.TransformationSequenceEngine._elements_are_iterated (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:719
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_sequences.TransformationSequenceEngine._has_double_cut_pattern (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:733
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_sequences.TransformationSequenceEngine.validate_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:747
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_sequences.TransformationSequenceEngine.replay_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:770
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_sequences.TransformationSequenceEngine.rollback_to_step (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:791
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_sequences.TransformationSequenceEngine.export_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:816
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_sequences.TransformationSequenceEngine.get_sequence_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:844
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:31
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator.psi_translate_with_universal_closure (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator.psi_translate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator._translate_implication_fixed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:71
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator._translate_with_proper_cut_management (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:84
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator._add_cut_with_conflict_resolution (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:92
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator._get_free_variables (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:132
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator._get_all_variables (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:138
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator._get_bound_variables (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:154
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator.verify_syntactic_identity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:168
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator._check_exact_syntactic_identity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:189
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator.verify_syntactic_entailment_preservation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:200
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator._check_entailment_structure_preservation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:222
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator.verify_beta_calculus_completeness (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:233
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter20_syntactic_equivalence_fixes.Chapter20SyntacticTranslator._verify_completeness_preservation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter20_syntactic_equivalence_fixes.py:259
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### tomos_index.CorpusEntry (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/tomos_index.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_pipeline.ConcreteInsertionRule._insert_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:41
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_pipeline.ConcreteInsertionRule._insert_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:63
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_pipeline.ConcreteInsertionRule._insert_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:98
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_pipeline.ConcreteInsertionRule.get_rule_type (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:128
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_transformation_pipeline.ConcreteErasureRule._erase_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:154
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_pipeline.ConcreteErasureRule._erase_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:181
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_pipeline.ConcreteErasureRule._erase_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:211
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_pipeline.ConcreteErasureRule.get_rule_type (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:251
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_transformation_pipeline.ConcreteIterationRule.get_rule_type (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:331
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_transformation_pipeline.EGITransformationPipeline.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:338
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_pipeline.EGITransformationPipeline.get_egi_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:404
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_transformation_pipeline.EGITransformationPipeline.get_transformation_history (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:409
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### nary_identity_relations.IdentityArity (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:15
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentitySpec (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:24
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityRelation.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityRelation.__str__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:46
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityRelation.__repr__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:50
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityRelation.is_binary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:53
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityRelation.get_binary_pairs (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:57
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityRelation.contains_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:65
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityRelation.can_separate_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:69
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.CreateNaryIdentityRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:77
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### nary_identity_relations.CreateNaryIdentityRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:80
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.CreateNaryIdentityRule._get_vertex_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:168
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.SeparateNaryIdentityRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:179
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### nary_identity_relations.SeparateNaryIdentityRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:182
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.SeparateNaryIdentityRule._find_nary_identities_containing_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:308
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityAnalyzer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:340
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityAnalyzer.get_all_nary_identities (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:344
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityAnalyzer.get_identities_by_arity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:350
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityAnalyzer.get_identities_containing_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:354
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityAnalyzer.get_max_arity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:358
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityAnalyzer.get_identity_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:363
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityAnalyzer.can_create_nary_identity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:379
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityAnalyzer._extract_nary_identities (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:401
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### nary_identity_relations.NaryIdentityAnalyzer._get_vertex_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/nary_identity_relations.py:427
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFTokenType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFLexer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:62
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFLexer.tokenize (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:67
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFLexer._skip_whitespace (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:96
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFLexer._read_comment (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:102
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFLexer._read_identifier (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:111
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFLexer._read_quoted_identifier (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:135
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParseNode.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:164
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParser.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:172
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParser.parse (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:179
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParser._advance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:195
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParser._expect (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:201
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParser._parse_expression (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:209
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParser._parse_compound_expression (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:221
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParser._parse_quantification (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:240
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParser._parse_negation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:261
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParser._parse_conjunction (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:272
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParser._parse_disjunction (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:286
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParser._parse_atomic_formula (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:300
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParser._convert_to_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:317
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.CLIFParser._finalize_alphabet_and_rho (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:373
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### clif_parser_dau.parse_clif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:424
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGIOperation.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:43
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.InsertVertex.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:51
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.InsertVertex.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:55
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.InsertEdge.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:75
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.InsertEdge.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:81
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.InsertCut.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:97
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.InsertCut.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:101
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.MoveElement.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:120
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.MoveElement.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:124
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.DeleteElement.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:150
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.DeleteElement.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:153
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.RenameVertex.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:169
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.RenameVertex._unquote (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:175
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.RenameVertex.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:181
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.VisualConformanceValidator.validate_visual_operation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:245
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_system.EGIRepository.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:291
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGIRepository.get_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:311
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGIRepository.observe (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:315
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_system.EGIRepository._visual_to_operation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:331
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGIRepository._notify_observers (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:353
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_system.EGIFProjection.generate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:362
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.CLIFProjection.generate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:372
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.CGIFProjection.generate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:382
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGDFProjection.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:392
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGDFProjection.generate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:396
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:507
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.insert_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:515
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.insert_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:518
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.insert_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:521
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.to_egif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:525
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.to_clif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:528
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.to_cgif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:531
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.to_egdf (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:534
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.get_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:537
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.get_current_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:541
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.observe_changes (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:544
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_system.EGISystem.move_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:551
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.delete_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:554
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.rename_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:557
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.replace_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:562
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.load_egif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:567
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.load_cgif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:574
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.EGISystem.load_linear (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:581
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.VisualEGIBridge (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:612
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.VisualEGIBridge.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:615
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.VisualEGIBridge.handle_visual_event (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:621
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.VisualEGIBridge._handle_drag (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:636
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.VisualEGIBridge._handle_create (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:679
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.VisualEGIBridge._handle_delete (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:694
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.VisualEGIBridge._handle_resize_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:698
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### egi_system.VisualEGIBridge._determine_target_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:708
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_system.VisualEGIBridge.sync_visual_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:713
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:21
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### efficient_historical_storage.DeltaCompressor.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:73
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaCompressor.compute_transformation_delta (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:76
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### efficient_historical_storage.DeltaCompressor._compute_vertex_deltas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:112
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaCompressor._compute_edge_deltas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:156
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaCompressor._compute_cut_deltas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:200
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaCompressor._compute_relation_deltas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:230
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaCompressor._compute_incidence_deltas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:243
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaCompressor._compute_area_deltas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:268
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaCompressor._compress_delta (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:293
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaCompressor.decompress_delta (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:338
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaCompressor._serialize_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:358
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaCompressor._serialize_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:367
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaCompressor._serialize_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:376
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaCompressor._vertices_equal (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:384
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.DeltaCompressor._edges_equal (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:390
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.EfficientHistoricalStorage.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:402
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.EfficientHistoricalStorage.store_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:419
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### efficient_historical_storage.EfficientHistoricalStorage.replay_from_deltas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:444
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### efficient_historical_storage.EfficientHistoricalStorage._add_element_from_delta (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:482
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.EfficientHistoricalStorage._remove_element_from_delta (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:497
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.EfficientHistoricalStorage._modify_element_from_delta (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:516
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.EfficientHistoricalStorage._modify_relation_from_delta (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:524
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.EfficientHistoricalStorage._deserialize_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:533
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.EfficientHistoricalStorage._deserialize_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:542
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.EfficientHistoricalStorage._deserialize_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:551
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.EfficientHistoricalStorage._should_create_snapshot (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:558
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.EfficientHistoricalStorage._update_storage_stats (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:562
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.EfficientHistoricalStorage.get_storage_efficiency (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:575
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### efficient_historical_storage.EfficientHistoricalStorage.optimize_storage (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/efficient_historical_storage.py:589
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_dau_compliance_engine.ComplianceLevel (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:22
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:51
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine.validate_dau_compliance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:149
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine._validate_structural_integrity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:190
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine._validate_isomorphism_requirements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:224
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine._validate_egi_structure (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:255
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine._validate_area_constraints (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:278
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine._validate_cut_nesting (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:292
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine._validate_ligature_consistency (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:315
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine._get_nesting_hierarchy (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:337
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine._calculate_cut_nesting_level (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:357
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine._cuts_overlap (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:367
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine._build_ligature_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:375
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine.get_supported_rules (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:387
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### enhanced_dau_compliance_engine.EnhancedDauComplianceEngine.set_compliance_level (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:401
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### chapter17_soundness_evaluation.ModelStructure.satisfies_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:46
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:66
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator.evaluate_rule_soundness (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:96
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._verify_model_preservation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:175
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._verify_egi_integrity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:207
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._verify_context_preservation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:225
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._verify_semantic_equivalence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:237
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._verify_ligature_properties (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:260
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._extract_identity_relations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:287
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._verify_identity_consistency (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:297
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._identity_preserved_transitively (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:308
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._verify_move_branches_properties (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:330
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._verify_extend_properties (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:361
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._verify_retract_properties (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:367
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._verify_rearrange_properties (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:373
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._verify_split_properties (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:379
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter17_soundness_evaluation.Chapter17SoundnessEvaluator._verify_merge_properties (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:386
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter17_soundness_evaluation.Chapter17ComplianceTestSuite.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:397
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter17_soundness_evaluation.Chapter17ComplianceTestSuite.run_comprehensive_soundness_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter17_soundness_evaluation.py:408
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### graph_isomorphism_engine.GraphIsomorphismEngine.find_isomorphic_subgraphs (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/graph_isomorphism_engine.py:138
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### graph_isomorphism_engine.GraphIsomorphismEngine._categorize_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/graph_isomorphism_engine.py:164
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### graph_isomorphism_engine.GraphIsomorphismEngine._vertices_structurally_identical (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/graph_isomorphism_engine.py:254
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### graph_isomorphism_engine.GraphIsomorphismEngine._edges_structurally_identical (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/graph_isomorphism_engine.py:265
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### graph_isomorphism_engine.GraphIsomorphismEngine._cuts_structurally_identical (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/graph_isomorphism_engine.py:293
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### graph_isomorphism_engine.GraphIsomorphismEngine._get_vertex_by_id (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/graph_isomorphism_engine.py:315
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### graph_isomorphism_engine.GraphIsomorphismEngine._generate_subgraphs_of_size (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/graph_isomorphism_engine.py:322
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### graph_isomorphism_engine.IsomorphismValidator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/graph_isomorphism_engine.py:338
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### graph_isomorphism_engine.IsomorphismValidator.validate_deiteration_candidate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/graph_isomorphism_engine.py:341
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### graph_isomorphism_engine.IsomorphismValidator.validate_endoporeutic_claim (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/graph_isomorphism_engine.py:362
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.WorkingRoom.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:31
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.WorkingRoom._darken_color (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:68
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.WorkingRoom._setup_room_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:73
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.WorkingRoom._create_room_icon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:147
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.ArisbeHomeWidget.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:191
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.ArisbeHomeWidget._setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:199
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.ArisbeHomeWidget._create_rooms (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:285
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.ArisbeHomeWidget._handle_room_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:331
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.IntegratedArisbeWindow.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:340
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.IntegratedArisbeWindow._setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:351
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.IntegratedArisbeWindow._setup_navigation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:427
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.IntegratedArisbeWindow._show_home (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:432
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.IntegratedArisbeWindow._handle_room_request (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:437
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.IntegratedArisbeWindow._enter_library (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:446
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.IntegratedArisbeWindow._enter_workshop (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:463
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.IntegratedArisbeWindow._enter_agon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:480
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.IntegratedArisbeWindow._handle_library_to_workshop_handoff (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:496
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### arisbe_home.IntegratedArisbeWindow._show_help_documentation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/arisbe_home.py:501
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_dto.LigatureDTO (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_dto.py:58
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_dto.EGIStateDTO.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_dto.py:90
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_dto.EGIStateDTO.to_yaml (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_dto.py:111
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_dto.EGIStateDTO.from_yaml (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_dto.py:116
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_dto.EGIStateDTO.to_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_dto.py:121
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_dto.EGIStateDTO.from_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_dto.py:126
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_dto.from_drawing_schema (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_dto.py:236
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_dto.to_constraint_engine_format (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_dto.py:325
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.MoveBranchesAlongLigatureRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:21
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### ligature_manipulation_rules.MoveBranchesAlongLigatureRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:24
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.MoveBranchesAlongLigatureRule._get_vertex_by_id (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:114
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.MoveBranchesAlongLigatureRule._get_vertex_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:121
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.MoveBranchesAlongLigatureRule._vertices_on_same_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:128
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.MoveBranchesAlongLigatureRule._vertices_connected_by_identity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:140
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.ExtendRestrictLigatureRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:180
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### ligature_manipulation_rules.ExtendRestrictLigatureRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:183
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.ExtendRestrictLigatureRule._get_vertex_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:279
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.RetractLigatureRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:293
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### ligature_manipulation_rules.RetractLigatureRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:296
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.RetractLigatureRule._vertices_form_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:420
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.RetractLigatureRule._get_vertex_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:452
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.LigatureRearrangementRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:466
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### ligature_manipulation_rules.LigatureRearrangementRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:469
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.LigatureRearrangementRule._vertices_form_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:592
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.LigatureRearrangementRule._get_vertex_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:624
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.LigatureManipulationEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:635
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### ligature_manipulation_rules.LigatureManipulationEngine.get_available_rules (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:670
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### ligature_manipulation_rules.LigatureManipulationEngine.describe_rule (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py:674
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egif_parsing_result.EGIFParsingResult (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parsing_result.py:16
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parsing_result.EGIFParsingResult.get_display_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parsing_result.py:30
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_refined_translation.RefinedChapter18Translator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_refined_translation.py:31
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_refined_translation.RefinedChapter18Translator.psi_translate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_refined_translation.py:37
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_refined_translation.RefinedChapter18Translator._extract_quantified_variables (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_refined_translation.py:43
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_refined_translation.RefinedChapter18Translator.phi_translate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_refined_translation.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_refined_translation.RefinedChapter18Translator._selective_quantifier_reconstruction (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_refined_translation.py:82
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_refined_translation.RefinedChapter18Translator._formula_has_existential (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_refined_translation.py:120
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_refined_translation.RefinedChapter18Translator._extract_variables_from_formula_string (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_refined_translation.py:137
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_refined_translation.RefinedChapter18Translator._translate_area_to_fopl_improved (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_refined_translation.py:144
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_refined_translation.EnhancedLogicalEquivalenceChecker.formulas_logically_equivalent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_refined_translation.py:188
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_refined_translation.EnhancedLogicalEquivalenceChecker.get_var (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_refined_translation.py:220
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_refined_translation.EnhancedLogicalEquivalenceChecker.normalize_string (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_refined_translation.py:288
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### non_closed_subgraph_handler.DecompositionStrategy (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/non_closed_subgraph_handler.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### non_closed_subgraph_handler.NonClosedSubgraphHandler.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/non_closed_subgraph_handler.py:63
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### non_closed_subgraph_handler.NonClosedSubgraphHandler.is_closed_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/non_closed_subgraph_handler.py:66
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### non_closed_subgraph_handler.NonClosedSubgraphHandler.create_decomposition_plan (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/non_closed_subgraph_handler.py:98
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### non_closed_subgraph_handler.NonClosedSubgraphHandler._create_edge_first_plan (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/non_closed_subgraph_handler.py:146
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### non_closed_subgraph_handler.NonClosedSubgraphHandler._create_vertex_first_plan (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/non_closed_subgraph_handler.py:184
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### non_closed_subgraph_handler.NonClosedSubgraphHandler._create_minimal_cuts_plan (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/non_closed_subgraph_handler.py:218
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### non_closed_subgraph_handler.NonClosedSubgraphHandler._find_boundary_edges (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/non_closed_subgraph_handler.py:228
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### non_closed_subgraph_handler.NonClosedSubgraphHandler._find_isolated_vertices (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/non_closed_subgraph_handler.py:252
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### non_closed_subgraph_handler.NonClosedSubgraphHandler.execute_decomposition_plan (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/non_closed_subgraph_handler.py:270
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### non_closed_subgraph_handler.NonClosedSubgraphHandler.erase_non_closed_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/non_closed_subgraph_handler.py:322
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.WizardStep (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:34
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.TransformationRuleType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:59
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.PositionType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:68
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.InsertionType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:75
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.TransformationWizard.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:118
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.TransformationWizard.get_format (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:125
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.TransformationWizard.handle_user_input (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:135
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.TransformationWizard.advance_step (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:139
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.TransformationWizard.execute_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:151
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.TransformationWizard._create_transformation_rule (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:209
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.DiagramTransformationWizard (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:231
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.DiagramTransformationWizard.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:234
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard.get_format (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:240
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_rule_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:265
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.DiagramTransformationWizard.handle_user_input (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:365
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard.get_wizard_flow (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:302
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.DiagramTransformationWizard.get_current_step_display (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:334
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_rule_selection_diagram (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:396
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.DiagramTransformationWizard._render_area_selection_diagram (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:416
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_position_selection_diagram (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:437
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_preview_diagram (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:466
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.DiagramTransformationWizard._render_execute_diagram (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:489
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._list_available_areas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:510
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_area_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:518
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_position_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:529
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._get_position_instructions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:549
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_preview (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:559
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.DiagramTransformationWizard._render_insertion_type_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:579
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.DiagramTransformationWizard._render_edge_details (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:601
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_vertex_details (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:619
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_cut_details (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:633
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_subgraph_source (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:653
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_element_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:664
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_placement_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:682
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_justification_search (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:707
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._get_area_contents (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:731
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_current_egi_structure (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:758
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._render_preview_structure (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:768
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.DiagramTransformationWizard._render_transformation_changes (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:960
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.DiagramTransformationWizard._render_final_egi_linear_form (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:800
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._get_cut_position_instructions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:807
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._get_default_position_instructions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:817
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._handle_rule_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:972
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.DiagramTransformationWizard._handle_area_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:869
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._handle_position_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:888
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._handle_cut_details (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1043
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._handle_preview_confirmation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:928
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._generate_preview (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:942
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.DiagramTransformationWizard._render_precondition_checks (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:948
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.DiagramTransformationWizard._handle_insertion_type_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:989
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._handle_edge_details (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1005
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._handle_vertex_details (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1030
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._handle_subgraph_source (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1057
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._handle_element_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1071
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._handle_placement_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1090
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._handle_justification_search (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1113
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._find_justifying_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1141
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._search_area_for_justification (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1160
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._get_parent_areas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1184
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._extract_subgraph_from_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1199
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._get_candidate_subgraphs_in_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1220
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._get_elements_in_area_ids (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1236
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._get_elements_in_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1257
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._get_valid_iteration_areas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1278
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._get_nested_areas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1296
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.DiagramTransformationWizard._handle_subgraph_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1309
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.FOPLTransformationWizard (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1332
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.FOPLTransformationWizard.get_format (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1335
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.FOPLTransformationWizard.handle_user_input (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1347
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.FOPLTransformationWizard._render_fopl_rule_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1351
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_transformation_wizards.FOPLTransformationWizard._render_fopl_subgraph_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1375
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.FOPLTransformationWizard._render_fopl_structure (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1395
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.FOPLTransformationWizard._list_fopl_subformulas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1408
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.UniversalTransformationWizardSystem.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1421
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_transformation_wizards.UniversalTransformationWizardSystem.create_wizard (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_wizards.py:1429
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_tests.TestDauSemanticEvaluation (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_tests.py:26
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_tests.TestDauSemanticEvaluation.setUp (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_tests.py:29
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_tests.TestDauSemanticSoundness (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_tests.py:308
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_tests.TestDauSemanticSoundness.setUp (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_tests.py:311
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### dau_semantic_evaluation_tests.run_dau_semantic_evaluation_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/dau_semantic_evaluation_tests.py:329
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.TokenType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:25
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFLexer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:52
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFLexer.tokenize (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:57
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFLexer._skip_whitespace (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:104
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFLexer._peek (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:109
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFLexer._read_variable (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:114
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFLexer._read_constant (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:127
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFLexer._read_identifier (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:144
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFLexer._is_bound_variable (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:154
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFSyntaxValidator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:164
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFSyntaxValidator.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:168
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFSyntaxValidator._current_token (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:177
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFSyntaxValidator._advance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:183
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFSyntaxValidator._validate_eg (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:188
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFSyntaxValidator._validate_node (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:193
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFSyntaxValidator._validate_relation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:208
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFSyntaxValidator._validate_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:226
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFSyntaxValidator._validate_variable_declaration (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:241
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFSyntaxValidator._validate_isolated_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:256
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:266
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._preprocess_text (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:282
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser.parse (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:315
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._current_token (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:347
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._advance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:353
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._parse_eg (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:358
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._parse_node (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:363
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._parse_relation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:378
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._parse_argument (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:404
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._parse_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:468
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system

### egif_parser_dau.EGIFParser._parse_variable_declaration (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:491
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._parse_isolated_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:517
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._pop_area_vars (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:569
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._is_ancestor_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:595
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._get_ancestor_chain (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:613
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._compute_lca (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:627
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser.depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:641
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### egif_parser_dau.EGIFParser._hoist_vertices_to_lca (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:650
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser.ancestors (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:655
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egif_parser_dau.EGIFParser._finalize_alphabet_and_rho (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:675
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.LogicalOperator (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:16
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGIGraph.is_empty (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGIGraph.contains_only_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:36
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGIGraph.contains_only_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:40
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGIGraph.contains_only_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:44
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.LogicalArea.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:57
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.LogicalArea.add_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.LogicalArea.add_child_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:79
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.LogicalArea._validate_conjunction_constraints (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:84
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.LogicalArea.get_all_vertices (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:92
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.LogicalArea.get_all_edges (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:99
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.LogicalArea.get_logical_size (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:106
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGILogicalSystem.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:122
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGILogicalSystem.create_negation_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:131
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGILogicalSystem.add_graph_to_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:153
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGILogicalSystem.create_vertex_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:164
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGILogicalSystem.create_edge_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:175
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGILogicalSystem.can_conjoin_graphs (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:187
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGILogicalSystem._separated_by_negation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:198
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGILogicalSystem._get_path_to_root (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:225
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGILogicalSystem.get_area_logical_content (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:236
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_logical_areas.EGILogicalSystem.validate_logical_consistency (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_logical_areas.py:262
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.InteractionMode (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.SelectionMethod (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.DisplayFormat (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:46
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.SubgraphValidator.validate_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:100
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_diagram_engine.SubgraphValidator._determine_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:138
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.ViewManager (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:158
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.ViewManager.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:161
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.ViewManager.create_focus_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:164
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.ViewManager._expand_from_focus (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:191
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.ViewManager._find_element_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:230
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.ViewManager._generate_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:244
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.ViewManager._generate_subgraph_hints (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:286
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.ViewManager._find_connected_components (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:317
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.UniversalEGIEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:360
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.UniversalEGIEngine._build_hierarchical_index (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:441
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.UniversalEGIEngine._calculate_area_polarity_and_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:458
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Connect to hierarchical_index.py

### chapter21_diagram_engine.UniversalEGIEngine.get_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:476
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.UniversalEGIEngine.synchronize_formats (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:481
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.UniversalEGIEngine.validate_round_trip_equivalence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:505
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.UniversalEGIEngine.validate_subgraph_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:528
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter21_diagram_engine.UniversalEGIEngine._create_transformation_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:543
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### chapter21_diagram_engine.UniversalEGIEngine._egi_to_egif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:549
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### theta_relation.ThetaPath.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:34
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### theta_relation.ThetaRelationEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:60
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### theta_relation.ThetaRelationEngine.compute_theta_relation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### theta_relation.ThetaRelationEngine._find_theta_paths (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:105
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### theta_relation.ThetaRelationEngine._build_identity_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:155
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### theta_relation.ThetaRelationEngine._satisfies_context_nesting (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:178
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### theta_relation.ThetaRelationEngine._validate_theta_path (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:194
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### theta_relation.ThetaRelationEngine._get_vertex_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:219
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### theta_relation.ThetaRelationEngine._get_edge_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:229
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### theta_relation.ThetaRelationEngine._calculate_nesting_level (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:239
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### theta_relation.ThetaRelationEngine._vertex_exists (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:264
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### theta_relation.ThetaRelationEngine.is_theta_reflexive (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:268
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### theta_relation.ThetaRelationEngine.is_theta_symmetric (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:272
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### theta_relation.ThetaRelationEngine.get_theta_equivalence_classes (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:315
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_iteration_rule.IndexedElement.tagged_id (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_iteration_rule.py:30
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_iteration_rule.FormalIterationEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_iteration_rule.py:71
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_iteration_rule.FormalIterationEngine._validate_iteration_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_iteration_rule.py:130
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_iteration_rule.FormalIterationEngine._build_iteration_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_iteration_rule.py:169
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_iteration_rule.FormalIterationEngine._determine_subgraph_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_iteration_rule.py:427
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_iteration_rule.FormalIterationEngine._satisfies_context_nesting_constraint (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_iteration_rule.py:445
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### formal_iteration_rule.FormalIterationEngine._calculate_nesting_level (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_iteration_rule.py:459
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### formal_iteration_rule.FormalIterationEngine._get_all_element_ids (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_iteration_rule.py:483
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### formal_iteration_rule.FormalIterationEngine._generate_fresh_edge_id (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/formal_iteration_rule.py:492
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_enhanced_translation.EnhancedChapter18Translator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_enhanced_translation.py:34
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_enhanced_translation.EnhancedChapter18Translator.reset_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_enhanced_translation.py:37
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_enhanced_translation.EnhancedChapter18Translator.psi_translate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_enhanced_translation.py:46
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_enhanced_translation.EnhancedChapter18Translator._identify_shared_variables (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_enhanced_translation.py:58
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_enhanced_translation.EnhancedChapter18Translator._psi_recursive (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_enhanced_translation.py:100
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_enhanced_translation.EnhancedChapter18Translator._translate_atomic_formula_enhanced (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_enhanced_translation.py:136
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_enhanced_translation.EnhancedChapter18Translator._juxtapose_egis_enhanced (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_enhanced_translation.py:182
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_enhanced_translation.EnhancedChapter18Translator._add_cut_around_egi_enhanced (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_enhanced_translation.py:247
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_enhanced_translation.EnhancedChapter18Translator.phi_translate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_enhanced_translation.py:323
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_enhanced_translation.EnhancedChapter18Translator._translate_area_to_fopl_enhanced (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_enhanced_translation.py:338
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_enhanced_translation.enhanced_fopl_to_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_enhanced_translation.py:380
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_enhanced_translation.enhanced_egi_to_fopl (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_enhanced_translation.py:387
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.ConceptType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:34
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.OntologyConnector (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:98
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.OntologyConnector.lookup_concept (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:101
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.OntologyConnector.search_concepts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:105
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.OntologyConnector.get_concept_relations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:109
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.OntologyConnector.validate_concept_uri (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:113
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.DomainModelManager.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:155
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.DomainModelManager.register_ontology (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:167
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.DomainModelManager.add_element_to_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:192
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.DomainModelManager.map_element_to_concept (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:219
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.DomainModelManager.create_semantic_annotation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:246
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.DomainModelManager.get_element_contexts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:269
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.DomainModelManager.lookup_concept_in_ontology (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:409
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.DomainModelManager.generate_natural_language_for_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:417
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.WordNetConnector (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:520
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.WordNetConnector.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:523
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.WordNetConnector.lookup_concept (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:527
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.WordNetConnector.search_concepts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:531
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.CycConnector (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:535
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.CycConnector.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:538
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.CycConnector.lookup_concept (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:542
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.OWLConnector (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:547
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.OWLConnector.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:550
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### domain_ontology_model.OWLConnector.lookup_concept (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:554
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_final_translation.FinalChapter18Translator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_final_translation.py:41
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_final_translation.FinalChapter18Translator.psi_translate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_final_translation.py:45
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_final_translation.FinalChapter18Translator._analyze_formula_structure (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_final_translation.py:68
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_final_translation.FinalChapter18Translator._has_existential_quantifier (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_final_translation.py:83
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_final_translation.FinalChapter18Translator._get_quantified_variables (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_final_translation.py:100
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_final_translation.FinalChapter18Translator._get_free_variables (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_final_translation.py:121
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_final_translation.FinalChapter18Translator._get_all_variables (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_final_translation.py:127
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_final_translation.FinalChapter18Translator._get_formula_type (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_final_translation.py:150
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_final_translation.FinalChapter18Translator.phi_translate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_final_translation.py:167
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_final_translation.FinalChapter18Translator._reconstruct_existential_quantifiers (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_final_translation.py:198
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_final_translation.FinalChapter18Translator._translate_area_to_fopl_final (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_final_translation.py:215
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_final_translation.PreciseLogicalEquivalenceChecker.formulas_logically_equivalent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_final_translation.py:259
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.AnnotationMode (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:14
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.AnnotationGenerator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:60
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.AnnotationGenerator.generate_hook_annotations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:63
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.AnnotationGenerator.generate_identity_annotations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:82
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.AnnotationGenerator.generate_ligature_annotations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:98
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.AnnotationGenerator.generate_annotations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:113
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.AnnotationRenderer (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:136
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.AnnotationRenderer.get_hook_display_text (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:140
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.AnnotationRenderer.get_identity_display_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:145
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.AnnotationRenderer.get_ligature_highlight_info (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:156
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.AnnotationRenderer.should_use_simplified_identity_display (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:165
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.create_annotations_for_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:172
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.get_branching_point_annotations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:179
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.get_identity_edge_display_mode (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:188
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.format_hook_label (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:195
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### diagram_annotations.get_ligature_membership (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/diagram_annotations.py:200
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### vertex_splitting_merging_rules.VertexSplittingRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:29
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### vertex_splitting_merging_rules.VertexSplittingRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### vertex_splitting_merging_rules.VertexSplittingRule._get_vertex_hooks (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:166
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### vertex_splitting_merging_rules.VertexSplittingRule._get_vertex_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:175
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### vertex_splitting_merging_rules.VertexSplittingRule._is_context_accessible_for_splitting (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:182
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### vertex_splitting_merging_rules.VertexSplittingRule._get_parent_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:211
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### vertex_splitting_merging_rules.VertexSplittingRule._get_edge_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:218
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### vertex_splitting_merging_rules.VertexSplittingRule._is_context_accessible (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:225
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### vertex_splitting_merging_rules.VertexMergingRule.get_rule_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:258
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### vertex_splitting_merging_rules.VertexMergingRule.check_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:261
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### vertex_splitting_merging_rules.VertexMergingRule._find_identity_edge_between_vertices (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:383
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### vertex_splitting_merging_rules.VertexMergingRule._get_vertex_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:396
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### vertex_splitting_merging_rules.VertexMergingRule._get_edge_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:403
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### vertex_splitting_merging_rules.VertexMergingRule._context_contains_or_equals (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/vertex_splitting_merging_rules.py:410
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.SpatialBounds.contains_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:34
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.SpatialBounds.contains_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.SpatialBounds.center (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:44
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.SpatialBounds.area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:48
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.SpatialBounds.overlaps (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:52
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.CutAreaCorrespondence.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:87
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.CutAreaCorrespondence.build_correspondence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:93
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.CutAreaCorrespondence._build_area_hierarchy (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:109
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### cut_area_correspondence.CutAreaCorrespondence._find_parent_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:127
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.CutAreaCorrespondence._layout_cuts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:134
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### cut_area_correspondence.CutAreaCorrespondence._calculate_nesting_depths (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:166
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### cut_area_correspondence.CutAreaCorrespondence.calculate_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:170
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### cut_area_correspondence.CutAreaCorrespondence._layout_cut_in_canvas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:180
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### cut_area_correspondence.CutAreaCorrespondence._layout_cut_in_parent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:212
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.CutAreaCorrespondence.get_area_for_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:247
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.CutAreaCorrespondence.get_correspondence_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:266
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.CutAreaCorrespondence._validate_correspondence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:292
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.CutAreaCorrespondence._validate_no_sibling_overlaps (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:317
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### cut_area_correspondence.CutAreaCorrespondence._validate_spatial_containment (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:331
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### egi_validity_analyzer.ValidationSeverity (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:17
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### egi_validity_analyzer.ValidationReport.get_issues_by_severity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:47
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.ValidationReport.get_issues_by_category (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:51
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.ValidationReport.has_critical_issues (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:55
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.ValidationReport.has_errors (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:59
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.EGIValidityAnalyzer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:79
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.EGIValidityAnalyzer.analyze_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:82
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.EGIValidityAnalyzer._calculate_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:110
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.EGIValidityAnalyzer._calculate_max_nesting_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:122
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### egi_validity_analyzer.EGIValidityAnalyzer.calculate_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:127
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### egi_validity_analyzer.EGIValidityAnalyzer._count_connected_components (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:142
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.EGIValidityAnalyzer.dfs (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:151
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.EGIValidityAnalyzer._check_structural_integrity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:171
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.EGIValidityAnalyzer._check_referential_consistency (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:209
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.EGIValidityAnalyzer._check_area_containment (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:243
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py
- Integrate with formal_transformation_rules.py

### egi_validity_analyzer.EGIValidityAnalyzer._check_cut_nesting (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:280
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py
- Integrate with formal_transformation_rules.py

### egi_validity_analyzer.EGIValidityAnalyzer.has_cycle (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:291
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.EGIValidityAnalyzer._check_edge_endpoints (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:312
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.EGIValidityAnalyzer._check_logical_consistency (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:336
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### egi_validity_analyzer.EGIValidityAnalyzer._check_egif_round_trip (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:370
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.EGIValidityAnalyzer._add_issue (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:405
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### egi_validity_analyzer.EGIValidityAnalyzer.generate_report_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:423
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLTokenType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:27
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLLexer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:105
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLLexer.advance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:110
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLLexer.skip_whitespace (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:118
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLLexer.read_identifier (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:123
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLLexer.tokenize (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:132
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLParser.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:199
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLParser.advance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:204
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLParser.parse (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:212
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLParser.parse_formula (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:216
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### chapter18_fopl_translation.FOPLParser.parse_implication (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:220
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLParser.parse_conjunction (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:232
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLParser.parse_negation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:244
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLParser.parse_quantification (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:254
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.FOPLParser.parse_atomic (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:288
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.Chapter18FOPLTranslator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:358
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.Chapter18FOPLTranslator.psi_translate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:363
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.Chapter18FOPLTranslator._psi_recursive (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:379
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.Chapter18FOPLTranslator._translate_atomic_formula (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:415
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.Chapter18FOPLTranslator._juxtapose_egis (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:466
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.Chapter18FOPLTranslator._add_cut_around_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:523
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.Chapter18FOPLTranslator.phi_translate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:606
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.Chapter18FOPLTranslator._assign_variables_to_vertices (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:620
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.Chapter18FOPLTranslator._translate_area_to_fopl (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:630
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.fopl_to_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:679
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_fopl_translation.egi_to_fopl (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_fopl_translation.py:686
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### hierarchical_index.NestingInfo.polarity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:23
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Connect to hierarchical_index.py

### hierarchical_index.HierarchicalIndex.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:38
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### hierarchical_index.HierarchicalIndex.add_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:43
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### hierarchical_index.HierarchicalIndex.get_nesting_level (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:85
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### hierarchical_index.HierarchicalIndex.get_polarity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:90
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system

### hierarchical_index.HierarchicalIndex.get_parent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:95
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### hierarchical_index.HierarchicalIndex.get_children (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:100
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### hierarchical_index.HierarchicalIndex.get_ancestors (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:105
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### hierarchical_index.HierarchicalIndex.is_ancestor (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:120
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### hierarchical_index.HierarchicalIndex.get_areas_at_level (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:125
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### hierarchical_index.HierarchicalIndex.get_positive_areas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:130
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system

### hierarchical_index.HierarchicalIndex.get_negative_areas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:135
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system

### hierarchical_index.HierarchicalIndex.remove_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:140
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### hierarchical_index.HierarchicalIndex.validate_containment (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:171
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### hierarchical_index.HierarchicalIndex.get_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:182
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_ligature_algorithms.EnhancedLigatureAlgorithms.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_ligature_algorithms.py:53
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_ligature_algorithms.EnhancedLigatureAlgorithms.analyze_ligature_network (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_ligature_algorithms.py:57
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_ligature_algorithms.EnhancedLigatureAlgorithms._find_theta_components (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_ligature_algorithms.py:101
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_ligature_algorithms.EnhancedLigatureAlgorithms.enhanced_move_branches_along_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_ligature_algorithms.py:137
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_ligature_algorithms.EnhancedLigatureAlgorithms.enhanced_extend_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_ligature_algorithms.py:214
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_ligature_algorithms.EnhancedLigatureAlgorithms._validate_path_context_constraints (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_ligature_algorithms.py:287
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_ligature_algorithms.EnhancedLigatureAlgorithms._check_transitivity_violations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_ligature_algorithms.py:307
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_ligature_algorithms.EnhancedLigatureAlgorithms._get_vertex_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_ligature_algorithms.py:329
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_ligature_algorithms.EnhancedLigatureAlgorithms._get_edge_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_ligature_algorithms.py:336
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### enhanced_ligature_algorithms.EnhancedLigatureAlgorithms._is_context_accessible (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_ligature_algorithms.py:343
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### enhanced_ligature_algorithms.EnhancedLigatureAlgorithms.validate_ligature_consistency (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/enhanced_ligature_algorithms.py:369
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_improved_translation.ImprovedChapter18Translator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_improved_translation.py:33
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_improved_translation.ImprovedChapter18Translator.phi_translate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_improved_translation.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_improved_translation.ImprovedChapter18Translator._analyze_quantification_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_improved_translation.py:62
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_improved_translation.ImprovedChapter18Translator._reconstruct_quantifiers (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_improved_translation.py:86
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_improved_translation.ImprovedChapter18Translator._translate_area_to_fopl_improved (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_improved_translation.py:109
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_improved_translation.LogicalEquivalenceChecker.formulas_logically_equivalent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_improved_translation.py:155
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### chapter18_improved_translation.LogicalEquivalenceChecker.get_normalized_var (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/chapter18_improved_translation.py:176
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.GameOutcome (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:29
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.UmpireDecision (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:37
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.GameMove (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:45
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:87
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:115
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.setup_game_board (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:144
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.setup_umpire_panel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:173
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.setup_hypothesis_manager (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:200
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.start_new_game (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:235
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.load_hypothesis (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:274
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.attempt_move (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:279
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### agon.endoporeutic_game.EndoporeuticGameEngine.umpire_accept_move (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:288
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.umpire_reject_move (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:293
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.umpire_end_inning (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:298
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.analyze_egi_outcome (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:333
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.make_umpire_decision (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:345
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.update_umpire_analysis (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:354
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.draw_current_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:359
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.compare_hypotheses (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:383
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.archive_hypothesis (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:393
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.add_competing_hypothesis (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:403
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### agon.endoporeutic_game.EndoporeuticGameEngine.update_hypothesis_display (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/agon/endoporeutic_game.py:423
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:29
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:44
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow.load_corpus_data (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:103
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow.load_category_items (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:121
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow.on_corpus_item_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:141
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow.display_corpus_info (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:148
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow.load_selected_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:166
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow.add_egi_to_controller (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:210
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow.render_egi_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:249
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow.render_egi_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:269
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow.render_egi_predicate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:286
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow.area_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:376
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.corpus_egi_test.CorpusEGITestWindow.render_egi_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:348
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_egi_test.CorpusEGITestWindow.render_egi_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_egi_test.py:395
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.universal_composition.UniversalComposer (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:5
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.universal_composition.UniversalComposer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:13
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.universal_composition.UniversalComposer.create_historical_sheet (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:24
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.universal_composition.UniversalComposer.compose_from_source (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:37
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.universal_composition.UniversalComposer._execute_sequence_with_history (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:94
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.universal_composition.UniversalComposer.import_from_egif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:146
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.universal_composition.UniversalComposer.import_from_cgif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:150
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.universal_composition.UniversalComposer.import_from_clif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:154
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.universal_composition.UniversalComposer.compose_from_text (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:158
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.universal_composition.UniversalComposer.add_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:162
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.universal_composition.UniversalComposer.compose_interactively (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:167
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.universal_composition.UniversalComposer.replay_to_checkpoint (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:172
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.universal_composition.UniversalComposer.create_branch (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:186
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.universal_composition.UniversalComposer.merge_graphs (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:194
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.universal_composition.UniversalComposer.get_composition_history (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/universal_composition.py:220
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SelectionCriterion (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphBoundary (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:30
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphExtractor (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:83
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphExtractor.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:91
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphExtractor.extract_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:108
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphExtractor._select_connected_component (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:167
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphExtractor._select_context_based (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:215
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphExtractor._select_spatial_region (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:228
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphExtractor._select_semantic_pattern (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:239
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphExtractor._select_depth_limited (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:246
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.subgraph_extractor.SubgraphExtractor._select_custom_predicate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:267
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphExtractor._create_subgraph_structure (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:370
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphExtractor._extract_spatial_info (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:414
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphExtractor.create_historical_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:426
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphSelector (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:452
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.subgraph_extractor.SubgraphSelector.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:457
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphSelector.select_around_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:460
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphSelector.select_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:472
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_extractor.SubgraphSelector.select_by_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:484
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.subgraph_extractor.SubgraphSelector.select_custom (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_extractor.py:498
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_cli_dau.EGICLIApplication.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_cli_dau.py:47
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_cli_dau.EGICLIApplication.run_interactive (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_cli_dau.py:52
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_cli_dau.EGICLIApplication.run_command_line (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_cli_dau.py:75
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_cli_dau.EGICLIApplication._process_command (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_cli_dau.py:95
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_cli_dau.EGICLIApplication._show_help (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_cli_dau.py:140
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_cli_dau.EGICLIApplication._load_egif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_cli_dau.py:178
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_cli_dau.EGICLIApplication._show_current_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_cli_dau.py:188
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_cli_dau.EGICLIApplication._show_graph_info (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_cli_dau.py:197
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_cli_dau.EGICLIApplication._list_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_cli_dau.py:396
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_cli_dau.EGICLIApplication._save_to_history (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_cli_dau.py:409
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_cli_dau.EGICLIApplication._undo (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_cli_dau.py:416
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.egi_cli_dau.EGICLIApplication._show_history (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_cli_dau.py:426
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.egi_cli_dau.EGICLIApplication._clear (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_cli_dau.py:437
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.Point2D (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.Point2D.__str__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:25
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.ValidationMode (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:29
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.DiagramCoordinator (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.DiagramCoordinator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:38
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.DiagramCoordinator.create_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:55
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.DiagramCoordinator.create_predicate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:84
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.DiagramCoordinator.create_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:115
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.DiagramCoordinator.update_vertex_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:153
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.DiagramCoordinator.update_predicate_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:162
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.DiagramCoordinator.update_cut_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:171
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.DiagramCoordinator.get_all_elements_in_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:182
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.DiagramCoordinator.get_element_count (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:186
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diagram_coordinator_dto_only.DiagramCoordinator.clear_all (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diagram_coordinator_dto_only.py:195
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_adapter.logical_to_relational_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_adapter.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.enhanced_transformation_history.ProofExportFormat (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:54
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:59
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory.export_proof_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:164
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory.add_semantic_annotation_to_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:188
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory.validate_transformation_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:203
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory.get_natural_language_narrative (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:238
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory._generate_linear_forms (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:270
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory._generate_state_natural_language (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:279
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory._generate_transformation_natural_language (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:296
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory._generate_proof_export (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:315
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory._export_natural_deduction (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:330
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory._export_coq_proof (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:343
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory._export_latex_proof (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:356
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory._compress_old_states (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:381
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory._determine_status (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:398
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory.get_collaboration_status (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:403
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory.acquire_lock (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:412
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.enhanced_transformation_history.EnhancedEGITransformationHistory.release_lock (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/enhanced_transformation_history.py:420
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.corpus_transformation_demo.transformation_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/corpus_transformation_demo.py:193
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rule_validation_system.TransformationRuleValidator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rule_validation_system.py:33
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rule_validation_system.TransformationRuleValidator._define_validation_criteria (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rule_validation_system.py:38
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rule_validation_system.TransformationRuleValidator.validate_rule_implementation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rule_validation_system.py:85
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rule_validation_system.TransformationRuleValidator.run_comprehensive_validation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rule_validation_system.py:140
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rule_validation_system.TransformationRuleValidator._print_validation_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rule_validation_system.py:202
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rule_validation_system.TransformationRuleValidator.generate_detailed_report (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rule_validation_system.py:243
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rule_validation_system.TransformationRuleValidator.fix_known_issues (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rule_validation_system.py:265
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rule_validation_system.run_comprehensive_validation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rule_validation_system.py:313
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.drawing_editor_integration.get_corpus_integration (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:28
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.get_export_manager (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:30
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.CorpusDockWidget.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.CorpusDockWidget.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:45
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.CorpusDockWidget.load_corpus_items (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:87
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.CorpusDockWidget.filter_items (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:99
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.CorpusDockWidget.on_item_double_clicked (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:115
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.CorpusDockWidget.load_selected_item (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:119
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.CorpusDockWidget.show_item_info (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:130
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.ExportDockWidget.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:156
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.ExportDockWidget.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:162
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.ExportDockWidget.get_drawing_schema (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:215
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.ExportDockWidget.export_to_clipboard (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:221
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.ExportDockWidget.export_to_file (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:253
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.ExportDockWidget.quick_egif_export (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:297
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.ExportDockWidget.generate_preview (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:321
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.ExportDockWidget._get_export_format (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:351
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.DrawingEditorIntegration.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:364
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.DrawingEditorIntegration.add_corpus_browser (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:369
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.DrawingEditorIntegration.add_export_panel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:383
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.DrawingEditorIntegration.on_corpus_item_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:405
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.DrawingEditorIntegration.load_schema_into_editor (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:431
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.DrawingEditorIntegration._populate_model_from_schema (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:458
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.drawing_editor_integration.integrate_drawing_editor (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/drawing_editor_integration.py:467
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.BranchingPointItem (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:172
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.BranchingPointItem.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:173
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.LigatureItem (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:179
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.PredicateItem (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:183
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.PredicateItem.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:184
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CutItem (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:191
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CutItem.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:192
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:201
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView.mousePressEvent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:211
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView._show_context_menu (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:271
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView._show_canvas_context_menu (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:291
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView._edit_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:302
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView._delete_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:318
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView._edit_predicate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:323
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView._delete_predicate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:338
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView._delete_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:343
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView._resize_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:348
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView._add_vertex_at_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:363
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView._add_predicate_at_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:368
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView._add_cut_at_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:377
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView._start_ligature_from_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:382
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView._start_ligature_from_predicate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:389
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIGraphicsView.mouseMoveEvent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:395
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIControlPanel.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:442
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIMainWindow.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:468
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIMainWindow._no_emit_command (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:595
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIMainWindow._clear_scene_min (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:603
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIMainWindow._update_graph_info_min (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:614
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIMainWindow._refresh_scene_min (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:638
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIMainWindow.set_show_variable_labels (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:654
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIMainWindow.set_show_arity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:661
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIMainWindow._init_corpus_dock (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:669
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIMainWindow._refresh_corpus_list (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:678
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIMainWindow.on_corpus_new (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:688
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIMainWindow._open_selected_corpus_action (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:713
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIMainWindow._inline_open_selected_corpus (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:721
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.EGIMainWindow._inline_corpus_new (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:747
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:753
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.populate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:779
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.current_entry (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:789
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._init_corpus_dock (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:796
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._refresh_corpus_list (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:806
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.on_corpus_new (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:813
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.on_corpus_open_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:836
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._inline_corpus_new (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:857
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._inline_save_egdf_beside (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:880
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._open_selected_corpus_action (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:915
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._inline_open_selected_corpus (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:944
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.graph_save_to_corpus (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:968
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.graph_export_tikz_to_corpus (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:995
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.graph_save_egdf_to_corpus (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1012
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._load_linear_and_refresh (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1044
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.open_linear_form_file (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1053
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.open_graph_file (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1071
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.reload_current_source (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1107
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._on_file_open_menu (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1138
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.open_egi_file (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1152
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._safe_load_egi_json (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1165
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._load_egi_json (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1204
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.load_egi_json (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1208
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._load_egi_dispatch (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1212
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._load_egi_inline_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1222
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._load_egdf_clear (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1260
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._load_egdf_file (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1264
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.save_egdf_to_sibling (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1281
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._normalized_egi_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1322
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._sorted_set (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1327
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.paste_linear_form (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1347
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.igi_seed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1354
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.clear_scene (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1365
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.refresh_scene (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1370
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._register (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1394
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._safe_update_chiron_contents (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1475
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.export_tikz (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1484
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._update_graph_info (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1514
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock.on_open_in_ergasterion (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1529
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._build_ergasterion_payload (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1537
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.CorpusDock._update_preview (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1562
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1576
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock._on_open_clicked (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1619
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock.update_info (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1637
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock._register_item (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1649
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock._set_item_highlight (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1657
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock.clear_highlight (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1684
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock.select_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1696
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock.clear_hover (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1714
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock.hover_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1725
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock._compute_connected_ids (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1762
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock.same_ctx (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1803
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock._emit_command (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:1824
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock._polyline_to_path (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:2036
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock._rounded_path (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:2051
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock._zigzag_points (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:2076
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock._init_chiron_dock (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:2144
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock._copy_text (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:2198
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock._update_chiron_contents (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:2205
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_egi_gui.GraphInfoDock.export_tikz (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_egi_gui.py:2221
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_discovery.TransformationAvailability (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:18
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_discovery.TransformationDiscoveryEngine (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:69
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Integrate with formal_transformation_rules.py

### legacy.transformation_discovery.TransformationDiscoveryEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:77
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_discovery.TransformationDiscoveryEngine.discover_transformations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:113
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_discovery.TransformationDiscoveryEngine._analyze_contexts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:164
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_discovery.TransformationDiscoveryEngine._discover_rule_transformations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:188
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_discovery.TransformationDiscoveryEngine._analyze_operation_availability (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:208
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_discovery.TransformationDiscoveryEngine._create_example_operation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:252
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_discovery.TransformationDiscoveryEngine._determine_availability (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:263
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_discovery.TransformationDiscoveryEngine._generate_descriptions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:283
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_discovery.SubgraphTransformationWorkflow (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:319
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_discovery.SubgraphTransformationWorkflow.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:324
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_discovery.SubgraphTransformationWorkflow.analyze_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:327
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_discovery.SubgraphTransformationWorkflow.get_transformation_menu (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:332
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_discovery.SubgraphTransformationWorkflow.create_operation_request (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_discovery.py:373
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.subgraph_isomorphism.DauSubgraphExtractor.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_isomorphism.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_isomorphism.DauSubgraphExtractor.extract_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_isomorphism.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.subgraph_isomorphism.DauSubgraphExtractor.get_area_hierarchy (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_isomorphism.py:77
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.subgraph_isomorphism.EGIsomorphismChecker.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_isomorphism.py:111
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_isomorphism.EGIsomorphismChecker.are_isomorphic (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_isomorphism.py:114
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_isomorphism.EGIsomorphismChecker._simple_structural_match (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_isomorphism.py:153
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_isomorphism.ITMinusValidator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_isomorphism.py:184
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.subgraph_isomorphism.ITMinusValidator.can_deiterate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_isomorphism.py:189
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.subgraph_isomorphism.ITMinusValidator._find_subgraph_candidates (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/subgraph_isomorphism.py:223
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.PresentationAdapter (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:31
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.PresentationAdapter.render_scene (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:34
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.PresentationAdapter.get_user_input (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:38
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.PresentationAdapter.show_linear_forms (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:42
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.PresentationAdapter.highlight_areas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:46
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.UserInteraction (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:52
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.RenderCommand (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:61
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:73
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.register_presentation_adapter (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:88
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.handle_user_interaction (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:110
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.get_linear_forms (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:136
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._on_egi_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:144
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.egi_controller.EGIController._refresh_all_presentations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:148
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._generate_area_aligned_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:179
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._handle_sigint (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:191
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._generate_validated_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:211
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._add_ligatures_to_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:284
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._ligature_crosses_cut_boundary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:370
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._line_intersects_rectangle (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:383
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._line_segments_intersect (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:409
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._route_ligature_around_cuts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:428
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._find_path_around_obstacles (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:476
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.segment_clear (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:499
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.heuristic (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:520
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._path_intersects_any_obstacle (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:566
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._point_in_rectangle_path (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:578
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._line_intersects_rectangle_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:584
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._route_around_rectangle (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:606
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._determine_cut_spatial_requirements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:632
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._analyze_element_spatial_constraints (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:660
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._find_cut_position_for_requirements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:683
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._satisfies_spatial_constraints (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:714
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._bounds_within_parent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:721
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._overlaps_existing_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:729
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._get_initial_area_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:744
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.enable_networkx_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:756
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.disable_networkx_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:761
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.get_validation_result (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:766
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.add_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:770
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.add_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:777
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.add_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:788
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.get_egif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:795
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.validate_current_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:799
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._find_cut_parent_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:819
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._find_element_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:827
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._find_non_colliding_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:834
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._get_exclusion_zones_for_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:895
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._position_in_exclusion_zones (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:915
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._bounds_contained_in (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:923
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._bounds_overlap_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:931
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.get_render_commands (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:938
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.get_valid_placement_areas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:984
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.get_cut_direct_contents (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:1002
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.get_cut_full_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:1026
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.collect_context_recursive (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:1031
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.check_collision (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:1055
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.validate_element_movement (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:1071
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.highlight_valid_placement_areas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:1101
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController.highlight_cut_contents (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:1108
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._can_place_element_in_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:1118
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._get_area_spatial_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:1131
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._bounds_overlap (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:1149
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.EGIController._point_in_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:1156
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_controller.create_egi_controller (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_controller.py:1163
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.user_workflow_integration.TransformationContext (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:14
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Integrate with formal_transformation_rules.py

### legacy.user_workflow_integration.SubgraphSelector.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:52
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.user_workflow_integration.SubgraphSelector.select_by_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:55
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.user_workflow_integration.SubgraphSelector.select_by_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:76
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.user_workflow_integration.SubgraphSelector._find_containing_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:89
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.user_workflow_integration.SubgraphSelector._find_common_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:98
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.user_workflow_integration.SubgraphSelector._determine_context_polarity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:113
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Connect to hierarchical_index.py

### legacy.user_workflow_integration.SubgraphSelector._calculate_nesting_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:119
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.user_workflow_integration.TransformationRuleDiscovery.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:136
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.user_workflow_integration.TransformationRuleDiscovery._initialize_rule_catalog (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:160
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.user_workflow_integration.WorkflowOrchestrator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:255
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.user_workflow_integration.WorkflowOrchestrator.create_transformation_workflow (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:260
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.user_workflow_integration.WorkflowOrchestrator._generate_preview_description (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:279
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.user_workflow_integration.WorkflowOrchestrator._predict_resulting_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/user_workflow_integration.py:299
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.arisbe_main.ArisbeMainApplication.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_main.py:25
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.arisbe_main.ArisbeMainApplication.create_module_panel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_main.py:125
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.arisbe_main.ArisbeMainApplication.launch_organon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_main.py:157
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.arisbe_main.ArisbeMainApplication.on_organon_close (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_main.py:168
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.arisbe_main.ArisbeMainApplication.launch_ergasterion (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_main.py:175
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.arisbe_main.ArisbeMainApplication.on_ergasterion_close (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_main.py:186
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.arisbe_main.ArisbeMainApplication.launch_agon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_main.py:193
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.arisbe_main.ArisbeMainApplication.on_agon_close (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_main.py:204
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.arisbe_main.ArisbeMainApplication.show_about (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_main.py:211
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.arisbe_main.ArisbeMainApplication.run (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_main.py:236
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.GameState (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.PlayerRole (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:33
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.EndoporeuticGameEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:89
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.EndoporeuticGameEngine.start_game (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:117
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.EndoporeuticGameEngine.get_game (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:138
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.EndoporeuticGame.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:160
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.EndoporeuticGame._initialize_game_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:187
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.EndoporeuticGame.make_claim (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:216
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.EndoporeuticGame.challenge_claim (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:254
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.EndoporeuticGame.attempt_proof_step (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:274
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.endoporeutic_game_system.EndoporeuticGame._requires_isomorphism_validation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:379
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.endoporeutic_game_system.EndoporeuticGame._validate_proof_step_isomorphism (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:385
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.EndoporeuticGame._get_nesting_hierarchy (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:408
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.endoporeutic_game_system.EndoporeuticGame.declare_victory (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:430
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.EndoporeuticGame.abandon_game (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:452
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.EndoporeuticGame._record_move (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:466
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.EndoporeuticGame.get_game_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:491
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.endoporeutic_game_system.EndoporeuticGame.export_game_transcript (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/endoporeutic_game_system.py:514
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.graph_building_visualizer.VisualizationFrame.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/graph_building_visualizer.py:31
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.graph_building_visualizer.GraphBuildingVisualizer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/graph_building_visualizer.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.graph_building_visualizer.GraphBuildingVisualizer.start_visualization_session (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/graph_building_visualizer.py:53
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.graph_building_visualizer.GraphBuildingVisualizer.visualize_utterance_building (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/graph_building_visualizer.py:76
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.graph_building_visualizer.GraphBuildingVisualizer.visualize_composition_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/graph_building_visualizer.py:103
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.graph_building_visualizer.GraphBuildingVisualizer._render_egi_to_svg (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/graph_building_visualizer.py:141
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.graph_building_visualizer.GraphBuildingVisualizer._calculate_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/graph_building_visualizer.py:203
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.graph_building_visualizer.GraphBuildingVisualizer._render_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/graph_building_visualizer.py:227
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.graph_building_visualizer.GraphBuildingVisualizer._render_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/graph_building_visualizer.py:253
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.graph_building_visualizer.GraphBuildingVisualizer._render_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/graph_building_visualizer.py:297
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.graph_building_visualizer.GraphBuildingVisualizer.generate_animation_html (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/graph_building_visualizer.py:332
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.graph_building_visualizer.GraphBuildingVisualizer.save_visualization_html (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/graph_building_visualizer.py:446
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.graph_building_visualizer.GraphBuildingVisualizer.get_session_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/graph_building_visualizer.py:455
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_context.StandardCompositionContexts (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_context.py:24
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_context.StandardCompositionContexts.calculate_nesting_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_context.py:101
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.composition_context.CompositionContextManager.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_context.py:177
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_context.CompositionContextManager.register_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_context.py:181
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_context.CompositionContextManager.set_active_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_context.py:185
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_context.CompositionContextManager.get_active_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_context.py:191
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_context.CompositionContextManager.get_composition_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_context.py:197
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_context.CompositionContextManager.create_graph_in_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_context.py:202
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_context.CompositionContextManager.list_contexts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_context.py:225
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_context.EndoporeuticGameContext.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_context.py:238
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_context.EndoporeuticGameContext.set_proposer_claim (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_context.py:248
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_context.EndoporeuticGameContext.add_move (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_context.py:259
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_context.EndoporeuticGameContext.get_game_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_context.py:268
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.IntegrationStatus (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:21
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.ConflictType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:30
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.IntegrationAttempt.add_conflict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.IntegrationAttempt.resolve_conflict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:70
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.UniverseOfDiscourse.add_integration (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:88
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.CompatibilityAnalyzer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:96
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.CompatibilityAnalyzer.analyze_compatibility (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:99
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.CompatibilityAnalyzer._check_naming_collisions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:136
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.CompatibilityAnalyzer._check_semantic_contradictions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:175
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.CompatibilityAnalyzer._check_structural_compatibility (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:197
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.CompatibilityAnalyzer._check_logical_consistency (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:219
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.IntegrationAdapter.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:249
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.IntegrationAdapter.adapt_for_integration (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:252
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.IntegrationAdapter._resolve_conflict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:263
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.agon_integration_process.IntegrationAdapter._resolve_naming_collision (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:271
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.AgonIntegrationProcess.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:281
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.AgonIntegrationProcess.establish_universe_of_discourse (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:292
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.AgonIntegrationProcess.attempt_integration (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:346
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.agon_integration_process.AgonIntegrationProcess._perform_integration (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:371
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.AgonIntegrationProcess.get_integration_attempt (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:404
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.AgonIntegrationProcess.list_integration_attempts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:408
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.agon_integration_process.AgonIntegrationProcess.analyze_integration_patterns (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/agon_integration_process.py:415
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_validation_pipeline.ValidationPolicy (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_validation_pipeline.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py
- Integrate with formal_transformation_rules.py

### legacy.transformation_validation_pipeline.TransformationValidationPipeline.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_validation_pipeline.py:55
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_validation_pipeline.TransformationValidationPipeline.validate_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_validation_pipeline.py:61
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_validation_pipeline.TransformationValidationPipeline._should_proceed_with_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_validation_pipeline.py:167
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_validation_pipeline.TransformationValidationPipeline._has_new_errors (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_validation_pipeline.py:200
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_validation_pipeline.TransformationValidationPipeline._analyze_validation_changes (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_validation_pipeline.py:212
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_validation_pipeline.TransformationValidationPipeline._create_error_result (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_validation_pipeline.py:224
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_validation_pipeline.TransformationValidationPipeline._create_blocked_result (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_validation_pipeline.py:270
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_validation_pipeline.TransformationValidationPipeline.get_validation_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_validation_pipeline.py:304
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_validation_pipeline.TransformationValidationPipeline.export_validation_report (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_validation_pipeline.py:337
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.GraphvizLayoutResult (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:16
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:23
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:30
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine.generate_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:34
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine._create_networkx_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:59
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine._add_cluster_attributes (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:89
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine._compute_graphviz_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:104
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine.timeout_handler (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:110
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine._generate_dot_with_clusters (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:151
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine._estimate_cluster_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:186
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine._generate_edge_paths (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:216
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine._scale_and_separate_positions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:227
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine._create_manual_area_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:253
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine._compute_proper_cluster_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:284
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine._extract_spatial_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:316
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine._add_networkx_ligatures (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:359
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine._find_element_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:418
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.networkx_spatial_layout.NetworkXEGILayoutEngine._find_cut_parent_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/networkx_spatial_layout.py:425
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegion.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:22
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegion.x (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:27
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegion.y (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:31
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegion.width (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegion.height (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegion.contains_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:42
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegion.get_available_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:47
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegionManager (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:54
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.spatial_region_manager.SpatialRegionManager.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:65
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegionManager._create_root_region (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:74
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegionManager.create_cut_region (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:84
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegionManager.get_region_for_logical_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:141
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegionManager.get_logical_area_at_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:146
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegionManager._get_region_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:167
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.spatial_region_manager.SpatialRegionManager.adjust_region_for_content_change (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:174
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.spatial_region_manager.SpatialRegionManager.get_all_regions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:208
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegionManager.validate_canvas_coverage (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:212
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_region_manager.SpatialRegionManager.get_region_hierarchy_info (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_region_manager.py:223
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.spatial_logical_alignment.SpatialBounds.contains_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_logical_alignment.py:17
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_logical_alignment.SpatialBounds.to_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_logical_alignment.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_logical_alignment.SpatialElement.to_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_logical_alignment.py:31
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_logical_alignment.SpatialAlignmentEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_logical_alignment.py:53
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_logical_alignment.SpatialAlignmentEngine._initialize_regions_from_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_logical_alignment.py:60
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_logical_alignment.SpatialAlignmentEngine._get_parent_area_for_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_logical_alignment.py:78
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_logical_alignment.SpatialAlignmentEngine.generate_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_logical_alignment.py:87
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_logical_alignment.SpatialAlignmentEngine._get_logical_area_for_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_logical_alignment.py:132
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_logical_alignment.SpatialAlignmentEngine.handle_spatial_drag (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_logical_alignment.py:142
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_logical_alignment.SpatialAlignmentEngine._signal_egi_update_required (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_logical_alignment.py:189
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_logical_alignment.SpatialAlignmentEngine.validate_spatial_logical_consistency (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_logical_alignment.py:194
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_logical_alignment.SpatialAlignmentEngine.get_conjunctive_groups (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_logical_alignment.py:209
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.spatial_logical_alignment.create_spatial_alignment_engine (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/spatial_logical_alignment.py:220
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_adapter.drawing_to_egdf_document (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_adapter.py:9
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.level_polarity_adjustment.LevelPolarityAdjuster.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/level_polarity_adjustment.py:33
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.level_polarity_adjustment.LevelPolarityAdjuster.calculate_adjustment (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/level_polarity_adjustment.py:36
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Connect to hierarchical_index.py
- Integrate with formal_transformation_rules.py

### legacy.level_polarity_adjustment.LevelPolarityAdjuster.adjust_subgraph_polarity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/level_polarity_adjustment.py:80
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Connect to hierarchical_index.py
- Integrate with formal_transformation_rules.py

### legacy.level_polarity_adjustment.LevelPolarityAdjuster._remove_outer_double_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/level_polarity_adjustment.py:116
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.level_polarity_adjustment.LevelPolarityAdjuster._add_outer_double_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/level_polarity_adjustment.py:171
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.level_polarity_adjustment.LevelPolarityAdjuster._adjust_cut_levels (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/level_polarity_adjustment.py:222
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py
- Integrate with formal_transformation_rules.py

### legacy.level_polarity_adjustment.LevelPolarityAdjuster.calculate_nesting_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/level_polarity_adjustment.py:238
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.level_polarity_adjustment.LevelPolarityAdjuster.get_polarity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/level_polarity_adjustment.py:247
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Connect to hierarchical_index.py

### legacy.replay_engine.ReplayStrategy (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.replay_engine.ReplayState.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:37
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.replay_engine.ReplayEngine (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:42
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.replay_engine.ReplayEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:50
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.replay_engine.ReplayEngine.replay_to_event (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.replay_engine.ReplayEngine._replay_from_beginning (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:95
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.replay_engine.ReplayEngine._replay_from_snapshot (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:141
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.replay_engine.ReplayEngine._replay_differential (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:200
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.replay_engine.ReplayEngine._rebuild_spatial_tracker (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:222
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.replay_engine.ReplayEngine.replay_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:234
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.replay_engine.ReplayEngine.create_replay_branch (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:271
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.replay_engine.ReplayEngine.validate_replay_consistency (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:305
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.replay_engine.ReplayEngine._compare_egi_states (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:331
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.replay_engine.ReplayEngine.get_replay_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:341
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.replay_engine.ReplayEngine.clear_cache (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:352
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.replay_engine.ReplayEngine.optimize_snapshots (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/replay_engine.py:356
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.LigatureTransformationType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:37
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.egi_spatial_correspondence.SpatialBounds.contains_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:54
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialBounds.contains_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:59
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialBounds.center (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.BranchingPoint.can_move_to (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:78
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.LigatureGeometry.validate_chapter16_constraints (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:101
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.CorrespondenceMapping.get_spatial_for_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:166
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.CorrespondenceMapping.get_egi_for_spatial (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:170
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.Chapter16Validator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:178
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.Chapter16Validator.validate_branch_movement (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:181
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.Chapter16Validator.validate_ligature_extension (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:187
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.Chapter16Validator.validate_ligature_retraction (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:193
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.Chapter16Validator.validate_ligature_rearrangement (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:208
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.Chapter16Validator._get_ligature_vertices (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:219
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:228
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.generate_spatial_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:244
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.generate_spatial_layout_staged (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:277
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.build_logical_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:293
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.fit_to_canvas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:332
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py
- Integrate with formal_transformation_rules.py

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.size_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:353
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.place_children (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:412
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._generate_cut_areas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:448
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.cut_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:454
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.overlaps (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2651
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.any_sibling_overlap (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:599
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._generate_ligatures_with_branching (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:641
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._position_predicates (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:721
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.rects_overlap (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1805
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._snap_ligatures_to_predicates (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:844
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._pt_in_rect (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1404
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._pt_on_rect_border (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1407
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._seg_still_crosses (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1460
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.build_padded_rects (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1496
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._pt_in_rect2 (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1325
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._pt_on_border2 (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1328
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._pass_through (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1335
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._hook_point_for_edge_argument (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1601
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._position_superscripts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1633
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._ligature_bounds_excluding_children (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1756
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.point_in_children (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1774
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._compute_border_hook (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1857
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.add_if_valid (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1873
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.validate_spatial_exclusion (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1944
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.contains (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1962
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.path_intersects_rect (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1964
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.seg_intersects (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:1967
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.orient (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2365
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.on_seg (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2367
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._validate_chapter16_compliance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2062
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.handle_branching_point_drag (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2069
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._identify_ligatures (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2113
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._generate_ligature_path (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2136
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.is_descendant_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2584
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._visibility_route (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2228
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.clear (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2252
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.h (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2268
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._compute_ligature_bridges (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2307
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.segs (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2319
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.path_len (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2340
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._segment_intersects_rect (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2352
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._segments_intersect (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2363
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._segment_rect_intersection_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2380
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._segment_intersection_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2394
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._interpolate_path (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2412
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._get_vertex_constant_label (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2435
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._calculate_ligature_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2440
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._determine_ligature_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2452
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._determine_vertex_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2465
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._ensure_all_vertices_present (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2472
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._determine_cut_parent_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2489
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._calculate_predicate_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2498
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._determine_element_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2551
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._clamp_bounds_into_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2558
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._pick_safe_point_in_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2574
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.point_in_rect (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2601
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._avoid_child_cut_holes (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2637
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._assert_path_within_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2687
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.point_in_rect_strict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2707
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine.point_in_rect_with_border (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2709
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._extend_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2734
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._restrict_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2738
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._retract_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2742
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.SpatialCorrespondenceEngine._rearrange_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2746
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_spatial_correspondence.create_spatial_correspondence_engine (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_spatial_correspondence.py:2760
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.AlphabetDAUSchema (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:13
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.EGIInlineSchema (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.EGIRefSchema (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.EGDFHeader (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:38
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.CutLayout (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:44
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.VertexLayout (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:51
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.PredicateLayout (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:57
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.LigaturePath (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:65
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.LigatureLayout (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:70
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.LayoutSection (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:75
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.StyleRule (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:83
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.egdf_parser.StylesSection (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:90
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.DeltaTranslate (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:96
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.DeltaRoute (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:105
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.EGDFSchema (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:114
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.EGDFDocument.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:139
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.EGDFDocument.to_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:162
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.EGDFDocument.to_json (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:172
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.EGDFDocument.to_yaml (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:175
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.EGDFDocument.from_json (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:190
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egdf_parser.EGDFDocument.from_yaml (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egdf_parser.py:194
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.reusable_rendering_core.BoundaryAnchor.rect_border_anchor (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/reusable_rendering_core.py:26
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.reusable_rendering_core.CutRenderer (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/reusable_rendering_core.py:97
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.reusable_rendering_core.CutRenderer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/reusable_rendering_core.py:100
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.reusable_rendering_core.CutRenderer.get_cut_style (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/reusable_rendering_core.py:108
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.reusable_rendering_core.LigatureRenderer (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/reusable_rendering_core.py:122
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.reusable_rendering_core.LigatureRenderer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/reusable_rendering_core.py:125
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.reusable_rendering_core.LigatureRenderer.render_identity_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/reusable_rendering_core.py:128
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.reusable_rendering_core.LigatureRenderer.render_predicate_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/reusable_rendering_core.py:173
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.reusable_rendering_core.VertexRenderer (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/reusable_rendering_core.py:194
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.reusable_rendering_core.VertexRenderer.render_vertex_spot (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/reusable_rendering_core.py:198
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationCanvas.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:43
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationCanvas.redraw_all (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:146
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationCanvas.draw_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:164
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationCanvas.draw_area_info (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:210
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.cut_visualization_gui.CutVisualizationCanvas.on_click (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:238
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationCanvas.on_drag (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:258
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationCanvas.on_release (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:286
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationCanvas.on_zoom (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:290
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationCanvas.show_cut_info (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:302
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationGUI.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:329
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationGUI.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:336
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationGUI.validate_constraints (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:423
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationGUI.show_rtree_info (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:435
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationGUI.reset_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:454
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.cut_visualization_gui.CutVisualizationGUI.run (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/cut_visualization_gui.py:463
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.CoordinateTransform.inverse (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.coordinate_negotiator.RenderingBackend (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:37
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.RenderingBackend.get_item_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:40
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.RenderingBackend.get_scene_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:44
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.RenderingBackend.get_items_at_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:48
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.CoordinateNegotiator (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:53
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.coordinate_negotiator.CoordinateNegotiator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:61
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.CoordinateNegotiator.set_rendering_backend (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:74
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.CoordinateNegotiator.register_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:78
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.CoordinateNegotiator.update_element_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:87
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.CoordinateNegotiator.get_logical_area_for_data_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:97
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.CoordinateNegotiator.get_logical_area_for_rendering_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:102
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.CoordinateNegotiator.get_rendering_position_for_data (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:107
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.CoordinateNegotiator.get_data_position_for_rendering (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:112
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.CoordinateNegotiator.synchronize_with_rendering_backend (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:117
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.CoordinateNegotiator.create_region_for_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:143
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.CoordinateNegotiator.get_valid_placement_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:175
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.CoordinateNegotiator.get_region_bounds_in_rendering_coordinates (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:186
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.QtRenderingBackend (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:291
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.QtRenderingBackend.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:294
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.QtRenderingBackend.get_item_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:297
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.QtRenderingBackend.get_scene_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:310
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.coordinate_negotiator.QtRenderingBackend.get_items_at_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/coordinate_negotiator.py:316
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.ConstraintViolationMessage.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.ConstraintViolationMessage._remove_self (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:40
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.ImprovedResizeHandle.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:49
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.ImprovedResizeHandle.itemChange (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:66
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.shared_diagram_renderer.ImprovedResizeHandle._validate_resize (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:97
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.InteractiveVertex.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:131
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.InteractiveVertex.itemChange (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:141
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.shared_diagram_renderer.InteractivePredicate.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:153
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.InteractivePredicate.paint (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:176
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.InteractivePredicate.itemChange (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:191
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.shared_diagram_renderer.InteractivePredicate._validate_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:202
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.InteractivePredicate._show_violation_message (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:244
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:254
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem.hoverEnterEvent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:300
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem.hoverLeaveEvent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:307
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem._show_resize_handles (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:313
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem._hide_resize_handles (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:333
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem.itemChange (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:340
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py
- Integrate with formal_transformation_rules.py

### legacy.shared_diagram_renderer.StyledCutItem._update_nesting_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:355
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.shared_diagram_renderer.StyledCutItem._validate_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:377
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem._move_contained_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:434
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem._show_violation_message (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:478
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem._attempt_collision_avoidance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:484
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem._is_valid_avoidance_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:524
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem._validate_resize (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:541
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem.mousePressEvent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:568
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem.mouseMoveEvent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:588
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem.mouseReleaseEvent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:614
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.StyledCutItem.paint (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:625
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:664
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:667
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer.calculate_nesting_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:685
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.shared_diagram_renderer.SharedDiagramRenderer.render_egdf (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:696
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer.update_ligatures_for_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:761
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer.update_ligatures_for_predicate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:813
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer.render_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:831
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer.toggle_annotation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:871
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer.identify_double_cuts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:877
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._is_valid_double_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:899
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._update_annotations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:940
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._update_double_cut_annotations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:946
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._update_predicate_arity_annotations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:970
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._update_vertex_variable_annotations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:984
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._get_predicate_arity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:998
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._get_vertex_variable_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1011
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._get_vertex_name (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1028
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._render_vertex_names (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1045
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._add_arity_annotation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1058
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._add_variable_annotation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1080
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._add_vertex_name_display (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1103
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._draw_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1127
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer.render_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1156
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._draw_predicate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1259
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._draw_ligature (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1297
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._draw_ligatures (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1327
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._rect_border_anchor (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1368
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._update_element_area_containment (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1402
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.shared_diagram_renderer.SharedDiagramRenderer._detect_containing_area_for_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1415
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._regenerate_egi_from_drawing_schema (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1475
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.shared_diagram_renderer.SharedDiagramRenderer._refresh_egif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/shared_diagram_renderer.py:1499
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.ergasterion_context.ExperimentStatus (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.HypothesisType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:28
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.Experiment.add_observation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:53
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.Experiment.add_conclusion (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:58
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.Experiment.update_status (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:63
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionWorkspace.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:83
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionWorkspace.create_experiment (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:102
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionWorkspace.set_active_experiment (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:200
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionWorkspace.get_experiment (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:206
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionWorkspace.get_active_experiment (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:210
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionWorkspace.list_experiments (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:216
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionWorkspace.create_workspace_snapshot (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:223
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionWorkspace.analyze_experiment_patterns (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:240
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionWorkspace._create_empty_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:274
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionManager.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:290
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionManager.create_workspace (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:294
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionManager.get_workspace (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:304
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionManager.get_active_workspace (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:308
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionManager.set_active_workspace (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:314
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionManager.list_workspaces (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:320
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.ergasterion_context.ErgasterionManager.analyze_cross_workspace_patterns (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/ergasterion_context.py:324
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.ViewType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.SynchronicView.get_vertex_count (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.SynchronicView.get_edge_count (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.SynchronicView.get_cut_count (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:43
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.SynchronicView.get_nesting_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:47
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.diachronic_synchronic_views.SynchronicView.analyze_logical_structure (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:52
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.DiachronicView.get_sequence_length (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:75
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.diachronic_synchronic_views.DiachronicView.get_rule_distribution (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:79
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.diachronic_synchronic_views.DiachronicView.get_temporal_span (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:87
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.diachronic_synchronic_views.DiachronicView.analyze_transformation_progression (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:96
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.diachronic_synchronic_views.DiachronicView._calculate_complexity_growth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:113
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.ViewManager.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:131
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.ViewManager.create_synchronic_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:136
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.ViewManager.create_diachronic_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:162
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.diachronic_synchronic_views.ViewManager.get_synchronic_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:201
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.ViewManager.get_diachronic_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:205
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.ViewManager.compare_synchronic_states (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:209
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.ViewManager._generate_semantic_description (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:230
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.ViewManager._analyze_egi_logic (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:258
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.ViewManager._analyze_connectivity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:275
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.ViewManager._analyze_nesting (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:290
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.diachronic_synchronic_views.ViewManager._generate_logical_progression (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:301
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.diachronic_synchronic_views.ViewManager._analyze_transformation_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:316
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.diachronic_synchronic_views.ViewManager._detect_alternation_patterns (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:334
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.diachronic_synchronic_views.ViewManager._track_complexity_evolution (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:346
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.diachronic_synchronic_views.ViewManager._assess_logical_coherence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/diachronic_synchronic_views.py:368
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.interaction_handler.DragState.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:23
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:30
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:38
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler.handle_mouse_press (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:51
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler.handle_mouse_move (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:62
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler.handle_mouse_release (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:71
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler.handle_key_press (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:82
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler.set_interaction_mode (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:112
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler.set_validation_mode (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:130
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler.register_graphics_item (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:138
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler.unregister_graphics_item (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:142
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler.get_element_id (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:146
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler._handle_left_click (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:152
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler._handle_right_click (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:199
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler._start_drag (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:210
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler._handle_drag_move (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:220
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler._handle_drag_end (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:232
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler._handle_ligature_creation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:256
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler._handle_delete_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:264
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler.get_current_mode (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:273
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler.get_validation_mode (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:277
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.interaction_handler.InteractionHandler.is_dragging (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/interaction_handler.py:281
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_testing_framework.TestResult (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_testing_framework.TransformationTestSuite.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:57
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_testing_framework.TransformationTestSuite._add_ins_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:90
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_testing_framework.TransformationTestSuite._add_era_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:135
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_testing_framework.TransformationTestSuite._add_dc_plus_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:166
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_testing_framework.TransformationTestSuite._add_dc_minus_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:183
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_testing_framework.TransformationTestSuite._add_it_plus_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:200
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_testing_framework.TransformationTestSuite._add_it_minus_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:220
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_testing_framework.TransformationTestSuite._add_composition_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:237
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_testing_framework.TransformationTestSuite._add_edge_case_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:254
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_testing_framework.TransformationTestSuite.run_test (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:285
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_testing_framework.TransformationTestSuite._run_transformation_test (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:306
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_testing_framework.TransformationTestSuite._run_composition_test (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:359
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_testing_framework.TransformationTestSuite._resolve_target_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:402
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_testing_framework.TransformationTestSuite._resolve_operation_details (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:445
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_testing_framework.TransformationTestSuite._calculate_nesting_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:454
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.transformation_testing_framework.TransformationTestSuite.run_all_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:463
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_testing_framework.run_comprehensive_tests (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_testing_framework.py:534
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.practice_mode_integration.get_transformation_engine (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:31
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.practice_mode_integration.PracticeModeState (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.PracticeSession.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:54
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.TransformationRulePalette.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.TransformationRulePalette.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:71
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.practice_mode_integration.TransformationRulePalette.create_rule_category (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:106
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.practice_mode_integration.TransformationRulePalette.on_rule_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:123
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.practice_mode_integration.TransformationRulePalette.update_for_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:127
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.practice_mode_integration.TransformationRulePalette.disable_all_rules (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:146
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.practice_mode_integration.TransformationRulePalette.update_rule_buttons (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:152
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.practice_mode_integration.TransformationRulePalette.update_status_display (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:166
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.practice_mode_integration.ValidationPanel.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:189
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.ValidationPanel.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:193
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.ValidationPanel.show_validation_result (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:224
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.ValidationPanel.clear (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:257
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.PracticeSessionPanel.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:268
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.PracticeSessionPanel.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:273
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.PracticeSessionPanel.start_session (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:320
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.PracticeSessionPanel.end_session (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:337
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.PracticeSessionPanel.record_transformation_attempt (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:350
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.practice_mode_integration.PracticeSessionPanel.update_stats_display (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:359
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.PracticeModeDockWidget.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:385
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.PracticeModeDockWidget.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:394
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.PracticeModeDockWidget.toggle_practice_mode (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:434
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.PracticeModeDockWidget.update_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:453
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.practice_mode_integration.PracticeModeDockWidget.on_rule_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:473
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.practice_mode_integration.PracticeModeDockWidget.cancel_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:555
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.practice_mode_integration.integrate_practice_mode (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/practice_mode_integration.py:565
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.immutable_transformation_architecture.TransformationRuleType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:17
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.immutable_transformation_architecture.ContextType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:27
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.immutable_transformation_architecture.TransformationSequence.add_step (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:71
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.immutable_transformation_architecture.TransformationSequence.get_current_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:76
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.immutable_transformation_architecture.ImmutableEGIRepository.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:84
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.immutable_transformation_architecture.ImmutableEGIRepository.store_egi_snapshot (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:89
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.immutable_transformation_architecture.ImmutableEGIRepository.store_transformation_step (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:93
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.immutable_transformation_architecture.ImmutableEGIRepository.store_transformation_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:97
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.immutable_transformation_architecture.ImmutableEGIRepository.get_egi_snapshot (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:101
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.immutable_transformation_architecture.ImmutableEGIRepository.get_transformation_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:105
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.immutable_transformation_architecture.ImmutableEGIRepository.get_egi_history (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:109
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.immutable_transformation_architecture.TransformationRule.get_rule_type (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:133
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.immutable_transformation_architecture.InsertionRule.get_rule_type (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:152
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.immutable_transformation_architecture.ErasureRule.get_rule_type (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:169
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.immutable_transformation_architecture.ImmutableTransformationEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:176
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.immutable_transformation_architecture.ErgasterionContext.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:247
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.immutable_transformation_architecture.ErgasterionContext.create_origination_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:253
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.immutable_transformation_architecture.AgonContext.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:300
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.immutable_transformation_architecture.AgonContext.set_universe_of_discourse (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:306
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.immutable_transformation_architecture.EndoporeuticGameReplay.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:332
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.immutable_transformation_architecture.EndoporeuticGameReplay.replay_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:335
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.immutable_transformation_architecture.EndoporeuticGameReplay.analyze_sequence_logic (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/immutable_transformation_architecture.py:356
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.dynamic_view_generator.NavigationMode (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:22
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.DetailLevel (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:30
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.dynamic_view_generator.ViewportBounds.width (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:48
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.ViewportBounds.height (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:52
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.ViewportBounds.center (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:56
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.RenderingHints.get_detail_level (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:74
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.dynamic_view_generator.ContextState.toggle (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:93
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.NavigationState.navigate_to (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:106
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.NavigationState.navigate_back (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:112
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.ViewGenerator.generate_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:125
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.GraphView.get_elements_by_type (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:174
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.GraphView.get_element_at_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:178
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.PeirceDauViewGenerator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:193
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.PeirceDauViewGenerator.generate_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:196
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.PeirceDauViewGenerator._determine_visible_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:247
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.PeirceDauViewGenerator._render_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:295
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.PeirceDauViewGenerator._render_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:333
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.PeirceDauViewGenerator._render_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:369
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.PeirceDauViewGenerator._is_in_collapsed_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:409
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.PeirceDauViewGenerator._get_nesting_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:420
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.dynamic_view_generator.DynamicViewManager (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:431
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.DynamicViewManager.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:434
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.DynamicViewManager.generate_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:444
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.DynamicViewManager.pan (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:458
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.DynamicViewManager.zoom (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:465
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.DynamicViewManager.toggle_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:480
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.DynamicViewManager.navigate_to_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:487
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.DynamicViewManager.get_navigation_options (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:498
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.DynamicViewManager.is_text_readable (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:528
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.DynamicViewManager.should_extend_page (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:533
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.ViewBasedSubgraphSelector (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:549
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.ViewBasedSubgraphSelector.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:552
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.ViewBasedSubgraphSelector.select_visible_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:556
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.dynamic_view_generator.ViewBasedSubgraphSelector.focus_on_subgraph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/dynamic_view_generator.py:581
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.ViewLevel (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:23
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.hierarchical_view_system.SpatialBounds.contains_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.SpatialBounds.intersects (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:43
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.SpatialBounds.area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:49
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.ContextSummary.get_display_text (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:62
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.ViewContext.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:69
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.ViewContext.should_show_details (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:80
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.ViewContext.calculate_complexity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:85
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.hierarchical_view_system.ViewContext._calculate_max_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:93
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.hierarchical_view_system.ViewContext._get_cut_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:101
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.hierarchical_view_system.ViewContext._find_parent_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:114
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.RTreeNode.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:125
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.RTreeNode.insert_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:132
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.RTreeNode.query_region (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:148
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.RTreeNode._update_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:163
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.RTreeNode._choose_subtree (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:178
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.RTreeNode._calculate_enlargement (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:192
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.RTreeNode._split_leaf (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:203
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.RTreeNode._recalculate_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:217
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:238
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.hierarchical_view_system.HierarchicalViewSystem.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:249
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem.build_hierarchical_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:258
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem.get_visible_contexts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:285
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem.collapse_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:309
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem.expand_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:320
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem.set_zoom_level (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:331
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.hierarchical_view_system.HierarchicalViewSystem._build_context_hierarchy (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:349
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.hierarchical_view_system.HierarchicalViewSystem._group_cuts_into_contexts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:370
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem._build_nested_contexts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:386
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem._calculate_context_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:418
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem._calculate_cut_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:437
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.hierarchical_view_system.HierarchicalViewSystem._find_parent_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:450
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem._layout_contexts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:457
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem._layout_sibling_contexts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:467
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem._layout_nested_contexts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:494
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem._build_spatial_index (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:511
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.hierarchical_view_system.HierarchicalViewSystem._optimize_view_levels (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/hierarchical_view_system.py:519
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.simplified_sheet_of_assertion.SheetOfAssertion (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simplified_sheet_of_assertion.py:5
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.simplified_sheet_of_assertion.SheetOfAssertion.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simplified_sheet_of_assertion.py:13
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simplified_sheet_of_assertion.SheetOfAssertion.current_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simplified_sheet_of_assertion.py:37
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simplified_sheet_of_assertion.SheetOfAssertion._record_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simplified_sheet_of_assertion.py:41
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.simplified_sheet_of_assertion.SheetOfAssertion.create_checkpoint (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simplified_sheet_of_assertion.py:58
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.simplified_sheet_of_assertion.SheetOfAssertion.replay_to_event (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simplified_sheet_of_assertion.py:62
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.simplified_sheet_of_assertion.SheetOfAssertion._rebuild_spatial_tracker (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simplified_sheet_of_assertion.py:72
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simplified_sheet_of_assertion.SheetOfAssertion.get_transformation_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simplified_sheet_of_assertion.py:86
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.simplified_sheet_of_assertion.SheetOfAssertion.branch_from_event (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simplified_sheet_of_assertion.py:90
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simplified_sheet_of_assertion.SheetOfAssertion.get_history_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simplified_sheet_of_assertion.py:94
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.simplified_sheet_of_assertion.SheetOfAssertion.export_with_history (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simplified_sheet_of_assertion.py:98
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.simplified_sheet_of_assertion.SheetOfAssertion.import_with_history (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simplified_sheet_of_assertion.py:112
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.arisbe_unified_app.AgonMainWindow.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_unified_app.py:76
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.arisbe_unified_app.ArisbeUnifiedMain.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_unified_app.py:89
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.arisbe_unified_app.ArisbeUnifiedMain._warn (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_unified_app.py:153
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.arisbe_unified_app.ArisbeUnifiedMain._on_edit_in_ergasterion (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_unified_app.py:165
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.arisbe_unified_app.ArisbeUnifiedMain._on_egi_from_ergasterion (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/arisbe_unified_app.py:185
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simple_graph_builder.GraphBuildingContext (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simple_graph_builder.GraphUtterance.get_step_count (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.simple_graph_builder.BuildingSession.add_utterance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:53
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simple_graph_builder.SimpleGraphBuilder.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:61
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simple_graph_builder.SimpleGraphBuilder.create_empty_context (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:67
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simple_graph_builder.SimpleGraphBuilder.start_building_session (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:96
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simple_graph_builder.SimpleGraphBuilder.build_graph_utterance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:110
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.simple_graph_builder.SimpleGraphBuilder.get_utterance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:165
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simple_graph_builder.SimpleGraphBuilder.get_utterance_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:169
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simple_graph_builder.SimpleGraphBuilder.list_utterances (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:178
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simple_graph_builder.SimpleGraphBuilder.analyze_utterance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:182
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simple_graph_builder.SimpleGraphBuilder._calculate_complexity_growth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:208
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.simple_graph_builder.SimpleGraphBuilder._get_rule_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:224
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.simple_graph_builder.create_basic_graph_utterances (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/simple_graph_builder.py:234
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_provenance_tracking.ProvenanceEventType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:21
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_provenance_tracking.EGILineage.add_descendant (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:57
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_provenance_tracking.TransformationChain.add_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:74
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_provenance_tracking.ProvenanceTracker.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:84
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_provenance_tracking.ProvenanceTracker.record_egi_creation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:91
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_provenance_tracking.ProvenanceTracker.record_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:139
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_provenance_tracking.ProvenanceTracker.record_context_transition (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:167
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_provenance_tracking.ProvenanceTracker.get_egi_lineage (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:193
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_provenance_tracking.ProvenanceTracker.get_transformation_chain (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:197
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_provenance_tracking.ProvenanceTracker.trace_egi_ancestry (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:209
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_provenance_tracking.ProvenanceTracker.find_common_ancestor (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:235
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_provenance_tracking.ProvenanceTracker.get_transformation_history (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:256
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_provenance_tracking.ProvenanceTracker.analyze_transformation_patterns (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:270
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_provenance_tracking.ProvenanceTracker.generate_provenance_report (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:302
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_provenance_tracking.ProvenanceTracker._store_event (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:365
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_provenance_tracking.ProvenanceTracker._update_lineages_for_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:370
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_provenance_tracking.ProvenanceTracker._update_chains_for_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_provenance_tracking.py:393
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_engine.TransformationEngine (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_engine.py:5
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_engine.TransformationEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_engine.py:13
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_engine.TransformationEngine._record_in_history (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_engine.py:88
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_engine.TransformationEngine.replay_transformation_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_engine.py:111
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.qt_correspondence_integration.QtInteractionEvent (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_correspondence_integration.py:15
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_correspondence_integration.QtRenderElement (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_correspondence_integration.py:22
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_correspondence_integration.QtCorrespondenceIntegration.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_correspondence_integration.py:34
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_correspondence_integration.QtCorrespondenceIntegration.generate_qt_scene (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_correspondence_integration.py:38
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_correspondence_integration.QtCorrespondenceIntegration._area_parity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_correspondence_integration.py:46
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.qt_correspondence_integration.create_qt_correspondence_integration (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/qt_correspondence_integration.py:143
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.GraphHandoffType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:21
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.ErgasterionWorkflowManager (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:49
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.ErgasterionWorkflowManager.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:52
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.ErgasterionWorkflowManager.receive_handoff (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:58
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.ErgasterionWorkflowManager._initialize_case1_workflow (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:71
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.ErgasterionWorkflowManager._initialize_case2_workflow (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:87
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.ErgasterionWorkflowManager._initialize_case3_workflow (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:116
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.ErgasterionWorkflowManager.check_completion_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:133
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.ErgasterionWorkflowManager.confirm_egi_match (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:156
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.ErgasterionWorkflowManager.is_egi_match_pending_confirmation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:168
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.ErgasterionWorkflowManager.create_return_package (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:172
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.ErgasterionWorkflowManager._egi_equivalent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:194
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.ErgasterionWorkflowManager._has_meaningful_content (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:211
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.ErgasterionWorkflowManager._determine_completion_status (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:220
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.OrganonErgasterionBridge (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:231
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.organon_ergasterion_protocol.OrganonErgasterionBridge.create_handoff_package (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/organon_ergasterion_protocol.py:235
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_transformer.CompositionTransformer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_transformer.py:41
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_transformer.CompositionTransformer._setup_standard_contexts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_transformer.py:50
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_transformer.CompositionTransformer.start_composition_session (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_transformer.py:60
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_transformer.CompositionTransformer.get_composition_analysis (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_transformer.py:97
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_transformer.CompositionTransformer.insert_in_composition_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_transformer.py:166
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.composition_transformer.CompositionTransformer.build_simple_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_transformer.py:208
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.composition_transformer.CompositionTransformer.get_session_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_transformer.py:227
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_transformer.CompositionTransformer.list_available_contexts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_transformer.py:242
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.composition_transformer.CompositionTransformer.create_endoporeutic_game_session (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/composition_transformer.py:246
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.TransformationRuleType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rules.ContextPolarity (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:37
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system

### legacy.transformation_rules.TransformationContext.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:51
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.ValidationResult.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.TransformationRule.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:86
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.TransformationRule.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:92
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rules.TransformationRule.get_context_polarity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:103
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system

### legacy.transformation_rules.TransformationRule.get_elements_in_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:130
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.InsertionRule.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:166
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.InsertionRule.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:170
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rules.ErasureRule.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:224
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.ErasureRule.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:228
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rules.IterationRule.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:306
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.IterationRule.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:310
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rules.DeiterationRule.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:368
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.DeiterationRule.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:372
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rules.DoubleCutInsertionRule.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:422
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.DoubleCutInsertionRule.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:426
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.DoubleCutErasureRule.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:469
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.DoubleCutErasureRule.validate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:473
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.TransformationEngine.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:535
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.transformation_rules.TransformationEngine._initialize_rules (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:539
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rules.TransformationEngine.get_available_rules (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:548
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rules.TransformationEngine.get_rule (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:552
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rules.TransformationEngine.validate_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:556
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rules.TransformationEngine.suggest_next_moves (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:603
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.transformation_rules.identify_double_negatives (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:620
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system
- Integrate with formal_transformation_rules.py

### legacy.transformation_rules.get_transformation_engine (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/transformation_rules.py:666
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.foundational_graph_builder.SheetType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:17
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.foundational_graph_builder.AssertionSheet.has_working_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.foundational_graph_builder.FoundationalGraphBuilder.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:60
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.foundational_graph_builder.FoundationalGraphBuilder.create_assertion_sheet (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:81
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.foundational_graph_builder.FoundationalGraphBuilder.prepare_sheet_for_construction (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:99
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.foundational_graph_builder.FoundationalGraphBuilder.start_construction (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:145
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.foundational_graph_builder.FoundationalGraphBuilder.add_to_construction (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:180
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.foundational_graph_builder.FoundationalGraphBuilder.copy_subgraph_pattern (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:213
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.foundational_graph_builder.FoundationalGraphBuilder.create_disjunction_pattern (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:274
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.foundational_graph_builder.FoundationalGraphBuilder.fill_disjunction_pattern (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:334
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.foundational_graph_builder.FoundationalGraphBuilder._create_empty_egi_id (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:378
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.foundational_graph_builder.FoundationalGraphBuilder._determine_rule_type (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:405
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.foundational_graph_builder.FoundationalGraphBuilder.get_sheet_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:411
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.foundational_graph_builder.FoundationalGraphBuilder.get_construction_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/foundational_graph_builder.py:428
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.phase1_validation_suite.Phase1ValidationSuite.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/phase1_validation_suite.py:33
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.phase1_validation_suite.Phase1ValidationSuite.run_all_validations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/phase1_validation_suite.py:37
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.phase1_validation_suite.Phase1ValidationSuite._generate_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/phase1_validation_suite.py:568
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.phase1_validation_suite.run_phase1_validation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/phase1_validation_suite.py:616
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rule_governed_composition.CompositionPattern (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:18
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.rule_governed_composition.ValidationLevel (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:27
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py
- Integrate with formal_transformation_rules.py

### legacy.rule_governed_composition.RuleGovernedComposer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:62
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rule_governed_composition.RuleGovernedComposer._initialize_composition_rules (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:72
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.rule_governed_composition.RuleGovernedComposer.create_composition_plan (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:129
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rule_governed_composition.RuleGovernedComposer.execute_composition_plan (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:148
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rule_governed_composition.RuleGovernedComposer.build_logical_expression (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:196
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.rule_governed_composition.RuleGovernedComposer._build_conjunction (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:211
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rule_governed_composition.RuleGovernedComposer._build_disjunction (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:235
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rule_governed_composition.RuleGovernedComposer._build_implication (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:290
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rule_governed_composition.RuleGovernedComposer._build_negation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:341
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rule_governed_composition.RuleGovernedComposer._validate_step_preconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:381
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rule_governed_composition.RuleGovernedComposer._validate_step_postconditions (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:398
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rule_governed_composition.RuleGovernedComposer._analyze_expected_outcome (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:415
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rule_governed_composition.RuleGovernedComposer.analyze_composition (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rule_governed_composition.py:438
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.ViolationType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:16
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:53
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator.validate_concordance (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:57
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._validate_area_membership (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:95
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.logic_spatial_validator.LogicSpatialValidator._validate_spatial_containment (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:118
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.logic_spatial_validator.LogicSpatialValidator._validate_ligature_boundaries (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:145
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### legacy.logic_spatial_validator.LogicSpatialValidator._validate_element_overlaps (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:179
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._validate_cut_nesting (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:199
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### legacy.logic_spatial_validator.LogicSpatialValidator._validate_orphaned_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:259
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._determine_spatial_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:285
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._point_to_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:290
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._is_spatially_contained (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:308
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._bounds_overlap (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:315
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._point_in_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:322
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._find_cut_crossings (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:328
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._line_intersects_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:339
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._find_cut_parent_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:350
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._calculate_canvas_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:357
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._generate_sample_points (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:369
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._find_areas_containing_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:383
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.LogicSpatialValidator._generate_validation_summary (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:400
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.logic_spatial_validator.create_validator (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/logic_spatial_validator.py:418
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.CutPlacementType (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:15
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.SpatialBounds.left (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:31
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.SpatialBounds.right (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:35
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.SpatialBounds.top (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.SpatialBounds.bottom (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:43
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.SpatialBounds.center_x (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:47
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.SpatialBounds.center_y (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:51
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.SpatialBounds.contains_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:54
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.SpatialBounds.intersects (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:59
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.SpatialBounds.contains_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:66
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.CutSpatialInfo.__hash__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:82
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeNode.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:89
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeNode.add_entry (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:95
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeNode.remove_entry (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:100
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeNode._update_bounds (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:106
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeNode.is_full (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:132
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeNode.search (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:136
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:154
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:157
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker.add_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:163
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker.remove_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:187
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker.move_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:200
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker.get_cuts_in_area (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:223
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker.get_nested_cuts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:227
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker.get_spatial_extent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:238
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker.query_region (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:252
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker._validate_placement (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:256
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker._cuts_overlap_with_spacing (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:278
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker._insert (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:288
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker._insert_recursive (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:297
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker._choose_subtree (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:308
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker._calculate_enlargement (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:322
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker._split_root (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:335
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker._split_node (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:344
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker._split_node_entries (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:355
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker._remove (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:370
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker._remove_recursive (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:374
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker.get_cut_info (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:390
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker.get_all_cuts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:394
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.rtree_cut_tracker.RTreeCutTracker.get_stats (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/rtree_cut_tracker.py:398
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.ExportFormat (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.ExportResult.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.EGIExporter.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:49
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.EGIExporter.export_drawing_schema (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:53
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.EGIExporter._convert_to_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:88
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.EGIExporter._validate_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:116
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.EGIExporter._export_egi_json (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:142
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.EGIExporter._export_egif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:210
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.EGIExporter._export_cgif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:258
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.EGIExporter._export_clif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:279
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.EGIExporter._export_drawing_schema (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:300
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.EGIExporter._get_timestamp (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:337
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.EGIExporter.get_supported_formats (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:342
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.EGIExporter.validate_drawing_schema (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:351
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.EGIConversionResult.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:385
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.ExportManager.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:395
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.ExportManager.export_with_dialog (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:400
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.ExportManager.quick_export_egif (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:413
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.ExportManager.export_to_string (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:425
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.ExportManager._get_timestamp_short (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:430
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_export.get_export_manager (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_export.py:439
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_io.load_egi_json (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_io.py:63
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### legacy.egi_io.save_egi_json (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/legacy/egi_io.py:70
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### controller.constraint_engine.ConstraintMode (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/controller/constraint_engine.py:36
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### controller.constraint_engine.ValidationResult.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/controller/constraint_engine.py:44
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### controller.constraint_engine.validate_movement_permissive (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/controller/constraint_engine.py:300
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### controller.constraint_engine.validate_movement_strict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/controller/constraint_engine.py:343
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### controller.constraint_engine.validate_naming_change (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/controller/constraint_engine.py:449
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### controller.constraint_engine.validate_arity_change (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/controller/constraint_engine.py:461
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### controller.constraint_engine.suggest_area_for_point (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/controller/constraint_engine.py:601
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.LinearFormDisplay (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app_pyside6.LinearFormDisplay.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:67
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.LinearFormDisplay.init_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:71
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.LinearFormDisplay.display_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:87
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.LinearFormDisplay.display_transformation_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:104
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app_pyside6.OrganonTab.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:137
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.OrganonTab.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:144
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.OrganonTab.load_corpus_data (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:220
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.OrganonTab.on_egi_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:273
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.OrganonTab.generate_linear_forms (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:344
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.OrganonTab.clear_linear_forms (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:410
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.OrganonTab.on_transfer_to_ergasterion (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:416
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.OrganonTab.receive_from_ergasterion (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:423
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app_pyside6.ErgasterionTab.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:438
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ErgasterionTab._create_transformation_rules (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:445
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app_pyside6.ErgasterionTab.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:456
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ErgasterionTab.load_egi_from_organon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:568
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ErgasterionTab.show_transformation_wizard (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:615
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app_pyside6.ErgasterionTab.convert_egi_to_json (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:697
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ErgasterionTab.display_transformation_result (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:712
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app_pyside6.ErgasterionTab.send_to_organon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:738
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app_pyside6.ErgasterionTab.generate_linear_forms (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:753
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ErgasterionTab.clear_linear_forms (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:818
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.AgonTab.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:828
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.AgonTab.init_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:833
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.AgonTab.receive_graph_for_integration (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:859
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ArisbeMainWindow.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:868
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ArisbeMainWindow.init_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:873
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ArisbeMainWindow.on_egi_selected_from_organon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:916
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ArisbeMainWindow.create_menu_bar (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:925
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ArisbeMainWindow.new_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:953
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ArisbeMainWindow.open_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:958
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ArisbeMainWindow.show_about (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:962
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ArisbeMainWindow.on_egi_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:973
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ArisbeMainWindow.setup_cross_tab_communication (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:978
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app_pyside6.ArisbeMainWindow.send_graph_to_agon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:983
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.agon_interface.AgonInterface.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:50
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.agon_interface.AgonInterface._setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:73
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.agon_interface.AgonInterface._create_endoporeutic_tab (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:97
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.agon_interface.AgonInterface._create_hypothesis_testing_tab (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:226
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.agon_interface.AgonInterface._setup_menus (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:284
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.agon_interface.AgonInterface._setup_toolbar (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:309
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.agon_interface.AgonInterface._setup_status_bar (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:323
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.agon_interface.AgonInterface._connect_signals (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:328
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.agon_interface.AgonInterface._initialize_agon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:338
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.agon_interface.AgonInterface._new_endoporeutic_game (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:348
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.agon_interface.AgonInterface._add_hypothesis (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:373
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.agon_interface.AgonInterface._validate_current_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:399
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.agon_interface.AgonInterface._on_hypothesis_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:412
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.agon_interface.AgonInterface._on_game_state_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/agon_interface.py:416
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.ergasterion_editor.ErgasterionEditor (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:27
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.ergasterion_editor.ErgasterionEditor.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:41
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.ergasterion_editor.ErgasterionEditor._setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.ergasterion_editor.ErgasterionEditor._create_diagram_panel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:85
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.ergasterion_editor.ErgasterionEditor._create_control_panel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:102
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.ergasterion_editor.ErgasterionEditor._setup_menus (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:163
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.ergasterion_editor.ErgasterionEditor._setup_toolbar (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:195
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.ergasterion_editor.ErgasterionEditor._setup_status_bar (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:213
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.ergasterion_editor.ErgasterionEditor._connect_signals (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:218
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.ergasterion_editor.ErgasterionEditor._initialize_empty_sheet (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:223
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.ergasterion_editor.ErgasterionEditor._update_display (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:244
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.ergasterion_editor.ErgasterionEditor._update_available_transformations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:258
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.ergasterion_editor.ErgasterionEditor._execute_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:299
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.ergasterion_editor.ErgasterionEditor._undo_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:330
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.ergasterion_editor.ErgasterionEditor._clear_all (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:341
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.ergasterion_editor.ErgasterionEditor._add_history_entry (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:345
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.ergasterion_editor.ErgasterionEditor._on_graph_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:349
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.ergasterion_editor.ErgasterionEditor._on_practice_mode_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:356
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.ergasterion_editor.ErgasterionEditor._save_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:363
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.ergasterion_editor.ErgasterionEditor._load_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/ergasterion_editor.py:368
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_egi_viewer.CleanEGIViewer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_egi_viewer.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_egi_viewer.CleanEGIViewer._setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_egi_viewer.py:48
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_egi_viewer.CleanEGIViewer._connect_signals (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_egi_viewer.py:101
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_egi_viewer.CleanEGIViewer.load_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_egi_viewer.py:111
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_egi_viewer.CleanEGIViewer._refresh_display (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_egi_viewer.py:145
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_egi_viewer.CleanEGIViewer._clear_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_egi_viewer.py:155
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_egi_viewer.CleanEGIViewer._on_selection_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_egi_viewer.py:159
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.clean_egi_viewer.CleanEGIViewer.highlight_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_egi_viewer.py:173
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_egi_viewer.CleanEGIViewer.get_current_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_egi_viewer.py:177
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_egi_viewer.CleanEGIViewer.mousePressEvent (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_egi_viewer.py:181
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.transformation_wizard_dialog.TransformationWizardDialog.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:18
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.transformation_wizard_dialog.TransformationWizardDialog.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.transformation_wizard_dialog.TransformationWizardDialog.populate_steps_list (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:105
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.transformation_wizard_dialog.TransformationWizardDialog.update_step_display (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:122
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.transformation_wizard_dialog.TransformationWizardDialog.update_step_content (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:145
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.transformation_wizard_dialog.TransformationWizardDialog.get_rule_description (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:327
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.transformation_wizard_dialog.TransformationWizardDialog.update_buttons (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:339
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.transformation_wizard_dialog.TransformationWizardDialog.go_back (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:357
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.transformation_wizard_dialog.TransformationWizardDialog.go_next (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:366
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.transformation_wizard_dialog.TransformationWizardDialog.execute_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:372
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.transformation_wizard_dialog.TransformationWizardDialog.on_area_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:396
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.transformation_wizard_dialog.TransformationWizardDialog.on_element_selection_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:401
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.transformation_wizard_dialog.TransformationWizardDialog.on_individual_selection_toggled (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:406
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.transformation_wizard_dialog.TransformationWizardDialog.on_position_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:414
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.transformation_wizard_dialog.TransformationWizardDialog.on_insertion_type_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:419
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.transformation_wizard_dialog.TransformationWizardDialog.update_insertion_details (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:427
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.transformation_wizard_dialog.TransformationWizardDialog.get_result (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/transformation_wizard_dialog.py:480
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:26
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.setup_enhanced_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:47
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.setup_menu_bar (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:61
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.setup_side_panels (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:95
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.setup_enhanced_toolbar (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:105
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.enable_advanced_features (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:121
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.new_diagram (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:141
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.open_diagram (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:146
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.save_diagram (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:161
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.save_diagram_as (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:177
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.export_svg (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:181
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.zoom_in (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:186
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.zoom_out (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:191
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.zoom_fit (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:196
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.update_zoom (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:201
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.toggle_grid (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:207
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.toggle_snap (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:212
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.draw_grid (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:216
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.enhanced_click (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:234
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.enhanced_drag (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:239
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.enhanced_release (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:252
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.select_elements_in_rectangle (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:273
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.save_state (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:282
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.undo (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:298
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.redo (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:306
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.export_diagram_data (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:315
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.enhanced_diagram_editor.EnhancedDiagramEditor.load_diagram_data (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/enhanced_diagram_editor.py:333
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_home.WorkingRoom.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_home.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_home.ArisbeHome.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_home.py:123
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_home.ArisbeHome.enter_organon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_home.py:209
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_home.ArisbeHome.enter_ergasterion (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_home.py:218
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_home.ArisbeHome.enter_agon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_home.py:229
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:34
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer._load_style_config (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:49
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer.render_egi_to_scene (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:68
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer._calculate_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:106
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer._build_element_chain (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:154
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer._render_vertices (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:206
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer._render_relations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:244
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer._render_edge_lines (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:263
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer._generate_ligature_path (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:307
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer._path_intersects_relations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:328
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer._line_intersects_rect (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:344
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer._render_cuts (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:363
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer.get_element_at_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:401
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.clean_diagram_renderer.CleanDiagramRenderer.highlight_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/clean_diagram_renderer.py:419
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.VertexElement.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:54
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.RelationElement.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:64
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.EdgeElement (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:69
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.EdgeElement.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:75
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.CutElement.__post_init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:84
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:91
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:122
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.create_toolbar (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:170
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.create_properties_panel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:229
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.bind_events (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:237
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.on_tool_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:252
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.diagram_editor.DiagramEditor.on_canvas_click (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:263
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.handle_element_click (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:279
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.handle_empty_click (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:297
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.create_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:310
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.create_relation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:342
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.start_cut_creation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:372
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.on_canvas_drag (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:378
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.on_canvas_release (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:411
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.create_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:431
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.find_element_by_canvas_id (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:456
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.select_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:463
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.deselect_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:475
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.clear_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:487
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.update_properties_panel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:492
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.create_element_properties (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:514
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.validate_diagram (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:560
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.build_diagram_representation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:574
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.find_containing_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:629
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.clear_canvas (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:660
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.export_diagram (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:669
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.get_element_properties (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:699
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.diagram_to_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:709
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.delete_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:728
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.select_all (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:740
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.undo (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:746
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.redo (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:751
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.update_context_display (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:756
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.draw_context_background (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:765
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.diagram_editor.DiagramEditor.update_transformation_buttons (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/diagram_editor.py:808
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app.CorpusManager (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:45
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.CorpusManager.get_categories (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:46
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.CorpusManager.get_items_by_category (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:47
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.CorpusIntegration (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:49
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.CorpusIntegration.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:50
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.CorpusItem (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:52
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.load_index (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:55
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.list_entries (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:56
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.LinearFormDisplay.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:70
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.LinearFormDisplay.init_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:74
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.LinearFormDisplay.display_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:90
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.LinearFormDisplay.display_transformation_sequence (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:107
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app.OrganonTab.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:139
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.init_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:145
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.populate_egi_tree (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:658
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.on_egi_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:726
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.import_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:643
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.load_corpus (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:653
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.export_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:817
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.send_to_ergasterion (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:477
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.show_export_options (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:494
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.set_view_mode (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:528
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.display_egi_with_mode (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:541
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.load_annotations_for_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:578
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.on_annotation_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:585
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app.OrganonTab.find_graphs (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:590
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.explore_universe_connections (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:597
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.on_search_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:602
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app.OrganonTab.on_filter_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:612
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app.OrganonTab.on_view_options_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:617
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app.OrganonTab.filter_corpus_tree (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:623
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.filter_by_category (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:628
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.update_display_options (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:633
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.create_new_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:638
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab._populate_sample_entries (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:704
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.populate_corpus_tree (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:722
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab._load_and_display_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:739
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.display_corpus_entry (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:827
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.OrganonTab.display_corpus_item (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:879
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:919
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab.init_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:924
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab.initialize_workspace (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1082
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab.set_mode (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1111
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab.adjust_layout (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1164
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab.create_new_fact (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1196
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab.create_new_hypothesis (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1211
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab.create_thought_structure (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1226
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab._initialize_wizard_system (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1232
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app.ErgasterionTab.start_transformation_wizard (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1244
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app.ErgasterionTab.handle_wizard_input (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1283
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab._execute_wizard_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1327
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.arisbe_main_app.ErgasterionTab._create_proof_sequence_from_wizard (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1368
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab.cancel_wizard (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1420
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab.load_exemplar_from_organon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1437
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab.send_to_agon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1483
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ErgasterionTab.receive_graph_for_integration (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1501
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.AgonTab.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1521
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.AgonTab.init_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1528
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.AgonTab.initialize_agon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1593
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.AgonTab.load_universe (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1610
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.AgonTab.create_universe (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1615
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.AgonTab.start_endoporeutic_game (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1620
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.AgonTab.pause_game (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1627
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.AgonTab.end_game (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1631
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.AgonTab.receive_graph_for_integration (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1638
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ArisbeMainWindow.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1658
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ArisbeMainWindow.init_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1663
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ArisbeMainWindow.create_menu_bar (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1708
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ArisbeMainWindow.new_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1736
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ArisbeMainWindow.open_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1741
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ArisbeMainWindow.show_about (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1745
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ArisbeMainWindow.on_egi_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1758
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ArisbeMainWindow.setup_cross_tab_communication (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1763
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.arisbe_main_app.ArisbeMainWindow.send_graph_to_agon (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:1768
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:45
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:91
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.bind_events (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:161
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.on_tool_change (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:175
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.simple_diagram_editor.SimpleDiagramEditor.draw_sheet_background (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:186
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.on_click (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:204
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.on_drag (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:234
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.on_release (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:258
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.create_vertex (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:266
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.start_cut_creation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:299
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.update_cut_preview (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:305
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.complete_cut_creation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:322
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.create_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:339
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.find_element_by_canvas_item (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:367
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.select_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:374
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.deselect_element (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:387
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.clear_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:403
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.delete_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:408
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.select_all (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:427
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.clear_all (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:433
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.validate_diagram (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:446
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.build_diagram_representation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:459
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.find_containing_cut (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:523
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.sync_to_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:548
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.update_transformation_buttons (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:559
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.simple_diagram_editor.SimpleDiagramEditor.get_current_polarity (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:592
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with HierarchicalIndex polarity system

### gui.simple_diagram_editor.SimpleDiagramEditor.get_context_depth (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:604
**Reason**: No incoming references found
**Integration Suggestions**:
- Connect to hierarchical_index.py

### gui.simple_diagram_editor.SimpleDiagramEditor.reconstruct_diagram_from_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:652
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.recreate_visual_elements (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:673
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.create_vertex_at_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:726
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.create_cut_at_position (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:750
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.handle_edge_click (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:769
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.update_edge_preview (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:782
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.cancel_edge_creation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:799
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.create_edge (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:812
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.validate_diagram_realtime (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:848
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.clear_validation_overlays (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:877
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.highlight_constraint_violations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:883
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.highlight_dominating_nodes_violations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:894
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.highlight_nary_relation_violations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:917
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.highlight_general_violations (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:938
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.add_violation_highlight (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:943
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.simple_diagram_editor.SimpleDiagramEditor.show_validation_tooltip (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:989
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### styling.style_manager.StyleQuery (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/styling/style_manager.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### styling.style_manager.StyleManager.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/styling/style_manager.py:27
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### styling.style_manager.StyleManager._load_theme (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/styling/style_manager.py:32
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### styling.style_manager.StyleManager.theme_path (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/styling/style_manager.py:48
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### styling.style_manager.StyleManager.set_theme_path (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/styling/style_manager.py:52
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### styling.style_manager.StyleManager.resolve (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/styling/style_manager.py:59
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### styling.style_manager.StyleManager.reload (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/styling/style_manager.py:84
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:63
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._init_corpus_dock (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:103
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._init_info_dock (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:116
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._init_linear_forms_dock (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:123
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._refresh_corpus (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:130
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow.refresh_current_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:134
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.organon.main_window.OrganonMainWindow._on_new_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:141
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._on_entry_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:220
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._load_graph_dir (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:232
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._update_status (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:273
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._update_handoff_visibility (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:282
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._read_egi_json (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:294
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._select_egdf_dialog (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:381
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow.on_ok (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:420
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow.on_cancel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:423
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._build_handoff_payload (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:442
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._on_open_in_ergasterion (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:462
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._on_egi_created (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:485
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._egi_to_json_dict (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:534
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow.process_egi_from_ergasterion (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:553
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.main_window.OrganonMainWindow._add_egdf_replica (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/main_window.py:611
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:53
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:70
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.setup_details_panel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:132
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.load_tomos_index (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:153
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.save_tomos_index (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:184
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.populate_tree (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:228
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.on_tree_selection (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:274
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.organon.corpus_navigator.CorpusNavigator.update_details_panel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:300
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.on_tree_double_click (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:342
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.on_search_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:346
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.organon.corpus_navigator.CorpusNavigator.refresh_corpus (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:357
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.create_universe (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:361
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.import_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:379
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.open_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:394
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.export_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:401
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.CorpusNavigator.delete_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:408
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.UniverseDialog.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:432
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.UniverseDialog.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:453
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.UniverseDialog.ok (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:489
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_navigator.UniverseDialog.cancel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:508
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.linear_forms_panel.LinearFormsPanel (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/linear_forms_panel.py:19
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.linear_forms_panel.LinearFormsPanel.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/linear_forms_panel.py:27
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.linear_forms_panel.LinearFormsPanel.clear (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/linear_forms_panel.py:58
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.linear_forms_panel.LinearFormsPanel.set_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/linear_forms_panel.py:65
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.linear_forms_panel.LinearFormsPanel._set_enabled (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/linear_forms_panel.py:70
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.linear_forms_panel.LinearFormsPanel._on_generate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/linear_forms_panel.py:76
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.linear_forms_panel.LinearFormsPanel._on_copy_current (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/linear_forms_panel.py:95
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.diagram_viewer.DiagramViewer (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/diagram_viewer.py:15
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.diagram_viewer.DiagramViewer.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/diagram_viewer.py:20
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.diagram_viewer.DiagramViewer.clear (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/diagram_viewer.py:28
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.diagram_viewer.DiagramViewer.load_egdf_path (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/diagram_viewer.py:34
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.diagram_viewer.DiagramViewer.load_egi_dto_readonly (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/diagram_viewer.py:39
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.diagram_viewer.DiagramViewer._convert_dto_to_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/diagram_viewer.py:51
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:17
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:33
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel._setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:42
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel._load_corpus (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:100
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel._get_graph_type_from_entry (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:138
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel._get_graph_status_from_entry (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:156
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel._get_graph_type (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:166
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel._get_graph_status (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:178
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel._filter_graphs (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:183
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel._on_graph_selected (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:191
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel._show_graph_details (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:211
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel._new_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:241
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel._edit_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:254
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel._practice_graph (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:261
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel.get_graph_data (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:273
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel.refresh_corpus (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:277
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel.add_graph_to_index (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:281
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.corpus_panel.CorpusPanel.populate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:326
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.info_panel.GraphInfo (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/info_panel.py:17
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.info_panel.InfoPanel (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/info_panel.py:22
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.info_panel.InfoPanel.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/info_panel.py:27
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.info_panel.InfoPanel.load_graph_dir (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/info_panel.py:113
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.info_panel.InfoPanel._populate_fields (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/info_panel.py:131
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.info_panel.InfoPanel._collect_fields (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/info_panel.py:173
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.info_panel.InfoPanel._update_enabled_based_on_field_source (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/info_panel.py:203
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.info_panel.InfoPanel._update_status (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/info_panel.py:234
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.info_panel.InfoPanel._on_edited (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/info_panel.py:243
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.info_panel.InfoPanel._on_save (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/info_panel.py:247
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.info_panel.InfoPanel._on_discard (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/info_panel.py:270
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:31
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:42
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.setup_ui (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:57
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.create_header (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:85
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.create_diagram_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:124
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.create_analysis_panel (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:165
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.create_status_bar (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:218
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.setup_connections (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:235
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.load_egi (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:239
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.clear (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:263
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.update_diagram_display (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:284
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.update_format_displays (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:309
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.update_validation_status (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:326
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.update_statistics (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:346
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.on_view_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:358
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.on_format_changed (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:376
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.preview_transformation (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:388
**Reason**: No incoming references found
**Integration Suggestions**:
- Integrate with formal_transformation_rules.py

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.request_edit (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:420
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.zoom_in (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:425
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.zoom_out (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:429
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.chapter21_diagram_panel.Chapter21DiagramPanel.fit_to_view (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/chapter21_diagram_panel.py:433
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.exports_panel.ExportsPanel (class)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/exports_panel.py:15
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.exports_panel.ExportsPanel.__init__ (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/exports_panel.py:23
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.exports_panel.ExportsPanel.clear (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/exports_panel.py:50
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.exports_panel.ExportsPanel.set_render_commands (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/exports_panel.py:55
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.exports_panel.ExportsPanel._set_enabled (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/exports_panel.py:61
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.exports_panel.ExportsPanel._on_generate (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/exports_panel.py:67
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal

### gui.organon.exports_panel.ExportsPanel._on_save (function)
**Location**: /Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/exports_panel.py:76
**Reason**: No incoming references found
**Integration Suggestions**:
- Review for potential consolidation or removal
