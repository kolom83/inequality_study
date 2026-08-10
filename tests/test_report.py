import os

import pandas as pd
import pytest

from src.report import build_report, export_pdf, uc5_section, uc7_section


def _write_csv(tmp_path, name, rows):
    path = os.path.join(tmp_path, name)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


class TestBuildReport:
    def test_creates_markdown_with_all_sections(self, tmp_path):
        uc2 = _write_csv(
            tmp_path,
            "uc2.csv",
            [
                {
                    "country": "FR",
                    "target": "gptinc_p0p100_992_j",
                    "variable": "mgdpro",
                    "correlation": 0.95,
                }
            ],
        )
        uc3 = _write_csv(
            tmp_path,
            "uc3.csv",
            [{"target": "gptinc_p0p100_992_j", "variable": "mgdpro", "correlation": 0.9}],
        )
        uc4 = _write_csv(
            tmp_path,
            "uc4.csv",
            [
                {
                    "target": "gptinc_p0p100_992_j",
                    "variable": "shweal",
                    "r_historical_abs": 0.75,
                    "r_cross_abs": 0.77,
                }
            ],
        )
        uc7_top = _write_csv(
            tmp_path,
            "uc7.csv",
            [
                {
                    "country": "US",
                    "labor_abs_r": 0.507,
                    "capital_abs_r": 0.941,
                    "stronger_type": "capital",
                }
            ],
        )
        path = build_report(
            output_dir=str(tmp_path),
            uc2_csv=uc2,
            uc3_csv=uc3,
            uc4_candidates_csv=uc4,
            uc7_top_csv=uc7_top,
        )
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert os.path.exists(path)
        for section in [
            "## 2. UC-2",
            "## 3. UC-3",
            "## 4. UC-4",
            "## 5. UC-5",
            "## 6. UC-7",
            "## 7. Финальный",
        ]:
            assert section in content
        assert "0.95" in content  # корреляции из CSV попадают в отчёт
        assert "0.941" in content  # корреляции капитального дохода из UC-7

    def test_missing_csv_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            build_report(output_dir=str(tmp_path), uc2_csv="nonexistent.csv")


class TestUc5Section:
    def test_contains_selected_indicators(self):
        section = uc5_section()
        assert "top1_share" in section
        assert "gini" in section
        assert "Джини" in section


class TestUc7Section:
    def test_contains_comparison(self):
        df = pd.DataFrame(
            [
                {
                    "country": "US",
                    "labor_abs_r": 0.507,
                    "capital_abs_r": 0.941,
                    "stronger_type": "capital",
                }
            ]
        )
        section = uc7_section(df)
        assert "0.941" in section
        assert "0.507" in section
        assert "UC-7" in section

    def test_empty_gives_message(self):
        import pandas as pd

        section = uc7_section(pd.DataFrame())
        assert "не найдено" in section


class TestExportPdf:
    def test_export_to_pdf(self, tmp_path):
        md = os.path.join(tmp_path, "report.md")
        with open(md, "w", encoding="utf-8") as f:
            f.write("# Тест отчёта\n\nРаздел текста.")
        try:
            pdf = export_pdf(md, output_dir=str(tmp_path))
        except (RuntimeError, FileNotFoundError):
            pytest.skip("pandoc/typst недоступны в окружении")
        assert os.path.exists(pdf)
        assert pdf.endswith(".pdf")
