"""
<MODULE_CONTRACT>
  <ID>M-8</ID>
  <PURPOSE>Единое место конфигурации проекта: список стран, переменных WID, аналитический период, параметры API и кэша.</PURPOSE>
  <SCOPE>Содержит только константы и структуры данных. НЕ выполняет запросы к API и НЕ содержит бизнес-логику.</SCOPE>
  <INPUTS>Нет.</INPUTS>
  <OUTPUTS>Набор констант: COUNTRIES, VARIABLES, YEAR_FROM, YEAR_TO, API_URL, CACHE_DIR.</OUTPUTS>
  <ERRORS>Нет.</ERRORS>
  <INVARIANTS>Все коды переменных WID валидны и проверены через countries-available-variables.</INVARIANTS>
  <DEPENDENCIES>Нет.</DEPENDENCIES>
</MODULE_CONTRACT>
"""

# START: api_config
API_URL = "https://rfap9nitz6.execute-api.eu-west-1.amazonaws.com/prod"
CACHE_DIR = ".cache/wid"
# END: api_config

# START: analysis_period
YEAR_FROM = 1990
YEAR_TO = 2025
# END: analysis_period

# START: countries
COUNTRIES = {
    "US": "США",
    "CA": "Канада",
    "BR": "Бразилия",
    "MX": "Мексика",
    "AR": "Аргентина",
    "CL": "Чили",
    "CO": "Колумбия",
    "DE": "Германия",
    "FR": "Франция",
    "GB": "Великобритания",
    "IT": "Италия",
    "ES": "Испания",
    "SE": "Швеция",
    "PL": "Польша",
    "CZ": "Чехия",
    "RU": "Россия",
    "TR": "Турция",
    "CN": "Китай",
    "JP": "Япония",
    "IN": "Индия",
    "KR": "Южная Корея",
    "ID": "Индонезия",
    "ZA": "ЮАР",
    "NG": "Нигерия",
    "KE": "Кения",
    "EG": "Египет",
    "SA": "Саудовская Аравия",
    "AU": "Австралия",
}
# END: countries

# START: variables
VARIABLES = {
    # Показатели неравенства
    "sptinc_p99p100_992_j": "Доля дохода топ-1%",
    "sptinc_p90p100_992_j": "Доля дохода топ-10%",
    "sptinc_p50p90_992_j": "Доля дохода средних 40%",
    "sptinc_p0p50_992_j": "Доля дохода нижних 50%",
    "gptinc_p0p100_992_j": "Индекс Джини (pre-tax)",
    "sfiinc_p99p100_992_j": "Доля топ-1% после налогов (fiscal income)",
    # Социально-экономические показатели
    "mgdpro_p0p100_999_i": "ВВП (национальная экономика)",
    "mnninc_p0p100_999_i": "Национальный доход на взрослого",
    "aptinc_p0p100_992_j": "Средний доход на взрослого",
    "ahweal_p0p100_992_j": "Среднее богатство на взрослого",
    "shweal_p99p100_992_j": "Доля богатства топ-1%",
    "npopul_p0p100_992_i": "Численность взрослого населения",
}
# END: variables

# START: correlations
CORRELATION_THRESHOLD = 0.7
# END: correlations
