#!/usr/bin/env python3
"""Quality Gate System - Automated quality monitoring."""

from coherence_framework import QualityGateSystem

def main():
    system = QualityGateSystem()
    metrics = system.run_all_checks()
    print(f"Quality Score: {metrics.overall_score()}/100")

if __name__ == "__main__":
    main()
