# Longitudinal Health Analytics — 4.7 Years of Samsung Health Data

Аналіз 4.7 року безперервних даних Samsung Health (кроки, сон, пульс, тренування) —
від щоденних патернів до довгострокових трендів форми. Частина DS-портфоліо та
аналітичне ядро персонального асистента JARVIS.

[![nbviewer](https://img.shields.io/badge/render-nbviewer-orange)](https://nbviewer.org/github/VictorReal/health_analytics/blob/main/health_longitudinal_analysis.ipynb)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/VictorReal/health_analytics/blob/main/health_longitudinal_analysis.ipynb)

> GitHub інколи не рендерить великі нотатники з графіками — **відкрий через nbviewer** (кнопка вище),
> щоб побачити всі візуалізації, або через Colab, щоб запустити інтерактивно.

## Що показано

- **Інженерія даних** — парсинг квіркового формату Samsung Health, дедублікація мультидевайсних записів, гнучке зіставлення колонок між версіями застосунку
- **Часові ряди** — ресемплінг, rolling-статистики, сезонна декомпозиція (statsmodels)
- **Статистика** — лінійна регресія трендів зі significance testing, кореляційний і лаговий аналіз
- **Виявлення аномалій** — rolling z-score (відпустки, хвороби, зміни режиму)
- **Візуалізація** — кастомна тема, теплові карти, мультипанельні дашборди

## Запуск

```bash
pip install pandas numpy matplotlib scipy statsmodels jupyter
python -m jupyterlab health_longitudinal_analysis.ipynb
```

У нотатнику: **Run → Run All Cells**.

Нотатник **автономний** — за відсутності даних сам згенерує синтетичний демо-набір
(`gen_demo.py`, 4.7 року, відтворюваний seed), тож запускається в будь-кого одразу.

## Власні дані

1. Samsung Health → Налаштування → Завантажити персональні дані
2. Розпакуй ZIP у `data/samsung_health/`
3. Перезапусти нотатник — reader знайде найсвіжіші файли й перерахує весь аналіз

> **Приватність:** реальні health-дані не комітяться в репозиторій (`data/` у `.gitignore`).
> У репо лишається лише генератор демо-даних для відтворюваності.

## Файли

| Файл | Опис |
|------|------|
| `health_longitudinal_analysis.ipynb` | Основний нотатник (виконаний, з графіками) |
| `gen_demo.py` | Генератор синтетичних демо-даних (4.7 року) |
| `README.md` | Цей файл |

## Стек

`pandas` · `numpy` · `matplotlib` · `scipy` · `statsmodels`