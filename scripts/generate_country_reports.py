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
        "A politikai hangulatot ebben az esetben belső társadalmi feszültség, tiltakozás, rendőri fellépés vagy kormányellenes nyomás formálja.",

    "EU-integráció és csatlakozási folyamat":
        "A diskurzus középpontjában az EU-csatlakozás, a reformfeltételek, a brüsszeli kapcsolatok és a bővítési folyamat áll.",

    "Koszovó–Szerbia feszültség":
        "A térség egyik legfontosabb konfliktusos tengelye jelenik meg: a szerb–koszovói viszony, a státuszkérdés, a határbiztonság és a politikai párbeszéd.",

    "Boszniai intézményi válság és OHR-vita":
        "Ez a téma Bosznia-Hercegovina intézményi törékenységét, az OHR szerepét, Christian Schmidt pozícióját és a Republika Srpska körüli vitákat jelzi.",

    "Korrupció, jogállamiság és igazságszolgáltatás":
        "A hangulatot jogállamisági ügyek, bírósági eljárások, korrupciós vádak vagy intézményi elszámoltathatósági kérdések befolyásolják.",

    "Biztonságpolitikai kockázatok és erőszak":
        "A hírekben erőszakos incidensek, fenyegetések, fegyveres vagy etnikai feszültségek, illetve instabilitási kockázatok jelennek meg.",

    "Kormányzati stabilitás és választási dinamika":
        "A politikai hangulatot a kormányzati működés, pártpolitikai verseny, választási dinamika vagy vezetői döntések alakítják.",

    "Gazdaság, energia és beruházások":
        "A napirendet gazdasági, energetikai és beruházási ügyek határozzák meg. Ezek stabilizáló témák is lehetnek, de stratégiai vállalatok vagy energiaügyek esetén politikai kockázatot is hordozhatnak.",

    "Nemzetközi kapcsolatok és nagyhatalmi befolyás":
        "Az ország politikai mozgásterét külső szereplők, NATO-, EU-, USA-, orosz, kínai vagy török kapcsolódások alakítják.",

    "Montenegró EU-csatlakozási előrehaladása":
        "Montenegró esetében az EU-tagsági folyamat, a tárgyalási fejezetek és a csatlakozási perspektíva adja a fő politikai keretet.",

    "Albán digitalizáció és kiberbiztonság":
        "Albánia esetében a digitális állam, a kiberbiztonság és az állami modernizáció jelenik meg hangsúlyos témaként.",

    "Bolgár–macedón identitásvita":
        "Észak-Macedónia politikai környezetét ebben a témában a bolgár–macedón történelmi, nyelvi és identitáspolitikai viták alakítják."
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


def get_risk_sentence(score, negative_hits, positive_hits):
    if score <= -15:
        return "A jelenlegi mintázat rövid távon fokozott politikai kockázatot jelez."
    if score < 0:
        return "A helyzet nem válságszerű, de a negatív hírelemek erősebben húzzák lefelé a hangulatot."
    if score == 0:
        return "A hangulat kiegyensúlyozott, nincs egyértelmű pozitív vagy negatív irány."
    if positive_hits > negative_hits:
        return "A pozitív hírelemek jelenleg részben ellensúlyozzák a kockázati témákat."
    return "A pozitív index ellenére érdemes figyelni, hogy a háttérben maradtak-e kockázati témák."


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
        "Belgrade", "Sarajevo", "Sofia", "Tirana", "Bulgaria",
        "Serbia", "Kosovo", "Montenegro", "Albania"
    ]

    found = []

    for name in known_names:
        if name.lower() in text.lower() and name not in found:
            found.append(name)

    return found[:6]


def get_top_topics(topic_scores, limit=4):
    return list(topic_scores.items())[:limit]


def build_topic_sentence(topic):
    topic_map = {
        "Belpolitikai tüntetések és társadalmi nyomás":
            "A belpolitikai nyomás azt jelzi, hogy a kormányzati szereplőknek nemcsak intézményi, hanem utcai vagy társadalmi reakciókkal is számolniuk kell.",

        "EU-integráció és csatlakozási folyamat":
            "Az EU-integrációs téma stabilizáló hatású lehet, de csak akkor, ha reformlépések és politikai kompromisszumok is társulnak hozzá.",

        "Koszovó–Szerbia feszültség":
            "A Koszovó–Szerbia ügy gyorsan biztonsági és diplomáciai dimenziót kap, ezért a régió egészének politikai hangulatát is befolyásolja.",

        "Boszniai intézményi válság és OHR-vita":
            "A boszniai intézményi vita azért érzékeny, mert egyszerre érinti az állami működést, a nemzetközi felügyeletet és a szerb entitás mozgásterét.",

        "Korrupció, jogállamiság és igazságszolgáltatás":
            "A jogállamisági ügyek hosszabb távon az EU-kapcsolatokra és a befektetői bizalomra is hatással lehetnek.",

        "Biztonságpolitikai kockázatok és erőszak":
            "A biztonsági jellegű hírek gyorsan rontják a politikai hangulatot, mert a stabilitás és a kiszámíthatóság kérdését érintik.",

        "Kormányzati stabilitás és választási dinamika":
            "A választási és kormányzati témák azt mutatják, hogy a politikai verseny vagy az intézményi működés került a figyelem középpontjába.",

        "Gazdaság, energia és beruházások":
            "A gazdasági és energetikai ügyek egyszerre mutathatnak fejlődést és sérülékenységet, főleg ha stratégiai ágazatokról van szó.",

        "Nemzetközi kapcsolatok és nagyhatalmi befolyás":
            "A külső szereplők jelenléte azt jelzi, hogy az ország mozgástere nemcsak belpolitikai, hanem geopolitikai tényezőktől is függ.",

        "Montenegró EU-csatlakozási előrehaladása":
            "Montenegró esetében az EU-pálya a politikai stabilitás egyik fő mércéje.",

        "Albán digitalizáció és kiberbiztonság":
            "A digitalizációs és kiberbiztonsági témák azt mutatják, hogy az állami modernizáció stratégiai politikai kérdéssé vált.",

        "Bolgár–macedón identitásvita":
            "Az identitásvita azért érzékeny, mert egyszerre érinti az EU-csatlakozást, a történelmi emlékezetet és a belpolitikai legitimációt."
    }

    return topic_map.get(
        topic,
        "A téma azért fontos, mert visszatérően megjelenik az aktuális híranyagban."
    )


def build_executive_summary(country, social_signal):
    name = country.get("name", "")
    score = country.get("score", 0)
    status = country.get("status", "neutral")
    topic_scores = country.get("topic_scores", {})
    main_topic = country.get("main_topic", "nincs adat")
    article_count = country.get("article_count", 0)
    negative_hits = country.get("negative_hits", 0)
    positive_hits = country.get("positive_hits", 0)
    top_articles = country.get("top_articles", [])

    social_score = social_signal.get("score", 0)
    social_mentions = social_signal.get("mentions", 0)
    social_topic = social_signal.get("main_topic", "nincs adat")

    top_topics = get_top_topics(topic_scores, 4)
    topic_names = [topic for topic, _ in top_topics]

    key_people = extract_named_clues(top_articles)

    if key_people:
        people_sentence = "A cikkekben kiemelten megjelenő szereplők és intézmények: " + ", ".join(key_people) + "."
    else:
        people_sentence = "A cikkcímek alapján nem emelkedik ki egyetlen domináns szereplő."

    if topic_names:
        topic_sentence = ", ".join(topic_names[:4])
    else:
        topic_sentence = "nincs egyértelműen kiemelkedő téma"

    if negative_hits > positive_hits:
        balance_sentence = (
            f"A negatív hírjelek száma ({negative_hits}) meghaladja a pozitív jelzésekét ({positive_hits}), "
            "ezért a politikai hangulat inkább kockázati irányba mozdul."
        )
    elif positive_hits > negative_hits:
        balance_sentence = (
            f"A pozitív hírjelek száma ({positive_hits}) meghaladja a negatív jelzésekét ({negative_hits}), "
            "ami mérsékelheti a politikai kockázatokat."
        )
    else:
        balance_sentence = (
            f"A negatív és pozitív hírjelek kiegyenlítettek ({negative_hits}–{positive_hits}), "
            "ezért a hangulatot főként a domináns témák jellege határozza meg."
        )

    if social_score >= 20:
        social_sentence = (
            f"A közösségi média jel erős: {social_mentions} releváns említés jelent meg, "
            f"a fő social téma pedig {social_topic}."
        )
    elif social_score >= 8:
        social_sentence = (
            f"A közösségi média aktivitás közepes: {social_mentions} releváns említés jelent meg. "
            f"A social térben leginkább a(z) {social_topic} téma látszik."
        )
    else:
        social_sentence = (
            f"A közösségi média aktivitás alacsony: {social_mentions} releváns említés látható. "
            "Ez arra utal, hogy a mostani helyzetképet elsősorban a hírforrások alakítják."
        )

    main_topic_sentence = build_topic_sentence(main_topic)
    risk_sentence = get_risk_sentence(score, negative_hits, positive_hits)

    return f"""
      <div class="executive-summary">
        <h2>Vezetői összefoglaló</h2>

        <p>
          <strong>{escape_html(name)}</strong> aktuális politikai hangulata
          <strong>{escape_html(get_score_direction(score))}</strong>. A híralapú index értéke
          <strong>{score}</strong>, a dashboard szerinti státusz pedig
          <strong>{escape_html(get_status_text(status))}</strong>.
        </p>

        <p>
          A legfontosabb ügy jelenleg:
          <strong>{escape_html(main_topic)}</strong>. Ez nem önálló elszigetelt téma,
          hanem több hírben visszatérő mintázat. {escape_html(main_topic_sentence)}
        </p>

        <p>
          A négy legerősebb témacsoport: <strong>{escape_html(topic_sentence)}</strong>.
          Ezek együtt adják meg, hogy az országban a politikai hangulatot inkább belpolitikai,
          gazdasági, biztonsági vagy külpolitikai kérdések mozgatják-e.
        </p>

        <p>
          A rendszer <strong>{article_count}</strong> releváns cikket azonosított.
          {escape_html(balance_sentence)}
        </p>

        <p>
          {escape_html(people_sentence)}
        </p>

        <p>
          {escape_html(social_sentence)}
        </p>

        <p>
          <strong>Rövid következtetés:</strong> {escape_html(risk_sentence)}
        </p>
      </div>
    """


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
        "Ez a téma az aktuális híranyagban visszatérő politikai mintázatot jelöl."
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
            f"A téma legerősebb kapcsolódása a következő cikkben jelenik meg: "
            f"<strong>{lead_title}</strong> ({lead_source})."
        )
    else:
        lead_sentence = (
            "A témához nem kapcsolódik külön kiemelt cikk, de a kulcsszavas mintázat alapján jelen van a híranyagban."
        )

    topic_context = build_topic_sentence(topic)

    return f"""
      <div class="topic-block">
        <h3>{escape_html(topic)}</h3>

        <p>
          <strong>Aktuális súly:</strong> {score}.
          {escape_html(explanation)}
        </p>

        <p>
          <strong>Konkrét jelzés:</strong>
          {lead_sentence}
        </p>

        <p>
          <strong>Elemző értelmezés:</strong>
          {escape_html(topic_context)}
          Ez azért fontos {escape_html(country_name)} esetében, mert a visszatérő témák nemcsak
          egy-egy hírt jelentenek, hanem a politikai környezet általános hangulatát is formálják.
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

    executive_summary = build_executive_summary(country, social_signal)
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

    .executive-summary {{
      background: #eff6ff;
      border-left: 5px solid #2563eb;
      padding: 16px;
      border-radius: 12px;
      margin: 22px 0;
    }}

    .executive-summary h2 {{
      margin-top: 0;
      border-bottom: none;
      padding-bottom: 0;
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

    {executive_summary}

    <h2>Domináns narratívák részletesen</h2>
    <p>
      Az alábbi négy blokk azt mutatja, hogy az aktuális híranyag alapján mely ügyek alakítják
      leginkább az ország politikai hangulatát. A szöveg a cikkcímekből, témasúlyokból,
      azonosított szereplőkből és social jelzésekből épül fel.
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
