"""
<MODULE_CONTRACT>
  <ID>M-2</ID>
  <PURPOSE>Загрузка данных неравенства и социально-экономических показателей из API WID World с кэшированием ответов.</PURPOSE>
  <SCOPE>Выполняет GET-запросы к /countries-variables, парсит ответ в pandas DataFrame, кэширует ответы на диск. НЕ выполняет статистический анализ и НЕ строит графики.</SCOPE>
  <INPUTS>Код страны (ISO-2), код переменной WID вида indicator_percentile_age_pop; конфигурация из M-8 (страны, переменные, период).</INPUTS>
  <OUTPUTS>pandas DataFrame с колонками: country, variable, year, value, data_quality.</OUTPUTS>
  <ERRORS>RuntimeError при HTTP-ошибке API (403, 5xx); ValueError при пустом ответе.</ERRORS>
  <INVARIANTS>Значения долей в диапазоне [0, 1]; годы в пределах YEAR_FROM..YEAR_TO; колонки DataFrame фиксированы.</INVARIANTS>
  <DEPENDENCIES>M-8 (config).</DEPENDENCIES>
</MODULE_CONTRACT>
"""

import json
import os

import pandas as pd
import requests

from src import config


# START: wid_client_class
class WidClient:
    def __init__(self, api_url=None, cache_dir=None, year_from=None, year_to=None):
        self.api_url = api_url or config.API_URL
        self.year_from = year_from or config.YEAR_FROM
        self.year_to = year_to or config.YEAR_TO
        self.cache_dir = cache_dir or config.CACHE_DIR
        self.api_key = os.getenv("WID_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "WID_API_KEY не задан. Скопируйте .env.example в .env или задайте переменную окружения."
            )
        self._session = requests.Session()
        self._session.headers.update({"x-api-key": self.api_key})

    # START: fetch
    def fetch(self, country, variable):
        """Загружает один ряд (страна, переменная) с кэшированием."""
        cache_file = self._cache_path(country, variable)
        if os.path.exists(cache_file):
            with open(cache_file, encoding="utf-8") as f:
                payload = json.load(f)
        else:
            payload = self._request(country, variable)
            self._write_cache(cache_file, payload)
        return self._parse_response(country, variable, payload)

    def fetch_all(self):
        """Загружает все страны и переменные из конфигурации в единый DataFrame."""
        columns = ["country", "variable", "year", "value", "data_quality"]
        frames = []
        for country in config.COUNTRIES:
            for variable in config.VARIABLES:
                try:
                    df = self.fetch(country, variable)
                    if not df.empty:
                        frames.append(df)
                except RuntimeError as e:
                    print(f"[wid_client] {country} {variable}: {e}")
        if not frames:
            raise RuntimeError("Не удалось загрузить ни одного ряда из API WID.")
        result = pd.concat(frames, ignore_index=True)
        return result.reindex(columns=columns)

    # END: fetch

    # START: request
    def _request(self, country, variable):
        resp = self._session.get(
            f"{self.api_url}/countries-variables",
            params={
                "countries": country,
                "variables": variable,
                "years": "all",
            },
            timeout=60,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"API WID вернул статус {resp.status_code} для {country} {variable}: {resp.text[:200]}"
            )
        payload = resp.json()
        if variable not in payload or not payload[variable]:
            raise RuntimeError(f"Переменная {variable} не найдена в ответе для {country}.")
        return payload

    # END: request

    # START: parse
    def _parse_response(self, country, variable, payload):
        rows = []
        for entry in payload.get(variable, []):
            if country in entry:
                country_data = entry[country]
                for value_entry in country_data.get("values", []):
                    year = value_entry.get("y")
                    val = value_entry.get("v")
                    if year is None or val is None:
                        continue
                    if self.year_from <= year <= self.year_to:
                        rows.append(
                            {
                                "country": country,
                                "variable": variable,
                                "year": year,
                                "value": val,
                                "data_quality": value_entry.get("dq"),
                            }
                        )
                break
        return pd.DataFrame(rows)

    # END: parse

    # START: cache
    def _cache_path(self, country, variable):
        return os.path.join(self.cache_dir, f"{country}_{variable}.json")

    def _write_cache(self, cache_file, payload):
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)

    # END: cache
    # END: wid_client_class
