"""One-off verification script (not part of the app) - triangulates
assistant_tools.py's tool wrappers against direct QueryBuilder/analytics_service
calls and the live REST API, per the plan's Stage 2 verification gate. Run
manually; not imported by anything else."""

import json
from datetime import date

from app.database.connection import SessionLocal
from app.services.assistant_tools import build_tools
from app.services.query_builder import QueryBuilder

db = SessionLocal()
tools = {t.name: t for t in build_tools(db)}
qb = QueryBuilder(db)


def show(label, value):
    print(f"{label}: {json.dumps(value, default=str)}")


print("=== get_total_revenue: tool vs direct QueryBuilder vs curl (anchor: 32399121.74 / 921) ===")
tool_result = tools["get_total_revenue"].invoke(
    {"hotel_id": 1, "start_date": "2025-12-01", "end_date": "2025-12-31"}
)
direct_result = qb.get_total_revenue(hotel_id=1, start_date=date(2025, 12, 1), end_date=date(2025, 12, 31))
show("tool  ", tool_result)
show("direct", direct_result)
assert tool_result["total_revenue"] == 32399121.74, tool_result
assert tool_result["total_bookings"] == 921, tool_result
assert tool_result == direct_result, "tool result diverged from direct QueryBuilder call"
print("MATCH\n")

print("=== get_occupancy_stats: tool vs direct QueryBuilder ===")
tool_result = tools["get_occupancy_stats"].invoke(
    {"hotel_id": 1, "start_date": "2025-12-01", "end_date": "2025-12-31"}
)
direct_result = qb.get_occupancy_stats(hotel_id=1, start_date=date(2025, 12, 1), end_date=date(2025, 12, 31))
show("tool  ", tool_result)
show("direct", direct_result)
assert tool_result == direct_result, "tool result diverged from direct QueryBuilder call"
print("MATCH\n")

print("=== get_occupancy_stats: unknown hotel_id returns clean error, not a crash ===")
tool_result = tools["get_occupancy_stats"].invoke({"hotel_id": 999})
show("tool  ", tool_result)
assert "error" in tool_result
print("OK (clean error)\n")

print("=== forecast_occupancy(1, 14): sanity + shape check ===")
tool_result = tools["forecast_occupancy"].invoke({"hotel_id": 1, "days_ahead": 14})
show("tool summary", tool_result["summary"])
print(f"predictions returned: {len(tool_result['predictions'])} (expect 7, truncated from 14)")
assert tool_result["forecast_engine"] == "xgboost_pooled"
assert len(tool_result["predictions"]) == 7
assert tool_result["summary"]["days_forecasted"] == 14
print("OK\n")

print("=== search_knowledge('what is RevPAR') ===")
tool_result = tools["search_knowledge"].invoke({"query": "what is RevPAR"})
top = tool_result["results"][0]
print(f"top hit: {top['source']} / {top['heading']}")
assert top["source"] == "metrics-explained.md"
print("OK\n")

print("=== list_hotels() ===")
tool_result = tools["list_hotels"].invoke({})
show("tool", tool_result)
assert len(tool_result["hotels"]) == 3
print("OK\n")

print("ALL CHECKS PASSED")
db.close()
