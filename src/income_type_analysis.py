"""
<MODULE_CONTRACT>
  <ID>M-9</ID>
  <PURPOSE>Проверка гипотезы о механизме связи концентрации богатства (доля топ-1%) с неравенством доходов: сравнение силы корреляции доли богатства с неравенством трудового и капитального дохода по отдельности.</PURPOSE>
  <SCOPE>Разделяет показатели дохода на трудовые (sptlin, spllin, sflinc, gflinc) и капитальные (sptkin, spkkin), строит временные ряды по странам, считает корреляции каждой меры неравенства вида дохода с shweal_p99p100 за пересекающийся период, сравнивает силу корреляции видов. НЕ строит кросс-страновые корреляции (данных недостаточно: только US, FR, TH).</SCOPE>
  <INPUTS>pandas DataFrame (длинный формат) с колонками country, variable, year, value, data_quality.</INPUTS>
  <OUTPUTS>DataFrame корреляций: country, income_type (labor/capital), variable, correlation; DataFrame сравнения силы (max |r| по каждому виду на страну); файлы PNG сравнения.</OUTPUTS>
  <ERRORS>ValueError при пустом DataFrame, отсутствии shweal_p99p100_992_j или отсутствии переменных видов дохода; при недостаточном числе наблюдений корреляция = NaN.</ERRORS>
  <INVARIANTS>Корреляции в диапазоне [-1, 1]; NaN не заменяются; трудовые и капитальные переменные не смешиваются.</INVARIANTS>
  <DEPENDENCIES>M-2 (wid_client) и M-8 (config) — формат данных и набор переменных.</DEPENDENCIES>
</MODULE_CONTRACT>
"""

import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from src import config


# START: type_classification
def labor_variables():
    """Переменные неравенства трудового дохода."""
    return [
        v
        for v in config.INCOME_TYPE_VARIABLES
        if v.startswith(("sptlin_", "spllin_", "sflinc_", "gflinc_"))
    ]


def capital_variables():
    """Переменные неравенства капитального дохода."""
    return [v for v in config.INCOME_TYPE_VARIABLES if v.startswith(("sptkin_", "spkkin_"))]


def income_type_of(variable):
    """Возвращает 'labor' или 'capital' для переменной вида дохода."""
    if variable in labor_variables():
        return "labor"
    if variable in capital_variables():
        return "capital"
    raise ValueError(f"Переменная {variable} не относится к виду дохода")


# END: type_classification


# START: wide_frame
def build_type_frame(df, country):
    """Строит широкую таблицу по годам для страны: только переменные видов дохода + shweal.

    Возвращает DataFrame index=year, columns=variable.
    """
    sub = df[(df["country"] == country) & (df["variable"].isin(config.INCOME_TYPE_VARIABLES))]
    sub = pd.concat(
        [
            sub,
            df[(df["country"] == country) & (df["variable"] == "shweal_p99p100_992_j")],
        ]
    )
    if sub.empty:
        raise ValueError(f"Нет данных видов дохода для {country}")
    wide = sub.pivot_table(index="year", columns="variable", values="value", aggfunc="mean")
    return wide.sort_index()


# END: wide_frame


# START: correlations
def correlate_with_wealth(df, country=None, method="pearson"):
    """Коррелирует каждую меру неравенства вида дохода с долей богатства топ-1%.

    country: None — все страны из данных; иначе один код страны.
    Возвращает DataFrame: country, income_type, variable, correlation.
    """
    countries = [country] if country else sorted(df["country"].unique())
    rows = []
    for c in countries:
        wide = build_type_frame(df, c)
        if "shweal_p99p100_992_j" not in wide.columns:
            continue
        # ограничиваем период пересечением: годы, где есть shweal и хоть одна
        # переменная вида дохода
        valid = wide.dropna(how="all")
        target = valid["shweal_p99p100_992_j"]
        for var in valid.columns:
            if var == "shweal_p99p100_992_j":
                continue
            pair = pd.concat([valid[var], target], axis=1).dropna()
            if pair.shape[0] < 3:
                continue
            r = pair.corr(method=method).iloc[0, 1]
            rows.append(
                {
                    "country": c,
                    "income_type": income_type_of(var),
                    "variable": var,
                    "correlation": r,
                }
            )
    if not rows:
        raise ValueError("Не найдено пар для корреляций с shweal_p99p100_992_j")
    return pd.DataFrame(rows)


# END: correlations


# START: comparison
def compare_types(corr_df):
    """Сравнивает силу корреляции трудового vs капитального дохода с концентрацией богатства.

    Для каждой страны берёт макс |r| по каждому виду дохода.
    Возвращает DataFrame: country, labor_max_abs_r, capital_max_abs_r, stronger_type.
    """
    rows = []
    for country, group in corr_df.groupby("country"):
        row = {"country": country}
        for itype in ["labor", "capital"]:
            sub = group[group["income_type"] == itype]
            row[f"{itype}_max_abs_r"] = sub["correlation"].abs().max() if len(sub) else None
        if row["labor_max_abs_r"] is None or row["capital_max_abs_r"] is None:
            row["stronger_type"] = None
        else:
            row["stronger_type"] = (
                "labor" if row["labor_max_abs_r"] > row["capital_max_abs_r"] else "capital"
            )
        rows.append(row)
    return pd.DataFrame(rows)


def top_share_pair(country):
    """Сопоставимая пара «доля топ-1%» для сравнения: (labor_var, capital_var).

    US/TH: sptlin/sptkin (ранжирование по общему доходу).
    FR: spllin/spkkin (по собственному виду дохода).
    """
    if country == "FR":
        return "spllin_p99p100_992_j", "spkkin_p99p100_992_j"
    return "sptlin_p99p100_992_j", "sptkin_p99p100_992_j"


def compare_top_shares(corr_df):
    """Сравнение корреляции ДОЛИ ТОП-1% трудового и капитального дохода с shweal.

    Гипотеза UC-7: капитальный доход (рента/процент) объясняет сильную связь
    концентрации богатства с неравенством доходов => корреляция капитальной
    топ-1% доли должна быть выше трудовой.
    Возвращает DataFrame: country, labor_var, labor_r, capital_var, capital_r, stronger_type.
    """
    rows = []
    for country, group in corr_df.groupby("country"):
        labor_var, capital_var = top_share_pair(country)
        lab = group[group["variable"] == labor_var]
        cap = group[group["variable"] == capital_var]
        if lab.empty or cap.empty:
            continue
        lr = lab["correlation"].iloc[0]
        cr = cap["correlation"].iloc[0]
        rows.append(
            {
                "country": country,
                "labor_var": labor_var,
                "labor_abs_r": abs(lr),
                "capital_var": capital_var,
                "capital_abs_r": abs(cr),
                "stronger_type": "labor" if abs(lr) > abs(cr) else "capital",
            }
        )
    return pd.DataFrame(rows)


def plot_correlations(corr_df, out_dir="output/uc7", dpi=150):
    """Горизонтальные бары корреляций видов дохода с shweal по странам."""
    os.makedirs(out_dir, exist_ok=True)
    saved = []
    for country, group in corr_df.groupby("country"):
        fig, ax = plt.subplots(figsize=(8, max(1.2 * len(group), 3)))
        colors = ["#4c72b0" if t == "labor" else "#dd8452" for t in group["income_type"]]
        labels = [
            f"[{t}] {config.INCOME_TYPE_VARIABLES.get(v, v)}"
            for t, v in zip(group["income_type"], group["variable"])
        ]
        y_pos = range(len(group))
        ax.barh(y_pos, group["correlation"], color=colors)
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(labels, fontsize=7)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_xlabel("r (Pearson) с долей богатства топ-1%")
        ax.set_title(
            f"Корреляция неравенства видов дохода с shweal: {config.COUNTRIES.get(country, country)}"
        )
        ax.set_xlim(-1, 1)
        fig.tight_layout()
        path = os.path.join(out_dir, f"corr_types_{country}.png")
        fig.savefig(path, dpi=dpi)
        plt.close(fig)
        saved.append(path)
    return saved


# END: comparison
