import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HISTORY_PATH = "docs/data/history.json"
LATEST_PATH = "docs/data/latest.json"

COUNTRIES = [
    {
        "name": "Szerbia",
        "queries": [
            "Serbia politics",
            "Belgrade government",
            "Vucic protest"
        ],
        "keywords": ["serbia", "serbian", "belgrade", "vucic"]
    },
    {
        "name": "Bosznia-Hercegovina",
        "queries": [
            "Bosnia politics",
            "Sarajevo government",
            "Republika Srpska Dodik"
        ],
        "keywords": ["bosnia", "sarajevo", "dodik", "republika srpska", "bih"]
    },
    {
        "name": "Koszovó",
        "queries": [
            "Kosovo politics",
            "Pristina government",
            "Kosovo Serbia tensions"
        ],
        "keywords": ["kosovo", "pristina", "kurti", "mitrovica"]
    },
    {
        "name": "Montenegró",
        "queries": [
            "Montenegro politics",
            "Podgorica government"
        ],
        "keywords": ["montenegro", "podgorica"]
    },
    {
        "name": "Észak-Macedónia",
        "queries": [
            "North Macedonia politics",
            "Skopje government"
        ],
        "keywords": ["north macedonia", "macedonia", "skopje"]
    },
    {
        "name": "Albánia",
        "queries": [
            "Albania politics",
            "Tirana government",
            "Edi Rama opposition"
        ],
        "keywords": ["albania", "albanian", "tirana", "rama"]
    }
]

NEGATIVE_WORDS = [
    "protest", "protests", "crisis", "corruption", "violence",
    "conflict", "tension", "tensions", "sanction", "sanctions",
    "arrest", "attack", "war", "unrest", "fraud", "dispute",
    "scandal", "threat", "instability", "clash", "clashes",
    "riot", "boycott", "polarization", "accuses", "genocide",
    "propaganda"
]

POSITIVE_WORDS = [
    "agreement", "reform", "growth", "cooperation", "investment",
    "stability", "dialogue", "progress", "development", "support",
    "partnership", "integration", "talks", "deal", "funding",
    "membership", "negotiations", "future", "economic growth",
    "eu accession"
]


def fetch_gdelt_articles(query):
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"

    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": 50,
        "sort": "datedesc",
        "timespan": "7d"
    }

    url = base_url + "?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            raw_data = response.read().decode("utf-8")
            data = json.loads(raw_data)
            return data.get("articles", [])

    except Exception as error:
        print(f"Hiba a GDELT lekérésnél: {query}")
        print(error)
        return []


def is_relevant(article, keywords):
    title = article.get("title", "").lower()
    url = article.get("url", "").lower()
    domain = article.get("domain", "").lower()

    text = f"{title} {url} {domain}"

    for keyword in keywords:
        if keyword.lower() in text:
            return True

    return False


def collect_articles(country):
    all_articles = []
    seen_urls = set()

    for query in country["queries"]:
        articles = fetch_gdelt_articles(query)

        for article in articles:
            url = article.get("url", "")

            if not url:
                continue

            if url in seen_urls:
                continue

            if not is_relevant(article, country["keywords"]):
                continue

            seen_urls.add(url)
            all_articles.append(article)

    return all_articles[:50]


def analyze_articles(articles):
    negative_hits = 0
    positive_hits = 0
    negative_topics = {}
    positive_topics = {}

    for article in articles:
        title = article.get("title", "").lower()

        article_negative = False
        article_positive = False

        for word in NEGATIVE_WORDS:
            if word in title:
                article_negative = True
                negative_topics[word] = negative_topics.get(word, 0) + 1

        for word in POSITIVE_WORDS:
            if word in title:
                article_positive = True
                positive_topics[word] = positive_topics.get(word, 0) + 1

        if article_negative:
            negative_hits += 1

        if article_positive:
            positive_hits += 1

    score = (positive_hits * 4) - (negative_hits * 4)
    score = max(min(score, 30), -30)

    return {
        "score": score,
        "negative_hits": negative_hits,
        "positive_hits": positive_hits,
        "negative_topics": negative_topics,
        "positive_topics": positive_topics
    }


def get_status(score):
    if score >= 8:
        return "positive"

    if score <= -8:
        return "negative"

    return "neutral"


def get_main_topic(analysis, articles):
    combined = {}

    for key, value in analysis["negative_topics"].items():
        combined[key] = combined.get(key, 0) + value

    for key, value in analysis["positive_topics"].items():
        combined[key] = combined.get(key, 0) + value

    if combined:
        sorted_topics = sorted(
            combined.items(),
            key=lambda item: item[1],
            reverse=True
        )
        return sorted_topics[0][0]

    if articles:
        return articles[0].get("title", "")[:100]

    return "nincs kiemelkedő téma"


def get_top_articles(articles):
    top_articles = []

    for article in articles[:5]:
        top_articles.append({
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "source": article.get("domain", ""),
            "seen_date": article.get("seendate", "")
        })

    return top_articles


def load_history():
    if not os.path.exists(HISTORY_PATH):
        return {
            "updated_at": "",
            "records": []
        }

    with open(HISTORY_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def save_history(latest_data):
    history = load_history()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    daily_record = {
        "date": today,
        "countries": []
    }

    for country in latest_data["countries"]:
        daily_record["countries"].append({
            "name": country["name"],
            "score": country["score"],
            "status": country["status"],
            "article_count": country["article_count"],
            "negative_hits": country["negative_hits"],
            "positive_hits": country["positive_hits"],
            "main_topic": country["main_topic"]
        })

    history["records"] = [
        record for record in history.get("records", [])
        if record.get("date") != today
    ]

    history["records"].append(daily_record)

    history["records"] = history["records"][-90:]

    history["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    with open(HISTORY_PATH, "w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)


def main():
    countries_output = []

    for country in COUNTRIES:
        print(f"Adatgyűjtés: {country['name']}")

        articles = collect_articles(country)

        print(f"Szűrt cikkek száma: {len(articles)}")

        analysis = analyze_articles(articles)

        countries_output.append({
            "name": country["name"],
            "score": analysis["score"],
            "status": get_status(analysis["score"]),
            "main_topic": get_main_topic(analysis, articles),
            "article_count": len(articles),
            "negative_hits": analysis["negative_hits"],
            "positive_hits": analysis["positive_hits"],
            "top_articles": get_top_articles(articles)
        })

    latest_data = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "GDELT",
        "method_note": "Kulcsszavas, híralapú politikai hangulatindex. Nem közvélemény-kutatás.",
        "countries": countries_output
    }

    with open(LATEST_PATH, "w", encoding="utf-8") as file:
        json.dump(latest_data, file, ensure_ascii=False, indent=2)

    save_history(latest_data)

    print("latest.json és history.json sikeresen frissítve")


if __name__ == "__main__":
    main()
