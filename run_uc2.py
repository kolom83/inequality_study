"""
Анализ динамики неравенства во времени по странам (UC-2).

Читает data_wid.csv, строит корреляции показателей с неравенством по каждой
стране, оценивает стабильность по периодам, сохраняет тепловые карты.
Результаты: output/uc2_summary.csv, output/heatmaps/*.png.
"""

import os

import pandas as pd

from src import config
from src.time_series_analysis import (
    analyze_country_time_series,
    inequality_targets,
    plot_heatmaps,
    stability_by_period,
    top_correlations,
)


def main():
    df = pd.read_csv("data_wid.csv")
    os.makedirs("output", exist_ok=True)

    analysis = analyze_country_time_series(df)
    targets = inequality_targets()

    summary = []
    for country in config.COUNTRIES:
        wide = analysis[country]["wide"]
        for target in targets:
            try:
                top = top_correlations(
                    wide,
                    target=target,
                    k=10,
                    threshold=config.CORRELATION_THRESHOLD,
                )
            except ValueError:
                continue
            for _, row in top.iterrows():
                summary.append(
                    {
                        "country": country,
                        "target": target,
                        "variable": row["variable"],
                        "correlation": round(row["correlation"], 3),
                    }
                )

    sdf = pd.DataFrame(summary)
    sdf = sdf.reindex(sdf["correlation"].abs().sort_values(ascending=False).index)
    sdf.to_csv("output/uc2_summary.csv", index=False)
    print(f"Сильных корреляций (|r|>={config.CORRELATION_THRESHOLD}): {len(sdf)}")
    print(sdf.head(20).to_string())

    periods = [(config.YEAR_FROM, 2005), (2006, config.YEAR_TO)]
    stability_rows = []
    for country in config.COUNTRIES:
        wide = analysis[country]["wide"]
        for target in targets:
            stab = stability_by_period(wide, target, periods)
            if stab.empty:
                continue
            stab["country"] = country
            stab["target"] = target
            stability_rows.append(stab)
    stab_df = pd.concat(stability_rows, ignore_index=True)
    stab_df.to_csv("output/uc2_stability.csv", index=False)
    print(f"\nСтабильность по периодам: {len(stab_df)} строк -> output/uc2_stability.csv")

    heatmaps = plot_heatmaps(analysis)
    print(f"\nТепловые карты: {len(heatmaps)} файлов")


if __name__ == "__main__":
    main()
