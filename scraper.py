import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

NOTICE_URL = "https://hub.rgukt.ac.in/hub/notice/index"

def _extract_notice_links(body_div):
    attachment_url = None
    external_url = None
    if not body_div:
        return attachment_url, external_url

    for a_tag in body_div.find_all("a", href=True):
        href = a_tag["href"]
        if any(href.lower().endswith(ext) for ext in [".pdf", ".doc", ".docx"]):
            attachment_url = urljoin(NOTICE_URL, href)
            break

    click_tag = body_div.find("a", string=lambda x: x and "here" in x.lower())
    if click_tag and click_tag.get("href"):
        external_url = urljoin(NOTICE_URL, click_tag.get("href"))
    else:
        text_urls = re.findall(r'https?://\S+', body_div.get_text())
        for u in text_urls:
            if u != attachment_url:
                external_url = u
                break
    return attachment_url, external_url

def scrape_last_10_notices():
    resp = requests.get(NOTICE_URL, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    notices = []

    for header in soup.find_all("div", class_="card-header"):
        title_tag = header.find("a", class_="card-link")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        tl = title.lower()
        if ("examination" not in tl) and ("external" not in tl) and ("internal" not in tl):
            continue

        collapse_div = header.find_next_sibling("div", class_="collapse")
        body_div = collapse_div.find("div", class_="card-body") if collapse_div else None
        attachment_url, external_url = _extract_notice_links(body_div)

        date = None
        if body_div:
            text = body_div.get_text()
            m = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
            if m:
                date = m.group(1)
            else:
                m = re.search(r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b', text)
                if m:
                    d, mo, y = m.groups()
                    date = f"{y}-{int(mo):02d}-{int(d):02d}"

        notice_id = f"{title}|{external_url}|{attachment_url}"
        notices.append((notice_id, title, external_url, attachment_url, date))

    notices.sort(key=lambda x: x[4] if x[4] else "9999-99-99")
    return notices[:10]
