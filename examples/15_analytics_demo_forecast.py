"""Example 15: Analytics demo mode and forecasting.

Demo mode generates deterministic synthetic data. Forecasting
uses OLS linear trend with a 3-day holdout and 7-day horizon.
"""
from apexgraphswarm.analytics import build_analytics
from datetime import datetime, timezone

now = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)

# Demo mode - deterministic synthetic data
result = build_analytics({"source": "demo", "days": 30}, now=now)

print(f"Demo attempts: {result['kpis']['attempts']}")
print(f"Demo succeeded: {result['kpis']['succeeded']}")
print(f"Demo success rate: {result['kpis']['successRate']:.2%}")

# Forecast
forecast = result["forecast"]
print(f"\nForecast status: {forecast['status']}")
print(f"Method: {forecast['method']}")
if forecast["status"] == "available":
    print(f"Backtest MAE: {forecast['backtestMAE']}")
    print(f"Naive MAE: {forecast['naiveMAE']}")
    print(f"Training dates: {len(forecast['trainingDates'])}")
    print(f"Holdout dates: {len(forecast['holdoutDates'])}")
    print(f"Forecast points: {len(forecast['points'])}")
    for point in forecast["points"][:3]:
        print(f"  {point['date']}: {point['predictedMicrousd']} "
              f"({point['lowerMicrousd']}-{point['upperMicrousd']})")

# Verify determinism
result2 = build_analytics({"source": "demo", "days": 30}, now=now)
assert result == result2, "Demo mode should be deterministic"
print("\nDeterminism verified: identical results")
