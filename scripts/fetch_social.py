import json
import re
from datetime import datetime, timezone, timedelta
import email.utils
import feedparser

SOCIAL_LATEST_PATH = "docs/data/social_latest.json"
MAX_AGE_DAYS = 7

COUNTRIES = [
    {
        "name": "Szerbia",
        "keywords": ["serbia", "serbian", "srbija", "vucic", "vučić", "belgrade", "beograd"]
    },
    {
        "name": "Bosznia-Hercegovina",
        "keywords": ["bosnia", "bih", "sarajevo", "dodik", "republika srpska", "bosnia and herzegovina"]
    },
    {
        "name": "Koszovó",
        "keywords": ["kosovo", "kosova", "pristina", "prishtina", "kurti", "mitrovica"]
    },
    {
        "name": "Montenegró",
        "keywords": ["montenegro", "crna gora", "podgorica"]
    },
    {
        "name": "Észak-Macedónia",
        "keywords": ["north macedonia", "macedonia", "makedonija", "skopje"]
    },
    {
        "name": "Albánia",
        "keywords": ["albania", "albanian", "shqiperi", "shqipëria", "tirana", "edi rama"]
    }
]

FEEDS = [
    ("mastodon", "https://mastodon.social/tags/balkan.rss", "balkan"),
    ("mastodon", "https://mastodon.social/tags/balkans.rss", "balkans"),
    ("mastodon", "https://mastodon.social/tags/serbia.rss", "serbia"),
    ("mastodon", "https://mastodon.social/tags/kosovo.rss", "kosovo"),
    ("mastodon", "https://mastodon.social/tags/bosnia.rss", "bosnia"),
    ("mastodon", "https://mastodon.social/tags/montenegro.rss", "montenegro"),
    ("mastodon", "https://mastodon.social/tags/albania.rss", "albania"),
    ("mastodon", "https://mastodon.social/tags/macedonia.rss", "macedonia"),

    ("reddit", "https://www.reddit.com/r/serbia/.rss", "serbia"),
    ("reddit", "https://www.reddit.com/r/kosovo/.rss", "kosovo"),
    ("reddit", "https://www.reddit.com/r/bih/.rss", "bih"),
    ("reddit", "https://www.reddit.com/r/montenegro/.rss", "montenegro"),
    ("reddit", "https://www.reddit.com/r/albania/.rss", "albania"),
    ("reddit", "https://www.reddit.com/r/mkd/.rss", "mkd"),
    ("reddit", "https://www.reddit.com/r/AskBalkans/.rss", "askbalkans"),
    ("reddit", "https://www.reddit.com/r/europe/.rss", "europe"),
    ("reddit", "https://www.reddit.com/r/geopolitics/.rss", "geopolitics")
]

POLITICAL_WORDS = [
    "politics", "political", "government", "president", "prime minister",
    "minister", "parliament", "opposition", "election", "elections",
    "vote", "party", "coalition", "law", "court", "police",
    "protest", "protests", "democracy", "rule of law", "corruption",
    "eu", "european union", "nato", "accession", "enlargement",
    "dialogue", "border", "security", "sanctions", "violence",
    "crisis", "conflict", "tension", "war", "ethnic", "minority",
    "dodik", "vucic", "vučić", "kurti", "rama", "ohr", "kfor",
    "schmidt", "high representative", "special court", "serbia-eu",
    "kosovo-serbia", "balkan insight", "politico", "bbc", "united nations"
]

NOISE_WORDS = [
    "eurovision", "esc2026", "esc", "song contest", "song", "music",
    "festival", "photo", "photography", "foto", "travel", "tourism",
    "beach", "trip", "roadtrip", "landscape", "hotel", "monastery",
    "church", "food", "recipe", "football", "basketball", "gaming",
    "movie", "film", "concert", "holiday", "vacation", "infrared",
    "blackwhite", "blackandwhite", "river", "mountain", "dua lipa",
    "samsung", "doctorwho", "tardis", "ancient macedonia", "alexanderthegreat",
    "hellenistic", "history"
]

NEGATIVE_WORDS = [
    "protest", "crisis", "corruption", "violence", "conflict",
    "tension", "sanction", "arrest", "attack", "war", "unrest",
    "fraud", "dispute", "scandal", "threat", "instability",
    "clash", "riot", "boycott", "polarization", "separatism",
    "nationalism", "blocked", "deadlock", "police violence",
    "assault", "collapse", "resignation", "punitive"
]

POSITIVE_WORDS = [
    "agreement", "reform", "growth", "cooperation", "investment",
    "stability", "dialogue", "progress", "development", "support",
    "partnership", "integration", "talks", "deal", "funding",
    "membership", "negotiations", "eu accession", "joining the eu"
]


def strip_html(text):
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def parse_feed(url):
    feedparser.USER_AGENT = "Balkan-Political-Social-Monitor/1.0"
    return feedparser.parse(url)


def parse_date(value):
    if not value:
        return None

    try:
        parsed = email.utils.parsedate_to_datetime(value)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    except Exception:
        return None


def is_recent(published):
    parsed = parse_date(published)

    if not parsed:
        return False

    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

    return parsed >= cutoff


def has_any(text_lc, words):
    return any(word in text_lc for word in words)


def is_noise(text_lc):
    return has_any(text_lc, NOISE_WORDS)


def is_political(text_lc):
    return has_any(text_lc, POLITICAL_WORDS)


def match_country(text_lc):
    matched = []

    for country in COUNTRIES:
        for keyword in country["keywords"]:
            if keyword.lower() in text_lc:
                matched.append(country["name"])
                break

    return matched


def collect_posts():
    all_posts = []
    seen = set()

    for source_type, url, tag in FEEDS:
        print(f"Feed lekérése: {source_type} / {tag}")

        feed = parse_feed(url)
        entries = getattr(feed, "entries", [])

        print(f"Találatok: {len(entries)}")

        for entry in entries:
            title = getattr(entry, "title", "") or ""
            link = getattr(entry, "link", "") or ""
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
            published = getattr(entry, "published", "") or getattr(entry, "updated", "") or ""

            if not is_recent(published):
                continue

            text = f"{title} {summary}"
            text_plain = strip_html(text)
            text_lc = text_plain.lower()

            if is_noise(text_lc):
                continue

            if not is_political(text_lc):
                continue

            countries = match_country(text_lc)

            if not countries:
                continue

            key = link or text_plain[:160]

            if key in seen:
                continue

            seen.add(key)

            all_posts.append({
                "title": strip_html(title)[:180],
                "text": strip_html(summary)[:320],
                "url": link,
                "source": source_type,
                "tag": tag,
                "seen_date": published,
                "matched_countries": countries
            })

    return all_posts


def analyze_country(country_name, posts):
    related = [
        post for post in posts
        if country_name in post["matched_countries"]
    ]

    mentions = len(related)
    negative_hits = 0
    positive_hits = 0

    source_counts = {
        "reddit": 0,
        "mastodon": 0
    }

    tag_counts = {}

    for post in related:
        text = f"{post.get('title', '')} {post.get('text', '')}".lower()
        source = post.get("source", "")
        tag = post.get("tag", "")

        if source in source_counts:
            source_counts[source] += 1

        if tag:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        if has_any(text, NEGATIVE_WORDS):
            negative_hits += 1

        if has_any(text, POSITIVE_WORDS):
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

    if tag_counts:
        main_topic = max(tag_counts, key=tag_counts.get)

    return {
        "score": score,
        "level": level,
        "mentions": mentions,
        "negative_hits": negative_hits,
        "positive_hits": positive_hits,
        "source_counts": source_counts,
        "tag_counts": tag_counts,
        "main_topic": main_topic,
        "top_posts": related[:5]
    }


def main():
    print("Social RSS-források lekérése erős politikai szűréssel...")

    posts = collect_posts()

    print(f"Összes politikailag releváns social találat: {len(posts)}")

    countries_output = []

    for country in COUNTRIES:
        analysis = analyze_country(country["name"], posts)

        countries_output.append({
            "name": country["name"],
            "social_signal": analysis
        })

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "Reddit RSS + Mastodon hashtag RSS",
        "method_note": "A social signal külön jelző. Csak 7 napon belüli, politikailag releváns és zajszűrt találatokat számol. Nem közvélemény-kutatás, és nem része a fő hírindexnek.",
        "countries": countries_output
    }

    with open(SOCIAL_LATEST_PATH, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print("social_latest.json sikeresen frissítve")


if __name__ == "__main__":
    main()
