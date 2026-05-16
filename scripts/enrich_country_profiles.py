import json
import os

PROFILE_PATH = "docs/data/country_profiles.json"

ENRICHMENT = {
    "Szerbia": {
        "ethnicity": [
            {"group": "Szerb", "percent": 83.3},
            {"group": "Magyar", "percent": 3.5},
            {"group": "Roma", "percent": 2.1},
            {"group": "Bosnyák", "percent": 2.0},
            {"group": "Egyéb / ismeretlen", "percent": 9.1}
        ],
        "sources": [
            {"name": "World Bank Data", "fields": ["population", "gdp", "trade", "inflation"]},
            {"name": "CIA World Factbook / census-based data", "fields": ["ethnicity", "religion"]},
            {"name": "National Bank of Serbia", "fields": ["central_bank.interest_rate"]},
            {"name": "ECB reference rates", "fields": ["fx_rates"]}
        ]
    },

    "Bosznia-Hercegovina": {
        "ethnicity": [
            {"group": "Bosnyák", "percent": 50.1},
            {"group": "Szerb", "percent": 30.8},
            {"group": "Horvát", "percent": 15.4},
            {"group": "Egyéb / nem nyilatkozott", "percent": 3.7}
        ],
        "sources": [
            {"name": "World Bank Data", "fields": ["population", "gdp", "trade", "inflation"]},
            {"name": "2013 census / World Factbook country data", "fields": ["ethnicity", "religion"]},
            {"name": "Central Bank of Bosnia and Herzegovina", "fields": ["currency_board", "BAM_EUR_peg"]}
        ]
    },

    "Koszovó": {
        "ethnicity": [
            {"group": "Albán", "percent": 91.8},
            {"group": "Szerb", "percent": 2.3},
            {"group": "Bosnyák", "percent": 1.7},
            {"group": "Török", "percent": 1.2},
            {"group": "Roma / askáli / egyiptomi / egyéb", "percent": 3.0}
        ],
        "sources": [
            {"name": "World Bank Data", "fields": ["population", "gdp", "trade", "inflation"]},
            {"name": "Kosovo census / country statistical data", "fields": ["ethnicity", "religion"]},
            {"name": "Central Bank of Kosovo", "fields": ["monetary_context"]}
        ]
    },

    "Montenegró": {
        "ethnicity": [
            {"group": "Montenegrói", "percent": 45.0},
            {"group": "Szerb", "percent": 28.7},
            {"group": "Bosnyák", "percent": 8.7},
            {"group": "Albán", "percent": 4.9},
            {"group": "Egyéb", "percent": 12.7}
        ],
        "sources": [
            {"name": "World Bank Data", "fields": ["population", "gdp", "trade", "inflation"]},
            {"name": "Census-based country data / World Factbook", "fields": ["ethnicity", "religion"]},
            {"name": "Central Bank of Montenegro", "fields": ["monetary_context"]}
        ]
    },

    "Észak-Macedónia": {
        "ethnicity": [
            {"group": "Macedón", "percent": 58.4},
            {"group": "Albán", "percent": 24.3},
            {"group": "Török", "percent": 3.9},
            {"group": "Roma", "percent": 2.5},
            {"group": "Szerb / bosnyák / egyéb", "percent": 10.9}
        ],
        "sources": [
            {"name": "World Bank Data", "fields": ["population", "gdp", "trade", "inflation"]},
            {"name": "National census / statistical office", "fields": ["ethnicity", "religion"]},
            {"name": "National Bank of the Republic of North Macedonia", "fields": ["central_bank.interest_rate"]},
            {"name": "ECB reference rates", "fields": ["fx_rates"]}
        ]
    },

    "Albánia": {
        "ethnicity": [
            {"group": "Albán", "percent": 91.0},
            {"group": "Görög", "percent": 1.0},
            {"group": "Roma / aromán / egyéb", "percent": 8.0}
        ],
        "sources": [
            {"name": "World Bank Data", "fields": ["population", "gdp", "trade", "inflation"]},
            {"name": "INSTAT / census-based data", "fields": ["ethnicity", "religion"]},
            {"name": "Bank of Albania", "fields": ["central_bank.interest_rate"]},
            {"name": "ECB reference rates", "fields": ["fx_rates"]}
        ]
    }
}


def main():
    if not os.path.exists(PROFILE_PATH):
        raise FileNotFoundError(f"Nincs ilyen fájl: {PROFILE_PATH}")

    with open(PROFILE_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    data["data_quality_note"] = (
        "Induló országprofil-adatbázis. A strukturális adatok forrásellenőrzéssel "
        "és időszakos frissítéssel kezelendők. A live FX/kamat adatok külön fájlból érkeznek."
    )

    data["global_sources"] = [
        {
            "name": "World Bank Data",
            "use": "Népesség, GDP, GDP/fő, infláció, munkanélküliség, kereskedelmi adatok"
        },
        {
            "name": "CIA World Factbook / országos statisztikai hivatalok",
            "use": "Etnikai, vallási és társadalmi szerkezeti adatok"
        },
        {
            "name": "ECB euro foreign exchange reference rates",
            "use": "EUR-alapú napi devizaárfolyamok"
        },
        {
            "name": "Nemzeti jegybankok",
            "use": "Jegybanki kamatok és monetáris politikai adatok"
        }
    ]

    for country in data.get("countries", []):
        name = country.get("name")

        if name in ENRICHMENT:
            country["ethnicity"] = ENRICHMENT[name]["ethnicity"]
            country["sources"] = ENRICHMENT[name]["sources"]
            country["data_quality"] = "starter_estimate_with_sources"

    with open(PROFILE_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print("country_profiles.json bővítve: ethnicity + sources")


if __name__ == "__main__":
    main()
