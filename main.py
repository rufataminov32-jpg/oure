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
        elif prop_type == "multi_select":
            return ", ".join([i["name"] for i in prop.get("multi_select", [])])
        elif prop_type == "date":
            return prop["date"]["start"] if prop.get("date") else ""
        elif prop_type == "files":
            files = prop.get("files", [])
            return files[0]["file"]["url"] if files else "—"
    except (KeyError, IndexError, TypeError):
        return "—"


def format_message(props):
    fio = get_text(props.get("1 Ф.И.Ш.", {}), "title")
    telefon = get_text(props.get("2 Телефон (шахсий)", {}), "phone_number")
    telefon_oila = get_text(props.get("3 Телефон (оила аъзоси)", {}), "phone_number")
    tug_sana = get_text(props.get("4 Туғилган санаси", {}), "date")
    ish_sana = get_text(props.get("5 Иш бошлаган сана", {}), "date")
    manzil = get_text(props.get("6 Яшаш манзили (Туман, МФЙ, Кўча, уй)", {}), "rich_text")
    pinfl = get_text(props.get("7 ПИНФЛ", {}), "number")
    pasport = get_text(props.get("8 Паспорт S/N", {}), "rich_text")
    plastik = get_text(props.get("9 Пластик карта рақами", {}), "number")
    malumot = get_text(props.get("10 Маълумоти", {}), "select")
    oila = get_text(props.get("11 Оилавий аҳволи", {}), "select")
    tillar = get_text(props.get("12 Чет тиллари", {}), "multi_select")
    oldin = get_text(props.get("13 Олдин ишлаган жой (ташкилот, лавозим)", {}), "rich_text")
    foto = get_text(props.get("14 фото", {}), "files")

    return (
        f"🆕 <b>ХОДИМ АНКЕТАСИ</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>Ф.И.Ш.</b>\n{fio}\n\n"
        f"📞 <b>Телефон</b>\n{telefon}\n\n"
        f"👨‍👩‍👧 <b>Оила телефони</b>\n{telefon_oila}\n"
        f"🎂 <b>Туғилган сана</b>\n{tug_sana}\n"
        f"📅 <b>Иш бошлаган сана</b>\n{ish_sana}\n"
        f"🏠 <b>Манзил</b>\n{manzil}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🪪 <b>ПИНФЛ:</b> <code>{pinfl}</code>\n"
        f"📄 <b>Паспорт:</b> <code>{pasport}</code>\n"
        f"💳 <b>Пластик:</b> <code>{plastik}</code>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"🎓 <b>Маълумот:</b> {malumot}\n"
        f"👪 <b>Оилавий аҳвол:</b> {oila}\n"
        f"🌐 <b>Тиллар:</b> {tillar}\n\n"
        f"🏢 <b>Олдин ишлаган жой</b>\n{oldin}\n\n"
        f"🖼 <b>Фото:</b> {foto}"
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
