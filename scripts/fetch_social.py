import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SOCIAL_LATEST_PATH = "docs/data/social_latest.json"

MASTODON_INSTANCES = [
    "https://mastodon.social",
    "https://mstdn.social",
    "https://fosstodon.org"
]

COUNTRIES = [
    {
        "name": "Szerbia",
        "keywords": ["serbia", "serbian", "belgrade", "vucic", "srbija", "beograd", "vučić"],
        "social_queries": ["Serbia", "Vucic", "Belgrade"]
    },
    {
        "name": "Bosznia-Hercegovina",
        "keywords": ["bosnia", "sarajevo", "dodik", "republika srpska", "bih", "bosnia and herzegovina"],
        "social_queries": ["Bosnia", "Dodik", "Republika Srpska"]
    },
    {
        "name": "Koszovó",
        "keywords": ["kosovo", "pristina", "kurti", "mitrovica", "kosova"],
        "social_queries": ["Kosovo", "Kurti", "Pristina"]
    },
    {
        "name": "Montenegró",
        "keywords": ["montenegro", "podgorica", "crna gora", "crnoj gori"],
        "social_queries": ["Montenegro", "Podgorica"]
    },
    {
        "name": "Észak-Macedónia",
        "keywords": ["north macedonia", "macedonia", "skopje", "makedonija", "скопје", "македонија"],
        "social_queries": ["North Macedonia", "Skopje", "Macedonia"]
    },
    {
        "name": "Albánia",
        "keywords": ["albania", "albanian", "tirana", "rama", "shqiperi", "shqipëria"],
        "social_queries": ["Albania", "Tirana", "Edi Rama"]
    }
]

NEGATIVE_WORDS = [
    "protest", "protests", "crisis", "corruption", "violence",
    "conflict", "tension", "tensions", "sanction", "sanctions",
    "arrest", "attack", "war", "unrest", "fraud", "dispute",
    "scandal", "threat", "instability", "clash", "clashes",
    "riot", "boycott", "polarization", "accuses", "genocide",
    "propaganda", "blocked", "deadlock", "resignation",
    "investigation", "charges", "convicted"
]

POSITIVE_WORDS = [
    "agreement", "reform", "growth", "cooperation", "investment",
    "stability", "dialogue", "progress", "development", "support",
    "partnership", "integration", "talks", "deal", "funding",
    "membership", "negotiations", "future", "economic growth",
    "eu accession", "approved"
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
            "User-Agent": "Mozilla/5.0 (compatible; BalkanPoliticalSocialMonitor/1.0)"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def fetch_json(url):
    raw_data = fetch_url(url).decode("utf-8")
    return json.loads(raw_data)


def is_relevant(item, keywords):
    title = item.get("title", "").lower()
    url = item.get("url", "").lower()
    source = item.get("source", "").lower()

    text = f"{title} {url} {source}"

    for keyword in keywords:
        if keyword.lower() in text:
            return True

    return False


def fetch_reddit_posts(query):
    posts = []

    try:
        params = {
            "q": query,
            "sort": "new",
            "t": "day",
            "limit": 20
        }

        url = "https://www.reddit.com/search.json?" + urllib.parse.urlencode(params)
        data = fetch_json(url)

        children = data.get("data", {}).get("children", [])

        for child in children:
            item = child.get("data", {})

            title = clean_text(item.get("title", ""))
            permalink = item.get("permalink", "")
            created = item.get("created_utc", "")

            if not title:
                continue

            posts.append({
                "title": title,
                "url": "https://www.reddit.com" + permalink,
                "source": "Reddit",
                "seen_date": str(created),
                "origin": "Reddit"
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
            "limit": 20,
            "sort": "latest"
        }

        url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?" + urllib.parse.urlencode(params)
        data = fetch_json(url)

        for item in data.get("posts", []):
            record = item.get("record", {})
            author = item.get("author", {})

            text = clean_text(record.get("text", ""))
            uri = item.get("uri", "")
            handle = author.get("handle", "")

            if not text:
                continue

            posts.append({
                "title": text[:180],
                "url": uri,
                "source": f"Bluesky/{handle}",
                "seen_date": record.get("createdAt", ""),
                "origin": "Bluesky"
            })

    except Exception as error:
        print(f"Bluesky hiba: {query}")
        print(error)

    return posts


def fetch_mastodon_posts(query):
    posts = []

    for instance in MASTODON_INSTANCES:
        try:
            params = {
                "q": query,
                "type": "statuses",
                "limit": 20,
                "resolve": "false"
            }

            url = instance + "/api/v2/search?" + urllib.parse.urlencode(params)
            data = fetch_json(url)

            for item in data.get("statuses", []):
                content = clean_text(item.get("content", ""))
                status_url = item.get("url", "")

                if not content:
                    continue

                posts.append({
                    "title": content[:180],
                    "url": status_url,
                    "source": f"Mastodon/{instance.replace('https://', '')}",
                    "seen_date": item.get("created_at", ""),
                    "origin": "Mastodon"
                })

        except Exception as error:
            print(f"Mastodon hiba: {instance} / {query}")
            print(error)

    return posts


def collect_social_posts(country):
    all_posts = []
    seen = set()

    for query in country["social_queries"]:
        source_posts = []

        source_posts.extend(fetch_reddit_posts(query))
        source_posts.extend(fetch_bluesky_posts(query))
        source_posts.extend(fetch_mastodon_posts(query))

        for post in source_posts:
            key = post.get("url") or post.get("title")

            if not key:
                continue

            if key in seen:
                continue

            if not is_relevant(post, country["keywords"]):
                continue

            seen.add(key)
            all_posts.append(post)

    return all_posts[:80]


def analyze_social_posts(posts):
    mentions = len(posts)
    negative_hits = 0
    positive_hits = 0

    source_counts = {
        "Reddit": 0,
        "Bluesky": 0,
        "Mastodon": 0
    }

    for post in posts:
        text = post.get("title", "").lower()
        origin = post.get("origin", "")

        if origin in source_counts:
            source_counts[origin] += 1

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

    if posts:
        main_topic = posts[0].get("title", "")[:120]

    return {
        "score": score,
        "level": level,
        "mentions": mentions,
        "negative_hits": negative_hits,
        "positive_hits": positive_hits,
        "source_counts": source_counts,
        "main_topic": main_topic,
        "top_posts": posts[:5]
    }


def main():
    countries_output = []

    for country in COUNTRIES:
        print(f"Social adatgyűjtés: {country['name']}")

        posts = collect_social_posts(country)

        print(f"Social találatok száma: {len(posts)}")

        analysis = analyze_social_posts(posts)

        countries_output.append({
            "name": country["name"],
            "social_signal": analysis
        })

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "Reddit + Bluesky + Mastodon",
        "method_note": "A social signal külön jelző. Nem közvélemény-kutatás, és nem része a fő hírindexnek.",
        "countries": countries_output
    }

    with open(SOCIAL_LATEST_PATH, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print("social_latest.json sikeresen frissítve")


if __name__ == "__main__":
    main()
