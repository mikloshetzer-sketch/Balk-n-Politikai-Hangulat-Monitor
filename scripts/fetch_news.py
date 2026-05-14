import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

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
            "Podgorica government",
            "Montenegro EU accession"
        ],
        "keywords": ["montenegro", "podgorica"]
    },
    {
        "name": "Észak-Macedónia",
        "queries": [
            "North Macedonia politics",
            "Skopje government",
            "North Macedonia election"
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
    "riot", "boycott", "polarization", "opposition accuses",
    "kriza", "protesti", "korupcija", "nasilje", "sukob",
    "hapšenje", "napad", "skandal", "tenzije"
]

POSITIVE_WORDS = [
    "agreement", "reform", "growth", "cooperation", "investment",
    "stability", "dialogue", "progress", "eu accession",
    "development", "support", "partnership", "integration",
    "talks", "deal", "funding", "membership", "negotiations",
    "sporazum", "reforma", "saradnja", "investicija",
    "stabilnost", "napredak", "podrška", "partnerstvo"
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


def score_articles(articles):
    score = 0
    topics = {}

    for article in articles:
        title = article.get("title", "").lower()

        for word in NEGATIVE_WORDS:
            if word in title:
                score -= 4
                topics[word] = topics.get(word, 0) + 1

        for word in POSITIVE_WORDS:
            if word in title:
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


def get_main_topic(topics, articles):
    if topics:
        sorted_topics = sorted(
            topics.items(),
            key=lambda item: item[1],
            reverse=True
        )

        return sorted_topics[0][0]

    if articles:
        title = articles[0].get("title", "")

        if title:
            return title[:100]

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


def main():
    countries_output = []

    for country in COUNTRIES:
        print(f"Adatgyűjtés: {country['name']}")

        articles = collect_articles(country)

        print(f"Szűrt cikkek száma: {len(articles)}")

        score, topics = score_articles(articles)

        countries_output.append({
            "name": country["name"],
            "score": score,
            "status": get_status(score),
            "main_topic": get_main_topic(topics, articles),
            "article_count": len(articles),
            "top_articles": get_top_articles(articles)
        })

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "GDELT",
        "method_note": "Kulcsszavas, híralapú politikai hangulatindex. Nem közvélemény-kutatás.",
        "countries": countries_output
    }

    with open("docs/data/latest.json", "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print("latest.json sikeresen frissítve")


if __name__ == "__main__":
    main()
