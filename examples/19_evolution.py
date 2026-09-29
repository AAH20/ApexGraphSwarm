"""Example 19: Running bounded algorithm evolution.

Evolution generates fixture splits, executes a candidate grid,
and gates held-out results with conservative promotion checks.
"""
from apexgraphswarm.evolution import run_evolution

result = run_evolution({
    "seed": 42,
    "trainCount": 8,
    "heldoutCount": 4,
    "sealedCount": 2,
    "itemsPerInstance": 10,
    "claimCount": 6,
    "costExponents": [0.0, 0.5, 1.0, 1.5],
    "tokenBudget": 100,
    "qualityFloor": 0.7,
    "maxAlgorithmLatencyMs": 5000,
})

print(f"Evolution protocol: {result['evolutionProtocol']}")
print(f"Claim: {result['claim']}")
print(f"Source hashes: {result['sourceHashes']}")
print(f"Config SHA256: {result['configurationSha256'][:16]}...")

# Dataset info
ds = result["dataset"]
print(f"\nDataset: {ds['generator']}")
print(f"Seed: {ds['seed']}")
print(f"Train: {ds['trainCount']}, Heldout: {ds['heldoutCount']}, Sealed: {ds['sealedCount']}")
print(f"Items per instance: {ds['itemsPerInstance']}")
print(f"Claim count: {ds['claimCount']}")

# Algorithm info
algo = result["algorithm"]
print(f"\nAlgorithm: {algo['name']}")
print(f"Objective: {algo['objective']}")
print(f"Work bound: {algo['workBound']['units']} / {algo['workBound']['maximum']}")

# Selection
sel = result["trainingSelection"]
print(f"\nSelected: {sel['candidateId']}")
print(f"Criterion: {sel['criterion']}")
print(f"Mean objective ratios: {sel['meanObjectiveRatioByCandidate']}")

# Promotion decision
promo = result["heldoutPromotionDecision"]
print(f"\nPromotion decision: {promo['decision']}")
print(f"Mean difference: {promo.get('meanDifference', 'N/A')}")
