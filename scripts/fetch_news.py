import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

COUNTRIES = [
    {
        "name": "Szerbia",
        "query": "Serbia"
    },
    {
        "name": "Bosznia-Hercegovina",
        "query": "Bosnia"
    },
    {
        "name": "Koszovó",
        "query": "Kosovo"
    },
    {
        "name": "Montenegró",
        "query": "Montenegro"
    },
    {
        "name": "Észak-Macedónia",
        "query": "North Macedonia"
    },
    {
        "name": "Albánia",
        "query": "Albania"
    }
]

NEGATIVE_WORDS = [
    "protest", "crisis", "corruption", "violence", "conflict",
    "tension", "sanction", "arrest", "attack", "war",
    "unrest", "fraud", "dispute", "scandal", "threat",
    "election dispute", "nationalist", "instability"
]

POSITIVE_WORDS = [
    "agreement", "reform", "growth", "cooperation", "investment",
    "stability", "dialogue", "progress", "eu accession",
    "development", "support", "partnership", "integration"
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

    print("Lekérdezés:", url)

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            raw_data = response.read().decode("utf-8")
            data = json.loads(raw_data)
            return data.get("articles", [])

    except Exception as error:
        print(f"Hiba a GDELT lekérésnél: {query}")
        print(error)
        return []


def score_articles(articles):
    score = 0
    topics = {}

    for article in articles:
        title = article.get("title", "").lower()
        seendate = article.get("seendate", "")
        source = article.get("sourceCountry", "")

        text = f"{title} {seendate} {source}".lower()

        for word in NEGATIVE_WORDS:
            if word in text:
                score -= 4
                topics[word] = topics.get(word, 0) + 1

        for word in POSITIVE_WORDS:
            if word in text:
                score += 3
                topics[word] = topics.get(word, 0) + 1

    score = max(min(score, 30), -30)

    return score, topics


def get_status(score):
    if score >= 8:
        return "positive"

    if score <= -8:
        return "negative"

    return "neutral"


def get_main_topic(topics):
    if not topics:
        return "nincs kiemelkedő téma"

    sorted_topics = sorted(
        topics.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return sorted_topics[0][0]


def main():
    countries_output = []

    for country in COUNTRIES:
        print(f"Adatgyűjtés: {country['name']}")

        articles = fetch_gdelt_articles(country["query"])

        print(f"Talált cikkek száma: {len(articles)}")

        score, topics = score_articles(articles)

        countries_output.append({
            "name": country["name"],
            "score": score,
            "status": get_status(score),
            "main_topic": get_main_topic(topics),
            "article_count": len(articles)
        })

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "GDELT",
        "countries": countries_output
    }

    with open("docs/data/latest.json", "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print("latest.json sikeresen frissítve")


if __name__ == "__main__":
    main()
