import json
import os
import re
import time
from datetime import datetime, timezone, timedelta
import email.utils

import feedparser
import requests


SOCIAL_LATEST_PATH = "docs/data/social_latest.json"
MAX_AGE_DAYS = 7

X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "").strip()
X_API_URL = "https://api.x.com/2/tweets/search/recent"
X_MAX_RESULTS_PER_QUERY = 10
X_SLEEP_SECONDS = 1


COUNTRIES = [
    {
        "name": "Szerbia",
        "x_query": "(Serbia OR Srbija OR Serbian OR Vucic OR Vučić OR Belgrade OR Beograd)",
        "keywords": ["serbia", "serbian", "srbija", "vucic", "vučić", "belgrade", "beograd"]
    },
    {
        "name": "Bosznia-Hercegovina",
        "x_query": "(Bosnia OR BiH OR Sarajevo OR Dodik OR \"Republika Srpska\" OR \"Bosnia and Herzegovina\")",
        "keywords": ["bosnia", "bih", "sarajevo", "dodik", "republika srpska", "bosnia and herzegovina"]
    },
    {
        "name": "Koszovó",
        "x_query": "(Kosovo OR Kosova OR Pristina OR Prishtina OR Kurti OR Mitrovica)",
        "keywords": ["kosovo", "kosova", "pristina", "prishtina", "kurti", "mitrovica"]
    },
    {
        "name": "Montenegró",
        "x_query": "(Montenegro OR \"Crna Gora\" OR Podgorica)",
        "keywords": ["montenegro", "crna gora", "podgorica"]
    },
    {
        "name": "Észak-Macedónia",
        "x_query": "(\"North Macedonia\" OR Macedonia OR Makedonija OR Skopje)",
        "keywords": ["north macedonia", "macedonia", "makedonija", "skopje"]
    },
    {
        "name": "Albánia",
        "x_query": "(Albania OR Albanian OR Shqiperi OR Shqipëria OR Tirana OR \"Edi Rama\")",
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
    "kosovo-serbia", "balkan insight", "politico", "bbc", "united nations",
    "state collapse", "peace envoy", "ruling party", "police violence",
    "minister of energy", "digital connectivity", "serbia-nato",
    "eu membership", "foreign agent", "constitutional court",
    "secession", "separatist", "referendum", "embassy", "diplomat",
    "geopolitical", "geopolitics", "rule-of-law", "rule of law",
    "organized crime", "media freedom", "press freedom", "judiciary"
]


NOISE_WORDS = [
    "eurovision", "esc2026", "esc", "song contest", "song", "music",
    "festival", "photo", "photography", "foto", "travel", "tourism",
    "beach", "trip", "roadtrip", "landscape", "hotel", "monastery",
    "church", "food", "recipe", "football", "basketball", "gaming",
    "movie", "film", "cinema", "concert", "holiday", "vacation",
    "infrared", "blackwhite", "blackandwhite", "river", "mountain",
    "dua lipa", "samsung", "doctorwho", "tardis", "ancient macedonia",
    "alexanderthegreat", "hellenistic", "history", "earthquake",
    "earth quake", "tërmet", "earthquake report", "travelphoto",
    "book", "books", "novel", "literature", "culture", "art",
    "gallery", "museum", "weather", "sports", "ukraine",
    "latin americans", "google gemini", "cybersecurity review",
    "crypto", "bitcoin", "airdrop", "giveaway", "onlyfans", "porn",
    "casino", "betting", "slot", "trading signal", "nft", "meme coin"
]


NEGATIVE_WORDS = [
    "protest", "crisis", "corruption", "violence", "conflict",
    "tension", "sanction", "arrest", "attack", "war", "unrest",
    "fraud", "dispute", "scandal", "threat", "instability",
    "clash", "riot", "boycott", "polarization", "separatism",
    "nationalism", "blocked", "deadlock", "police violence",
    "assault", "collapse", "resignation", "punitive", "detention",
    "crackdown", "authoritarian", "ethnic tension", "border incident"
]


POSITIVE_WORDS = [
    "agreement", "reform", "growth", "cooperation", "investment",
    "stability", "dialogue", "progress", "development", "support",
    "partnership", "integration", "talks", "deal", "funding",
    "membership", "negotiations", "eu accession", "joining the eu",
    "stabilization", "peace process", "reconciliation"
]


def strip_html(text):
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_text(text):
    text = strip_html(text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"#", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_feed(url):
    feedparser.USER_AGENT = "Balkan-Political-Social-Monitor/1.1"
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


def parse_iso_date(value):
    if not value:
        return None

    try:
        value = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(value)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    except Exception:
        return None


def is_recent(published):
    parsed = parse_date(published) or parse_iso_date(published)

    if not parsed:
        return False

    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

    return parsed >= cutoff


def has_any(text_lc, words):
    return any(word in text_lc for word in words)


def count_hits(text_lc, words):
    return sum(1 for word in words if word in text_lc)


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


def passes_quality_filter(text_lc, countries):
    if not countries:
        return False

    if is_noise(text_lc):
        return False

    political_hits = count_hits(text_lc, POLITICAL_WORDS)
    negative_hits = count_hits(text_lc, NEGATIVE_WORDS)
    positive_hits = count_hits(text_lc, POSITIVE_WORDS)

    if political_hits >= 1:
        return True

    if negative_hits >= 1 or positive_hits >= 1:
        return True

    return False


def collect_rss_posts():
    all_posts = []
    seen = set()

    for source_type, url, tag in FEEDS:
        print(f"Feed lekérése: {source_type} / {tag}")

        try:
            feed = parse_feed(url)
            entries = getattr(feed, "entries", [])
        except Exception as exc:
            print(f"Hiba a feed lekérésekor: {source_type} / {tag} / {exc}")
            continue

        print(f"Találatok: {len(entries)}")

        for entry in entries:
            title = getattr(entry, "title", "") or ""
            link = getattr(entry, "link", "") or ""
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
            published = getattr(entry, "published", "") or getattr(entry, "updated", "") or ""

            if not is_recent(published):
                continue

            text = f"{title} {summary}"
            text_plain = normalize_text(text)
            text_lc = text_plain.lower()

            countries = match_country(text_lc)

            if not passes_quality_filter(text_lc, countries):
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
                "matched_countries": countries,
                "engagement": 0,
                "quality": "rss_filtered"
            })

    return all_posts


def build_x_query(country):
    base = country["x_query"]

    political_context = (
        "(politics OR government OR protest OR election OR corruption OR "
        "EU OR NATO OR security OR crisis OR tension OR parliament OR president "
        "OR minister OR opposition OR police OR sanctions OR dialogue OR border "
        "OR democracy OR \"rule of law\")"
    )

    return (
        f"{base} {political_context} "
        "-is:retweet -is:reply lang:en"
    )


def collect_x_posts():
    if not X_BEARER_TOKEN:
        print("X_BEARER_TOKEN nincs beállítva. X lekérés kihagyva.")
        return [], {
            "enabled": False,
            "status": "missing_token",
            "message": "X_BEARER_TOKEN nincs beállítva, ezért az X forrás kimaradt."
        }

    headers = {
        "Authorization": f"Bearer {X_BEARER_TOKEN}",
        "User-Agent": "Balkan-Political-Social-Monitor/1.1"
    }

    all_posts = []
    errors = []

    for country in COUNTRIES:
        query = build_x_query(country)

        params = {
            "query": query,
            "max_results": X_MAX_RESULTS_PER_QUERY,
            "tweet.fields": "created_at,lang,public_metrics",
            "expansions": "author_id"
        }

        print(f"X lekérés: {country['name']}")

        try:
            response = requests.get(
                X_API_URL,
                headers=headers,
                params=params,
                timeout=30
            )

            if response.status_code == 429:
                print("X API rate limit. X lekérés megszakítva, RSS források ettől még működnek.")
                errors.append({
                    "country": country["name"],
                    "status_code": response.status_code,
                    "message": "rate_limit"
                })
                break

            if response.status_code != 200:
                print(f"X API hiba: {country['name']} / {response.status_code} / {response.text[:300]}")
                errors.append({
                    "country": country["name"],
                    "status_code": response.status_code,
                    "message": response.text[:300]
                })
                continue

            data = response.json()
            tweets = data.get("data", [])

            for tweet in tweets:
                tweet_id = tweet.get("id", "")
                text = tweet.get("text", "")
                created_at = tweet.get("created_at", "")

                if not is_recent(created_at):
                    continue

                text_plain = normalize_text(text)
                text_lc = text_plain.lower()

                countries = match_country(text_lc)

                if country["name"] not in countries:
                    countries.append(country["name"])

                if not passes_quality_filter(text_lc, countries):
                    continue

                metrics = tweet.get("public_metrics", {}) or {}
                likes = int(metrics.get("like_count", 0) or 0)
                reposts = int(metrics.get("retweet_count", 0) or 0)
                replies = int(metrics.get("reply_count", 0) or 0)
                quotes = int(metrics.get("quote_count", 0) or 0)

                engagement = likes + reposts + replies + quotes

                all_posts.append({
                    "title": text_plain[:180],
                    "text": text_plain[:320],
                    "url": f"https://x.com/i/web/status/{tweet_id}" if tweet_id else "",
                    "source": "x",
                    "tag": country["name"],
                    "seen_date": created_at,
                    "matched_countries": countries,
                    "engagement": engagement,
                    "metrics": {
                        "likes": likes,
                        "reposts": reposts,
                        "replies": replies,
                        "quotes": quotes
                    },
                    "quality": "x_api_filtered"
                })

            time.sleep(X_SLEEP_SECONDS)

        except Exception as exc:
            print(f"X lekérési kivétel: {country['name']} / {exc}")
            errors.append({
                "country": country["name"],
                "status_code": "exception",
                "message": str(exc)[:300]
            })
            continue

    status = "ok" if not errors else "partial_error"

    return all_posts, {
        "enabled": True,
        "status": status,
        "errors": errors,
        "collected": len(all_posts)
    }


def deduplicate_posts(posts):
    deduped = []
    seen = set()

    for post in posts:
        url = post.get("url", "")
        title = post.get("title", "")
        text = post.get("text", "")
        key = url or f"{title} {text}"[:180]

        if key in seen:
            continue

        seen.add(key)
        deduped.append(post)

    return deduped


def analyze_country(country_name, posts):
    related = [
        post for post in posts
        if country_name in post.get("matched_countries", [])
    ]

    mentions = len(related)
    negative_hits = 0
    positive_hits = 0
    engagement_total = 0

    source_counts = {
        "reddit": 0,
        "mastodon": 0,
        "x": 0
    }

    tag_counts = {}

    for post in related:
        text = f"{post.get('title', '')} {post.get('text', '')}".lower()
        source = post.get("source", "")
        tag = post.get("tag", "")
        engagement_total += int(post.get("engagement", 0) or 0)

        if source in source_counts:
            source_counts[source] += 1
        else:
            source_counts[source] = source_counts.get(source, 0) + 1

        if tag:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        if has_any(text, NEGATIVE_WORDS):
            negative_hits += 1

        if has_any(text, POSITIVE_WORDS):
            positive_hits += 1

    engagement_bonus = min(engagement_total // 20, 5)

    raw_score = mentions + (negative_hits * 3) + (positive_hits * 2) + engagement_bonus
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

    related_sorted = sorted(
        related,
        key=lambda item: int(item.get("engagement", 0) or 0),
        reverse=True
    )

    return {
        "score": score,
        "level": level,
        "mentions": mentions,
        "negative_hits": negative_hits,
        "positive_hits": positive_hits,
        "engagement_total": engagement_total,
        "source_counts": source_counts,
        "tag_counts": tag_counts,
        "main_topic": main_topic,
        "top_posts": related_sorted[:5]
    }


def main():
    print("Social források lekérése erős politikai szűréssel...")

    rss_posts = collect_rss_posts()
    print(f"RSS alapú politikailag releváns social találat: {len(rss_posts)}")

    x_posts, x_status = collect_x_posts()
    print(f"X alapú politikailag releváns social találat: {len(x_posts)}")

    posts = deduplicate_posts(rss_posts + x_posts)
    print(f"Összes politikailag releváns social találat deduplikálás után: {len(posts)}")

    countries_output = []

    for country in COUNTRIES:
        analysis = analyze_country(country["name"], posts)

        countries_output.append({
            "name": country["name"],
            "social_signal": analysis
        })

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "Reddit RSS + Mastodon hashtag RSS + X API",
        "method_note": (
            "A social signal külön jelző. Csak 7 napon belüli, politikailag releváns "
            "és zajszűrt találatokat számol. Nem közvélemény-kutatás, és nem része "
            "a fő hírindexnek. Az X API opcionális: ha nem érhető el vagy hibát ad, "
            "a Reddit és Mastodon RSS-források továbbra is frissülnek."
        ),
        "x_status": x_status,
        "countries": countries_output
    }

    with open(SOCIAL_LATEST_PATH, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print("social_latest.json sikeresen frissítve")


if __name__ == "__main__":
    main()
