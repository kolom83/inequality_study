"""
Perplexity-ресерч для UC-5: выбор показателя неравенства на основе литературы.

Критерии приёмки UC-5:
  - обзор не менее 5 научных статей/отчётов по измерению неравенства за 5 лет;
  - сравнительная таблица показателей (Джини, Тейл, P90/P10, топ-1%, Аткинсон);
  - обоснованный выбор 1-2 показателей;
  - фиксация вида неравенства (доходы vs богатство);
  - запись в glossary.md.

Результаты: uc5_research_results.json / .md.
"""

import json
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "PERPLEXITY_API_KEY не задан. Скопируйте .env.example в .env или задайте переменную окружения."
    )

from perplexity import Perplexity

MODEL = "sonar-pro"
client = Perplexity(API_KEY)

queries = [
    {
        "title": "Сравнение показателей неравенства",
        "query": (
            "Compare income inequality indicators: Gini coefficient, Theil index, P90/P10 ratio, "
            "top-1% income share, Atkinson index. What are the strengths and limitations of each "
            "for cross-country research on inequality over the past 5 years? Which measures are "
            "recommended by recent methodological literature (2020-2025)?"
        ),
    },
    {
        "title": "DINA Guidelines и распределительные национальные счета",
        "query": (
            "What do the DINA Guidelines 2025 (Distributional National Accounts) recommend as the "
            "preferred inequality measures? How should income and wealth inequality be defined and "
            "measured per World Inequality Lab methodology? Pre-tax vs post-tax income concepts."
        ),
    },
    {
        "title": "Выбор меры неравенства для анализа факторов",
        "query": (
            "In empirical research on the determinants of inequality (GDP, productivity, wealth "
            "concentration), which inequality indicator is most informative and why: Gini, top-1% "
            "share, top-10% share, or income share of bottom 50%? Recent academic evidence "
            "2020-2025 on sensitivity of different measures to changes at different parts of the "
            "income distribution."
        ),
    },
    {
        "title": "Неравенство доходов vs неравенство богатства",
        "query": (
            "Income inequality vs wealth inequality: which is more relevant for studying "
            "distributive processes and why? How strongly do income and wealth concentration "
            "co-move across countries? Recent research 2020-2025 on the relationship between "
            "income and wealth inequality."
        ),
    },
]

results = []

for item in queries:
    print(f"\n{'='*60}")
    print(f"Запрос: {item['title']}")
    print(f"{'='*60}")
    try:
        response = client.chat(item["query"], model=MODEL)
        answer = response["choices"][0]["message"]["content"]
        citations = response.get("citations", [])
        print(f"Ответ получен ({len(answer)} символов), источников: {len(citations)}")
        results.append(
            {
                "title": item["title"],
                "query": item["query"],
                "answer": answer,
                "citations": citations,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        print(f"Ошибка: {e}")
        results.append(
            {
                "title": item["title"],
                "query": item["query"],
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        )

output = {
    "generated": datetime.now().isoformat(),
    "model": MODEL,
    "purpose": "UC-5: выбор показателя неравенства по литературе",
    "results": results,
}

with open("uc5_research_results.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

with open("uc5_research_results.md", "w", encoding="utf-8") as f:
    f.write("# Результаты исследования UC-5: показатели неравенства\n\n")
    f.write(f"Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    f.write(f"Модель: {MODEL}\n\n---\n\n")
    for r in results:
        f.write(f"## {r['title']}\n\n")
        f.write(f"**Запрос:** {r['query']}\n\n")
        if "error" in r:
            f.write(f"**Ошибка:** {r['error']}\n\n")
        else:
            f.write(r["answer"] + "\n\n")
            if r["citations"]:
                f.write("### Источники\n\n")
                for i, c in enumerate(r["citations"], 1):
                    f.write(f"{i}. {c}\n")
                f.write("\n")
        f.write("---\n\n")

print("\n\nГотово! Результаты сохранены в:")
print("  - uc5_research_results.json")
print("  - uc5_research_results.md")
