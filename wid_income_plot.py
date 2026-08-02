import os
from dotenv import load_dotenv
import requests
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

load_dotenv()

API_URL = "https://rfap9nitz6.execute-api.eu-west-1.amazonaws.com/prod"
API_KEY = os.getenv("WID_API_KEY")
if not API_KEY:
    raise RuntimeError("WID_API_KEY не задан. Скопируйте .env.example в .env или задайте переменную окружения.")
VARIABLE = "sptinc_p99p100_992_j"  # share, pre-tax national income, top 1%, adults, equal-split
YEAR_FROM = 1990
YEAR_TO = 2020

def fetch_top1_share(country_code):
    params = {
        "countries": country_code,
        "variables": VARIABLE,
    }
    headers = {"x-api-key": API_KEY}
    resp = requests.get(
        f"{API_URL}/countries-variables",
        params=params,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    items = data.get(VARIABLE, [])
    country_data = {}
    for item in items:
        if country_code in item:
            country_data = item[country_code]
            break
    values = country_data.get("values", [])
    result = {}
    for entry in values:
        year = entry.get("y")
        val = entry.get("v")
        if year is None or val is None:
            continue
        if YEAR_FROM <= year <= YEAR_TO:
            result[year] = val * 100
    return result

countries = {
    "RU": "Россия",
    "DE": "Германия",
    "US": "США",
}

series = {}
for code, label in countries.items():
    print(f"Загрузка данных для {label}...")
    series[code] = fetch_top1_share(code)

plt.style.use("seaborn-v0_8-whitegrid")
fig, ax = plt.subplots(figsize=(10, 5.5))

colors = {"RU": "#e74c3c", "DE": "#f1c40f", "US": "#3498db"}

for code, label in countries.items():
    years = sorted(series[code].keys())
    vals = [series[code][y] for y in years]
    ax.plot(years, vals, label=label, color=colors[code], linewidth=2.2, marker="o", markersize=3.5)

ax.set_title("Доля доходов топ-1% (источник: WID)", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Год", fontsize=11)
ax.set_ylabel("Доля в национальном доходе, %", fontsize=11)
ax.legend(fontsize=10, framealpha=0.9)
ax.set_xlim(YEAR_FROM, YEAR_TO)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
ax.grid(True, alpha=0.35)
fig.tight_layout()

plt.savefig("wid_top1_income.png", dpi=150)
print("График сохранён в wid_top1_income.png")
