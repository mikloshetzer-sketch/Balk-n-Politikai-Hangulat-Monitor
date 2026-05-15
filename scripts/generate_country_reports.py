import json
import os
import re
from datetime import datetime, timezone

LATEST_PATH = "docs/data/latest.json"
SOCIAL_PATH = "docs/data/social_latest.json"
REPORTS_DIR = "docs/reports"
REPORTS_INDEX_PATH = "docs/data/reports_index.json"


TOPIC_KEYWORDS = {
    "Belpolitikai tüntetések és társadalmi nyomás": [
        "protest", "protests", "student", "students", "police", "violence",
        "riot", "unrest", "blocked", "boycott", "demonstration"
    ],
    "EU-integráció és csatlakozási folyamat": [
        "eu", "european union", "accession", "membership", "enlargement",
        "brussels", "negotiations", "integration", "marta kos"
    ],
    "Koszovó–Szerbia feszültség": [
        "kosovo", "serbia", "kurti", "vucic", "vučić", "mitrovica",
        "pristina", "prishtina", "serb", "kfor", "border", "territory"
    ],
    "Boszniai intézményi válság és OHR-vita": [
        "dodik", "republika srpska", "ohr", "high representative",
        "christian schmidt", "dayton", "bosnia envoy", "peace envoy",
        "state collapse"
    ],
    "Korrupció, jogállamiság és igazságszolgáltatás": [
        "corruption", "court", "special court", "charges", "investigation",
        "fraud", "trial", "justice", "rights", "prosecution"
    ],
    "Biztonságpolitikai kockázatok és erőszak": [
        "violence", "attack", "assault", "clash", "security", "threat",
        "war", "conflict", "tension", "armed", "weapon", "military"
    ],
    "Kormányzati stabilitás és választási dinamika": [
        "government", "prime minister", "president", "parliament",
        "opposition", "election", "party", "coalition", "mayor",
        "cabinet", "resignation", "ruling party"
    ],
    "Gazdaság, energia és beruházások": [
        "investment", "growth", "energy", "nis", "mol", "infrastructure",
        "funding", "development", "trade", "business", "summit",
        "foreign direct investment"
    ],
    "Nemzetközi kapcsolatok és nagyhatalmi befolyás": [
        "nato", "russia", "china", "united states", "usa", "turkey",
        "un", "united nations", "sanctions", "foreign policy",
        "diplomacy"
    ],
    "Montenegró EU-csatlakozási előrehaladása": [
        "montenegro", "podgorica", "eu", "accession", "membership",
        "negotiation", "chapters", "joining"
    ],
    "Albán digitalizáció és kiberbiztonság": [
        "cybersecurity", "digital", "digital transformation", "electronic",
        "e-governance", "cyber", "infrastructure"
    ],
    "Bolgár–macedón identitásvita": [
        "bulgaria", "sofia", "macedonian", "identity", "historical",
        "language", "veto"
    ]
}


TOPIC_EXPLANATIONS = {
    "Belpolitikai tüntetések és társadalmi nyomás":
        "Ez a téma azt mutatja, hogy az adott ország politikai hangulatát utcai tiltakozások, társadalmi elégedetlenség, rendőri fellépés vagy belpolitikai nyomás alakítja.",

    "EU-integráció és csatlakozási folyamat":
        "Ez a narratíva az EU-csatlakozás, a reformfeltételek, a brüsszeli kapcsolatok és a bővítési folyamat körül szerveződik.",

    "Koszovó–Szerbia feszültség":
        "Ez a téma a szerb–koszovói viszonyt, a határ- és státuszkérdéseket, valamint a Kurti–Vučić tengely körüli politikai feszültségeket fogja össze.",

    "Boszniai intézményi válság és OHR-vita":
        "Ez a blokk Bosznia-Hercegovina intézményi törékenységét, az OHR szerepét, Christian Schmidt pozícióját és a Republika Srpska körüli vitákat jelzi.",

    "Korrupció, jogállamiság és igazságszolgáltatás":
        "Ez a narratíva bírósági ügyekre, korrupciós vádakra, jogállamisági vitákra és intézményi elszámoltathatóságra utal.",

    "Biztonságpolitikai kockázatok és erőszak":
        "Ez a téma erőszakos incidenseket, biztonsági fenyegetéseket, fegyveres vagy etnikai feszültségeket és instabilitási jeleket fog össze.",

    "Kormányzati stabilitás és választási dinamika":
        "Ez a blokk a kormányzati működést, választási folyamatokat, pártpolitikai versenyt és vezetői döntéseket követi.",

    "Gazdaság, energia és beruházások":
        "Ez a narratíva a gazdasági döntéseket, energiaügyeket, beruházásokat és stratégiai vállalati folyamatokat fogja össze.",

    "Nemzetközi kapcsolatok és nagyhatalmi befolyás":
        "Ez a téma az ország külső kapcsolatait, NATO-, EU-, USA-, orosz, kínai vagy török kapcsolódásait és diplomáciai mozgásterét mutatja.",

    "Montenegró EU-csatlakozási előrehaladása":
        "Ez Montenegró EU-tagsági folyamatára, tárgyalási fejezeteire és a csatlakozási perspektíva aktuális politikai hatására utal.",

    "Albán digitalizáció és kiberbiztonság":
        "Ez Albánia digitális átalakulásával, kiberbiztonsági kapacitásaival és állami modernizációs lépéseivel kapcsolatos híreket gyűjti össze.",

    "Bolgár–macedón identitásvita":
        "Ez Észak-Macedónia külpolitikai és identitáspolitikai vitáit jelöli, különösen a bolgár–macedón történelmi és nyelvi kérdések körül."
}


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


def get_social_level_text(level):
    if level == "high":
        return "magas"
    if level == "medium":
        return "közepes"
    return "alacsony"


def article_text(article):
    title = article.get("title", "")
    source = article.get("source", "")
    return f"{title} {source}".lower()


def match_articles_to_topic(topic, articles):
    keywords = TOPIC_KEYWORDS.get(topic, [])
    matched = []

    for article in articles:
        text = article_text(article)

        if any(keyword.lower() in text for keyword in keywords):
            matched.append(article)

    if matched:
        return matched[:3]

    return articles[:2]


def extract_named_clues(articles):
    text = " ".join(article.get("title", "") for article in articles)

    known_names = [
        "Vučić", "Vucic", "Kurti", "Dodik", "Christian Schmidt",
        "Marta Kos", "Rama", "Mickoski", "Osmani", "Bolton",
        "Macut", "MOL", "NIS", "OHR", "KFOR", "NATO", "EU",
        "UN", "Republika Srpska", "Podgorica", "Pristina",
        "Belgrade", "Sarajevo", "Sofia", "Tirana"
    ]

    found = []

    for name in known_names:
        if name.lower() in text.lower() and name not in found:
            found.append(name)

    return found[:6]


def build_source_list(articles):
    if not articles:
        return "<p class=\"meta\">Nincs közvetlenül illesztett forráscikk ehhez a narratívához.</p>"

    items = []

    for article in articles:
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


def build_topic_paragraph(topic, score, country_name, matched_articles):
    explanation = TOPIC_EXPLANATIONS.get(
        topic,
        "Ez a téma az aktuális hírmintában visszatérő politikai narratívát jelöl."
    )

    clues = extract_named_clues(matched_articles)

    if clues:
        clues_text = ", ".join(escape_html(item) for item in clues)
    else:
        clues_text = "a kiemelt cikkek címei alapján nem azonosítható egyetlen domináns szereplő"

    if matched_articles:
        lead_article = matched_articles[0]
        lead_title = escape_html(lead_article.get("title", "Cím nélkül"))
        lead_source = escape_html(lead_article.get("source", "ismeretlen forrás"))
        lead_sentence = (
            f"A legerősebb kapcsolódó jelzés a következő cikkből érkezik: "
            f"<strong>{lead_title}</strong> ({lead_source})."
        )
    else:
        lead_sentence = (
            "A témához nem kapcsolódik külön kiemelt cikk, de a kulcsszavas mintázat alapján megjelent a híranyagban."
        )

    return f"""
      <div class="topic-block">
        <h3>{escape_html(topic)}</h3>

        <p>
          <strong>Aktuális súly:</strong> {score}.
          {escape_html(explanation)}
        </p>

        <p>
          <strong>Mi mozgatja most a hangulatot?</strong>
          {lead_sentence}
          A narratíva az aktuális adatok alapján azért fontos {escape_html(country_name)} esetében,
          mert több hírben is ugyanahhoz a politikai mintázathoz kapcsolódó jelzések jelennek meg.
        </p>

        <p>
          <strong>Azonosított szereplők / intézmények / helyek:</strong>
          {clues_text}.
        </p>

        <div class="source-list">
          <strong>Kapcsolódó források:</strong>
          {build_source_list(matched_articles)}
        </div>
      </div>
    """


def build_topic_blocks(country):
    topic_scores = country.get("topic_scores", {})
    top_articles = country.get("top_articles", [])
    country_name = country.get("name", "")

    if not topic_scores:
        return "<p>Nincs elég adat a domináns narratívák részletes értékeléséhez.</p>"

    blocks = []

    for topic, score in list(topic_scores.items())[:4]:
        matched_articles = match_articles_to_topic(topic, top_articles)
        blocks.append(
            build_topic_paragraph(topic, score, country_name, matched_articles)
        )

    return "\n".join(blocks)


def build_articles_list(articles):
    if not articles:
        return "<p>Nincs megjeleníthető kiemelt cikk.</p>"

    items = []

    for article in articles[:5]:
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

    topic_blocks = build_topic_blocks(country)
    articles_html = build_articles_list(top_articles)

    return f"""<!DOCTYPE html>
<html lang="hu">
<head>
  <meta charset="UTF-8">
  <title>{escape_html(name)} – szöveges helyzetkép</title>
  <style>
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: #f3f4f6;
      color: #111827;
      line-height: 1.6;
    }}

    main {{
      max-width: 980px;
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
      margin-top: 30px;
      border-bottom: 1px solid #e5e7eb;
      padding-bottom: 6px;
    }}

    h3 {{
      margin-top: 0;
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
      padding: 16px;
      border-radius: 10px;
      margin-bottom: 16px;
    }}

    .source-list {{
      margin-top: 12px;
      padding-top: 10px;
      border-top: 1px solid #e5e7eb;
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
    <h1>{escape_html(name)} – szöveges helyzetkép</h1>
    <p class="meta">Frissítve: {escape_html(updated_at)}</p>

    <p>
      Az aktuális híralapú hangulatindex <strong>{score}</strong>, amelynek státusza:
      <strong>{get_status_text(status)}</strong>. A fő hírnarratíva jelenleg:
      <strong>{escape_html(main_topic)}</strong>.
    </p>

    <div class="summary-grid">
      <div class="box">Hírindex<strong>{score}</strong></div>
      <div class="box">Cikkek száma<strong>{article_count}</strong></div>
      <div class="box">Negatív hírjelek<strong>{negative_hits}</strong></div>
      <div class="box">Pozitív hírjelek<strong>{positive_hits}</strong></div>
    </div>

    <h2>Domináns narratívák részletesen</h2>
    <p>
      Az alábbi négy blokk azt mutatja, hogy az aktuális hírminta alapján mely témák alakítják
      leginkább az ország politikai hangulatát. Minden témánál konkrét cikkek, események,
      szereplők vagy intézmények is megjelennek, ha ezek a címekből azonosíthatók.
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
      <div class="box">Fő social téma<strong>{escape_html(social_topic)}</strong></div>
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
      Az események, szereplők és döntések az elérhető cikkcímek és forrásmezők alapján kerülnek azonosításra.
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
