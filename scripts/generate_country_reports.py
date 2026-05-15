import json
import os
import re
from datetime import datetime, timezone

LATEST_PATH = "docs/data/latest.json"
SOCIAL_PATH = "docs/data/social_latest.json"

REPORTS_DIR = "docs/reports"
REPORTS_INDEX_PATH = "docs/data/reports_index.json"

REGIONAL_REPORT_FILENAME = "regional-overview.html"


def slugify(text):
    text = text.lower()

    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ö": "o",
        "ő": "o",
        "ú": "u",
        "ü": "u",
        "ű": "u",
        "–": "-",
        " ": "-"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^a-z0-9\-]", "", text)
    text = re.sub(r"-+", "-", text)

    return text.strip("-")


def escape_html(text):
    if text is None:
        return ""

    text = str(text)

    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


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


def get_score_direction(score):
    if score <= -15:
        return "kifejezetten negatív"

    if score < 0:
        return "mérsékelten negatív"

    if score == 0:
        return "semleges"

    if score < 15:
        return "mérsékelten pozitív"

    return "kifejezetten pozitív"


def get_social_level_text(level):
    if level == "high":
        return "magas"

    if level == "medium":
        return "közepes"

    return "alacsony"


def extract_named_clues(articles):
    text = " ".join(
        article.get("title", "")
        for article in articles
    )

    known_names = [
        "Vučić",
        "Vucic",
        "Kurti",
        "Dodik",
        "Christian Schmidt",
        "Marta Kos",
        "Rama",
        "Mickoski",
        "Osmani",
        "Bolton",
        "Macut",
        "MOL",
        "NIS",
        "OHR",
        "KFOR",
        "NATO",
        "EU",
        "UN",
        "Republika Srpska",
        "Podgorica",
        "Pristina",
        "Belgrade",
        "Sarajevo",
        "Sofia",
        "Tirana"
    ]

    found = []

    for name in known_names:
        if name.lower() in text.lower():
            if name not in found:
                found.append(name)

    return found[:6]


def build_risk_sentence(score):
    if score <= -20:
        return (
            "A jelenlegi mintázat alapján az ország politikai környezete "
            "rövid távon is instabilitási jeleket mutat."
        )

    if score <= -8:
        return (
            "A politikai hangulat továbbra is inkább negatív irányba húz, "
            "különösen a konfliktusos vagy intézményi témák miatt."
        )

    if score < 8:
        return (
            "A politikai környezet vegyes képet mutat, nincs egyetlen domináns "
            "pozitív vagy negatív irány."
        )

    return (
        "A jelenlegi hírminta inkább stabilizáló vagy pozitív narratívákat jelez."
    )


def build_topic_analysis(topic, score, matched_articles, country_name):
    if matched_articles:
        lead = matched_articles[0]

        lead_title = escape_html(
            lead.get("title", "Cím nélkül")
        )

        lead_source = escape_html(
            lead.get("source", "ismeretlen forrás")
        )

        lead_sentence = (
            f"A legerősebb kapcsolódó jelzés a következő cikkből érkezik: "
            f"<strong>{lead_title}</strong> ({lead_source})."
        )
    else:
        lead_sentence = (
            "A témához jelenleg nem kapcsolódik külön kiemelt cikk."
        )

    clues = extract_named_clues(matched_articles)

    if clues:
        clue_text = ", ".join(clues)
    else:
        clue_text = (
            "nincs egyértelműen azonosítható domináns szereplő"
        )

    return f"""
      <div class="topic-block">
        <h3>{escape_html(topic)}</h3>

        <p>
          A témacsoport aktuális súlya:
          <strong>{score}</strong>.
          Ez azt jelzi, hogy a kapcsolódó kulcsszavak több releváns
          hírforrásban is visszatérően megjelentek.
        </p>

        <p>
          {lead_sentence}
        </p>

        <p>
          A jelenlegi mintázat alapján ez a narratíva azért fontos
          <strong>{escape_html(country_name)}</strong> esetében,
          mert nem egyetlen eseményhez kapcsolódik,
          hanem több párhuzamos politikai vagy társadalmi jelzéshez.
        </p>

        <p>
          <strong>Azonosított szereplők / intézmények:</strong>
          {escape_html(clue_text)}.
        </p>

        {build_source_list(matched_articles)}
      </div>
    """


def build_source_list(articles):
    if not articles:
        return (
            '<p class="meta">'
            'Nincs kapcsolódó forrás.'
            '</p>'
        )

    items = []

    for article in articles[:3]:
        title = escape_html(
            article.get("title", "Cím nélkül")
        )

        url = escape_html(
            article.get("url", "#")
        )

        source = escape_html(
            article.get("source", "ismeretlen forrás")
        )

        items.append(f"""
          <li>
            <a href="{url}" target="_blank" rel="noopener noreferrer">
              {title}
            </a>
            <br>
            <span>{source}</span>
          </li>
        """)

    return f"""
      <div class="source-list">
        <strong>Kapcsolódó források:</strong>
        <ul>
          {''.join(items)}
        </ul>
      </div>
    """


def match_articles_to_topic(topic, articles):
    topic_words = topic.lower().split()

    matched = []

    for article in articles:
        title = article.get("title", "").lower()

        if any(word in title for word in topic_words):
            matched.append(article)

    if matched:
        return matched[:3]

    return articles[:2]


def build_executive_summary(country, social_signal):
    name = country.get("name", "")

    score = country.get("score", 0)

    status = country.get("status", "neutral")

    main_topic = country.get(
        "main_topic",
        "nincs adat"
    )

    topic_scores = country.get(
        "topic_scores",
        {}
    )

    article_count = country.get(
        "article_count",
        0
    )

    negative_hits = country.get(
        "negative_hits",
        0
    )

    positive_hits = country.get(
        "positive_hits",
        0
    )

    social_score = social_signal.get(
        "score",
        0
    )

    social_mentions = social_signal.get(
        "mentions",
        0
    )

    social_topic = social_signal.get(
        "main_topic",
        "nincs adat"
    )

    top_articles = country.get(
        "top_articles",
        []
    )

    topic_names = list(
        topic_scores.keys()
    )[:4]

    people = extract_named_clues(top_articles)

    if topic_names:
        topic_sentence = ", ".join(topic_names)
    else:
        topic_sentence = (
            "nincs egyértelmű domináns téma"
        )

    if people:
        people_sentence = (
            "A cikkekben hangsúlyosan megjelenik: "
            + ", ".join(people)
            + "."
        )
    else:
        people_sentence = (
            "A cikkekben nem emelkedik ki egyetlen domináns szereplő."
        )

    if negative_hits > positive_hits:
        balance_sentence = (
            f"A negatív hírjelek száma ({negative_hits}) "
            f"magasabb, mint a pozitívaké ({positive_hits}), "
            "ezért a hangulat inkább kockázati irányba tolódik."
        )
    elif positive_hits > negative_hits:
        balance_sentence = (
            f"A pozitív hírelemek ({positive_hits}) "
            f"meghaladják a negatívakat ({negative_hits}), "
            "ami részben stabilizáló hatású lehet."
        )
    else:
        balance_sentence = (
            f"A pozitív és negatív hírjelek kiegyenlítettek "
            f"({positive_hits}–{negative_hits})."
        )

    if social_score >= 20:
        social_sentence = (
            f"A social media aktivitás erős: "
            f"{social_mentions} releváns említés jelent meg. "
            f"A fő social téma: {social_topic}."
        )
    elif social_score >= 8:
        social_sentence = (
            f"A social media aktivitás közepes: "
            f"{social_mentions} releváns említés jelent meg."
        )
    else:
        social_sentence = (
            f"A social media aktivitás visszafogott "
            f"({social_mentions} releváns említés)."
        )

    risk_sentence = build_risk_sentence(score)

    return f"""
      <div class="executive-summary">
        <h2>Vezetői összefoglaló</h2>

        <p>
          <strong>{escape_html(name)}</strong>
          aktuális politikai hangulata
          <strong>{escape_html(get_score_direction(score))}</strong>.
          A híralapú index értéke:
          <strong>{score}</strong>,
          amely jelenleg
          <strong>{escape_html(get_status_text(status))}</strong>
          státuszt jelez.
        </p>

        <p>
          A jelenlegi diskurzust leginkább
          <strong>{escape_html(main_topic)}</strong>
          alakítja.
          A legerősebb narratívák:
          <strong>{escape_html(topic_sentence)}</strong>.
        </p>

        <p>
          A rendszer
          <strong>{article_count}</strong>
          releváns cikket azonosított.
          {escape_html(balance_sentence)}
        </p>

        <p>
          {escape_html(people_sentence)}
        </p>

        <p>
          {escape_html(social_sentence)}
        </p>

        <p>
          <strong>Rövid következtetés:</strong>
          {escape_html(risk_sentence)}
        </p>
      </div>
    """


def build_topic_blocks(country):
    topic_scores = country.get(
        "topic_scores",
        {}
    )

    top_articles = country.get(
        "top_articles",
        []
    )

    country_name = country.get(
        "name",
        ""
    )

    if not topic_scores:
        return (
            "<p>"
            "Nincs elég adat a domináns narratívák részletes elemzéséhez."
            "</p>"
        )

    blocks = []

    for topic, score in list(topic_scores.items())[:4]:
        matched_articles = match_articles_to_topic(
            topic,
            top_articles
        )

        blocks.append(
            build_topic_analysis(
                topic,
                score,
                matched_articles,
                country_name
            )
        )

    return "\n".join(blocks)


def build_articles_list(articles):
    if not articles:
        return (
            "<p>"
            "Nincs megjeleníthető kiemelt cikk."
            "</p>"
        )

    items = []

    for article in articles[:5]:
        title = escape_html(
            article.get("title", "Cím nélkül")
        )

        url = escape_html(
            article.get("url", "#")
        )

        source = escape_html(
            article.get("source", "ismeretlen forrás")
        )

        items.append(f"""
        <li>
          <a href="{url}" target="_blank" rel="noopener noreferrer">
            {title}
          </a>
          <br>
          <span>{source}</span>
        </li>
        """)

    return f"<ul>{''.join(items)}</ul>"


def page_styles():
    return """
  <style>
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: #f3f4f6;
      color: #111827;
      line-height: 1.6;
    }

    main {
      max-width: 980px;
      margin: 30px auto;
      padding: 0 16px;
    }

    .card {
      background: white;
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    }

    h1 {
      margin-top: 0;
      font-size: 30px;
    }

    h2 {
      margin-top: 30px;
      border-bottom: 1px solid #e5e7eb;
      padding-bottom: 6px;
    }

    h3 {
      margin-top: 0;
    }

    .meta {
      color: #6b7280;
      font-size: 14px;
    }

    .summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin: 20px 0;
    }

    .box {
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 12px;
    }

    .box strong {
      display: block;
      font-size: 22px;
      margin-top: 4px;
    }

    .executive-summary {
      background: #eff6ff;
      border-left: 5px solid #2563eb;
      padding: 16px;
      border-radius: 12px;
      margin: 22px 0;
    }

    .executive-summary h2 {
      margin-top: 0;
      border-bottom: none;
      padding-bottom: 0;
    }

    .topic-block {
      background: #f9fafb;
      border-left: 5px solid #2563eb;
      padding: 16px;
      border-radius: 10px;
      margin-bottom: 16px;
    }

    .source-list {
      margin-top: 12px;
      padding-top: 10px;
      border-top: 1px solid #e5e7eb;
    }

    ul {
      padding-left: 20px;
    }

    li {
      margin-bottom: 10px;
    }

    a {
      color: #2563eb;
      text-decoration: none;
    }

    a:hover {
      text-decoration: underline;
    }

    .back {
      display: inline-block;
      margin-bottom: 16px;
      color: #2563eb;
      text-decoration: none;
      font-size: 14px;
    }

    .country-row {
      border-left: 5px solid #2563eb;
      background: #f9fafb;
      border-radius: 10px;
      padding: 14px;
      margin-bottom: 14px;
    }
  </style>
"""


def build_report_html(country, social_signal, updated_at):
    name = country.get("name", "")

    score = country.get("score", 0)

    status = country.get("status", "neutral")

    main_topic = country.get(
        "main_topic",
        "nincs adat"
    )

    article_count = country.get(
        "article_count",
        0
    )

    negative_hits = country.get(
        "negative_hits",
        0
    )

    positive_hits = country.get(
        "positive_hits",
        0
    )

    top_articles = country.get(
        "top_articles",
        []
    )

    social_score = social_signal.get(
        "score",
        0
    )

    social_level = social_signal.get(
        "level",
        "low"
    )

    social_mentions = social_signal.get(
        "mentions",
        0
    )

    social_negative = social_signal.get(
        "negative_hits",
        0
    )

    social_positive = social_signal.get(
        "positive_hits",
        0
    )

    social_topic = social_signal.get(
        "main_topic",
        "nincs adat"
    )

    source_counts = social_signal.get(
        "source_counts",
        {}
    )

    executive_summary = build_executive_summary(
        country,
        social_signal
    )

    topic_blocks = build_topic_blocks(country)

    articles_html = build_articles_list(top_articles)

    return f"""<!DOCTYPE html>
<html lang="hu">
<head>
  <meta charset="UTF-8">
  <title>{escape_html(name)} – szöveges helyzetkép</title>
  {page_styles()}
</head>

<body>
<main>
  <a class="back" href="../index.html">← Vissza a dashboardra</a>

  <div class="card">
    <h1>{escape_html(name)} – szöveges helyzetkép</h1>

    <p class="meta">
      Frissítve: {escape_html(updated_at)}
    </p>

    <p>
      Az aktuális híralapú hangulatindex
      <strong>{score}</strong>,
      amely jelenleg
      <strong>{escape_html(get_status_text(status))}</strong>
      státuszt jelez.
      A domináns hírnarratíva:
      <strong>{escape_html(main_topic)}</strong>.
    </p>

    <div class="summary-grid">
      <div class="box">
        Hírindex
        <strong>{score}</strong>
      </div>

      <div class="box">
        Cikkek száma
        <strong>{article_count}</strong>
      </div>

      <div class="box">
        Negatív hírjelek
        <strong>{negative_hits}</strong>
      </div>

      <div class="box">
        Pozitív hírjelek
        <strong>{positive_hits}</strong>
      </div>
    </div>

    {executive_summary}

    <h2>Domináns narratívák részletesen</h2>

    <p>
      Az alábbi blokkok azt mutatják,
      hogy az aktuális híranyag alapján
      mely ügyek alakítják leginkább
      az ország politikai hangulatát.
    </p>

    {topic_blocks}

    <h2>Social signal</h2>

    <p>
      A social media index külön jelző.
      Nem része a fő hírindexnek.
      Jelenlegi értéke:
      <strong>{social_score}</strong>,
      aktivitási szintje:
      <strong>{escape_html(get_social_level_text(social_level))}</strong>.
    </p>

    <div class="summary-grid">
      <div class="box">
        Social említések
        <strong>{social_mentions}</strong>
      </div>

      <div class="box">
        Social negatív jelek
        <strong>{social_negative}</strong>
      </div>

      <div class="box">
        Social pozitív jelek
        <strong>{social_positive}</strong>
      </div>

      <div class="box">
        Fő social téma
        <strong>{escape_html(social_topic)}</strong>
      </div>
    </div>

    <p class="meta">
      Reddit: {source_counts.get("reddit", 0)} |
      Mastodon: {source_counts.get("mastodon", 0)}
    </p>

    <h2>Kiemelt forráscikkek</h2>

    {articles_html}

    <h2>Módszertani megjegyzés</h2>

    <p>
      Ez a szöveges helyzetkép automatikusan készül
      a dashboard aktuális JSON-adatfájljaiból.
      A narratívák kulcsszavas,
      híralapú csoportosításon alapulnak.
      Az eredmény nem közvélemény-kutatás,
      hanem nyílt forrású politikai hangulatjelzés.
    </p>
  </div>
</main>
</body>
</html>
"""


def build_regional_overview(
    latest_data,
    social_data,
    updated_at
):
    countries = latest_data.get("countries", [])

    if not countries:
        body = (
            "<p>"
            "Nincs elérhető országadat."
            "</p>"
        )
    else:
        most_negative = min(
            countries,
            key=lambda item: item.get("score", 0)
        )

        most_positive = max(
            countries,
            key=lambda item: item.get("score", 0)
        )

        most_articles = max(
            countries,
            key=lambda item: item.get("article_count", 0)
        )

        social_rows = []

        for country in countries:
            social = get_social_signal(
                country.get("name", ""),
                social_data
            )

            social_rows.append({
                "name": country.get("name", ""),
                "score": social.get("score", 0),
                "mentions": social.get("mentions", 0),
                "topic": social.get("main_topic", "nincs adat")
            })

        strongest_social = max(
            social_rows,
            key=lambda item: item.get("score", 0)
        )

        topic_counter = {}

        for country in countries:
            main_topic = country.get(
                "main_topic",
                "nincs adat"
            )

            topic_counter[main_topic] = (
                topic_counter.get(main_topic, 0) + 1
            )

        dominant_regional_topic = max(
            topic_counter,
            key=topic_counter.get
        )

        country_blocks = []

        for country in countries:
            social = get_social_signal(
                country.get("name", ""),
                social_data
            )

            country_blocks.append(f"""
              <div class="country-row">
                <h3>{escape_html(country.get("name", ""))}</h3>

                <p>
                  Hírindex:
                  <strong>{country.get("score", 0)}</strong>,
                  státusz:
                  <strong>{get_status_text(country.get("status", "neutral"))}</strong>.
                  Fő téma:
                  <strong>{escape_html(country.get("main_topic", "nincs adat"))}</strong>.
                </p>

                <p>
                  Social media index:
                  <strong>{social.get("score", 0)}</strong>,
                  releváns említések:
                  <strong>{social.get("mentions", 0)}</strong>.
                </p>

                <p>
                  {escape_html(
                    build_risk_sentence(
                      country.get("score", 0),
                      country.get("negative_hits", 0),
                      country.get("positive_hits", 0)
                    )
                  )}
                </p>
              </div>
            """)

        body = f"""
          <div class="executive-summary">
            <h2>Régiós vezetői összefoglaló</h2>

            <p>
              A mai Balkán-helyzetkép alapján
              a legnegatívabb híralapú index
              <strong>{escape_html(most_negative.get("name", ""))}</strong>
              esetében látható
              ({most_negative.get("score", 0)}).
            </p>

            <p>
              A legkedvezőbb hangulatot
              <strong>{escape_html(most_positive.get("name", ""))}</strong>
              mutatja
              ({most_positive.get("score", 0)}).
            </p>

            <p>
              A legtöbb releváns hír
              <strong>{escape_html(most_articles.get("name", ""))}</strong>
              körül jelent meg
              ({most_articles.get("article_count", 0)} cikk).
            </p>

            <p>
              A legerősebb social media jel
              <strong>{escape_html(strongest_social.get("name", ""))}</strong>
              esetében látható
              ({strongest_social.get("score", 0)} social index,
              {strongest_social.get("mentions", 0)} említés).
            </p>

            <p>
              Régiós szinten a leggyakrabban
              visszatérő fő narratíva:
              <strong>{escape_html(dominant_regional_topic)}</strong>.
            </p>

            <p>
              <strong>Rövid következtetés:</strong>
              a térségben jelenleg egyszerre vannak jelen
              intézményi,
              geopolitikai,
              biztonsági
              és gazdasági narratívák,
              ezért a politikai hangulat országonként jelentősen eltér.
            </p>
          </div>

          <h2>Országonkénti gyors helyzetkép</h2>

          {''.join(country_blocks)}
        """

    return f"""<!DOCTYPE html>
<html lang="hu">
<head>
  <meta charset="UTF-8">
  <title>Mai Balkán helyzetkép</title>
  {page_styles()}
</head>

<body>
<main>
  <a class="back" href="../index.html">
    ← Vissza a dashboardra
  </a>

  <div class="card">
    <h1>Mai Balkán helyzetkép</h1>

    <p class="meta">
      Frissítve:
      {escape_html(updated_at)}
    </p>

    {body}

    <h2>Módszertani megjegyzés</h2>

    <p>
      Ez a régiós helyzetkép automatikusan készül
      az országonkénti hírindex,
      social signal
      és domináns narratívák alapján.
      Nem közvélemény-kutatás,
      hanem nyílt forrású politikai hangulatjelzés.
    </p>
  </div>
</main>
</body>
</html>
"""


def main():
    os.makedirs(
        REPORTS_DIR,
        exist_ok=True
    )

    latest_data = load_json(LATEST_PATH)
    social_data = load_json(SOCIAL_PATH)

    updated_at = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d %H:%M UTC")

    report_index = {
        "updated_at": updated_at,
        "regional_overview":
            f"reports/{REGIONAL_REPORT_FILENAME}",
        "reports": []
    }

    for country in latest_data.get("countries", []):
        country_name = country.get("name", "")

        slug = slugify(country_name)

        filename = f"{slug}.html"

        output_path = os.path.join(
            REPORTS_DIR,
            filename
        )

        social_signal = get_social_signal(
            country_name,
            social_data
        )

        html = build_report_html(
            country,
            social_signal,
            updated_at
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(html)

        report_index["reports"].append({
            "name": country_name,
            "url": f"reports/{filename}",
            "updated_at": updated_at
        })

        print(
            f"Riport elkészült: {output_path}"
        )

    regional_html = build_regional_overview(
        latest_data,
        social_data,
        updated_at
    )

    regional_path = os.path.join(
        REPORTS_DIR,
        REGIONAL_REPORT_FILENAME
    )

    with open(
        regional_path,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(regional_html)

    print(
        f"Régiós riport elkészült: {regional_path}"
    )

    with open(
        REPORTS_INDEX_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report_index,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        "reports_index.json sikeresen frissítve"
    )


if __name__ == "__main__":
    main()
