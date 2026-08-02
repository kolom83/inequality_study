import pandas as pd
import pytest

from src.indicator_selection import (
    comparison_table,
    get_indicator,
    glossary_entry,
    recommended_selection,
)


class TestComparisonTable:
    def test_returns_dataframe_with_expected_columns(self):
        table = comparison_table()
        assert isinstance(table, pd.DataFrame)
        assert {"name", "code", "strengths", "limitations"}.issubset(table.columns)

    def test_covers_all_key_indicators(self):
        table = comparison_table()
        codes = set(table["code"])
        assert {"gini", "theil", "p90_p10", "top1_share", "atkinson"}.issubset(codes)


class TestGetIndicator:
    def test_known_indicator(self):
        row = get_indicator("top1_share")
        assert row["name"] == "Доля топ-1%"

    def test_unknown_raises(self):
        with pytest.raises(ValueError):
            get_indicator("unknown")


class TestRecommendedSelection:
    def test_selected_are_known(self):
        rec = recommended_selection()
        for code in rec["selected"]:
            assert get_indicator(code) is not None

    def test_income_concept_and_type_recorded(self):
        rec = recommended_selection()
        assert "pre-tax" in rec["income_concept"]
        assert "income" in rec["inequality_type"]


class TestGlossaryEntry:
    def test_entry_contains_selection_and_sources(self):
        entry = glossary_entry()
        assert "Доля дохода топ-1%" in entry
        assert "Джини" in entry
        assert "DINA Guidelines 2025" in entry
        assert "https://" in entry
