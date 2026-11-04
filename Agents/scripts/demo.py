"""Local end-to-end logic demo, no external service required."""
import json
from backend.agents.orchestrator import run_demo

if __name__ == "__main__":
    for intent in ("negotiate", "fraud_check"):
        print("\n===", intent.upper(), "===")
        print(json.dumps(run_demo(intent), ensure_ascii=False, indent=2))
