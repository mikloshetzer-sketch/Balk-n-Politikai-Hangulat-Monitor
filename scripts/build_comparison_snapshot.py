import json
import os
from datetime import datetime, timezone

PROFILES_PATH = "docs/data/country_profiles.json"
LIVE_PATH = "docs/data/country_profiles_live.json"
LATEST_PATH = "docs/data/latest.json"
SOCIAL_PATH = "docs/data/social_latest.json"
SECURITY_PATH = "docs/data/security_risk.json"

OUTPUT_PATH = "docs/data/comparison_snapshot.json"


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def load_json(path, fallback=None):
    if not os.path.exists(path):
        return fallback

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_country(data, name):
    if not data:
        return None

    for item in data.get("countries", []):
        if item.get("name") == name:
            return item

    return None


def main():
    profiles = load_json(PROFILES_PATH, {"countries": []})
    live = load_json(LIVE_PATH, {"countries": []})
    latest = load_json(LATEST_PATH, {"countries": []})
    social = load_json(SOCIAL_PATH, {"countries": []})
    security = load_json(SECURITY_PATH, {"countries": []})

    countries_output = []

    for profile in profiles.get("countries", []):
        name = profile.get("name")

        economy = profile.get("economy", {})

        live_country = get_country(live, name) or {}
        latest_country = get_country(latest, name) or {}
        social_country = get_country(social, name) or {}
        security_country = get_country(security, name) or {}

        social_signal = social_country.get("social_signal", {})
        fx = live_country.get("fx", {})
        bank = live_country.get("central_bank", {})

        countries_output.append({
            "name": name,

            "population": profile.get("population"),
            "median_age": profile.get("median_age"),

            "gdp_billion_usd": economy.get("gdp_billion_usd"),
            "gdp_per_capita_usd": economy.get("gdp_per_capita_usd"),

            "average_net_salary_eur": economy.get("average_net_salary_eur"),

            "inflation_percent": economy.get("inflation_percent"),
            "unemployment_percent": economy.get("unemployment_percent"),

            "exports_billion_usd": economy.get("exports_billion_usd"),
            "imports_billion_usd": economy.get("imports_billion_usd"),
            "trade_balance_billion_usd": economy.get("trade_balance_billion_usd"),

            "currency": profile.get("currency"),
            "fx_rate": fx.get("rate"),
            "fx_note": fx.get("note"),

            "policy_rate": bank.get("policy_rate"),
            "central_bank": bank.get("name"),

            "news_score": latest_country.get("score", 0),
            "news_status": latest_country.get("status", "neutral"),
            "main_topic": latest_country.get("main_topic", "nincs adat"),

            "social_score": social_signal.get("score", 0),
            "social_mentions": social_signal.get("mentions", 0),

            "security_score": security_country.get("security_score", 0),
            "security_level": security_country.get("security_level", "none"),
            "security_topic": security_country.get("main_event_type", "nincs adat")
        })

    output = {
        "updated_at": now_utc(),
        "method_note": (
            "Összehasonlító snapshot a Balkán Országprofil Dashboard számára. "
            "A strukturális, politikai, social és security adatokat egyesíti."
        ),
        "countries": countries_output
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print("comparison_snapshot.json frissítve")


if __name__ == "__main__":
    main()
