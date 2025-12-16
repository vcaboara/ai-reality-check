#!/usr/bin/env python3
"""Test script for ai-reality-check feasibility analyzer."""

# Load environment variables FIRST before any other imports
# This ensures ASMF providers pick up the correct env vars
from dotenv import load_dotenv
load_dotenv()

import sys
import json
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from analyzers.feasibility_analyzer import FeasibilityAnalyzer


# Sample technical description for testing
SAMPLE_TEXT = """
Proposed Biomass Pyrolysis System

System Overview:
A continuous pyrolysis reactor for converting agricultural waste into bio-oil and biochar.
The system processes 500 kg/hour of corn stover at 550°C in an oxygen-free environment.

Technical Specifications:
- Reactor Type: Fast pyrolysis fluidized bed reactor
- Operating Temperature: 550°C ± 25°C
- Residence Time: 2 seconds
- Feedstock: Corn stover (10-15% moisture)
- Expected Products:
  * Bio-oil: 60% yield
  * Biochar: 20% yield
  * Syngas: 20% yield

Heat Recovery:
The system includes a heat exchanger recovering 75% of thermal energy from flue gases
to preheat incoming feedstock, reducing overall energy consumption by 40%.

Estimated Energy Balance:
- Energy Input: 2.5 MJ/kg feedstock
- Energy Output (bio-oil): 17 MJ/kg
- Net Energy Ratio: 6.8
"""


def main():
    """Run feasibility analysis test."""
    print("=" * 80)
    print("AI Reality Check - Test Analysis")
    print("=" * 80)
    print()

    # Initialize analyzer
    print("Loading domain configuration and expert system...")
    config_path = Path(__file__).parent / "config" / "domain.yaml"
    analyzer = FeasibilityAnalyzer(config_path)
    print(f"[OK] Loaded domain: {analyzer.domain_config.domain_name}")
    print()

    # Run analysis
    print("Analyzing sample pyrolysis system description...")
    print("-" * 80)
    print(SAMPLE_TEXT)
    print("-" * 80)
    print()

    context = {
        "project_name": "Test Biomass Pyrolysis",
        "analyst": "Test Script"
    }

    print("Running AI analysis (this may take 1-5 minutes depending on model)...")
    result = analyzer.analyze(SAMPLE_TEXT, context)

    # Display results
    print()
    print("=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    print()

    print("Technical Validation:")
    print(json.dumps(result.get("technical_validation", {}), indent=2))
    print()

    print("AI Analysis:")
    print(result.get("analysis", "No analysis generated"))
    print()

    print("Metadata:")
    metadata = result.get("metadata", {})
    print(f"  Domain: {metadata.get('domain', 'unknown')}")
    print(f"  Provider: {metadata.get('provider', 'unknown')}")
    print(f"  Model: {metadata.get('model', 'unknown')}")
    print(f"  Timestamp: {metadata.get('timestamp', 'unknown')}")
    print()

    # Save result
    output_dir = Path(__file__).parent / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "test_analysis.json"

    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"[OK] Results saved to: {output_file}")
    print()


if __name__ == "__main__":
    main()
