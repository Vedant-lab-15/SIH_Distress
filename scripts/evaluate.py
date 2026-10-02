from pathlib import Path
import json
import pandas as pd

root = Path(__file__).resolve().parents[1]
metrics = json.loads((root / "reports/metrics.json").read_text())
print("Model comparison:")
print(pd.read_csv(root / "reports/model_comparison.csv").to_string(index=False))
print()
print("Victim-level split:", metrics["victim_counts"])
