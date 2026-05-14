import json
from datetime import datetime

data = {
    "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    "countries": [
        {
            "name": "Szerbia",
            "score": -15,
            "status": "negative",
            "main_topic": "kormányellenes tüntetések"
        },
        {
            "name": "Bosznia-Hercegovina",
            "score": -6,
            "status": "neutral",
            "main_topic": "alkotmányos viták"
        },
        {
            "name": "Koszovó",
            "score": -20,
            "status": "negative",
            "main_topic": "határfeszültség"
        },
        {
            "name": "Montenegró",
            "score": 8,
            "status": "positive",
            "main_topic": "EU-csatlakozás"
        },
        {
            "name": "Észak-Macedónia",
            "score": -3,
            "status": "neutral",
            "main_topic": "választási kampány"
        },
        {
            "name": "Albánia",
            "score": 12,
            "status": "positive",
            "main_topic": "gazdasági növekedés"
        }
    ]
}

with open("docs/data/latest.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print("latest.json sikeresen frissítve")
