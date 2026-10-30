# Задание № 2. Анализ HTTP-запроса и ответа через DevTools

В отчёте разобраны загрузка формы входа, ошибочный и успешный вход, получение заявок с фильтром.

| Материал | Содержание |
|---|---|
| [Анализ_HTTP.docx](Анализ_HTTP.docx) | отчёт Word |
| [Анализ_HTTP.md](Анализ_HTTP.md) | тот же отчёт Markdown |
| [data/conference_login.har](data/conference_login.har) | повторный захват 30.10.2026, импортируется в Network |
| [data/captured_requests.json](data/captured_requests.json) | полные сведения четырёх запросов и ответов |
| `img/` | снимки исходного анализа DevTools 22.10.2026 |

Повторный захват выполняет [tools/collect_evidence.py](../tools/collect_evidence.py) через Chrome DevTools Protocol. В отчёте разделены результаты двух запусков и указаны версии исходников.
