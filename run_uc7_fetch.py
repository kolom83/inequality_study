"""
Догрузка данных UC-7 (виды дохода: трудовой/капитальный).

Читает data_wid.csv, догружает для US, FR, TH переменные трудового/капитального
дохода (INCOME_TYPE_VARIABLES) и базовые показатели для TH (которого нет в
data_wid.csv). Результат: output/uc7_data.csv.
"""

import os

from dotenv import load_dotenv

load_dotenv("D:/project/inequality_study/.env")
import pandas as pd

from src import config
from src.wid_client import WidClient

# Базовые переменные, которые могут отсутствовать для TH в data_wid.csv
BASE_VARIABLES = {
    "sptinc_p99p100_992_j": "Доля дохода топ-1%",
    "gptinc_p0p100_992_j": "Индекс Джини (pre-tax)",
    "shweal_p99p100_992_j": "Доля богатства топ-1%",
}


def main():
    os.makedirs("output", exist_ok=True)
    df = pd.read_csv("data_wid.csv")
    client = WidClient()

    frames = [df]
    for country in config.INCOME_TYPE_COUNTRIES:
        for variable in config.INCOME_TYPE_VARIABLES:
            try:
                sub = client.fetch(country, variable)
                if not sub.empty:
                    frames.append(sub)
            except RuntimeError as e:
                print(f"[uc7_fetch] {country} {variable}: {e}")
        if country not in df["country"].values:
            for variable in BASE_VARIABLES:
                try:
                    sub = client.fetch(country, variable)
                    if not sub.empty:
                        frames.append(sub)
                except RuntimeError as e:
                    print(f"[uc7_fetch] {country} {variable}: {e}")

    result = pd.concat(frames, ignore_index=True)
    result.to_csv("output/uc7_data.csv", index=False)
    print(f"Сохранено {len(result)} строк в output/uc7_data.csv")
    cover = result[result["country"].isin(config.INCOME_TYPE_COUNTRIES)]
    print(cover.groupby(["country", "variable"]).size().reset_index(name="n").to_string())


if __name__ == "__main__":
    main()
