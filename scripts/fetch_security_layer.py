import json
import os
import re
import urllib.request
from datetime import datetime, timezone

BASE_URL = "https://mikloshetzer-sketch.github.io/balkan-security-map"

OUTPUT_EVENTS = "docs/data/security_events.json"
OUTPUT_RISK = "docs/data/security_risk.json"

COUNTRIES = [
    "Szerbia",
    "Bosznia-Hercegovina",
    "Koszovó",
    "Montenegró",
    "Észak-Macedónia",
    "Albánia"
]

COUNTRY_ALIASES = {
    "Szerbia": [
        "serbia", "szerbia", "srbija", "belgrade", "beograd"
    ],
    "Bosznia-Hercegovina": [
        "bosnia", "bosnia and herzegovina", "bih", "sarajevo",
        "republika srpska", "bosnia-herzegovina"
    ],
    "Koszovó": [
        "kosovo", "kosova", "pristina", "prishtina", "mitrovica"
    ],
    "Montenegró": [
        "montenegro", "crna gora", "podgorica"
    ],
    "Észak-Macedónia": [
        "north macedonia", "macedonia", "skopje", "makedonija"
    ],
    "Albánia": [
        "albania", "albanian", "tirana", "shqiperi", "shqipëria"
    ]
}

CANDIDATE_FILES = [
    "data/security_events.json",
    "data/events.json",
    "data/stories.json",
    "data/gdelt_events.json",
    "data/rss_signals.json",
    "data/gdacs_alerts.json",
    "data/usgs_alerts.json",
    "data/latest.json",
    "data/snapshot.json",
    "data/balkan_risk.json",
    "data/hotspots.json",
    "data/security_risk.json",
    "data/risk.json"
]

POLITICAL_SECURITY_KEYWORDS = [
    "protest", "demonstration", "riot", "unrest", "clash", "attack",
    "violence", "armed", "shooting", "explosion", "border", "kfor",
    "police", "arrest", "detained", "ethnic", "nationalist",
    "cyber", "hack", "malware", "ddos", "threat", "security",
    "terror", "extremist", "military", "troops", "weapon",
    "sanction", "secession", "dodik", "republika srpska",
    "mitrovica", "kosovo serbia", "serbia kosovo"
]

NATURAL_ALERT_KEYWORDS = [
    "earthquake", "quake", "usgs", "gdacs", "flood", "storm",
    "wildfire", "weather", "rain", "landslide"
]

NOISE_KEYWORDS = [
    "hotspot_cell",
    "municipality of",
    "county",
    "gdelt':",
    "{'gdelt'",
    "cell",
    "grid",
    "risk snapshot",
    "rss_count",
    "trend"
]


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def fetch_json(url):
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Balkan-Political-Monitor/1.0"}
        )

        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read().decode("utf-8")

        return json.loads(raw)

    except Exception as error:
        print(f"Nem sikerült lekérni: {url}")
        print(error)
        return None


def text_blob(item):
    if isinstance(item, dict):
        return " ".join(str(value) for value in item.values()).lower()

    if isinstance(item, list):
        return " ".join(text_blob(value) for value in item).lower()

    return str(item).lower()


def detect_country(item):
    text = text_blob(item)

    for country, aliases in COUNTRY_ALIASES.items():
        for alias in aliases:
            if alias.lower() in text:
                return country

    return None


def flatten_items(data):
    items = []

    if isinstance(data, list):
        for value in data:
            items.extend(flatten_items(value))

    elif isinstance(data, dict):
        if looks_like_possible_event(data):
            items.append(data)

        for value in data.values():
            if isinstance(value, (list, dict)):
                items.extend(flatten_items(value))

    return items


def looks_like_possible_event(item):
    if not isinstance(item, dict):
        return False

    keys = set(item.keys())

    event_like_keys = {
        "title", "headline", "summary", "text", "description",
        "country", "url", "source", "type", "category",
        "event_type", "published", "published_at", "date",
        "severity", "score", "risk"
    }

    return bool(keys.intersection(event_like_keys))


def event_title(item):
    for key in ["title", "headline", "summary", "text", "description", "name"]:
        value = item.get(key)

        if value:
            title = str(value).strip()

            if len(title) >= 8:
                return title

    return ""


def event_url(item):
    for key in ["url", "link", "source_url"]:
        value = item.get(key)

        if value:
            return str(value)

    return ""


def event_source(item):
    for key in ["source", "domain", "provider", "origin"]:
        value = item.get(key)

        if value:
            return str(value)

    return "balkan-security-map"


def event_date(item):
    for key in ["date", "published_at", "published", "seen_date", "updated_at", "time"]:
        value = item.get(key)

        if value:
            return str(value)

    return now_utc()


def event_score(item):
    for key in ["score", "risk", "risk_score", "severity"]:
        value = item.get(key)

        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(value)
        except Exception:
            pass

    return 0


def has_any_keyword(text, keywords):
    return any(keyword.lower() in text for keyword in keywords)


def is_noise_item(item):
    text = text_blob(item)

    if has_any_keyword(text, NOISE_KEYWORDS):
        return True

    title = event_title(item)

    if not title:
        return True

    if title.lower() in ["biztonsági jelzés", "security signal", "hotspot"]:
        return True

    return False


def classify_event_type(item):
    text = text_blob(item)

    if has_any_keyword(text, NATURAL_ALERT_KEYWORDS):
        return "natural_alert"

    if any(word in text for word in ["cyber", "hack", "malware", "ddos"]):
        return "cyber"

    if any(word in text for word in ["protest", "demonstration", "riot", "unrest"]):
        return "protest"

    if any(word in text for word in ["border", "kfor", "mitrovica", "kosovo serbia", "serbia kosovo"]):
        return "border_tension"

    if any(word in text for word in ["attack", "clash", "violence", "armed", "shooting", "explosion"]):
        return "security_incident"

    if any(word in text for word in ["secession", "dodik", "republika srpska", "ohr"]):
        return "institutional_security_risk"

    if any(word in text for word in ["police", "arrest", "detained"]):
        return "public_order"

    return "general_security_signal"


def risk_level_from_score(score):
    try:
        value = float(score)
    except Exception:
        value = 0

    if value >= 75:
        return "critical"

    if value >= 50:
        return "high"

    if value >= 25:
        return "medium"

    if value > 0:
        return "low"

    return "none"


def is_political_security_event(item):
    text = text_blob(item)

    if is_noise_item(item):
        return False

    if has_any_keyword(text, NATURAL_ALERT_KEYWORDS):
        return False

    return has_any_keyword(text, POLITICAL_SECURITY_KEYWORDS)


def build_events(all_remote_items):
    events = []
    seen = set()

    for item in all_remote_items:
        if not is_political_security_event(item):
            continue

        country = detect_country(item)

        if not country:
            continue

        title = event_title(item)
        url = event_url(item)
        source = event_source(item)
        score = event_score(item)
        blob = text_blob(item)

        event_id = f"{country}|{title}|{url}"

        if event_id in seen:
            continue

        seen.add(event_id)

        event_type = classify_event_type(item)

        if event_type == "natural_alert":
            continue

        calculated_score = score

        if calculated_score <= 0:
            if event_type in ["security_incident", "border_tension"]:
                calculated_score = 35
            elif event_type in ["protest", "public_order"]:
                calculated_score = 25
            elif event_type in ["cyber", "institutional_security_risk"]:
                calculated_score = 30
            else:
                calculated_score = 15

        event = {
            "country": country,
            "title": title,
            "url": url,
            "source": source,
            "date": event_date(item),
            "event_type": event_type,
            "score": calculated_score,
            "level": risk_level_from_score(calculated_score)
        }

        lat = item.get("lat")
        lng = item.get("lng") or item.get("lon")

        if lat is not None and lng is not None:
            event["lat"] = lat
            event["lng"] = lng

        events.append(event)

    return events[:300]


def build_country_risk(events):
    countries = []

    for country in COUNTRIES:
        country_events = [
            event for event in events
            if event.get("country") == country
        ]

        event_count = len(country_events)

        type_counter = {}

        for event in country_events:
            event_type = event.get("event_type", "general_security_signal")
            type_counter[event_type] = type_counter.get(event_type, 0) + 1

        if type_counter:
            main_type = max(type_counter, key=type_counter.get)
        else:
            main_type = "nincs adat"

        total_score = sum(float(event.get("score", 0) or 0) for event in country_events)

        calculated_score = min(
            100,
            round(total_score + event_count * 5, 1)
        )

        countries.append({
            "name": country,
            "security_score": calculated_score,
            "security_level": risk_level_from_score(calculated_score),
            "event_count": event_count,
            "main_event_type": main_type,
            "top_events": country_events[:5]
        })

    return countries


def main():
    os.makedirs("docs/data", exist_ok=True)

    all_items = []
    successful_sources = []

    for path in CANDIDATE_FILES:
        url = f"{BASE_URL}/{path}"
        data = fetch_json(url)

        if data is None:
            continue

        successful_sources.append(url)
        all_items.extend(flatten_items(data))

    events = build_events(all_items)
    country_risk = build_country_risk(events)

    security_events_output = {
        "updated_at": now_utc(),
        "source": "balkan-security-map",
        "source_base_url": BASE_URL,
        "successful_sources": successful_sources,
        "event_count": len(events),
        "events": events
    }

    security_risk_output = {
        "updated_at": now_utc(),
        "source": "balkan-security-map",
        "method_note": (
            "Politikai-biztonsági réteg a balkan-security-map publikált JSON adatai alapján. "
            "A technikai hotspot_cell, rács- és természeti riasztási elemek kiszűrve. "
            "Nem hivatalos kockázati minősítés."
        ),
        "countries": country_risk
    }

    with open(OUTPUT_EVENTS, "w", encoding="utf-8") as file:
        json.dump(security_events_output, file, ensure_ascii=False, indent=2)

    with open(OUTPUT_RISK, "w", encoding="utf-8") as file:
        json.dump(security_risk_output, file, ensure_ascii=False, indent=2)

    print(f"security_events.json elkészült: {len(events)} esemény")
    print("security_risk.json elkészült")

    if not successful_sources:
        print("Figyelem: nem sikerült publikált JSON-forrást találni a balkan-security-map repóból.")

    if len(events) == 0:
        print("Figyelem: a szigorú szűrés után nem maradt politikai-biztonsági esemény.")


if __name__ == "__main__":
    main()
