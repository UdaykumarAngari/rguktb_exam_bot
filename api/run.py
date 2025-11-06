import os
import requests
from upstash_redis import Redis
from scraper import scrape_last_10_notices

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_CHAT_ID = int(os.environ["GROUP_CHAT_ID"])
REDIS_URL = os.environ["UPSTASH_REDIS_REST_URL"]
REDIS_TOKEN = os.environ["UPSTASH_REDIS_REST_TOKEN"]

redis = Redis(url=REDIS_URL, token=REDIS_TOKEN)
SEEN_SET_KEY = "rgukt_exam_bot:seen_notice_ids"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def _build_message(title, external_url, attachment_url):
    lines = [title]
    if external_url:
        lines.append(f"URL: {external_url}")
    if attachment_url:
        lines.append(f"Notice Attachment: {attachment_url}")
    return "\n".join(lines)

def _send_telegram(text):
    r = requests.post(
        TELEGRAM_API,
        json={"chat_id": GROUP_CHAT_ID, "text": text, "disable_web_page_preview": True},
        timeout=20,
    )
    r.raise_for_status()

def handler(request):
    notices = scrape_last_10_notices()
    sent_count = 0
    for notice_id, title, external, attachment, _ in notices:
        if not redis.sismember(SEEN_SET_KEY, notice_id):
            _send_telegram(_build_message(title, external, attachment))
            redis.sadd(SEEN_SET_KEY, notice_id)
            sent_count += 1

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": f'{{"processed": {len(notices)}, "sent": {sent_count}}}'
    }
