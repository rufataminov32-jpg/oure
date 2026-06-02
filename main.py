import os
import time
import requests
from datetime import datetime

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DB_ID = os.environ["NOTION_DB_ID"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def get_new_entries():
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    payload = {
        "filter": {
            "property": "Telegram",
            "checkbox": {"equals": False}
        }
    }
    res = requests.post(url, headers=NOTION_HEADERS, json=payload)
    return res.json().get("results", [])


def mark_as_sent(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Telegram": {"checkbox": True}
        }
    }
    requests.patch(url, headers=NOTION_HEADERS, json=payload)


def get_text(prop, prop_type="rich_text"):
    try:
        if prop_type == "title":
            return prop["title"][0]["plain_text"]
        elif prop_type == "rich_text":
            return prop["rich_text"][0]["plain_text"]
        elif prop_type == "phone_number":
            return prop["phone_number"] or ""
        elif prop_type == "number":
            return str(prop["number"] or "")
        elif prop_type == "select":
            return prop["select"]["name"] if prop.get("select") else ""
        elif prop_type == "date":
            return prop["date"]["start"] if prop.get("date") else ""
    except (KeyError, IndexError, TypeError):
        return "—"


def format_message(props):
    fio = get_text(props.get("1 Ф.И.Ш.", {}), "title")
    lavozim = get_text(props.get("Лавозим", {}), "rich_text")
    telefon = get_text(props.get("2 Телефон (шахсий)", {}), "phone_number")
    pinfl = get_text(props.get("7 ПИНФЛ", {}), "rich_text")
    sana = get_text(props.get("5 Иш бошлаган сана", {}), "date")

    return (
        f"✅ <b>Yangi anketa!</b>\n\n"
        f"👤 <b>F.I.Sh.:</b> {fio}\n"
        f"💼 <b>Lavozim:</b> {lavozim}\n"
        f"📞 <b>Telefon:</b> {telefon}\n"
        f"🪪 <b>PINFL:</b> {pinfl}\n"
        f"📅 <b>Ish boshlagan:</b> {sana}\n"
    )


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)


def run():
    print(f"[{datetime.now()}] Bot ishga tushdi...")
    while True:
        try:
            entries = get_new_entries()
            for entry in entries:
                props = entry["properties"]
                msg = format_message(props)
                send_telegram(msg)
                mark_as_sent(entry["id"])
                print(f"[{datetime.now()}] Yuborildi: {entry['id']}")
        except Exception as e:
            print(f"[{datetime.now()}] Xato: {e}")
        time.sleep(60)


if __name__ == "__main__":
    run()
