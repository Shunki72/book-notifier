import json
import polars as pl
import re

from functools import wraps
from pathlib import Path
from time import sleep

from models import BookRecord, Configuration


PROJECT_DIR = Path(__file__).resolve().parents[1]


def _path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_DIR / path


def load_config() -> Configuration:
    config_path = PROJECT_DIR / Path("data/config.json")
    data = json.loads(config_path.read_text(encoding="utf-8"))

    return Configuration(
        database_path=_path(data["database_path"]),
        google_credentials_path=_path(data["google_credentials_path"]),
        google_token_path=_path(data["google_token_path"]),
        google_scopes=data["google_scopes"],
        google_calendar_id=data["google_calendar_id"],
        google_calendar_color_id=data["google_calendar_color_id"],
        line_token_path=_path(data["line_token_path"]),
        timezone=data["timezone"]
    )


def _load_record(record: dict) -> BookRecord:
    alert_id = record["アラートID"]
    category = record["カテゴリー"]
    title = record["タイトル"]
    calendar_title = record["カレンダー用タイトル"]
    volume = record["最新巻"]
    release_date = record["発売日"]

    # アラートIDが整数
    alert_id = int(alert_id)

    # カテゴリーが漫画・ラノベ・電子書籍
    category = category.strip()

    if category.strip() not in {"漫画", "ラノベ", "電子書籍"}:
        raise ValueError(f"非対応のカテゴリー: {category}")

    # タイトルの整形
    title = title.strip()
    calendar_title = calendar_title.strip()

    # 巻数は整数
    volume = int(volume)

    # 発売日はYYYY年MM月DD日形式
    release_date = release_date.strip()

    if not re.match(r"\d{4}年\d{2}月\d{2}日", release_date):
        raise ValueError(f"非対応の日付形式: {release_date}")

    return BookRecord(
        alert_id=alert_id,
        category=category,
        title=title,
        calendar_title=calendar_title,
        volume=volume,
        release_date=release_date
    )


def load_db(database_path: Path) -> list[BookRecord]:
    table = pl.read_excel(database_path)

    return [
        _load_record(record)
        for record in table.iter_rows(named=True)
    ]


def save_db(
    book_db: list[BookRecord],
    database_path: Path
) -> None:
    rows = []

    for book in book_db:
        rows.append(
            {
                "アラートID": book.alert_id,
                "カテゴリー": book.category,
                "タイトル": book.title,
                "カレンダー用タイトル": book.calendar_title,
                "最新巻": book.volume,
                "発売日": book.release_date
            }
        )

    table = pl.DataFrame(rows).unique().sort("タイトル", "カテゴリー")
    table.write_excel(database_path)


def retry(
    n_retry: int = 10,
    interval: float = 5,
    exceptions: tuple = (Exception,)
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(n_retry):
                try:
                    return func(*args, **kwargs)

                except exceptions:
                    if attempt == n_retry:
                        raise

                    if interval > 0:
                        sleep(interval)

        return wrapper

    return decorator