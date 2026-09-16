import re
import requests

from bs4 import BeautifulSoup

from utils import retry


BELL_ALERT_URL = "https://alert.shop-bell.com/"

CATEGORY_PATH = {
    "漫画": "comic/",
    "ラノベ": "ranobe/detail/",
    "電子書籍": "comic/ebook/"
}


@retry(n_retry=10)
def fetch_latest_release(
    alert_id: int,
    category: str
) -> tuple[int, str]:
    if category not in CATEGORY_PATH:
        raise ValueError(f"未対応のカテゴリーです: {category}")

    url = f"{BELL_ALERT_URL}{CATEGORY_PATH[category]}{alert_id}"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    lead = soup.find("div", class_="iteminfo lead")

    if lead is None:
        return None, None

    # 次の巻数と発売予定日が取得できるかどうか
    text = lead.text.strip()

    matched = re.search(
        r"(\d+)巻は(\d{4}年\d{2}月\d{2}日)の発売予定です。",
        text
    )

    if matched:
        return int(matched.group(1)), matched.group(2)

    # 次巻の発売予定日を取得できるかどうか
    matched = re.search(
        r"次巻は(\d{4}年\d{2}月\d{2}日)の発売予定です。",
        text
    )

    if matched:
        return None, matched.group(1)

    # 既巻
    matched = re.search(
        r"(\d+)巻は(\d{4}年\d{2}月\d{2}日)に発売されました。",
        text
    )

    if matched:
        return int(matched.group(1)), matched.group(2)
    else:
        return None, None

