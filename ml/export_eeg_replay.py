#!/usr/bin/env python3
"""Build a small, de-identified held-out EEG feature replay for Android."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


FEATURES = [
    "n_channels_used",
    "alpha_power_mean", "alpha_power_std",
    "beta_power_mean", "beta_power_std",
    "delta_power_mean", "delta_power_std",
    "gamma_power_mean", "gamma_power_std",
    "line_length_mean", "line_length_std",
    "mean_mean", "mean_std",
    "ptp_mean", "ptp_std",
    "rms_mean", "rms_std",
    "std_mean", "std_std",
    "theta_power_mean", "theta_power_std",
    "zero_crossing_rate_mean", "zero_crossing_rate_std",
]


def select_rows(frame: pd.DataFrame) -> pd.DataFrame:
    allowed = frame[frame["dataset"].isin(["chbmit", "siena"])].copy()
    non_seizure = (
        allowed[allowed["window_label"].eq("non_seizure")]
        .sort_values("probability_seizure")
        .head(6)
    )
    chb_candidates = allowed[
        allowed["dataset"].eq("chbmit")
        & allowed["window_label"].eq("seizure")
        & allowed["probability_seizure"].ge(0.60)
    ].sort_values("probability_seizure")
    chb_seizure = chb_candidates.iloc[
        [0, len(chb_candidates) // 2, len(chb_candidates) - 1]
    ]
    siena_seizure = (
        allowed[
            allowed["dataset"].eq("siena")
            & allowed["window_label"].eq("seizure")
        ]
        .sort_values("probability_seizure")
        .tail(3)
    )
    selected = pd.concat([non_seizure, chb_seizure, siena_seizure], ignore_index=True)
    if len(selected) != 12:
        raise RuntimeError(f"Expected 12 replay rows, selected {len(selected)}")
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    features = pd.read_csv(args.features)
    predictions = pd.read_csv(args.predictions)
    merged = features.merge(
        predictions[["window_id", "probability_seizure"]],
        on="window_id",
        validate="one_to_one",
    )
    merged = merged[
        merged["status"].eq("ok")
        & merged["model_split"].eq("test")
        & merged[FEATURES].notna().all(axis=1)
    ]
    selected = select_rows(merged)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    columns = ["replay_id", "dataset", "ground_truth", "reference_probability", *FEATURES]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for index, row in selected.iterrows():
            writer.writerow({
                "replay_id": f"heldout_{index + 1:02d}",
                "dataset": row["dataset"],
                "ground_truth": row["window_label"],
                "reference_probability": f"{row['probability_seizure']:.10f}",
                **{feature: f"{row[feature]:.10g}" for feature in FEATURES},
            })

    print(f"Wrote {len(selected)} de-identified replay rows to {args.output}")


if __name__ == "__main__":
    main()
