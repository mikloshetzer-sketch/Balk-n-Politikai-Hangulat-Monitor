import json
import os
from datetime import datetime, timezone

SOCIAL_LATEST_PATH = "docs/data/social_latest.json"
SOCIAL_HISTORY_PATH = "docs/data/social_history.json"


def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def load_json(path, fallback):
    if not os.path.exists(path):
        return fallback

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    latest = load_json(SOCIAL_LATEST_PATH, None)

    if not latest:
        print("Nincs social_latest.json")
        return

    history = load_json(SOCIAL_HISTORY_PATH, {
        "updated_at": "",
        "records": []
    })

    date = today()

    new_record = {
        "date": date,
        "updated_at": latest.get("updated_at", now_utc()),
        "source": latest.get("source", ""),
        "countries": []
    }

    for country in latest.get("countries", []):
        signal = country.get("social_signal", {})

        new_record["countries"].append({
            "name": country.get("name"),
            "social_score": signal.get("score", 0),
            "social_level": signal.get("level", "low"),
            "mentions": signal.get("mentions", 0),
            "negative_hits": signal.get("negative_hits", 0),
            "positive_hits": signal.get("positive_hits", 0),
            "main_topic": signal.get("main_topic", "nincs adat"),
            "source_counts": signal.get("source_counts", {})
        })

    history["records"] = [
        item for item in history.get("records", [])
        if item.get("date") != date
    ]

    history["records"].append(new_record)
    history["records"] = history["records"][-60:]
    history["updated_at"] = now_utc()

    with open(SOCIAL_HISTORY_PATH, "w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)

    print("social_history.json sikeresen frissítve")


if __name__ == "__main__":
    main()
