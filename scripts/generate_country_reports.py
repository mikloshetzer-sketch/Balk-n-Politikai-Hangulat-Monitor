import json
import os
import re
from datetime import datetime, timezone

LATEST_PATH = "docs/data/latest.json"
SOCIAL_PATH = "docs/data/social_latest.json"
REPORTS_DIR = "docs/reports"
REPORTS_INDEX_PATH = "docs/data/reports_index.json"


def slugify(text):
    text = text.lower()
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ö": "o",
        "ő": "o", "ú": "u", "ü": "u", "ű": "u",
        "–": "-", " ": "-"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^a-z0-9\-]", "", text)
    text = re.sub(r"-+", "-", text)

    return text.strip("-")


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_social_signal(country_name, social_data):
    for item in social_data.get("countries", []):
        if item.get("name") == country_name:
            return item.get("social_signal", {})

    return {
        "score": 0,
        "level": "low",
        "mentions": 0,
        "negative_hits": 0,
        "positive_hits": 0,
        "main_topic": "nincs adat",
        "source_counts": {}
    }


def get_status_text(status):
    if status == "positive":
        return "pozitív"
    if status == "negative":
        return "negatív"
    return "semleges"


def get_social_level_text(level):
    if level == "high":
        return "magas"
    if level == "medium":
        return "közepes"
    return "alacsony"


def build_topic_paragraphs(topic_scores):
    if not topic_scores:
        return "<p>Nincs elég adat a domináns narratívák részletes értékeléséhez.</p>"

    paragraphs = []

    for index, (topic, score) in enumerate(list(topic_scores.items())[:4], start=1):
        paragraphs.append(f"""
        <div class="topic-block">
          <h3>{index}. {topic}</h3>
          <p>
            Ez a narratíva jelenleg <strong>{score}</strong> súlyponttal szerepel az ország híralapú mintájában.
            A magasabb érték azt jelzi, hogy a témához kapcsolódó kulcsszavak több releváns cikkben is megjelentek.
            Ez nem közvélemény-kutatási adat, hanem nyílt forrású hírfigyelésből képzett jelzés.
          </p>
        </div>
        """)

    return "\n".join(paragraphs)


def build_articles_list(articles):
    if not articles:
        return "<p>Nincs megjeleníthető kiemelt cikk.</p>"

    items = []

    for article in articles[:5]:
        title = article.get("title", "Cím nélkül")
        url = article.get("url", "#")
        source = article.get("source", "ismeretlen forrás")

        items.append(f"""
        <li>
          <a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>
          <br>
          <span>{source}</span>
        </li>
        """)

    return f"<ul>{''.join(items)}</ul>"


def build_report_html(country, social_signal, updated_at):
    name = country.get("name", "")
    score = country.get("score", 0)
    status = country.get("status", "neutral")
    main_topic = country.get("main_topic", "nincs adat")
    topic_scores = country.get("topic_scores", {})
    article_count = country.get("article_count", 0)
    negative_hits = country.get("negative_hits", 0)
    positive_hits = country.get("positive_hits", 0)
    top_articles = country.get("top_articles", [])

    social_score = social_signal.get("score", 0)
    social_level = social_signal.get("level", "low")
    social_mentions = social_signal.get("mentions", 0)
    social_negative = social_signal.get("negative_hits", 0)
    social_positive = social_signal.get("positive_hits", 0)
    social_topic = social_signal.get("main_topic", "nincs adat")
    source_counts = social_signal.get("source_counts", {})

    topic_blocks = build_topic_paragraphs(topic_scores)
    articles_html = build_articles_list(top_articles)

    return f"""<!DOCTYPE html>
<html lang="hu">
<head>
  <meta charset="UTF-8">
  <title>{name} – szöveges helyzetkép</title>
  <style>
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: #f3f4f6;
      color: #111827;
      line-height: 1.6;
    }}

    main {{
      max-width: 920px;
      margin: 30px auto;
      padding: 0 16px;
    }}

    .card {{
      background: white;
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    }}

    h1 {{
      margin-top: 0;
      font-size: 30px;
    }}

    h2 {{
      margin-top: 28px;
      border-bottom: 1px solid #e5e7eb;
      padding-bottom: 6px;
    }}

    .meta {{
      color: #6b7280;
      font-size: 14px;
    }}

    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin: 20px 0;
    }}

    .box {{
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 12px;
    }}

    .box strong {{
      display: block;
      font-size: 22px;
      margin-top: 4px;
    }}

    .topic-block {{
      background: #f9fafb;
      border-left: 5px solid #2563eb;
      padding: 14px;
      border-radius: 10px;
      margin-bottom: 14px;
    }}

    ul {{
      padding-left: 20px;
    }}

    li {{
      margin-bottom: 10px;
    }}

    a {{
      color: #2563eb;
      text-decoration: none;
    }}

    a:hover {{
      text-decoration: underline;
    }}

    .back {{
      display: inline-block;
      margin-bottom: 16px;
      color: #2563eb;
      text-decoration: none;
      font-size: 14px;
    }}
  </style>
</head>

<body>
<main>
  <a class="back" href="../index.html">← Vissza a dashboardra</a>

  <div class="card">
    <h1>{name} – szöveges helyzetkép</h1>
    <p class="meta">Frissítve: {updated_at}</p>

    <p>
      Az aktuális híralapú hangulatindex <strong>{score}</strong>, amelynek státusza:
      <strong>{get_status_text(status)}</strong>. A fő hírnarratíva jelenleg:
      <strong>{main_topic}</strong>.
    </p>

    <div class="summary-grid">
      <div class="box">Hírindex<strong>{score}</strong></div>
      <div class="box">Cikkek száma<strong>{article_count}</strong></div>
      <div class="box">Negatív hírjelek<strong>{negative_hits}</strong></div>
      <div class="box">Pozitív hírjelek<strong>{positive_hits}</strong></div>
    </div>

    <h2>Domináns narratívák</h2>
    <p>
      Az alábbi négy téma mutatja, hogy az aktuális hírminta alapján mely ügyek alakítják
      leginkább az ország politikai hangulatát.
    </p>

    {topic_blocks}

    <h2>Social signal</h2>
    <p>
      A social media index külön jelző. Nem része a fő hírindexnek.
      Jelenlegi értéke <strong>{social_score}</strong>, aktivitási szintje:
      <strong>{get_social_level_text(social_level)}</strong>.
    </p>

    <div class="summary-grid">
      <div class="box">Social említések<strong>{social_mentions}</strong></div>
      <div class="box">Social negatív jelek<strong>{social_negative}</strong></div>
      <div class="box">Social pozitív jelek<strong>{social_positive}</strong></div>
      <div class="box">Fő social téma<strong>{social_topic}</strong></div>
    </div>

    <p class="meta">
      Reddit: {source_counts.get("reddit", 0)} |
      Mastodon: {source_counts.get("mastodon", 0)}
    </p>

    <h2>Kiemelt forráscikkek</h2>
    {articles_html}

    <h2>Módszertani megjegyzés</h2>
    <p>
      Ez a szöveges helyzetkép automatikusan készül a dashboard aktuális JSON-adatfájljaiból.
      A narratívák kulcsszavas, híralapú csoportosításon alapulnak.
      Az eredmény nem közvélemény-kutatás, hanem nyílt forrású politikai hangulatjelzés.
    </p>
  </div>
</main>
</body>
</html>
"""


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    latest_data = load_json(LATEST_PATH)
    social_data = load_json(SOCIAL_PATH)

    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    report_index = {
        "updated_at": updated_at,
        "reports": []
    }

    for country in latest_data.get("countries", []):
        country_name = country.get("name", "")
        slug = slugify(country_name)
        filename = f"{slug}.html"
        output_path = os.path.join(REPORTS_DIR, filename)

        social_signal = get_social_signal(country_name, social_data)

        html = build_report_html(country, social_signal, updated_at)

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(html)

        report_index["reports"].append({
            "name": country_name,
            "url": f"reports/{filename}",
            "updated_at": updated_at
        })

        print(f"Riport elkészült: {output_path}")

    with open(REPORTS_INDEX_PATH, "w", encoding="utf-8") as file:
        json.dump(report_index, file, ensure_ascii=False, indent=2)

    print("reports_index.json sikeresen frissítve")


if __name__ == "__main__":
    main()
