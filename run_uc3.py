"""
Кросс-страновый анализ на актуальных данных (UC-3).

Читает data_wid.csv, собирает кросс-секционную таблицу за 2024 год, считает
кросс-страновые корреляции неравенства с соц-экономическими показателями,
оценивает робастность по группам стран, строит scatter plots.
Результаты: output/uc3_summary.csv, output/uc3_robustness.csv, output/scatter/*.png.
"""

import os

import pandas as pd

from src import config
from src.cross_section_analysis import (
    build_cross_section,
    plot_scatter,
    robustness_by_group,
    top_cross_correlations,
)
from src.time_series_analysis import inequality_targets


REFERENCE_YEAR = 2024

DEVELOPED = ["US", "CA", "DE", "FR", "GB", "IT", "ES", "SE", "PL", "CZ", "JP", "KR", "AU"]
DEVELOPING = [
    "BR", "MX", "AR", "CL", "CO", "RU", "TR", "CN", "IN", "ID", "ZA", "NG", "KE", "EG", "SA",
]


def main():
    df = pd.read_csv("data_wid.csv")
    os.makedirs("output", exist_ok=True)

    table = build_cross_section(df, reference_year=REFERENCE_YEAR)
    print(f"Кросс-секционная таблица: {table.shape[0]} стран x {table.shape[1]} переменных")
    print(f"Страны без данных за {REFERENCE_YEAR}:\n{table[table.isna().all(axis=1)].index.tolist()}")
    table = table.dropna(how="all")
    print(f"После удаления пустых строк: {table.shape[0]} стран")

    summary = []
    for target in inequality_targets():
        try:
            top = top_cross_correlations(
                table, target=target, k=10, threshold=config.CORRELATION_THRESHOLD
            )
        except ValueError:
            continue
        for _, row in top.iterrows():
            summary.append(
                {
                    "target": target,
                    "variable": row["variable"],
                    "correlation": round(row["correlation"], 3),
                }
            )

    sdf = pd.DataFrame(summary)
    sdf = sdf.reindex(sdf["correlation"].abs().sort_values(ascending=False).index)
    sdf.to_csv("output/uc3_summary.csv", index=False)
    print(f"\nСильных кросс-страновых корреляций (|r|>={config.CORRELATION_THRESHOLD}): {len(sdf)}")
    print(sdf.head(15).to_string())

    groups = {"developed": DEVELOPED, "developing": DEVELOPING}
    rob = robustness_by_group(table, groups)
    rob.to_csv("output/uc3_robustness.csv", index=False)
    print(f"\nРобастность по группам: {len(rob)} строк -> output/uc3_robustness.csv")
    if not rob.empty:
        rob_abs = rob.assign(abs_corr=rob["correlation"].abs())
        top_rob = rob_abs.nlargest(10, "abs_corr")[["country_group", "target", "variable", "correlation"]]
        print(top_rob.to_string(index=False))

    targets_with_data = [
        t for t in inequality_targets() if t in table.columns and table[t].notna().sum() >= 10
    ]
    print(f"\nScatter plots по целям: {targets_with_data}")
    for target in targets_with_data:
        paths = plot_scatter(table, target=target)
        print(f"  {target}: {len(paths)} файлов")


if __name__ == "__main__":
    main()
