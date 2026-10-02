from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split


def victim_level_split(
    df: pd.DataFrame, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    victims = df["victim_id"].dropna().astype(str).unique()
    train_v, temp_v = train_test_split(victims, test_size=0.30, random_state=seed)
    val_v, test_v = train_test_split(temp_v, test_size=0.50, random_state=seed)

    train = df[df["victim_id"].astype(str).isin(set(train_v))].copy()
    val = df[df["victim_id"].astype(str).isin(set(val_v))].copy()
    test = df[df["victim_id"].astype(str).isin(set(test_v))].copy()

    train_ids = set(train["victim_id"])
    val_ids = set(val["victim_id"])
    test_ids = set(test["victim_id"])
    assert train_ids.isdisjoint(val_ids), "Victim overlap between train and validation"
    assert train_ids.isdisjoint(test_ids), "Victim overlap between train and test"
    assert val_ids.isdisjoint(test_ids), "Victim overlap between validation and test"

    return train.sort_values(["victim_id", "interaction_number"]),            val.sort_values(["victim_id", "interaction_number"]),            test.sort_values(["victim_id", "interaction_number"])
