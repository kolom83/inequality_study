import pandas as pd
import pytest

from src.analysis_comparison import (
    comparison_table,
    drop_outlier_correlation,
    historical_correlations,
    lagged_correlation,
    top_by_both,
)


def _make_time_df():
    rows = []
    years = list(range(1990, 2001))
    for c, base in [("FR", 0.30), ("US", 0.35), ("DE", 0.28), ("BR", 0.50)]:
        for y in years:
            rows.append(
                {
                    "country": c,
                    "variable": "gptinc_p0p100_992_j",
                    "year": y,
                    "value": base + 0.005 * (y - 1990),
                    "data_quality": 4.0,
                }
            )
            rows.append(
                {
                    "country": c,
                    "variable": "mgdpro_p0p100_999_i",
                    "year": y,
                    "value": 1000 + 30 * (y - 1990),
                    "data_quality": 4.0,
                }
            )
            rows.append(
                {
                    "country": c,
                    "variable": "npopul_p0p100_992_i",
                    "year": y,
                    "value": 60_000 + 100 * (y - 1990),
                    "data_quality": 4.0,
                }
            )
    return pd.DataFrame(rows)


def _make_cross_table():
    countries = {
        "FR": (0.30, 1800),
        "US": (0.35, 2100),
        "DE": (0.28, 1680),
        "BR": (0.50, 3000),
        "CN": (0.45, 2700),
        "IN": (0.48, 2880),
    }
    rows = []
    for c, (gini, gdp) in countries.items():
        rows.append({"country": c, "gptinc_p0p100_992_j": gini, "mgdpro_p0p100_999_i": gdp})
    return pd.DataFrame(rows).set_index("country")


class TestHistoricalCorrelations:
    def test_mean_across_countries(self):
        df = _make_time_df()
        hist = historical_correlations(df, target="gptinc_p0p100_992_j")
        assert "mean_correlation" in hist.columns
        assert "mean_abs_correlation" in hist.columns
        assert "n_countries" in hist.columns
        assert hist.loc[hist["variable"] == "mgdpro_p0p100_999_i", "n_countries"].iloc[0] == 4

    def test_missing_target_raises(self):
        df = _make_time_df()
        with pytest.raises(ValueError):
            historical_correlations(df, target="shweal_p99p100_992_j")


class TestComparisonTable:
    def test_columns_and_join(self):
        df = _make_time_df()
        cross = _make_cross_table()
        hist = historical_correlations(df, target="gptinc_p0p100_992_j")
        comp = comparison_table(hist, cross, target="gptinc_p0p100_992_j")
        assert {"r_historical", "r_cross", "r_cross_abs"}.issubset(comp.columns)
        assert len(comp) == 2  # mgdpro, npopul
        r = comp.loc[comp["variable"] == "mgdpro_p0p100_999_i", "r_historical"].iloc[0]
        assert abs(r - 1.0) < 1e-6

    def test_missing_target_raises(self):
        df = _make_time_df()
        cross = _make_cross_table()
        hist = historical_correlations(df, target="gptinc_p0p100_992_j")
        with pytest.raises(ValueError):
            comparison_table(hist, cross, target="shweal_p99p100_992_j")


class TestTopByBoth:
    def test_ranks_and_threshold(self):
        df = _make_time_df()
        cross = _make_cross_table()
        hist = historical_correlations(df, target="gptinc_p0p100_992_j")
        comp = comparison_table(hist, cross, target="gptinc_p0p100_992_j")
        top = top_by_both(comp, target="gptinc_p0p100_992_j", k=2, threshold=0.9)
        assert len(top) <= 2
        assert "mean_rank" in top.columns
        assert top.iloc[0]["variable"] == "mgdpro_p0p100_999_i"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            top_by_both(pd.DataFrame(), target="gptinc_p0p100_992_j")


class TestRobustness:
    def test_lagged_correlation(self):
        df = _make_time_df()
        r0 = lagged_correlation(df, "gptinc_p0p100_992_j", "mgdpro_p0p100_999_i", lag=0)
        r1 = lagged_correlation(df, "gptinc_p0p100_992_j", "mgdpro_p0p100_999_i", lag=1)
        assert abs(r0 - 1.0) < 1e-6
        assert abs(r1 - 1.0) < 1e-6  # линейный рост без шума устойчив к лагу

    def test_drop_outlier_restores_perfect(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        y = [1.0, 2.0, 3.0, 4.0, 5.0, 60.0]
        r_before = pd.Series(x).corr(pd.Series(y))
        r_after = drop_outlier_correlation(pd.Series(x), pd.Series(y))
        assert abs(r_after - 1.0) < 1e-6
        assert abs(r_before) < abs(r_after)
