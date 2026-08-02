"""
<MODULE_CONTRACT>
  <ID>M-5</ID>
  <PURPOSE>Сопоставление результатов исторического (UC-2/M-3) и кросс-странового (UC-3/M-4) анализа: сводная таблица корреляций по подходам, выделение показателей, входящих в топ-N по обоим подходам, дополнительная проверка устойчивости (временной лаг, исключение выбросов).</PURPOSE>
  <SCOPE>Считает среднюю историческую корреляцию по странам, объединяет с кросс-страновыми корреляциями, выделяет кандидатов в топ-N по обоим подходам, проводит проверку устойчивости для отобранных показателей. НЕ генерирует итоговый отчёт (это UC-6/M-7) и НЕ выбирает показатель неравенства по литературе (это UC-5/M-6).</SCOPE>
  <INPUTS>pandas DataFrame с колонками country, variable, year, value, data_quality; кросс-секционная таблица (index=country, columns=variable); список кандидатов.</INPUTS>
  <OUTPUTS>Сводная таблица корреляций по двум подходам; DataFrame топ-кандидатов; DataFrame устойчивости с лагами и исключением выбросов.</OUTPUTS>
  <ERRORS>ValueError при пустых входных данных; при отсутствии переменной в одном из подходов корреляция = NaN.</ERRORS>
  <INVARIANTS>Корреляции в диапазоне [-1, 1]; средние считаются по странам, для которых есть данные.</INVARIANTS>
  <DEPENDENCIES>M-3 (time_series_analysis) — исторические корреляции; M-4 (cross_section_analysis) — кросс-страновые корреляции.</DEPENDENCIES>
</MODULE_CONTRACT>
"""

import numpy as np
import pandas as pd

from src.time_series_analysis import build_wide_frame


# START: historical_summary
def historical_correlations(df, target, method="pearson"):
    """Средняя корреляция целевой переменной с остальными по всем странам.

    Возвращает DataFrame: variable, mean_correlation (среднее со знаком),
    mean_abs_correlation, n_countries.
    """
    pairs = []
    for _, sub in df.groupby("country"):
        wide = build_wide_frame(sub)
        if target not in wide.columns:
            continue
        corr = wide.corr(method=method)
        for var in corr.index:
            if var == target:
                continue
            value = corr.loc[target, var]
            if pd.notna(value):
                pairs.append(
                    {"variable": var, "country": sub["country"].iloc[0], "correlation": value}
                )
    if not pairs:
        raise ValueError(f"Целевая переменная {target} отсутствует в данных")
    pairs_df = pd.DataFrame(pairs)
    return (
        pairs_df.groupby("variable")["correlation"]
        .agg(
            mean_correlation="mean",
            mean_abs_correlation=lambda s: s.abs().mean(),
            n_countries="count",
        )
        .reset_index()
    )


# END: historical_summary


# START: comparison
def comparison_table(hist_df, cross_table, target, method="pearson"):
    """Объединяет средние исторические корреляции с кросс-страновыми.

    cross_table: кросс-секционная таблица (index=country, columns=variable).
    Для каждой переменной считается r_historical (среднее по странам, со знаком)
    и r_cross (кросс-страновое).
    """
    if cross_table.shape[0] < 3 or target not in cross_table.columns:
        raise ValueError(f"Недостаточно стран или отсутствует {target} в кросс-секции")
    cross_corr = cross_table.corr(method=method)
    rows = []
    for _, row in hist_df.iterrows():
        var = row["variable"]
        r_cross = cross_corr.loc[target, var] if var in cross_corr.columns else float("nan")
        rows.append(
            {
                "variable": var,
                "r_historical": row["mean_correlation"],
                "r_historical_abs": row["mean_abs_correlation"],
                "n_countries": row["n_countries"],
                "r_cross": r_cross,
                "r_cross_abs": abs(r_cross) if pd.notna(r_cross) else float("nan"),
            }
        )
    return pd.DataFrame(rows)


# END: comparison


# START: top_both
def top_by_both(comparison, target, k=5, threshold=None):
    """Показатели, входящие в топ-k по |корреляции| в обоих подходах.

    Возвращает DataFrame сравнения, отсортированный по среднему рангу.
    """
    if comparison.empty:
        raise ValueError("Пустая таблица сравнения")
    result = comparison.copy()
    result["rank_h"] = result["r_historical_abs"].rank(ascending=False, method="min")
    result["rank_c"] = result["r_cross_abs"].rank(ascending=False, method="min")
    result["mean_rank"] = (result["rank_h"] + result["rank_c"]) / 2
    result = result.sort_values("mean_rank", na_position="last")
    if threshold is not None:
        result = result[
            (result["r_historical_abs"] >= threshold) & (result["r_cross_abs"] >= threshold)
        ]
    return result.head(k)


# END: top_both


# START: robustness
def lagged_correlation(df, target, variable, lag=1, method="pearson"):
    """Корреляция между целевой переменной и переменной со сдвигом во времени.

    lag>0: переменная сдвинута в прошлое (сравниваем target[t] с variable[t-lag]);
    lag<0: переменная опережает (variable[t] сравнивается с target[t+lag]).
    Возвращает среднее по странам.
    """
    values = []
    for _, sub in df.groupby("country"):
        wide = build_wide_frame(sub)
        if target not in wide.columns or variable not in wide.columns:
            continue
        t = wide[target]
        v = wide[variable]
        if lag > 0:
            corr = t.corr(v.shift(lag), method=method)
        else:
            corr = t.shift(-lag).corr(v, method=method)
        if pd.notna(corr):
            values.append(corr)
    if not values:
        return float("nan")
    return float(pd.Series(values).mean())


def drop_outlier_correlation(series_x, series_y, method="pearson"):
    """Корреляция после исключения наиболее удалённой точки (max |остаток| OLS)."""
    df = pd.DataFrame({"x": series_x, "y": series_y}).dropna()
    if df.shape[0] < 4:
        return float("nan")
    x, y = df["x"].values, df["y"].values
    slope, intercept = np.polyfit(x, y, 1)
    resid = y - (slope * x + intercept)
    idx = np.argmax(np.abs(resid))
    xr = np.delete(x, idx)
    yr = np.delete(y, idx)
    if xr.shape[0] < 4:
        return float("nan")
    return float(pd.Series(xr).corr(pd.Series(yr), method=method))


# END: robustness
