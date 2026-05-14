import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

HISTORY_PATH = "docs/data/history.json"
LATEST_PATH = "docs/data/latest.json"

RSS_FEEDS = [
    {"name": "Balkan Insight", "url": "https://balkaninsight.com/feed/"},
    {"name": "RFE/RL Balkans", "url": "https://www.rferl.org/api/zrqiteuuir"},
    {"name": "B92 English", "url": "https://www.b92.net/rss/b92/english"},

    {"name": "N1 Serbia", "url": "https://n1info.rs/feed/"},
    {"name": "Danas Serbia", "url": "https://www.danas.rs/feed/"},
    {"name": "Nova Serbia", "url": "https://nova.rs/feed/"},

    {"name": "Klix Bosnia", "url": "https://www.klix.ba/rss"},
    {"name": "Avaz Bosnia", "url": "https://avaz.ba/rss"},

    {"name": "Vijesti Montenegro", "url": "https://www.vijesti.me/rss"},
    {"name": "CDM Montenegro", "url": "https://www.cdm.me/feed/"},

    {"name": "Gazeta Express Kosovo", "url": "https://www.gazetaexpress.com/feed/"},
    {"name": "Koha Kosovo", "url": "https://www.koha.net/rss"},

    {"name": "Exit News Albania", "url": "https://exit.al/en/feed/"},
    {"name": "Albanian Daily News", "url": "https://albaniandailynews.com/rss"},

    {"name": "Macedonia Kurir", "url": "https://kurir.mk/feed/"},
    {"name": "SDK Macedonia", "url": "https://sdk.mk/index.php/feed/"}
]

COUNTRIES = [
    {
        "name": "Szerbia",
        "queries": ["Serbia politics", "Belgrade government", "Vucic protest"],
        "keywords": ["serbia", "serbian", "belgrade", "vucic", "srbija", "beograd", "vučić"]
    },
    {
        "name": "Bosznia-Hercegovina",
        "queries": ["Bosnia politics", "Sarajevo government", "Republika Srpska Dodik"],
        "keywords": ["bosnia", "sarajevo", "dodik", "republika srpska", "bih", "bosnia and herzegovina"]
    },
    {
        "name": "Koszovó",
        "queries": ["Kosovo politics", "Pristina government", "Kosovo Serbia tensions"],
        "keywords": ["kosovo", "pristina", "kurti", "mitrovica", "kosova"]
    },
    {
        "name": "Montenegró",
        "queries": ["Montenegro politics", "Podgorica government"],
        "keywords": ["montenegro", "podgorica", "crna gora", "crnoj gori"]
    },
    {
        "name": "Észak-Macedónia",
        "queries": ["North Macedonia politics", "Skopje government"],
        "keywords": ["north macedonia", "macedonia", "skopje", "makedonija", "скопје", "македонија"]
    },
    {
        "name": "Albánia",
        "queries": ["Albania politics", "Tirana government", "Edi Rama opposition"],
        "keywords": ["albania", "albanian", "tirana", "rama", "shqiperi", "shqipëria"]
    }
]

NEGATIVE_WORDS = [
    "protest", "protests", "crisis", "corruption", "violence", "conflict",
    "tension", "tensions", "sanction", "sanctions", "arrest", "attack",
    "war", "unrest", "fraud", "dispute", "scandal", "threat",
    "instability", "clash", "clashes", "riot", "boycott", "polarization",
    "accuses", "genocide", "propaganda", "blocked", "deadlock",
    "resignation", "investigation", "charges", "convicted",
    "kriza", "protest", "protesti", "korupcija", "nasilje", "sukob",
    "hapšenje", "napad", "skandal", "tenzije", "blokada"
]

POSITIVE_WORDS = [
    "agreement", "reform", "growth", "cooperation", "investment",
    "stability", "dialogue", "progress", "development", "support",
    "partnership", "integration", "talks", "deal", "funding",
    "membership", "negotiations", "future", "economic growth",
    "eu accession", "opens talks", "approved", "aid package",
    "sporazum", "reforma", "saradnja", "investicija", "stabilnost",
    "napredak", "podrška", "partnerstvo"
]


def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")

    return " ".join(text.split())


def fetch_url(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


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
        raw_data = fetch_url(url).decode("utf-8")
        data = json.loads(raw_data)

        articles = []

        for item in data.get("articles", []):
            articles.append({
                "title": clean_text(item.get("title", "")),
                "url": item.get("url", ""),
                "source": item.get("domain", "GDELT"),
                "seen_date": item.get("seendate", ""),
                "description": "",
                "origin": "GDELT"
            })

        return articles

    except Exception as error:
        print(f"Hiba a GDELT lekérésnél: {query}")
        print(error)
        return []


def fetch_rss_articles(feed):
    articles = []

    try:
        raw_xml = fetch_url(feed["url"])
        root = ET.fromstring(raw_xml)

        for item in root.findall(".//item"):
            title = clean_text(item.findtext("title", ""))
            link = clean_text(item.findtext("link", ""))
            pub_date = clean_text(item.findtext("pubDate", ""))
            description = clean_text(item.findtext("description", ""))

            if not title or not link:
                continue

            articles.append({
                "title": title,
                "url": link,
                "source": feed["name"],
                "seen_date": pub_date,
                "description": description,
                "origin": "RSS"
            })

        print(f"RSS találatok: {feed['name']} - {len(articles)}")

    except Exception as error:
        print(f"RSS hiba vagy nem elérhető feed: {feed['name']}")
        print(error)

    return articles


def fetch_all_rss_articles():
    all_articles = []

    for feed in RSS_FEEDS:
        all_articles.extend(fetch_rss_articles(feed))

    return all_articles


def is_relevant(article, keywords):
    title = article.get("title", "").lower()
    url = article.get("url", "").lower()
    source = article.get("source", "").lower()
    description = article.get("description", "").lower()

    text = f"{title} {url} {source} {description}"

    for keyword in keywords:
        if keyword.lower() in text:
            return True

    return False


def collect_articles(country, rss_articles):
    all_articles = []
    seen_urls = set()

    for query in country["queries"]:
        gdelt_articles = fetch_gdelt_articles(query)

        for article in gdelt_articles:
            url = article.get("url", "")

            if not url:
                continue

            if url in seen_urls:
                continue

            if not is_relevant(article, country["keywords"]):
                continue

            seen_urls.add(url)
            all_articles.append(article)

    for article in rss_articles:
        url = article.get("url", "")

        if not url:
            continue

        if url in seen_urls:
            continue

        if not is_relevant(article, country["keywords"]):
            continue

        seen_urls.add(url)
        all_articles.append(article)

    return all_articles[:80]


def analyze_articles(articles):
    negative_hits = 0
    positive_hits = 0
    negative_topics = {}
    positive_topics = {}

    for article in articles:
        title = article.get("title", "").lower()
        description = article.get("description", "").lower()
        text = f"{title} {description}"

        article_negative = False
        article_positive = False

        for word in NEGATIVE_WORDS:
            if word in text:
                article_negative = True
                negative_topics[word] = negative_topics.get(word, 0) + 1

        for word in POSITIVE_WORDS:
            if word in text:
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
            "source": article.get("source", ""),
            "seen_date": article.get("seen_date", ""),
            "origin": article.get("origin", "")
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

    print("RSS-források lekérése...")
    rss_articles = fetch_all_rss_articles()

    for country in COUNTRIES:
        print(f"Adatgyűjtés: {country['name']}")

        articles = collect_articles(country, rss_articles)

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
        "source": "GDELT + regional RSS",
        "method_note": "Kulcsszavas, híralapú politikai hangulatindex. Nem közvélemény-kutatás.",
        "countries": countries_output
    }

    with open(LATEST_PATH, "w", encoding="utf-8") as file:
        json.dump(latest_data, file, ensure_ascii=False, indent=2)

    save_history(latest_data)

    print("latest.json és history.json sikeresen frissítve")


if __name__ == "__main__":
    main()
