import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SOCIAL_LATEST_PATH = "docs/data/social_latest.json"

COUNTRIES = [
    {
        "name": "Szerbia",
        "social_queries": ["Serbia", "Vucic", "Belgrade"]
    },
    {
        "name": "Bosznia-Hercegovina",
        "social_queries": ["Bosnia", "Dodik", "Sarajevo"]
    },
    {
        "name": "Koszovó",
        "social_queries": ["Kosovo", "Kurti", "Pristina"]
    },
    {
        "name": "Montenegró",
        "social_queries": ["Montenegro", "Podgorica"]
    },
    {
        "name": "Észak-Macedónia",
        "social_queries": ["North Macedonia", "Skopje"]
    },
    {
        "name": "Albánia",
        "social_queries": ["Albania", "Tirana", "Edi Rama"]
    }
]

NEGATIVE_WORDS = [
    "protest", "crisis", "corruption", "violence", "conflict",
    "tension", "sanction", "arrest", "attack", "war", "unrest",
    "fraud", "dispute", "scandal", "threat", "instability",
    "clash", "riot", "boycott", "polarization"
]

POSITIVE_WORDS = [
    "agreement", "reform", "growth", "cooperation", "investment",
    "stability", "dialogue", "progress", "development", "support",
    "partnership", "integration", "talks", "deal", "funding",
    "membership", "negotiations"
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
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; BalkanPoliticalSocialMonitor/1.0)",
            "Accept": "application/json"
        }
    )

    with urllib.request.urlopen(request, timeout=8) as response:
        return response.read()


def fetch_json(url):
    raw_data = fetch_url(url).decode("utf-8")
    return json.loads(raw_data)


def fetch_reddit_posts(query):
    posts = []

    try:
        params = {
            "q": query,
            "sort": "new",
            "t": "day",
            "limit": 10,
            "type": "link"
        }

        url = "https://www.reddit.com/search.json?" + urllib.parse.urlencode(params)
        data = fetch_json(url)

        children = data.get("data", {}).get("children", [])

        print(f"Reddit találatok - {query}: {len(children)}")

        for child in children:
            item = child.get("data", {})

            title = clean_text(item.get("title", ""))
            permalink = item.get("permalink", "")
            created = item.get("created_utc", "")

            if not title or not permalink:
                continue

            posts.append({
                "title": title,
                "url": "https://www.reddit.com" + permalink,
                "source": "Reddit",
                "seen_date": str(created),
                "origin": "Reddit",
                "query": query
            })

    except Exception as error:
        print(f"Reddit hiba: {query}")
        print(error)

    return posts


def fetch_bluesky_posts(query):
    posts = []

    try:
        params = {
            "q": query,
            "limit": 10,
            "sort": "latest"
        }

        url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?" + urllib.parse.urlencode(params)
        data = fetch_json(url)

        items = data.get("posts", [])

        print(f"Bluesky találatok - {query}: {len(items)}")

        for item in items:
            record = item.get("record", {})
            author = item.get("author", {})

            text = clean_text(record.get("text", ""))
            handle = author.get("handle", "")
            uri = item.get("uri", "")

            if not text:
                continue

            posts.append({
                "title": text[:180],
                "url": uri,
                "source": f"Bluesky/{handle}",
                "seen_date": record.get("createdAt", ""),
                "origin": "Bluesky",
                "query": query
            })

    except Exception as error:
        print(f"Bluesky hiba: {query}")
        print(error)

    return posts


def collect_social_posts(country):
    all_posts = []
    seen = set()

    for query in country["social_queries"]:
        source_posts = []

        source_posts.extend(fetch_reddit_posts(query))
        source_posts.extend(fetch_bluesky_posts(query))

        for post in source_posts:
            key = post.get("url") or post.get("title")

            if not key:
                continue

            if key in seen:
                continue

            seen.add(key)
            all_posts.append(post)

    return all_posts[:50]


def analyze_social_posts(posts):
    mentions = len(posts)
    negative_hits = 0
    positive_hits = 0

    source_counts = {
        "Reddit": 0,
        "Bluesky": 0
    }

    query_counts = {}

    for post in posts:
        text = post.get("title", "").lower()
        origin = post.get("origin", "")
        query = post.get("query", "")

        if origin in source_counts:
            source_counts[origin] += 1

        if query:
            query_counts[query] = query_counts.get(query, 0) + 1

        if any(word in text for word in NEGATIVE_WORDS):
            negative_hits += 1

        if any(word in text for word in POSITIVE_WORDS):
            positive_hits += 1

    raw_score = mentions + (negative_hits * 3) + (positive_hits * 2)
    score = min(raw_score, 30)

    if score >= 20:
        level = "high"
    elif score >= 8:
        level = "medium"
    else:
        level = "low"

    main_topic = "nincs adat"

    if query_counts:
        main_topic = max(query_counts, key=query_counts.get)

    return {
        "score": score,
        "level": level,
        "mentions": mentions,
        "negative_hits": negative_hits,
        "positive_hits": positive_hits,
        "source_counts": source_counts,
        "query_counts": query_counts,
        "main_topic": main_topic,
        "top_posts": posts[:5]
    }


def main():
    countries_output = []

    for country in COUNTRIES:
        print("")
        print(f"Social adatgyűjtés: {country['name']}")

        posts = collect_social_posts(country)

        print(f"Összes social találat: {len(posts)}")

        analysis = analyze_social_posts(posts)

        countries_output.append({
            "name": country["name"],
            "social_signal": analysis
        })

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "Reddit + Bluesky",
        "method_note": "A social signal külön jelző. Nem közvélemény-kutatás, és nem része a fő hírindexnek. A Mastodon ideiglenesen kikapcsolva a futási idő csökkentése miatt.",
        "countries": countries_output
    }

    with open(SOCIAL_LATEST_PATH, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print("social_latest.json sikeresen frissítve")


if __name__ == "__main__":
    main()
