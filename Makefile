# Convenience targets for validation, rewrites, and quarantine

.PHONY: help validate validate-scholars validate-all rewrite rewrite-scholars rewrite-all quarantine-dry quarantine-move

help:
	@echo "Targets:"
	@echo "  validate           - Validate canonical (EGIF round-trip)"
	@echo "  validate-scholars  - Validate scholars (no round-trip, skip harvest)"
	@echo "  validate-all       - Validate canonical+scholars (no round-trip, skip harvest)"
	@echo "  rewrite            - Rewrite canonical goldens deterministically"
	@echo "  rewrite-scholars   - Rewrite scholars goldens deterministically"
	@echo "  rewrite-all        - Rewrite canonical+scholars goldens"
	@echo "  quarantine-dry     - Detect noisy scholar files (dry run)"
	@echo "  quarantine-move    - Move noisy scholar files to rejected_tmp/"

validate:
	python tools/validate_corpus_linear_forms.py --sets canonical --roundtrip egif

validate-scholars:
	python tools/validate_corpus_linear_forms.py --sets scholars --roundtrip none

validate-all:
	python tools/validate_corpus_linear_forms.py --sets all --roundtrip none

rewrite:
	python tools/rewrite_linear_goldens.py

rewrite-scholars:
	python tools/rewrite_linear_goldens.py scholars

rewrite-all:
	python tools/rewrite_linear_goldens.py all

quarantine-dry:
	python tools/quarantine_scholars.py --dry-run

quarantine-move:
	python tools/quarantine_scholars.py --move
