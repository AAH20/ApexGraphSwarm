"""Example 22: Metric profiles and weighted scoring.

Five built-in profiles (coding, research, analytics, operations,
physical_simulation) with non-compensating hard gates.
"""
from apexgraphswarm.hierarchy import (
    get_metric_profile,
    normalize_metric_weights,
    weighted_score,
    METRIC_PROFILES,
    HARD_GATES,
)

# List all profiles
print("Available profiles:")
for pid, profile in METRIC_PROFILES.items():
    print(f"  {pid}: {profile['label']} (v{profile['version']})")
    print(f"    Weights: {profile['weights']}")

print(f"\nHard gates (non-compensating): {HARD_GATES}")

# Get a specific profile
coding = get_metric_profile("coding")
print(f"\nCoding profile: {coding['label']}")
print(f"  Score range: {coding['scoreRange']}")
print(f"  Weight total: {coding['weightTotal']}")

# Score with default weights
scores = {
    "correctness": 0.9,
    "test_coverage": 0.8,
    "regression_control": 0.85,
    "evidence_provenance": 0.95,
    "reliability": 0.9,
    "latency": 0.7,
    "cost_efficiency": 0.6,
    "coordination_efficiency": 0.85,
}
result = weighted_score("coding", scores)
print(f"\nWeighted score: {result['score']:.4f}")
print(f"Complete: {result['complete']}")
print(f"Components:")
for metric, comp in result["components"].items():
    print(f"  {metric}: {comp['score']:.2f} × {comp['weightPercent']}% = {comp['weightedContribution']:.4f}")

# Custom weights (must sum to 100)
custom_weights = {
    "correctness": 50,
    "test_coverage": 20,
    "regression_control": 10,
    "evidence_provenance": 10,
    "reliability": 5,
    "latency": 2,
    "cost_efficiency": 2,
    "coordination_efficiency": 1,
}
result_custom = weighted_score("coding", scores, weights=custom_weights, weight_version="custom-v1")
print(f"\nCustom weighted score: {result_custom['score']:.4f}")
print(f"Weight version: {result_custom['metricWeightVersion']}")
