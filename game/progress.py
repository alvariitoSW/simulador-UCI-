"""Guardado local de progreso y mejores puntuaciones (JSON, no versionado)."""
import json
import os

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "save")
SAVE_PATH = os.path.join(SAVE_DIR, "progress.json")


def _default():
    return {"best_scores": {}, "stars": {}, "completed": []}


def load():
    if not os.path.exists(SAVE_PATH):
        return _default()
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        base = _default()
        base.update(data)
        return base
    except (json.JSONDecodeError, OSError):
        return _default()


def save(data):
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def record_result(case_id, score, stars, won):
    data = load()
    best = data["best_scores"].get(case_id, -1)
    if score > best:
        data["best_scores"][case_id] = score
    best_stars = data["stars"].get(case_id, 0)
    if stars > best_stars:
        data["stars"][case_id] = stars
    if won and case_id not in data["completed"]:
        data["completed"].append(case_id)
    save(data)
    return data
