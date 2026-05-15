import json
import os
from datetime import datetime, timezone

RISK_PATH = "docs/data/security_risk.json"
HISTORY_PATH = "docs/data/security_history.json"


def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_json(path, fallback):
    if not os.path.exists(path):
        return fallback

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    risk_data = load_json(RISK_PATH, None)

    if not risk_data:
        print("Nincs security_risk.json")
        return

    history = load_json(HISTORY_PATH, {
        "updated_at": "",
        "records": []
    })

    date = today()

    new_record = {
        "date": date,
        "updated_at": risk_data.get("updated_at"),
        "countries": []
    }

    for country in risk_data.get("countries", []):
        new_record["countries"].append({
            "name": country.get("name"),
            "security_score": country.get("security_score", 0),
            "security_level": country.get("security_level", "none"),
            "security_source": country.get("security_source", "none"),
            "main_event_type": country.get("main_event_type", "nincs adat"),
            "event_count": country.get("event_count", 0)
        })

    history["records"] = [
        item for item in history.get("records", [])
        if item.get("date") != date
    ]

    history["records"].append(new_record)
    history["records"] = history["records"][-60:]
    history["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    with open(HISTORY_PATH, "w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)

    print("security_history.json frissítve")


if __name__ == "__main__":
    main()
