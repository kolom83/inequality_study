import numpy as np
import pandas as pd
import pytest

from src.income_type_analysis import (
    build_type_frame,
    compare_top_shares,
    compare_types,
    correlate_with_wealth,
    income_type_of,
    plot_correlations,
)

rng = np.random.default_rng(42)


def _make_df():
    rows = []
    countries = ["US", "FR"]
    years = list(range(1990, 2001))
    wealth_fn = lambda y: 0.20 + 0.006 * (y - 1990)
    vars_ = {
        # трудовой доход: слабая связь с богатством (шум)
        "sptlin_p99p100_992_j": lambda y: 0.07 + 0.0005 * (y - 1990) + 0.004 * rng.normal(),
        "spllin_p99p100_992_j": lambda y: 0.07 + 0.0005 * (y - 1990) + 0.004 * rng.normal(),
        # капитальный доход: почти детерминированная связь с богатством
        "sptkin_p99p100_992_j": lambda y: 0.05 + 0.7 * (wealth_fn(y) - 0.20),
        "spkkin_p99p100_992_j": lambda y: 0.05 + 0.7 * (wealth_fn(y) - 0.20),
        "shweal_p99p100_992_j": wealth_fn,
    }
    for c in countries:
        for y in years:
            for var, fn in vars_.items():
                rows.append(
                    {
                        "country": c,
                        "variable": var,
                        "year": y,
                        "value": fn(y),
                        "data_quality": 4.0,
                    }
                )
    return pd.DataFrame(rows)


class TestTypeClassification:
    def test_labor_variables(self):
        from src.income_type_analysis import labor_variables as lv

        assert "sptlin_p99p100_992_j" in lv()
        assert "sflinc_p99p100_996_i" in lv()
        assert "gflinc_p0p100_996_i" in lv()

    def test_capital_variables(self):
        from src.income_type_analysis import capital_variables as cv

        assert "sptkin_p99p100_992_j" in cv()
        assert "spkkin_p99p100_992_j" in cv()

    def test_income_type_of(self):
        assert income_type_of("sptlin_p99p100_992_j") == "labor"
        assert income_type_of("sptkin_p99p100_992_j") == "capital"
        with pytest.raises(ValueError):
            income_type_of("mgdpro_p0p100_999_i")


class TestBuildTypeFrame:
    def test_returns_wide_with_wealth(self):
        df = _make_df()
        wide = build_type_frame(df, "US")
        assert wide.index.name == "year"
        assert "shweal_p99p100_992_j" in wide.columns
        assert "sptlin_p99p100_992_j" in wide.columns
        assert "sptkin_p99p100_992_j" in wide.columns

    def test_raises_on_empty(self):
        df = _make_df()
        with pytest.raises(ValueError):
            build_type_frame(df, "XX")


class TestCorrelateWithWealth:
    def test_returns_correlations(self):
        df = _make_df()
        corr = correlate_with_wealth(df, country="US")
        assert "country" in corr.columns
        assert "income_type" in corr.columns
        assert "variable" in corr.columns
        assert "correlation" in corr.columns
        assert len(corr) == 4  # 2 трудовых + 2 капитальных

    def test_capital_correlates_stronger(self):
        df = _make_df()
        corr = correlate_with_wealth(df, country="US")
        cap = corr[corr.income_type == "capital"]["correlation"].abs().max()
        lab = corr[corr.income_type == "labor"]["correlation"].abs().max()
        assert cap > lab

    def test_all_countries(self):
        df = _make_df()
        corr = correlate_with_wealth(df)
        assert set(corr["country"]) == {"US", "FR"}


class TestCompareTypes:
    def test_stronger_is_capital(self):
        df = _make_df()
        corr = correlate_with_wealth(df)
        comp = compare_types(corr)
        assert "labor_max_abs_r" in comp.columns
        assert "capital_max_abs_r" in comp.columns
        assert set(comp["stronger_type"]) == {"capital"}

    def test_one_row_per_country(self):
        df = _make_df()
        comp = compare_types(correlate_with_wealth(df))
        assert len(comp) == 2


class TestCompareTopShares:
    def test_capital_top_share_stronger(self):
        df = _make_df()
        corr = correlate_with_wealth(df)
        top = compare_top_shares(corr)
        # капитальная топ-1% доля (sptkin/spkkin) коррелирует с шока strong
        assert set(top["stronger_type"]) == {"capital"}
        assert "labor_abs_r" in top.columns
        assert "capital_abs_r" in top.columns
        assert len(top) == 2  # US и FR


class TestPlotCorrelations:
    def test_plots_saved(self, tmp_path):
        df = _make_df()
        corr = correlate_with_wealth(df)
        paths = plot_correlations(corr, out_dir=str(tmp_path))
        assert len(paths) == 2
        assert all(p.endswith(".png") for p in paths)
