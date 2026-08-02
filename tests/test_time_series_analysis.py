import numpy as np
import pandas as pd
import pytest

from src.time_series_analysis import (
    analyze_country_time_series,
    build_wide_frame,
    correlation_matrix,
    plot_heatmaps,
    stability_by_period,
    top_correlations,
)


def _make_df():
    rows = []
    countries = ["FR", "US"]
    years = list(range(1990, 2001))
    vars_ = {
        "gptinc_p0p100_992_j": lambda y: 0.30 + 0.005 * (y - 1990),
        "mgdpro_p0p100_999_i": lambda y: 1000 + 30 * (y - 1990),
        "sptinc_p99p100_992_j": lambda y: 0.10 + 0.002 * (y - 1990),
        "npopul_p0p100_992_i": lambda y: 60_000 + 100 * (y - 1990),
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


class TestBuildWideFrame:
    def test_returns_pivot_country_variable_year(self):
        df = _make_df()
        wide = build_wide_frame(df)
        assert isinstance(wide, pd.DataFrame)
        assert "gptinc_p0p100_992_j" in wide.columns
        assert "mgdpro_p0p100_999_i" in wide.columns
        assert wide.index.name == "year"

    def test_per_country(self):
        df = _make_df()
        wide = build_wide_frame(df[df.country == "FR"])
        assert len(wide) == 11  # 1990..2000


class TestCorrelationMatrix:
    def test_perfect_correlation_detected(self):
        df = _make_df()
        wide = build_wide_frame(df[df.country == "FR"])
        corr = correlation_matrix(wide)
        r = corr.loc["gptinc_p0p100_992_j", "mgdpro_p0p100_999_i"]
        assert abs(r - 1.0) < 1e-6


class TestTopCorrelations:
    def test_returns_series_sorted_by_abs(self):
        df = _make_df()
        wide = build_wide_frame(df[df.country == "FR"])
        top = top_correlations(wide, target="gptinc_p0p100_992_j", k=2)
        assert len(top) == 2
        assert "variable" in top.columns
        assert "correlation" in top.columns

    def test_threshold_filtering(self):
        df = _make_df()
        wide = build_wide_frame(df[df.country == "FR"])
        top = top_correlations(
            wide, target="gptinc_p0p100_992_j", k=10, threshold=0.9
        )
        assert all(abs(v) >= 0.9 for v in top["correlation"])


class TestStabilityByPeriod:
    def test_period_split(self):
        df = _make_df()
        wide = build_wide_frame(df[df.country == "FR"])
        stab = stability_by_period(
            wide,
            target="gptinc_p0p100_992_j",
            periods=[(1990, 1995), (1996, 2000)],
        )
        assert "period" in stab.columns
        assert "correlation" in stab.columns
        assert set(stab["period"]) == {"1990-1995", "1996-2000"}


class TestPlotHeatmaps:
    def test_heatmaps_saved(self, tmp_path):
        df = _make_df()
        analysis = analyze_country_time_series(df)
        paths = plot_heatmaps(analysis, out_dir=str(tmp_path))
        assert len(paths) == 2  # FR и US
        assert all(path.endswith(".png") for path in paths)
