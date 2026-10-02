from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parents[1]
source = root / "data/raw/reference_dataset.xlsx"
out = root / "data/synthetic/synthetic_distress_dataset.csv"
df = pd.read_excel(source, sheet_name="dataset")
df.to_csv(out, index=False)
print(f"Prepared {len(df):,} rows -> {out}")
