"""Standalone entry point mirroring data_generator.py's __main__ pattern -
runs the full metrics recalculation without a live HTTP server, so it can
run as a Docker build step (baking calculated metrics into the image)."""

from app.database.connection import SessionLocal
from app.utils.metrics_calculator import recalculate_all_metrics

if __name__ == "__main__":
    session = SessionLocal()
    
    try:
        result = recalculate_all_metrics(session)
        print("Metrics recalculation result:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    finally:
        session.close()
