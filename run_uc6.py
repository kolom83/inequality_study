"""
Генерация итогового исследовательского отчёта (UC-6).

Собирает результаты UC-2..UC-5 в docs/report.md и экспортирует в docs/report.pdf
через pandoc + typst.
"""

from src.report import build_report, export_pdf


def main():
    md = build_report()
    print(f"Отчёт Markdown: {md}")
    pdf = export_pdf(md)
    print(f"Отчёт PDF: {pdf}")


if __name__ == "__main__":
    main()
