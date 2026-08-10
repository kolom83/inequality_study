"""
Анализ неравенства доходов по видам (трудовой/капитальный), UC-7.

Проверка гипотезы: сильная корреляция концентрации богатства (шока топ-1%)
с неравенством доходов объясняется капитальным доходом (рентой/процентами).

Читает output/uc7_data.csv, считает корреляции каждой меры неравенства вида
дохода с shweal_p99p100 за пересекающийся период по странам (US, FR, TH),
сравнивает силу корреляции видов, строит графики.
Результаты: output/uc7_correlations.csv, output/uc7_comparison.csv,
output/uc7/*.png.
"""

import os

import pandas as pd

from src.income_type_analysis import (
    compare_top_shares,
    compare_types,
    correlate_with_wealth,
    plot_correlations,
)


def main():
    os.makedirs("output", exist_ok=True)
    df = pd.read_csv("output/uc7_data.csv")

    corr = correlate_with_wealth(df)
    corr["correlation"] = corr["correlation"].round(3)
    corr.to_csv("output/uc7_correlations.csv", index=False)
    print("Корреляции с shweal_p99p100 (доля богатства топ-1%):")
    print(corr.to_string(index=False))

    comp = compare_types(corr)
    comp.to_csv("output/uc7_comparison.csv", index=False)
    print("\nСравнение силы корреляции видов дохода (max |r|):")
    print(comp.to_string(index=False))

    top = compare_top_shares(corr)
    top.to_csv("output/uc7_top_shares_comparison.csv", index=False)
    print("\nСопоставимые пары «доля топ-1%» труда vs капитала:")
    print(top.to_string(index=False))

    plots = plot_correlations(corr)
    print(f"\nГрафики: {len(plots)} файлов -> output/uc7/")


if __name__ == "__main__":
    main()