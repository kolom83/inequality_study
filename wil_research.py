import os
from dotenv import load_dotenv
from perplexity import Perplexity
import json
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not API_KEY:
    raise RuntimeError("PERPLEXITY_API_KEY не задан. Скопируйте .env.example в .env или задайте переменную окружения.")

MODEL = "sonar-pro"

client = Perplexity(API_KEY)

queries = [
    {
        "title": "Последние отчёты World Inequality Lab",
        "query": "What are the latest 2025-2026 reports and findings from World Inequality Lab (WID.world) on global income and wealth inequality?",
    },
    {
        "title": "Неравенство доходов и производительность труда",
        "query": "What is the relationship between income inequality and labor productivity? Recent research from World Inequality Lab, Piketty, and academic studies on how inequality affects productivity growth",
    },
    {
        "title": "Топ-1% доходов по странам",
        "query": "Latest data on top 1% income share across countries (US, Europe, Russia, China) from World Inequality Database - trends and comparisons 2020-2025",
    },
    {
        "title": "Неравенство и технологические изменения",
        "query": "How do technological change and AI affect income inequality and labor productivity? Research from World Inequality Lab and academic sources on skill-biased technical change and inequality",
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
        print(f"Ответ получен ({len(answer)} символов)")
        if citations:
            print(f"Источников: {len(citations)}")
        results.append({
            "title": item["title"],
            "query": item["query"],
            "answer": answer,
            "citations": citations,
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        print(f"Ошибка: {e}")
        results.append({
            "title": item["title"],
            "query": item["query"],
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })

output = {
    "generated": datetime.now().isoformat(),
    "model": MODEL,
    "results": results,
}

with open("wil_research_results.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

with open("wil_research_results.md", "w", encoding="utf-8") as f:
    f.write("# Результаты исследования World Inequality Lab\n\n")
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

print(f"\n\nГотово! Результаты сохранены в:")
print("  - wil_research_results.json")
print("  - wil_research_results.md")
