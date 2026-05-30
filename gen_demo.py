"""
Генератор синтетичних Samsung Health CSV (4.7 року) у форматі реального експорту.
Формат точно сумісний з parser.py: рядок 0 = метадані, рядок 1 = заголовки,
day_time у мілісекундах, коди фаз сну 40001-40004, trailing-кома.
Дані реалістичні: тренд форми вгору, сезонність (літо активніше), вихідні vs будні,
поступове зниження resting HR, кілька "відпускних" аномалій.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

np.random.seed(42)

OUT = Path("data/samsung_health")
OUT.mkdir(parents=True, exist_ok=True)

START = datetime(2021, 9, 1)
END   = datetime(2026, 5, 30)
DAYS  = (END - START).days
dates = [START + timedelta(days=i) for i in range(DAYS)]

def ms(dt): return int(dt.timestamp() * 1000)

def seasonal(dt):
    # літо (день року ~172) активніше, зима менше
    doy = dt.timetuple().tm_yday
    return np.sin((doy - 80) / 365 * 2 * np.pi)  # пік ~червень

def fitness_trend(i):
    # поступове зростання форми за 4.7 року (0→1) з плато
    return min(1.0, i / (DAYS * 0.7))

# ── STEPS (pedometer_day_summary) ────────────────────────────────────
steps_rows = []
for i, dt in enumerate(dates):
    is_weekend = dt.weekday() >= 5
    base = 7000 + 3500 * fitness_trend(i) + 1800 * seasonal(dt)
    base += 1500 if is_weekend else 0
    # відпустка: 2 тижні в липні кожного року — або дуже активно, або зовсім ні
    if dt.month == 7 and 10 <= dt.day <= 24:
        base *= np.random.choice([0.3, 1.8])
    val = max(500, int(np.random.normal(base, 2200)))
    dist = val * 0.00075 * 1000          # м
    cal  = val * 0.04
    active = val * 0.008 * 60000          # мс
    # Samsung часто дублює день (phone+watch) — додаємо 1-2 записи
    n_dup = np.random.choice([1, 2], p=[0.4, 0.6])
    for _ in range(n_dup):
        f = np.random.uniform(0.5, 1.0)
        steps_rows.append({
            "com.samsung.health.step_count.day_time": ms(dt),
            "com.samsung.health.step_count.count": int(val * f),
            "com.samsung.health.step_count.distance": dist * f,
            "com.samsung.health.step_count.calorie": cal * f,
            "com.samsung.health.step_count.active_time": active * f,
        })

# ── SLEEP ────────────────────────────────────────────────────────────
sleep_rows = []
for i, dt in enumerate(dates):
    bedtime = dt.replace(hour=23, minute=0) + timedelta(minutes=int(np.random.normal(0, 50)))
    dur_h = np.clip(np.random.normal(7.1 + 0.4 * fitness_trend(i), 1.0), 3.5, 10)
    wake = bedtime + timedelta(hours=dur_h)
    eff = np.clip(np.random.normal(85 + 5 * fitness_trend(i), 7), 50, 99)
    score = np.clip(np.random.normal(70 + 12 * fitness_trend(i), 12), 20, 100)
    sid = f"sleep_{i}"
    sleep_rows.append({
        "com.samsung.health.sleep.start_time": bedtime.strftime("%Y-%m-%d %H:%M:%S.000"),
        "com.samsung.health.sleep.end_time": wake.strftime("%Y-%m-%d %H:%M:%S.000"),
        "com.samsung.health.sleep.efficiency": round(eff, 1),
        "com.samsung.health.sleep.sleep_score": round(score, 0),
        "com.samsung.health.sleep.sleep_id": sid,
    })

# ── SLEEP STAGES ─────────────────────────────────────────────────────
stage_rows = []
for i, dt in enumerate(dates):
    bedtime = dt.replace(hour=23, minute=0)
    dur_h = 7.1
    # розкладка фаз: light ~50%, deep ~20%, rem ~22%, awake ~8%
    cur = bedtime
    total_min = int(dur_h * 60)
    mins = {40002: int(total_min*0.50), 40003: int(total_min*0.20),
            40004: int(total_min*0.22), 40001: int(total_min*0.08)}
    for code, m in mins.items():
        seg = max(5, m // np.random.randint(2, 5))
        left = m
        while left > 0:
            d = min(seg, left)
            stage_rows.append({
                "com.samsung.health.sleep_stage.start_time": cur.strftime("%Y-%m-%d %H:%M:%S.000"),
                "com.samsung.health.sleep_stage.end_time": (cur+timedelta(minutes=d)).strftime("%Y-%m-%d %H:%M:%S.000"),
                "com.samsung.health.sleep_stage.stage": code,
                "com.samsung.health.sleep_stage.sleep_id": f"sleep_{i}",
            })
            cur += timedelta(minutes=d)
            left -= d

# ── HEART RATE ───────────────────────────────────────────────────────
hr_rows = []
for i, dt in enumerate(dates):
    resting = 62 - 8 * fitness_trend(i) + np.random.normal(0, 2)  # форма росте → resting падає
    for _ in range(np.random.randint(8, 16)):
        t = dt + timedelta(hours=np.random.uniform(0, 24))
        hour = t.hour
        if 0 <= hour <= 6:
            hr = np.random.normal(resting, 4)
        elif np.random.random() < 0.12:
            hr = np.random.normal(135, 20)  # активність
        else:
            hr = np.random.normal(78, 12)
        hr = int(np.clip(hr, 42, 190))
        hr_rows.append({
            "com.samsung.health.heart_rate.start_time": t.strftime("%Y-%m-%d %H:%M:%S.000"),
            "com.samsung.health.heart_rate.heart_rate": hr,
            "com.samsung.health.heart_rate.min": max(40, hr-5),
            "com.samsung.health.heart_rate.max": hr+5,
        })

# ── EXERCISE ─────────────────────────────────────────────────────────
ex_rows = []
ex_types = [1002, 1001, 11007, 15006, 14001]  # run, walk, cycle, strength, hike
for i, dt in enumerate(dates):
    if np.random.random() < 0.25 + 0.2 * fitness_trend(i):  # частіше з ростом форми
        t = dt.replace(hour=18) + timedelta(minutes=int(np.random.normal(0,60)))
        dur = np.random.uniform(20, 80)
        etype = int(np.random.choice(ex_types))
        dist = dur * np.random.uniform(0.1, 0.2) if etype in (1002,1001,11007,14001) else 0
        ex_rows.append({
            "com.samsung.health.exercise.start_time": t.strftime("%Y-%m-%d %H:%M:%S.000"),
            "com.samsung.health.exercise.end_time": (t+timedelta(minutes=dur)).strftime("%Y-%m-%d %H:%M:%S.000"),
            "com.samsung.health.exercise.duration": int(dur*60000),
            "com.samsung.health.exercise.exercise_type": etype,
            "com.samsung.health.exercise.distance": dist*1000,
            "com.samsung.health.exercise.calorie": dur*np.random.uniform(6,11),
            "com.samsung.health.exercise.mean_heart_rate": int(np.random.normal(135,12)),
            "com.samsung.health.exercise.max_heart_rate": int(np.random.normal(165,10)),
        })

def write_sh(rows, name):
    """Пише CSV у форматі Samsung Health: рядок0=метадані, рядок1=заголовки, trailing-кома."""
    df = pd.DataFrame(rows)
    ts = "20260530120000"
    path = OUT / f"{name}.{ts}.csv"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"com.samsung.shealth,1,{name}\n")   # рядок метаданих (parser робить skiprows=1)
        df.to_csv(f, index=False, lineterminator=",\n")  # trailing-кома як у Samsung
    return path, len(df)

p1 = write_sh(steps_rows, "com.samsung.shealth.tracker.pedometer_day_summary")
p2 = write_sh(sleep_rows, "com.samsung.shealth.sleep")
p3 = write_sh(stage_rows, "com.samsung.health.sleep_stage")
p4 = write_sh(hr_rows, "com.samsung.shealth.tracker.heart_rate")
p5 = write_sh(ex_rows, "com.samsung.shealth.exercise")
for p, n in [p1,p2,p3,p4,p5]:
    print(f"{p.name}: {n} рядків")
print(f"\nПеріод: {START.date()} → {END.date()} ({DAYS} днів, {DAYS/365:.1f} років)")
