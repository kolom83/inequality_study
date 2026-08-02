import pandas as pd
import pytest

from src.cross_section_analysis import (
    build_cross_section,
    cross_section_correlations,
    plot_scatter,
    robustness_by_group,
    top_cross_correlations,
)


def _make_cross_df():
    """Кросс-секционные данные: 6 стран, неравенство и соц-экон показатели за 2024."""
    rows = []
    countries = {
        "US": (0.10, 2000),
        "FR": (0.09, 1800),
        "DE": (0.08, 1600),
        "BR": (0.07, 1400),
        "CN": (0.06, 1200),
        "IN": (0.05, 1000),
    }
    for c, (gini, gdp) in countries.items():
        rows.append({"country": c, "variable": "gptinc_p0p100_992_j", "year": 2024, "value": gini})
        rows.append(
            {"country": c, "variable": "mgdpro_p0p100_999_i", "year": 2024, "value": gdp}
        )
        rows.append(
            {"country": c, "variable": "npopul_p0p100_992_i", "year": 2024, "value": 1000}
        )
    return pd.DataFrame(rows)


class TestBuildCrossSection:
    def test_shape_and_index(self):
        df = _make_cross_df()
        table = build_cross_section(df, reference_year=2024)
        assert isinstance(table, pd.DataFrame)
        assert list(table.index) == ["BR", "CN", "DE", "FR", "IN", "US"]
        assert "gptinc_p0p100_992_j" in table.columns

    def test_falls_back_to_latest_year(self):
        df = _make_cross_df()
        table = build_cross_section(df, reference_year=1999)
        assert table.index.name == "country"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            build_cross_section(pd.DataFrame())


class TestCrossCorrelations:
    def test_perfect_correlation_detected(self):
        df = _make_cross_df()
        table = build_cross_section(df, reference_year=2024)
        corr = cross_section_correlations(table)
        r = corr.loc["gptinc_p0p100_992_j", "mgdpro_p0p100_999_i"]
        assert abs(r - 1.0) < 1e-6

    def test_top_with_threshold(self):
        df = _make_cross_df()
        table = build_cross_section(df, reference_year=2024)
        top = top_cross_correlations(
            table, target="gptinc_p0p100_992_j", k=10, threshold=0.9
        )
        assert len(top) == 1
        assert top.iloc[0]["variable"] == "mgdpro_p0p100_999_i"

    def test_missing_target_raises(self):
        df = _make_cross_df()
        table = build_cross_section(df, reference_year=2024)
        with pytest.raises(ValueError):
            top_cross_correlations(table, target="shweal_p99p100_992_j")


class TestRobustnessByGroup:
    def test_group_split(self):
        df = _make_cross_df()
        table = build_cross_section(df, reference_year=2024)
        groups = {"developed": ["US", "FR", "DE"], "developing": ["BR", "CN", "IN"]}
        rob = robustness_by_group(table, groups)
        assert "country_group" in rob.columns
        assert "correlation" in rob.columns
        assert set(rob["country_group"]) == {"developed", "developing"}

    def test_insufficient_group_skipped(self):
        df = _make_cross_df()
        table = build_cross_section(df, reference_year=2024)
        groups = {"developed": ["US"], "developing": ["BR", "CN", "IN"]}
        rob = robustness_by_group(table, groups)
        assert set(rob["country_group"]) == {"developing"}


class TestPlotScatter:
    def test_scatter_saved(self, tmp_path):
        df = _make_cross_df()
        table = build_cross_section(df, reference_year=2024)
        paths = plot_scatter(table, target="gptinc_p0p100_992_j", out_dir=str(tmp_path))
        assert len(paths) == 2
        assert all(p.endswith(".png") for p in paths)
