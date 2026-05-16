import json
import os
from datetime import datetime, timezone

LIVE_PATH = "docs/data/country_profiles_live.json"
OUTPUT_PATH = "docs/data/interest_rate_history.json"


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
    live = load_json(LIVE_PATH, None)

    if not live:
        print("Nincs country_profiles_live.json")
        return

    history = load_json(OUTPUT_PATH, {
        "updated_at": "",
        "records": []
    })

    record = {
        "date": today(),
        "updated_at": live.get("updated_at", now_utc()),
        "countries": []
    }

    for country in live.get("countries", []):
        bank = country.get("central_bank", {})

        record["countries"].append({
            "name": country.get("name"),
            "currency": country.get("currency"),
            "policy_rate": bank.get("policy_rate"),
            "central_bank": bank.get("name"),
            "note": bank.get("note", "")
        })

    history["records"] = [
        item for item in history.get("records", [])
        if item.get("date") != record["date"]
    ]

    history["records"].append(record)
    history["records"] = history["records"][-90:]
    history["updated_at"] = now_utc()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)

    print("interest_rate_history.json frissítve")


if __name__ == "__main__":
    main()
