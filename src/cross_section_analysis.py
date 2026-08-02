"""
<MODULE_CONTRACT>
  <ID>M-4</ID>
  <PURPOSE>Кросс-страновый анализ на актуальных данных: построение кросс-секционной таблицы по странам, корреляции Пирсона/Спирмена между социально-экономическими показателями и неравенством, оценка робастности по регионам, scatter plots.</PURPOSE>
  <SCOPE>Собирает последние доступные значения по странам за опорный год, считает кросс-страновые корреляции, выделяет показатели с |r| > порога, проверяет робастность на подгруппах стран (развитые/развивающиеся), строит scatter plots. НЕ анализирует временные ряды (это UC-2/M-3) и НЕ сравнивает результаты подходов (это UC-4/M-5).</SCOPE>
  <INPUTS>pandas DataFrame с колонками country, variable, year, value, data_quality.</INPUTS>
  <OUTPUTS>Кросс-секционная таблица (DataFrame); DataFrame кросс-страновых корреляций; DataFrame робастности по регионам; файлы PNG scatter plots.</OUTPUTS>
  <ERRORS>ValueError при пустом DataFrame, отсутствии опорного года в данных или отсутствии целевой переменной; при недостаточном числе стран корреляция = NaN.</ERRORS>
  <INVARIANTS>Корреляции в диапазоне [-1, 1]; NaN не заменяются значениями; опорный год не старше максимума в данных.</INVARIANTS>
  <DEPENDENCIES>M-2 (wid_client) — формат входных данных; M-8 (config) — список стран и переменных.</DEPENDENCIES>
</MODULE_CONTRACT>
"""

import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from src import config
from src.time_series_analysis import inequality_targets


# START: cross_section_table
def build_cross_section(df, reference_year=None):
    """Собирает кросс-секционную таблицу: index=country, columns=variable.

    Если reference_year не задан или отсутствует в данных, берётся последний год.
    """
    if df.empty:
        raise ValueError("Пустой DataFrame")
    if reference_year is None:
        reference_year = df["year"].max()
    if reference_year not in df["year"].values:
        reference_year = df["year"].max()
    sub = df[df["year"] == reference_year]
    table = sub.pivot_table(index="country", columns="variable", values="value", aggfunc="mean")
    return table


# END: cross_section_table


# START: cross_correlations
def cross_section_correlations(table, method="pearson"):
    """Кросс-страновые корреляции между каждой парой переменных."""
    return table.corr(method=method)


def top_cross_correlations(table, target, k=5, threshold=None, method="pearson"):
    """Возвращает показатели с наибольшей |корреляцией| с целевой переменной на кросс-страновой выборке."""
    corr = cross_section_correlations(table, method=method)
    if target not in corr.columns:
        raise ValueError(f"Целевая переменная {target} отсутствует в данных")
    series = corr[target].drop(labels=[target]).dropna()
    ranked = series.reindex(series.abs().sort_values(ascending=False).index)
    result = pd.DataFrame({"variable": ranked.index, "correlation": ranked.values}).reset_index(
        drop=True
    )
    if threshold is not None:
        result = result[result["correlation"].abs() >= threshold]
    return result.head(k)


# END: cross_correlations


# START: regions
def robustness_by_group(table, groups, method="pearson"):
    """Считает кросс-страновые корреляции отдельно по подгруппам стран.

    groups: dict {group_name: [country_codes]}.
    Возвращает длинный DataFrame: country_group, target, variable, correlation.
    """
    rows = []
    for group, countries in groups.items():
        sub = table.loc[[c for c in countries if c in table.index]]
        if sub.shape[0] < 3:
            continue
        corr = sub.corr(method=method)
        for target in inequality_targets():
            if target not in corr.columns:
                continue
            for var in corr.index:
                if var == target:
                    continue
                rows.append(
                    {
                        "country_group": group,
                        "target": target,
                        "variable": var,
                        "correlation": corr.loc[target, var],
                    }
                )
    return pd.DataFrame(rows)


# END: regions


# START: scatter_plots
def plot_scatter(table, target, out_dir="output/scatter", dpi=150):
    """Строит scatter plot зависимости целевой переменной от каждого другого показателя.

    Возвращает список сохранённых путей.
    """
    os.makedirs(out_dir, exist_ok=True)
    saved = []
    for var in table.columns:
        if var == target:
            continue
        sub = table[[var, target]].dropna()
        if sub.shape[0] < 5:
            continue
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(sub[var], sub[target], alpha=0.8)
        for _, row in sub.iterrows():
            ax.annotate(row.name, (row[var], row[target]), fontsize=6, alpha=0.7)
        ax.set_xlabel(config.VARIABLES.get(var, var))
        ax.set_ylabel(config.VARIABLES.get(target, target))
        ax.set_title(f"{config.VARIABLES.get(target, target)} vs {config.VARIABLES.get(var, var)}")
        fig.tight_layout()
        short = var.replace("_992_j", "").replace("_999_i", "").replace("_992_i", "")
        path = os.path.join(out_dir, f"scatter_{target.replace('_992_j', '')}_vs_{short}.png")
        fig.savefig(path, dpi=dpi)
        plt.close(fig)
        saved.append(path)
    return saved


# END: scatter_plots
