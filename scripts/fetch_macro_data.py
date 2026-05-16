import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

OUTPUT_PATH = "docs/data/country_profiles_live.json"

ECB_DAILY_XML = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"

COUNTRIES = [
    {
        "name": "Szerbia",
        "currency": "RSD",
        "central_bank": "National Bank of Serbia",
        "policy_rate_url": "https://www.nbs.rs/en/ciljevi-i-funkcije/monetarna-politika/kamatne-stope/",
        "rate_regex": r"Key policy rate\s*([0-9]+(?:[.,][0-9]+)?)%"
    },
    {
        "name": "Bosznia-Hercegovina",
        "currency": "BAM",
        "central_bank": "Central Bank of Bosnia and Herzegovina",
        "fixed_eur_rate": 1.95583,
        "policy_rate": None,
        "note": "BAM euróhoz kötött valutatanács-rendszerben."
    },
    {
        "name": "Koszovó",
        "currency": "EUR",
        "central_bank": "Central Bank of Kosovo",
        "fixed_eur_rate": 1.0,
        "policy_rate": None,
        "note": "Koszovó eurót használ, nincs klasszikus önálló alapkamat."
    },
    {
        "name": "Montenegró",
        "currency": "EUR",
        "central_bank": "Central Bank of Montenegro",
        "fixed_eur_rate": 1.0,
        "policy_rate": None,
        "note": "Montenegró eurót használ, nincs klasszikus önálló EUR-árfolyam."
    },
    {
        "name": "Észak-Macedónia",
        "currency": "MKD",
        "central_bank": "National Bank of the Republic of North Macedonia",
        "policy_rate": 5.2,
        "note": "Induló érték. Később külön jegybanki scraperrel pontosítható."
    },
    {
        "name": "Albánia",
        "currency": "ALL",
        "central_bank": "Bank of Albania",
        "policy_rate_url": "https://www.bankofalbania.org/Markets/Interest_rates/",
        "rate_regex": r"Repo Rate\s*([0-9]+(?:[.,][0-9]+)?)\s*%"
    }
]


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def fetch_text(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Balkan-Country-Profiles/1.0"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def fetch_ecb_rates():
    try:
        raw_xml = fetch_text(ECB_DAILY_XML)

        root = ET.fromstring(raw_xml)

        rates = {}

        date = None

        for cube in root.iter():
            if cube.tag.endswith("Cube"):
                if "time" in cube.attrib:
                    date = cube.attrib.get("time")

                currency = cube.attrib.get("currency")
                rate = cube.attrib.get("rate")

                if currency and rate:
                    rates[currency] = float(rate)

        return {
            "date": date,
            "base": "EUR",
            "rates": rates,
            "source": "ECB euro foreign exchange reference rates",
            "url": ECB_DAILY_XML
        }

    except Exception as error:
        print("ECB árfolyam lekérés sikertelen")
        print(error)

        return {
            "date": None,
            "base": "EUR",
            "rates": {},
            "source": "ECB euro foreign exchange reference rates",
            "url": ECB_DAILY_XML,
            "error": str(error)
        }


def parse_policy_rate_from_page(url, pattern):
    try:
        html = fetch_text(url)

        clean = re.sub(r"<[^>]+>", " ", html)
        clean = re.sub(r"\s+", " ", clean)

        match = re.search(pattern, clean, flags=re.IGNORECASE)

        if not match:
            return None

        value = match.group(1).replace(",", ".")

        return float(value)

    except Exception as error:
        print(f"Kamat lekérés sikertelen: {url}")
        print(error)
        return None


def build_country_live(country, ecb_data):
    currency = country["currency"]

    fx_rate = None
    fx_source = "ECB / fixed EUR context"
    fx_note = ""

    if "fixed_eur_rate" in country:
        fx_rate = country["fixed_eur_rate"]

        if currency == "EUR":
            fx_note = "EUR használat, ezért az EUR/EUR árfolyam 1."
        else:
            fx_note = "Fix euróárfolyam / valutatanács-kötés."

    else:
        fx_rate = ecb_data.get("rates", {}).get(currency)

        if fx_rate is None:
            fx_note = "Az ECB napi listában nem található friss árfolyam ehhez a valutához."
        else:
            fx_note = f"1 EUR = {fx_rate} {currency}"

    policy_rate = country.get("policy_rate")

    if policy_rate is None and country.get("policy_rate_url") and country.get("rate_regex"):
        parsed_rate = parse_policy_rate_from_page(
            country["policy_rate_url"],
            country["rate_regex"]
        )

        if parsed_rate is not None:
            policy_rate = parsed_rate

    return {
        "name": country["name"],
        "currency": currency,
        "fx": {
            "base": "EUR",
            "quote": currency,
            "rate": fx_rate,
            "date": ecb_data.get("date"),
            "source": fx_source,
            "note": fx_note
        },
        "central_bank": {
            "name": country.get("central_bank"),
            "policy_rate": policy_rate,
            "source_url": country.get("policy_rate_url"),
            "note": country.get("note", "")
        }
    }


def main():
    os.makedirs("docs/data", exist_ok=True)

    ecb_data = fetch_ecb_rates()

    countries = [
        build_country_live(country, ecb_data)
        for country in COUNTRIES
    ]

    output = {
        "updated_at": now_utc(),
        "method_note": (
            "Live országprofil-kiegészítő adatok. "
            "Az FX értékek elsődlegesen ECB EUR referenciaárfolyamok. "
            "BAM fix EUR-kötésként, EUR-t használó országok EUR/EUR=1 alapon jelennek meg. "
            "A kamatok országonként eltérő jegybanki logikát követnek."
        ),
        "fx_source": {
            "name": ecb_data.get("source"),
            "url": ecb_data.get("url"),
            "date": ecb_data.get("date")
        },
        "countries": countries
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print("country_profiles_live.json elkészült")


if __name__ == "__main__":
    main()
