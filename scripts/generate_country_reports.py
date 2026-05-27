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
        "á": "a", "é": "e", "í": "i", "ó": "o", "ö": "o",
        "ő": "o", "ú": "u", "ü": "u", "ű": "u",
        "–": "-", " ": "-"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^a-z0-9\-]", "", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def escape_html(text):
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_social_signal(country_name, social_data):
    fallback = {
        "score": 0,
        "level": "low",
        "scale": "0-60 risk index",
        "mentions": 0,
        "negative_hits": 0,
        "positive_hits": 0,
        "trusted_hits": 0,
        "engagement_total": 0,
        "raw_engagement_total": 0,
        "quality_total": 0,
        "geopolitical_total": 0,
        "main_topic": "nincs adat",
        "source_counts": {},
        "category_counts": {},
        "top_posts": []
    }

    for item in social_data.get("countries", []):
        if item.get("name") == country_name:
            signal = item.get("social_signal", {})
            return {**fallback, **signal}

    return fallback


def get_status_text(status):
    if status == "positive":
        return "pozitív"
    if status == "negative":
        return "negatív"
    return "semleges"


def get_social_level_text(level):
    if level == "high":
        return "magas kockázati jel"
    if level == "medium":
        return "közepes kockázati jel"
    return "alacsony kockázati jel"


def format_social_topic(topic):
    labels = {
        "government_crisis": "kormányzati / politikai válság",
        "security": "biztonsági kockázat",
        "eu_integration": "EU-integráció",
        "ethnic_tension": "etnikai / identitási feszültség",
        "protest": "tiltakozás",
        "corruption_rule_of_law": "korrupció / jogállamiság",
        "foreign_influence": "külső befolyás",
        "migration": "migráció",
        "economic_infrastructure": "gazdaság / infrastruktúra",
        "uncategorized": "nem kategorizált",
        "nincs adat": "nincs adat"
    }
    return labels.get(topic, topic or "nincs adat")


def risk_interpretation(score):
    if score >= 45:
        return (
            "A social térben erős kockázati mintázat látszik. Ez nem önmagában válságot jelent, "
            "de azt mutatja, hogy a politikai vagy biztonsági témák nagy intenzitással vannak jelen."
        )
    if score >= 30:
        return (
            "A social jelzés érdemi kockázatot mutat. A figyelem nemcsak általános aktivitásból, "
            "hanem konfliktusos vagy intézményi témákból is épül."
        )
    if score >= 15:
        return (
            "A social aktivitás mérsékelt kockázati szintet jelez. A témák jelen vannak, "
            "de nem dominálják teljesen a politikai teret."
        )
    return (
        "A social tér alapján alacsony kockázati jel látható. A helyzetképet inkább a híralapú "
        "források és nem a közösségi média aktivitása formálja."
    )


def news_interpretation(score, negative_hits, positive_hits):
    if score <= -15:
        return "A híralapú index erősen negatív irányt mutat, ami politikai nyomásra vagy konfliktusos napirendre utal."
    if score < 0:
        return "A híralapú index mérsékelten negatív. A kockázati témák erősebbek, mint a stabilizáló jelek."
    if score == 0:
        return "A híralapú index semleges. A pozitív és negatív jelek nem adnak egyértelmű irányt."
    if positive_hits > negative_hits:
        return "A híralapú index pozitívabb, és a stabilizáló vagy reformjellegű narratívák erősebben vannak jelen."
    return "A híralapú index pozitív, de a háttérben továbbra is lehetnek kockázati témák."


def build_scenario(country, social_signal):
    name = country.get("name", "")
    main_topic = country.get("main_topic", "nincs adat")
    social_topic = social_signal.get("main_topic", "nincs adat")
    social_score = social_signal.get("score", 0)
    negative_hits = country.get("negative_hits", 0)

    if social_score >= 40 or negative_hits >= 6:
        risk = (
            "A következő napok fő kockázata az, hogy a politikai vita tovább keményedik, "
            "és a social térben látható narratívák visszahatnak a hírnapirendre."
        )
    elif social_score >= 20:
        risk = (
            "A legvalószínűbb rövid távú forgatókönyv a fokozott figyelem, de nem feltétlenül "
            "azonnali eszkaláció. A kockázat akkor nőhet, ha új biztonsági, etnikai vagy intézményi esemény jelenik meg."
        )
    else:
        risk = (
            "Rövid távon nem látszik erős social alapú eszkalációs jel. A helyzetet inkább a hivatalos "
            "politikai és diplomáciai események mozgathatják."
        )

    return (
        f"{name} esetében a fő hírtéma jelenleg: {main_topic}. "
        f"A social térben a domináns kategória: {format_social_topic(social_topic)}. "
        f"{risk}"
    )


def build_watchlist(country, social_signal):
    topic = social_signal.get("main_topic", "nincs adat")
    main_topic = country.get("main_topic", "nincs adat")

    items = [
        f"a(z) {main_topic} témához kapcsolódó új hírforrások megjelenése",
        f"a social térben a(z) {format_social_topic(topic)} kategória erősödése",
        "a negatív és pozitív jelzések arányának változása",
        "a megbízható forrásokból származó megerősítések száma"
    ]

    return "".join(f"<li>{escape_html(item)}</li>" for item in items)


def build_category_table(category_counts):
    if not category_counts:
        return "<p class='meta'>Nincs kategóriaadat.</p>"

    rows = []
    for key, value in sorted(category_counts.items(), key=lambda item: item[1], reverse=True):
        rows.append(f"""
          <tr>
            <td>{escape_html(format_social_topic(key))}</td>
            <td><strong>{value}</strong></td>
          </tr>
        """)

    return f"""
      <table>
        <thead>
          <tr>
            <th>Kategória</th>
            <th>Találat</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    """


def build_social_sources(source_counts):
    return f"""
      <div class="summary-grid">
        <div class="box">X<strong>{source_counts.get("x", 0)}</strong></div>
        <div class="box">Reddit<strong>{source_counts.get("reddit", 0)}</strong></div>
        <div class="box">Mastodon<strong>{source_counts.get("mastodon", 0)}</strong></div>
      </div>
    """


def build_top_posts(posts):
    if not posts:
        return "<p class='meta'>Nincs megjeleníthető social találat.</p>"

    items = []
    for post in posts[:5]:
        title = escape_html(post.get("title") or post.get("text") or "Cím nélkül")
        url = escape_html(post.get("url", "#"))
        source = escape_html(post.get("source", "ismeretlen"))
        category = escape_html(format_social_topic(post.get("event_category", "nincs adat")))
        score = escape_html(post.get("geopolitical_score", 0))

        items.append(f"""
          <li>
            <a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>
            <br>
            <span>{source} | kategória: {category} | geopolitikai pont: {score}</span>
          </li>
        """)

    return f"<ul>{''.join(items)}</ul>"


def build_articles_list(articles):
    if not articles:
        return "<p>Nincs megjeleníthető kiemelt cikk.</p>"

    items = []
    for article in articles[:6]:
        title = escape_html(article.get("title", "Cím nélkül"))
        url = escape_html(article.get("url", "#"))
        source = escape_html(article.get("source", "ismeretlen forrás"))

        items.append(f"""
          <li>
            <a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>
            <br>
            <span>{source}</span>
          </li>
        """)

    return f"<ul>{''.join(items)}</ul>"


def build_deep_analysis(country, social_signal):
    name = country.get("name", "")
    score = country.get("score", 0)
    article_count = country.get("article_count", 0)
    negative_hits = country.get("negative_hits", 0)
    positive_hits = country.get("positive_hits", 0)
    main_topic = country.get("main_topic", "nincs adat")

    social_score = social_signal.get("score", 0)
    social_mentions = social_signal.get("mentions", 0)
    social_negative = social_signal.get("negative_hits", 0)
    social_positive = social_signal.get("positive_hits", 0)
    social_topic = social_signal.get("main_topic", "nincs adat")
    trusted_hits = social_signal.get("trusted_hits", 0)
    geopolitical_total = social_signal.get("geopolitical_total", 0)

    return f"""
      <section class="analysis-block">
        <h2>Elemző helyzetértékelés</h2>

        <p>
          <strong>{escape_html(name)}</strong> esetében a híralapú index jelenleg
          <strong>{score}</strong>. A rendszer <strong>{article_count}</strong> releváns cikket azonosított.
          A negatív hírjelek száma <strong>{negative_hits}</strong>, a pozitív hírjelek száma
          <strong>{positive_hits}</strong>. {escape_html(news_interpretation(score, negative_hits, positive_hits))}
        </p>

        <p>
          A fő hírnarratíva jelenleg: <strong>{escape_html(main_topic)}</strong>.
          Ez azt jelenti, hogy az ország körüli napirendet nem egyetlen elszigetelt esemény,
          hanem visszatérő politikai vagy geopolitikai mintázat alakítja.
        </p>

        <p>
          A social media réteg már nem egyszerű aktivitási mutatóként jelenik meg, hanem
          <strong>0–60-as kockázati indexként</strong>. A jelenlegi social risk érték:
          <strong>{social_score}</strong>, amelynek értelmezése:
          <strong>{escape_html(get_social_level_text(social_signal.get("level", "low")))}</strong>.
          {escape_html(risk_interpretation(social_score))}
        </p>

        <p>
          A social térben <strong>{social_mentions}</strong> releváns említés jelent meg.
          Ezek közül <strong>{social_negative}</strong> negatív és <strong>{social_positive}</strong>
          pozitív jellegű. A domináns social kategória:
          <strong>{escape_html(format_social_topic(social_topic))}</strong>.
        </p>

        <p>
          A megbízható források száma <strong>{trusted_hits}</strong>, az összesített geopolitikai pontszám
          <strong>{geopolitical_total}</strong>. Ez segít elkülöníteni a valóban releváns politikai jeleket
          a puszta közösségi média zajtól.
        </p>
      </section>
    """


def build_scenario_block(country, social_signal):
    return f"""
      <section class="analysis-block warning">
        <h2>Kockázati forgatókönyv</h2>
        <p>{escape_html(build_scenario(country, social_signal))}</p>

        <h3>Mit érdemes figyelni?</h3>
        <ul>
          {build_watchlist(country, social_signal)}
        </ul>
      </section>
    """


def page_styles():
    return """
  <style>
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: #f3f4f6;
      color: #111827;
      line-height: 1.65;
    }

    main {
      max-width: 1040px;
      margin: 30px auto;
      padding: 0 16px;
    }

    .card {
      background: white;
      border-radius: 16px;
      padding: 26px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    }

    h1 {
      margin-top: 0;
      font-size: 31px;
    }

    h2 {
      margin-top: 30px;
      border-bottom: 1px solid #e5e7eb;
      padding-bottom: 7px;
    }

    h3 {
      margin-top: 18px;
    }

    .meta {
      color: #6b7280;
      font-size: 14px;
    }

    .summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(165px, 1fr));
      gap: 12px;
      margin: 18px 0;
    }

    .box {
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 12px;
    }

    .box strong {
      display: block;
      font-size: 24px;
      margin-top: 5px;
    }

    .executive-summary {
      background: #eff6ff;
      border-left: 5px solid #2563eb;
      padding: 17px;
      border-radius: 12px;
      margin: 22px 0;
    }

    .analysis-block {
      background: #f9fafb;
      border-left: 5px solid #2563eb;
      padding: 17px;
      border-radius: 12px;
      margin: 20px 0;
    }

    .warning {
      background: #fff7ed;
      border-left-color: #ea580c;
    }

    .social-block {
      background: #f8fafc;
      border-left: 5px solid #d97706;
      padding: 17px;
      border-radius: 12px;
      margin: 20px 0;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: 14px;
    }

    th, td {
      border-bottom: 1px solid #e5e7eb;
      text-align: left;
      padding: 8px;
    }

    th {
      background: #f3f4f6;
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
    main_topic = country.get("main_topic", "nincs adat")
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
    category_counts = social_signal.get("category_counts", {})
    top_posts = social_signal.get("top_posts", [])

    return f"""<!DOCTYPE html>
<html lang="hu">
<head>
  <meta charset="UTF-8">
  <title>{escape_html(name)} – elemző helyzetkép</title>
  {page_styles()}
</head>

<body>
<main>
  <a class="back" href="../index.html">← Vissza a dashboardra</a>

  <div class="card">
    <h1>{escape_html(name)} – elemző helyzetkép</h1>
    <p class="meta">Frissítve: {escape_html(updated_at)}</p>

    <div class="executive-summary">
      <h2>Vezetői összefoglaló</h2>
      <p>
        <strong>{escape_html(name)}</strong> aktuális helyzetképe a híralapú index,
        a social risk index és a domináns narratívák együttes értelmezésén alapul.
        A híralapú index <strong>{score}</strong>, státusza
        <strong>{escape_html(get_status_text(status))}</strong>.
        A fő hírnarratíva: <strong>{escape_html(main_topic)}</strong>.
      </p>
      <p>
        A social risk index <strong>{social_score}</strong> pont a 0–60-as skálán,
        ami <strong>{escape_html(get_social_level_text(social_level))}</strong>.
        A domináns social kategória:
        <strong>{escape_html(format_social_topic(social_topic))}</strong>.
      </p>
    </div>

    <div class="summary-grid">
      <div class="box">Hírindex<strong>{score}</strong></div>
      <div class="box">Cikkek száma<strong>{article_count}</strong></div>
      <div class="box">Negatív hírjelek<strong>{negative_hits}</strong></div>
      <div class="box">Pozitív hírjelek<strong>{positive_hits}</strong></div>
    </div>

    {build_deep_analysis(country, social_signal)}

    <section class="social-block">
      <h2>Social media és X-alapú kockázati jel</h2>

      <div class="summary-grid">
        <div class="box">Social risk index<strong>{social_score}</strong></div>
        <div class="box">Említések<strong>{social_mentions}</strong></div>
        <div class="box">Negatív social jelek<strong>{social_negative}</strong></div>
        <div class="box">Pozitív social jelek<strong>{social_positive}</strong></div>
      </div>

      {build_social_sources(source_counts)}

      <p>
        A social jel nem közvélemény-kutatás. Arra szolgál, hogy jelezze,
        milyen intenzitással jelennek meg politikai, biztonsági vagy geopolitikai témák
        a közösségi média és RSS-alapú social forrásokban.
      </p>

      <h3>Social kategóriák</h3>
      {build_category_table(category_counts)}

      <h3>Kiemelt social találatok</h3>
      {build_top_posts(top_posts)}
    </section>

    {build_scenario_block(country, social_signal)}

    <h2>Kiemelt forráscikkek</h2>
    {build_articles_list(top_articles)}

    <h2>Módszertani megjegyzés</h2>
    <p>
      Ez a jelentés automatikusan készül a dashboard aktuális JSON-adatfájljaiból.
      A híralapú index, a social risk index, a kategóriabontás és a forráslisták
      nyílt forrású monitoringot támogatnak. Az eredmény nem közvélemény-kutatás,
      nem hivatalos kockázati minősítés, hanem elemző célú OSINT-jelzőrendszer.
    </p>
  </div>
</main>
</body>
</html>
"""


def build_regional_overview(latest_data, social_data, updated_at):
    countries = latest_data.get("countries", [])

    if not countries:
        body = "<p>Nincs elérhető országadat.</p>"
    else:
        social_rows = []
        for country in countries:
            social = get_social_signal(country.get("name", ""), social_data)
            social_rows.append({
                "name": country.get("name", ""),
                "score": social.get("score", 0),
                "mentions": social.get("mentions", 0),
                "topic": social.get("main_topic", "nincs adat")
            })

        strongest_social = max(social_rows, key=lambda item: item.get("score", 0))
        most_articles = max(countries, key=lambda item: item.get("article_count", 0))
        most_negative = min(countries, key=lambda item: item.get("score", 0))
        most_positive = max(countries, key=lambda item: item.get("score", 0))

        rows = []
        for country in countries:
            social = get_social_signal(country.get("name", ""), social_data)
            rows.append(f"""
              <div class="country-row">
                <h3>{escape_html(country.get("name", ""))}</h3>
                <p>
                  Hírindex: <strong>{country.get("score", 0)}</strong> |
                  státusz: <strong>{escape_html(get_status_text(country.get("status", "neutral")))}</strong> |
                  fő hír téma: <strong>{escape_html(country.get("main_topic", "nincs adat"))}</strong>
                </p>
                <p>
                  Social risk index: <strong>{social.get("score", 0)}</strong> |
                  említések: <strong>{social.get("mentions", 0)}</strong> |
                  fő social téma:
                  <strong>{escape_html(format_social_topic(social.get("main_topic", "nincs adat")))}</strong>
                </p>
              </div>
            """)

        body = f"""
          <div class="executive-summary">
            <h2>Régiós vezetői összefoglaló</h2>
            <p>
              A mai Balkán-helyzetképben a legerősebb social risk jel
              <strong>{escape_html(strongest_social.get("name", ""))}</strong>
              esetében látható
              ({strongest_social.get("score", 0)} pont, {strongest_social.get("mentions", 0)} említés).
            </p>
            <p>
              A legtöbb hír <strong>{escape_html(most_articles.get("name", ""))}</strong>
              körül jelent meg. A legnegatívabb híralapú index
              <strong>{escape_html(most_negative.get("name", ""))}</strong>,
              a legkedvezőbb híralapú index pedig
              <strong>{escape_html(most_positive.get("name", ""))}</strong> esetében látszik.
            </p>
            <p>
              A térség egészében a fő figyelmeztető jel az, hogy a social térben megjelenő
              biztonsági, etnikai, intézményi vagy EU-integrációs narratívák gyorsabban mozdulhatnak,
              mint a hagyományos hírindex.
            </p>
          </div>

          <h2>Országonkénti gyors helyzetkép</h2>
          {''.join(rows)}
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
  <a class="back" href="../index.html">← Vissza a dashboardra</a>

  <div class="card">
    <h1>Mai Balkán helyzetkép</h1>
    <p class="meta">Frissítve: {escape_html(updated_at)}</p>

    {body}

    <h2>Módszertani megjegyzés</h2>
    <p>
      A régiós riport automatikusan készül az országonkénti hírindex,
      social risk index és domináns narratívák alapján. Nem közvélemény-kutatás,
      hanem nyílt forrású politikai és geopolitikai hangulatjelzés.
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
        "regional_overview": f"reports/{REGIONAL_REPORT_FILENAME}",
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

    regional_html = build_regional_overview(latest_data, social_data, updated_at)
    regional_path = os.path.join(REPORTS_DIR, REGIONAL_REPORT_FILENAME)

    with open(regional_path, "w", encoding="utf-8") as file:
        file.write(regional_html)

    print(f"Régiós riport elkészült: {regional_path}")

    with open(REPORTS_INDEX_PATH, "w", encoding="utf-8") as file:
        json.dump(report_index, file, ensure_ascii=False, indent=2)

    print("reports_index.json sikeresen frissítve")


if __name__ == "__main__":
    main()
