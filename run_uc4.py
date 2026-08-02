"""
Сопоставление исторической и кросс-страновой корреляции (UC-4).

Читает data_wid.csv, считает средние исторические корреляции (UC-2) и
кросс-страновые (UC-3), объединяет в сводную таблицу, выделяет кандидатов,
попавших в топ-N по обоим подходам, проводит проверку устойчивости (лаг,
исключение выбросов).
Результаты: output/uc4_comparison.csv, output/uc4_candidates.csv,
output/uc4_robustness.csv.
"""

import os
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)

from src import config
from src.analysis_comparison import (
    comparison_table,
    drop_outlier_correlation,
    historical_correlations,
    lagged_correlation,
    top_by_both,
)
from src.cross_section_analysis import build_cross_section
from src.time_series_analysis import inequality_targets


REFERENCE_YEAR = 2024
N_TOP = 5


def main():
    df = pd.read_csv("data_wid.csv")
    os.makedirs("output", exist_ok=True)

    table = build_cross_section(df, reference_year=REFERENCE_YEAR).dropna(how="all")
    targets = [t for t in inequality_targets() if t in table.columns and table[t].notna().sum() >= 10]

    all_comparisons = []
    all_candidates = []
    for target in targets:
        hist = historical_correlations(df, target=target)
        comp = comparison_table(hist, table, target=target)
        comp["target"] = target
        all_comparisons.append(comp)

        cand = top_by_both(comp, target=target, k=N_TOP, threshold=config.CORRELATION_THRESHOLD)
        if not cand.empty:
            cand["target"] = target
            all_candidates.append(cand)

    comp_df = pd.concat(all_comparisons, ignore_index=True)
    comp_df.to_csv("output/uc4_comparison.csv", index=False)
    print(f"Сводная таблица: {len(comp_df)} строк -> output/uc4_comparison.csv")

    if all_candidates:
        cand_df = pd.concat(all_candidates, ignore_index=True)
        cand_df.to_csv("output/uc4_candidates.csv", index=False)
        print(f"\nКандидаты в топ-{N_TOP} по обоим подходам (|r|>={config.CORRELATION_THRESHOLD}):")
        print(cand_df[["target", "variable", "r_historical_abs", "r_cross_abs", "mean_rank"]].round(3).to_string(index=False))

        robustness = []
        for _, row in cand_df.iterrows():
            target, var = row["target"], row["variable"]
            for lag in [0, 1, 2]:
                robustness.append(
                    {
                        "target": target,
                        "variable": var,
                        "lag": lag,
                        "correlation": round(lagged_correlation(df, target, var, lag=lag), 3),
                    }
                )
            # Исключение выбросов на кросс-выборке
            xs = table[var].dropna()
            ys = table.loc[xs.index, target].dropna()
            common = xs.index.intersection(ys.index)
            if len(common) >= 5:
                r_full = pd.Series(table.loc[common, var]).corr(pd.Series(table.loc[common, target]))
                r_wo = drop_outlier_correlation(
                    table.loc[common, var], table.loc[common, target]
                )
                robustness.append(
                    {
                        "target": target,
                        "variable": var,
                        "lag": "drop_outlier",
                        "correlation": round(r_full, 3),
                    }
                )
                robustness.append(
                    {
                        "target": target,
                        "variable": var,
                        "lag": "after_drop",
                        "correlation": round(r_wo, 3),
                    }
                )
        rob_df = pd.DataFrame(robustness)
        rob_df.to_csv("output/uc4_robustness.csv", index=False)
        print(f"\nПроверка устойчивости: {len(rob_df)} строк -> output/uc4_robustness.csv")
        print(rob_df.to_string(index=False))
    else:
        print("\nКандидатов, попавших в топ-5 по обоим подходам с порогом 0.7, не найдено.")


if __name__ == "__main__":
    main()
