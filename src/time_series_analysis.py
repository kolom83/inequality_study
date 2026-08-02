"""
<MODULE_CONTRACT>
  <ID>M-3</ID>
  <PURPOSE>Анализ динамики неравенства во времени по отдельным странам: временные ряды, корреляции Пирсона/Спирмена между социально-экономическими показателями и неравенством, оценка стабильности по периодам, тепловые карты корреляций.</PURPOSE>
  <SCOPE>Преобразует длинный DataFrame (из M-2) в широкий формат, считает корреляции для каждой страны отдельно, выделяет показатели с |r| > порога, строит тепловые карты корреляций по странам. НЕ сравнивает страны между собой (это UC-3/M-4).</SCOPE>
  <INPUTS>pandas DataFrame с колонками country, variable, year, value, data_quality.</INPUTS>
  <OUTPUTS>Словарь {country: (wide_df, corr_df)}; DataFrame топ-корреляций; DataFrame стабильности по периодам; файлы PNG тепловых карт.</OUTPUTS>
  <ERRORS>ValueError при пустом DataFrame или отсутствии целевой переменной; при недостаточном числе наблюдений корреляция = NaN.</ERRORS>
  <INVARIANTS>Корреляции в диапазоне [-1, 1]; NaN не заменяются значениями.</INVARIANTS>
  <DEPENDENCIES>M-2 (wid_client) — формат входных данных.</DEPENDENCIES>
</MODULE_CONTRACT>
"""

import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from src import config


# START: wide_frame
def build_wide_frame(df):
    """Преобразует длинный DataFrame в широкий: index=year, columns=variable, values=value."""
    wide = df.pivot_table(index="year", columns="variable", values="value", aggfunc="mean")
    wide = wide.sort_index()
    return wide


# END: wide_frame


# START: correlations
def correlation_matrix(wide, method="pearson"):
    """Считает корреляционную матрицу для всех переменных временного ряда."""
    return wide.corr(method=method)


def top_correlations(wide, target, k=5, threshold=None, method="pearson"):
    """Возвращает показатели с наибольшей |корреляцией| с целевой переменной.

    threshold: минимальный порог |r| (если задан, фильтрует результаты).
    """
    corr = wide.corr(method=method)
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


# END: correlations


# START: stability
def stability_by_period(wide, target, periods, method="pearson"):
    """Оценивает корреляцию целевой переменной с остальными в отдельных подпериодах."""
    rows = []
    for start, end in periods:
        sub = wide.loc[(wide.index >= start) & (wide.index <= end)]
        if target not in sub.columns or sub.shape[0] < 3:
            continue
        corr = sub.corr(method=method)
        for var in sub.columns:
            if var == target:
                continue
            rows.append(
                {
                    "period": f"{start}-{end}",
                    "variable": var,
                    "correlation": corr.loc[target, var],
                }
            )
    return pd.DataFrame(rows)


# END: stability


# START: per_country
def analyze_country_time_series(df, method="pearson"):
    """Для каждой страны строит широкий DataFrame и корреляционную матрицу.

    Возвращает dict: {country: {"wide": DataFrame, "corr": DataFrame}}.
    """
    result = {}
    for country, sub in df.groupby("country"):
        wide = build_wide_frame(sub)
        result[country] = {
            "wide": wide,
            "corr": wide.corr(method=method),
        }
    return result


# END: per_country


# START: target_variables
def inequality_targets():
    """Возвращает набор переменных-показателей неравенства из конфигурации."""
    return [
        v for v in config.VARIABLES if v.startswith(("sptinc_", "gptinc_", "sfiinc_", "shweal_"))
    ]


# END: target_variables


# START: heatmap
def plot_heatmaps(analysis, out_dir="output/heatmaps", dpi=150):
    """Строит тепловые карты корреляций для каждой страны и сохраняет PNG.

    analysis: результат analyze_country_time_series.
    Возвращает список сохранённых путей.
    """
    os.makedirs(out_dir, exist_ok=True)
    saved = []
    for country, data in analysis.items():
        corr = data["corr"]
        if corr.empty:
            continue
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=90, fontsize=7)
        ax.set_yticklabels(corr.columns, fontsize=7)
        ax.set_title(f"Корреляции показателей: {config.COUNTRIES.get(country, country)}")
        fig.colorbar(im, ax=ax, shrink=0.8, label="Pearson r")
        fig.tight_layout()
        path = os.path.join(out_dir, f"heatmap_{country}.png")
        fig.savefig(path, dpi=dpi)
        plt.close(fig)
        saved.append(path)
    return saved


# END: heatmap
