# Журнал сессий

## Формат записи
Каждая сессия добавляет запись СВЕРХУ по шаблону.

---

## [2026-08-02] Сессия 1
- **Сделано:** Реализованы M-8 (config) и M-2 (wid_client) — UC-1. Изучен API WID (эндпоинты countries-variables, countries-available-variables, countries-variables-metadata; ключ публичный из пакета wid). Подтверждены 12 переменных: 6 показателей неравенства (топ-1%/10%, средние 40%, нижние 50%, Джини, топ-1% посленалоговый sfiinc) и 6 соц-экономических (ВВП mgdpro, нац. доход mnninc, средний доход aptinc, богатство ahweal/shweal, население npopul). Загружено 11 035 строк для 28 стран (1990-2024). Кэширование в .cache/wid. Данные в data_wid.csv.
- **В работе (не завершено):** Фаза P-2 — модуль M-3 (time_series_analysis) для UC-2.
- **Известные проблемы:** sfiinc (посленалоговый топ-1%) доступен только для ~9 стран (FR, US и др.); для остальных ряд пуст. Тейл-индекса в WID нет. Данные долей топ-1% для 1990-х по ряду стран имеют качество dq=1..3.
- **Следующий шаг:** Реализовать T-3 (модуль M-3 time_series_analysis) по UC-2.

---

## [2026-08-02] Сессия 0
- **Сделано:** Инициализация скелета проекта по GRACE. Созданы структура папок (docs/, docs/decisions/, src/, tests/), все XML-документы (requirements, technology, development-plan, verification-plan, knowledge-graph), session-log.md, glossary.md, ADR-000, AGENTS.md, rules.md, README.md, .gitignore. Установлены pytest и ruff. Ключи API (Perplexity, WID) вынесены в .env (gitignored), создан .env.example.
- **В работе (не завершено):** Фаза P-1 — модуль M-2 (wid_client) для загрузки данных из API WID World (UC-1).
- **Известные проблемы:** Модули M-2..M-7 пока не реализованы (только контракты в knowledge-graph.xml). Файл-пример M-1 (src/main.py) реализует только паттерн, не бизнес-логику.
- **Следующий шаг:** Реализовать T-2 (модуль M-2 wid_client) по UC-1.

---
