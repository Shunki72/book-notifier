from dataclasses import dataclass
from pathlib import Path


@dataclass
class BookRecord:
    alert_id: int       # アラートID
    category: str       # カテゴリー: 漫画 or ラノベ or 電子書籍
    title: str          # タイトル
    calendar_title: str # カレンダー登録用タイトル
    volume: int         # 最新巻
    release_date: str   # 発売日


@dataclass
class Configuration:
    database_path: Path
    google_credentials_path: Path
    google_token_path: Path
    google_scopes: list[str]
    google_calendar_id: str
    google_calendar_color_id: str
    line_token_path: Path
    timezone: str

