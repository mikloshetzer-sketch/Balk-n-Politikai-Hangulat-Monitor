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
        "keywords": ["serbia", "serbian", "srbija", "vucic", "vučić", "belgrade", "beograd"],
        "strong_keywords": ["vucic", "vučić", "belgrade", "beograd", "srbija", "serbian president"]
    },
    {
        "name": "Bosznia-Hercegovina",
        "x_query": "(Bosnia OR BiH OR Sarajevo OR Dodik OR \"Republika Srpska\" OR \"Bosnia and Herzegovina\")",
        "keywords": ["bosnia", "bih", "sarajevo", "dodik", "republika srpska", "bosnia and herzegovina"],
        "strong_keywords": ["dodik", "republika srpska", "sarajevo", "ohr", "high representative"]
    },
    {
        "name": "Koszovó",
        "x_query": "(Kosovo OR Kosova OR Pristina OR Prishtina OR Kurti OR Mitrovica)",
        "keywords": ["kosovo", "kosova", "pristina", "prishtina", "kurti", "mitrovica"],
        "strong_keywords": ["kurti", "pristina", "prishtina", "mitrovica", "belgrade-pristina"]
    },
    {
        "name": "Montenegró",
        "x_query": "(Montenegro OR \"Crna Gora\" OR Podgorica)",
        "keywords": ["montenegro", "crna gora", "podgorica"],
        "strong_keywords": ["podgorica", "crna gora", "djukanovic", "đukanović", "montenegrin"]
    },
    {
        "name": "Észak-Macedónia",
        "x_query": "(\"North Macedonia\" OR Macedonia OR Makedonija OR Skopje OR Mickoski)",
        "keywords": ["north macedonia", "macedonia", "makedonija", "skopje", "mickoski"],
        "strong_keywords": ["north macedonia", "skopje", "mickoski", "bulgarians in the constitution"]
    },
    {
        "name": "Albánia",
        "x_query": "(Albania OR Albanian OR Shqiperi OR Shqipëria OR Tirana OR \"Edi Rama\")",
        "keywords": ["albania", "albanian", "shqiperi", "shqipëria", "tirana", "edi rama"],
        "strong_keywords": ["tirana", "edi rama", "albanian government", "albania-eu"]
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


EVENT_CATEGORIES = {
    "eu_integration": [
        "eu accession", "european union", "enlargement", "membership",
        "intergovernmental conference", "accession process", "cluster chapters",
        "negotiations", "eu integration", "candidate country", "brussels"
    ],
    "security": [
        "security", "border", "kfor", "nato", "military", "defence",
        "defense", "police", "salw", "peacekeeping", "stability",
        "armed", "attack", "incident", "troops"
    ],
    "government_crisis": [
        "resignation", "government crisis", "collapse", "prime minister",
        "president", "parliament", "ruling party", "opposition",
        "constitutional", "declaration", "veto", "blocked"
    ],
    "protest": [
        "protest", "protests", "demonstration", "rally", "unrest",
        "riot", "boycott", "march", "strike"
    ],
    "corruption_rule_of_law": [
        "corruption", "anti-corruption", "judiciary", "rule of law",
        "court", "fraud", "scandal", "organized crime", "media freedom",
        "press freedom", "benchmarking"
    ],
    "ethnic_tension": [
        "ethnic", "minority", "republika srpska", "bulgarians",
        "albanian language", "serb entity", "recognition",
        "normalization", "belgrade-pristina"
    ],
    "foreign_influence": [
        "russia", "china", "turkey", "usa", "united states",
        "embassy", "sanctions", "geopolitical", "foreign influence"
    ],
    "migration": [
        "migration", "asylum", "migrants", "refugees", "border management"
    ],
    "economic_infrastructure": [
        "investment", "infrastructure", "energy", "transport",
        "trade", "growth", "funding", "development"
    ]
}


CATEGORY_WEIGHTS = {
    "ethnic_tension": 10,
    "security": 9,
    "government_crisis": 9,
    "protest": 8,
    "corruption_rule_of_law": 8,
    "foreign_influence": 8,
    "eu_integration": 6,
    "migration": 6,
    "economic_infrastructure": 4
}


RISK_CATEGORY_WEIGHTS = {
    "ethnic_tension": 5,
    "security": 4,
    "government_crisis": 4,
    "protest": 4,
    "corruption_rule_of_law": 3,
    "foreign_influence": 3,
    "migration": 2,
    "eu_integration": 1,
    "economic_infrastructure": 1
}


NEGATIVE_WORDS = [
    "protest", "crisis", "corruption", "violence", "conflict", "tension",
    "sanction", "arrest", "attack", "war", "unrest", "fraud", "dispute",
    "scandal", "threat", "instability", "clash", "riot", "boycott",
    "polarization", "separatism", "nationalism", "blocked", "deadlock",
    "police violence", "collapse", "resignation", "detention",
    "crackdown", "authoritarian", "ethnic tension", "border incident",
    "indictment", "abuse", "pressure", "intimidation", "destabilization",
    "proxy", "occupation", "apartheid", "humiliating", "tyranny"
]


POSITIVE_WORDS = [
    "agreement", "reform", "growth", "cooperation", "investment",
    "stability", "dialogue", "progress", "development", "support",
    "partnership", "integration", "talks", "deal", "funding",
    "membership", "negotiations", "eu accession", "joining the eu",
    "stabilization", "peace process", "reconciliation"
]


NOISE_WORDS = [
    "eurovision", "song contest", "music", "festival", "photo",
    "photography", "travel", "tourism", "beach", "trip", "roadtrip",
    "landscape", "hotel", "food", "recipe", "football", "basketball",
    "gaming", "movie", "film", "concert", "holiday", "vacation",
    "ancient macedonia", "alexanderthegreat", "hellenistic",
    "earthquake", "earth quake", "weather", "sports", "crypto",
    "bitcoin", "airdrop", "giveaway", "onlyfans", "casino", "betting",
    "nft", "meme coin", "superhero", "superheroes", "fictional universe",
    "paranormal", "cheap way", "train from", "bus from", "flight",
    "airport", "discord channel", "weekly free-for-all",
    "casual conversations", "childhood memory", "restaurant",
    "dating", "moving to", "visa question", "tourist", "itinerary",
    "upsc", "prelims", "ias", "exam", "quiz", "trivia",
    "amazon", "amazondeals", "fashion", "womenfashion", "ethnicwear",
    "buy here", "off on amazon", "discount", "sale", "coupon"
]


LOW_QUALITY_PATTERNS = [
    "weekly free-for-all", "casual conversations", "what would be",
    "what do you think", "how do i get", "cheap way", "travel to",
    "moving to", "visiting", "tourist", "superheroes",
    "fictional universe", "childhood memory", "normal childhood",
    "discord channel", "where can i buy", "restaurant", "hotel",
    "airport", "train station", "bus ticket", "song", "movie",
    "football", "basketball", "correct answer", "upsc", "prelims",
    "currentaffairs", "ias", "amazonfinds", "buy here"
]


TRUSTED_SOURCE_HINTS = [
    "balkaninsight.com", "balkan insight", "euractiv", "politico",
    "reuters", "apnews", "associated press", "bbc", "dw.com",
    "rferl", "rfe/rl", "aljazeera", "euronews", "consilium.europa.eu",
    "eucouncil", "european commission", "eu commission", "nato",
    "osce", "united nations", "undp", "guardian", "theguardian.com",
    "bne intellinews", "intellinews"
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
    feedparser.USER_AGENT = "Balkan-Political-Social-Monitor/1.4"
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
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
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


def is_low_quality(text_lc):
    return has_any(text_lc, LOW_QUALITY_PATTERNS)


def is_trusted_source(text_lc):
    return has_any(text_lc, TRUSTED_SOURCE_HINTS)


def detect_event_categories(text_lc):
    categories = []
    for category, keywords in EVENT_CATEGORIES.items():
        hits = count_hits(text_lc, keywords)
        if hits > 0:
            categories.append({
                "category": category,
                "hits": hits,
                "weight": CATEGORY_WEIGHTS.get(category, 5)
            })

    categories = sorted(
        categories,
        key=lambda item: (item["weight"], item["hits"]),
        reverse=True
    )

    return categories


def main_event_category(text_lc):
    categories = detect_event_categories(text_lc)
    if not categories:
        return "uncategorized"
    return categories[0]["category"]


def geopolitical_score(text_lc):
    categories = detect_event_categories(text_lc)
    if not categories:
        return 0

    score = 0

    for item in categories:
        score += item["weight"] * item["hits"]

    if is_trusted_source(text_lc):
        score += 4

    if has_any(text_lc, NEGATIVE_WORDS):
        score += 3

    if has_any(text_lc, POSITIVE_WORDS):
        score += 1

    if is_noise(text_lc):
        score -= 12

    if is_low_quality(text_lc):
        score -= 14

    return max(score, 0)


def match_country_with_confidence(text_lc):
    results = []

    for country in COUNTRIES:
        weak_hits = count_hits(text_lc, country["keywords"])
        strong_hits = count_hits(text_lc, country["strong_keywords"])

        if weak_hits == 0 and strong_hits == 0:
            continue

        confidence = weak_hits + (strong_hits * 3)

        if country["name"] == "Észak-Macedónia":
            if "ancient macedonia" in text_lc or "alexander the great" in text_lc:
                confidence = 0

        if confidence > 0:
            results.append({
                "name": country["name"],
                "confidence": confidence
            })

    results = sorted(results, key=lambda item: item["confidence"], reverse=True)
    return results


def filtered_country_matches(text_lc, source_type):
    matches = match_country_with_confidence(text_lc)

    if not matches:
        return [], {}

    top_confidence = matches[0]["confidence"]
    accepted = []

    for item in matches:
        name = item["name"]
        confidence = item["confidence"]

        if source_type == "x":
            if confidence >= 3:
                accepted.append(name)
            elif confidence >= 2 and confidence >= top_confidence:
                accepted.append(name)
        else:
            if confidence >= 2:
                accepted.append(name)
            elif confidence >= 1 and top_confidence <= 2:
                accepted.append(name)

    if len(accepted) > 3:
        accepted = accepted[:3]

    confidence_map = {item["name"]: item["confidence"] for item in matches}

    return accepted, confidence_map


def source_reliability(text_lc, source_type):
    if is_trusted_source(text_lc):
        return 5
    if source_type == "mastodon":
        return 3
    if source_type == "x":
        return 2
    if source_type == "reddit":
        return 1
    return 1


def quality_score(text_lc, source_type):
    score = geopolitical_score(text_lc)

    if source_type == "reddit":
        score -= 2

    if source_type == "x":
        score -= 1

    score += source_reliability(text_lc, source_type)

    return max(score, 0)


def passes_quality_filter(text_lc, countries, source_type):
    if not countries:
        return False

    if is_noise(text_lc):
        return False

    if is_low_quality(text_lc):
        return False

    categories = detect_event_categories(text_lc)

    if not categories:
        return False

    g_score = geopolitical_score(text_lc)
    q_score = quality_score(text_lc, source_type)

    if source_type == "x":
        return g_score >= 9 and q_score >= 9

    if source_type == "reddit":
        return g_score >= 9 and q_score >= 8

    if source_type == "mastodon":
        return g_score >= 6 and q_score >= 6

    return g_score >= 8


def capped_engagement(metrics):
    likes = int(metrics.get("like_count", 0) or 0)
    reposts = int(metrics.get("retweet_count", 0) or 0)
    replies = int(metrics.get("reply_count", 0) or 0)
    quotes = int(metrics.get("quote_count", 0) or 0)

    raw = likes + reposts + replies + quotes
    capped = min(raw, 120)

    return raw, capped, {
        "likes": likes,
        "reposts": reposts,
        "replies": replies,
        "quotes": quotes
    }


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

            full_text = f"{title} {summary} {link}"
            text_plain = normalize_text(full_text)
            text_lc = text_plain.lower()

            countries, confidence_map = filtered_country_matches(text_lc, source_type)

            if not passes_quality_filter(text_lc, countries, source_type):
                continue

            key = link or text_plain[:180]
            if key in seen:
                continue

            seen.add(key)

            all_posts.append({
                "title": strip_html(title)[:180],
                "text": strip_html(summary)[:360],
                "url": link,
                "source": source_type,
                "tag": tag,
                "seen_date": published,
                "matched_countries": countries,
                "country_confidence": confidence_map,
                "event_category": main_event_category(text_lc),
                "event_categories": detect_event_categories(text_lc),
                "geopolitical_score": geopolitical_score(text_lc),
                "quality_score": quality_score(text_lc, source_type),
                "source_reliability": source_reliability(text_lc, source_type),
                "trusted_source_hint": is_trusted_source(text_lc),
                "engagement": 0,
                "raw_engagement": 0,
                "quality": "rss_filtered"
            })

    return all_posts


def build_x_query(country):
    base = country["x_query"]

    political_context = (
        "(government OR protest OR election OR corruption OR EU OR NATO OR security "
        "OR crisis OR tension OR parliament OR president OR minister OR opposition "
        "OR police OR sanctions OR dialogue OR border OR democracy OR \"rule of law\" "
        "OR accession OR enlargement OR judiciary OR ethnic OR minority)"
    )

    exclusions = (
        "-is:retweet -is:reply "
        "-upsc -exam -quiz -football -basketball -travel -tourism -crypto "
        "-casino -amazon -fashion -discount -sale -coupon"
    )

    return f"{base} {political_context} {exclusions} lang:en"


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
        "User-Agent": "Balkan-Political-Social-Monitor/1.4"
    }

    all_posts = []
    errors = []

    for country in COUNTRIES:
        query = build_x_query(country)

        params = {
            "query": query,
            "max_results": X_MAX_RESULTS_PER_QUERY,
            "tweet.fields": "created_at,lang,public_metrics"
        }

        print(f"X lekérés: {country['name']}")

        try:
            response = requests.get(
                X_API_URL,
                headers=headers,
                params=params,
                timeout=30
            )

            if response.status_code == 402:
                print("X API kredit elfogyott. X lekérés megszakítva.")
                errors.append({
                    "country": country["name"],
                    "status_code": response.status_code,
                    "message": response.text[:300]
                })
                break

            if response.status_code == 429:
                print("X API rate limit. X lekérés megszakítva.")
                errors.append({
                    "country": country["name"],
                    "status_code": response.status_code,
                    "message": "rate_limit"
                })
                break

            if response.status_code != 200:
                print(f"X API hiba: {country['name']} / {response.status_code}")
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

                countries, confidence_map = filtered_country_matches(text_lc, "x")

                if country["name"] not in countries:
                    own_conf = confidence_map.get(country["name"], 0)
                    if own_conf >= 3:
                        countries.append(country["name"])

                if not passes_quality_filter(text_lc, countries, "x"):
                    continue

                raw_engagement, engagement, metrics = capped_engagement(
                    tweet.get("public_metrics", {}) or {}
                )

                all_posts.append({
                    "title": text_plain[:180],
                    "text": text_plain[:360],
                    "url": f"https://x.com/i/web/status/{tweet_id}" if tweet_id else "",
                    "source": "x",
                    "tag": country["name"],
                    "seen_date": created_at,
                    "matched_countries": countries,
                    "country_confidence": confidence_map,
                    "event_category": main_event_category(text_lc),
                    "event_categories": detect_event_categories(text_lc),
                    "geopolitical_score": geopolitical_score(text_lc),
                    "quality_score": quality_score(text_lc, "x"),
                    "source_reliability": source_reliability(text_lc, "x"),
                    "trusted_source_hint": is_trusted_source(text_lc),
                    "engagement": engagement,
                    "raw_engagement": raw_engagement,
                    "metrics": metrics,
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

    return all_posts, {
        "enabled": True,
        "status": "ok" if not errors else "partial_error",
        "errors": errors,
        "collected": len(all_posts)
    }


def deduplicate_posts(posts):
    deduped = []
    seen_urls = set()
    seen_texts = set()

    for post in posts:
        url = post.get("url", "")
        text = normalize_text(f"{post.get('title', '')} {post.get('text', '')}").lower()
        text_key = text[:220]

        if url and url in seen_urls:
            continue

        if text_key in seen_texts:
            continue

        if url:
            seen_urls.add(url)

        seen_texts.add(text_key)
        deduped.append(post)

    return deduped


def calculate_risk_score(
    mentions,
    negative_hits,
    positive_hits,
    trusted_hits,
    engagement_total,
    quality_total,
    geopolitical_total,
    category_counts
):
    engagement_bonus = min(engagement_total // 40, 3)
    trusted_bonus = min(trusted_hits, 4)
    quality_bonus = min(quality_total // 25, 5)
    geopolitical_bonus = min(geopolitical_total // 30, 6)

    risk_category_bonus = 0

    for category, count in category_counts.items():
        weight = RISK_CATEGORY_WEIGHTS.get(category, 1)
        risk_category_bonus += count * weight

    positive_balance_penalty = min(positive_hits * 2, 10)

    raw_score = (
        mentions
        + negative_hits * 4
        + risk_category_bonus
        + engagement_bonus
        + trusted_bonus
        + quality_bonus
        + geopolitical_bonus
        - positive_balance_penalty
    )

    return max(0, min(raw_score, 60))


def classify_risk_level(score):
    if score >= 40:
        return "high"
    if score >= 20:
        return "medium"
    return "low"


def analyze_country(country_name, posts):
    related = [
        post for post in posts
        if country_name in post.get("matched_countries", [])
    ]

    mentions = len(related)
    negative_hits = 0
    positive_hits = 0
    trusted_hits = 0
    engagement_total = 0
    raw_engagement_total = 0
    quality_total = 0
    geopolitical_total = 0

    source_counts = {
        "reddit": 0,
        "mastodon": 0,
        "x": 0
    }

    category_counts = {}
    tag_counts = {}

    for post in related:
        text = f"{post.get('title', '')} {post.get('text', '')}".lower()
        source = post.get("source", "")
        tag = post.get("tag", "")
        category = post.get("event_category", "uncategorized")

        engagement_total += int(post.get("engagement", 0) or 0)
        raw_engagement_total += int(post.get("raw_engagement", 0) or 0)
        quality_total += int(post.get("quality_score", 0) or 0)
        geopolitical_total += int(post.get("geopolitical_score", 0) or 0)

        if post.get("trusted_source_hint"):
            trusted_hits += 1

        source_counts[source] = source_counts.get(source, 0) + 1

        if tag:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        if category:
            category_counts[category] = category_counts.get(category, 0) + 1

        if has_any(text, NEGATIVE_WORDS):
            negative_hits += 1

        if has_any(text, POSITIVE_WORDS):
            positive_hits += 1

    score = calculate_risk_score(
        mentions=mentions,
        negative_hits=negative_hits,
        positive_hits=positive_hits,
        trusted_hits=trusted_hits,
        engagement_total=engagement_total,
        quality_total=quality_total,
        geopolitical_total=geopolitical_total,
        category_counts=category_counts
    )

    level = classify_risk_level(score)

    main_topic = "nincs adat"
    if category_counts:
        main_topic = max(category_counts, key=category_counts.get)

    related_sorted = sorted(
        related,
        key=lambda item: (
            int(item.get("quality_score", 0) or 0),
            int(item.get("geopolitical_score", 0) or 0),
            int(item.get("engagement", 0) or 0)
        ),
        reverse=True
    )

    return {
        "score": score,
        "level": level,
        "scale": "0-60 risk index",
        "mentions": mentions,
        "negative_hits": negative_hits,
        "positive_hits": positive_hits,
        "trusted_hits": trusted_hits,
        "engagement_total": engagement_total,
        "raw_engagement_total": raw_engagement_total,
        "quality_total": quality_total,
        "geopolitical_total": geopolitical_total,
        "source_counts": source_counts,
        "category_counts": category_counts,
        "tag_counts": tag_counts,
        "main_topic": main_topic,
        "top_posts": related_sorted[:5]
    }


def main():
    print("Social források lekérése érzékenyebb geopolitikai risk indexszel...")

    rss_posts = collect_rss_posts()
    print(f"RSS alapú geopolitikailag releváns social találat: {len(rss_posts)}")

    x_posts, x_status = collect_x_posts()
    print(f"X alapú geopolitikailag releváns social találat: {len(x_posts)}")

    posts = deduplicate_posts(rss_posts + x_posts)
    print(f"Összes találat deduplikálás után: {len(posts)}")

    countries_output = []

    for country in COUNTRIES:
        countries_output.append({
            "name": country["name"],
            "social_signal": analyze_country(country["name"], posts)
        })

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "Reddit RSS + Mastodon hashtag RSS + optional X API",
        "method_note": (
            "A social signal külön geopolitikai kockázati jelző. A rendszer 7 napon belüli, "
            "ország szerint illesztett, kategorizált és zajszűrt posztokat számol. "
            "Nem közvélemény-kutatás, és nem része közvetlenül a fő hírindexnek. "
            "Az új social score 0-60 skálájú risk index. A negatív, biztonsági, "
            "etnikai feszültségi, kormányzati válság, tiltakozási, korrupciós és külső "
            "befolyási jeleket erősebben súlyozza. A pozitív integrációs vagy együttműködési "
            "jelek csökkentik a kockázati pontszámot."
        ),
        "x_status": x_status,
        "countries": countries_output
    }

    with open(SOCIAL_LATEST_PATH, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print("social_latest.json sikeresen frissítve")


if __name__ == "__main__":
    main()
