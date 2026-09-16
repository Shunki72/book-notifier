from datetime import datetime
from time import sleep

from utils import load_config, load_db, save_db
from google_api.google_api import GoogleAPI
from services.bell_alert import fetch_latest_release
from google_api.google_calendar import (
    find_events,
    add_event,
    delete_events
)
from line_api.line_messaging import send_message


def output_log(text: str) -> None:
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print(f"{now} [INFO] {text}", flush=True)


def books_to_message(books: list[str, str]) -> str:
    books_by_date = dict()

    for title, release_date in books:
        books_by_date.setdefault(release_date, [])
        books_by_date[release_date].append(title)

    return "\n\n".join(
        f"{release_date}\n{'\n'.join(sorted(titles))}"
        for release_date, titles in sorted(books_by_date.items())
    )


if __name__ == "__main__":
    output_log("開始")
    today = datetime.now().strftime("%Y年%m月%d日")

    output_log("設定の読み込み")
    config = load_config()

    output_log("新刊通知リスト読み込み")
    book_db = load_db(config.database_path)

    output_log("Google APIクライアント構築")
    service = GoogleAPI(
        credentials_path=config.google_credentials_path,
        token_path=config.google_token_path,
        scopes=config.google_scopes
    )

    output_log("新しい新刊情報の取得開始")

    books_add = []
    books_del = []

    for book in book_db:
        alert_id = book.alert_id
        category = book.category

        # 新刊情報の取得
        volume, release_date = fetch_latest_release(alert_id, category)
        sleep(0.5)

        # 新刊情報なし
        if volume is None and release_date is None:
            continue

        # カレンダー用タイトル
        if volume is None:
            calendar_title = f"{book.calendar_title} 新刊"
            volume = 0
        else:
            calendar_title = f"{book.calendar_title} {volume}"

        # 日付が異なる
        if release_date != book.release_date:

            # データベースの発売日に予定が残っていれば削除
            found_event_ids = find_events(
                service=service.calendar,
                date_str=book.release_date,
                title=calendar_title,
                calendar_id=config.google_calendar_id,
                timezone=config.timezone
            )

            if found_event_ids:
                delete_events(
                    service=service.calendar,
                    event_ids=found_event_ids,
                    calendar_id=config.google_calendar_id
                )

                output_log(f"削除: {book.release_date} {calendar_title}")
                books_del.append((calendar_title, book.release_date))

            # 最新の新刊情報を登録
            found_event_ids = find_events(
                service=service.calendar,
                date_str=release_date,
                title=calendar_title,
                calendar_id=config.google_calendar_id,
                timezone=config.timezone
            )

            # カレンダー未登録なら追加
            if not found_event_ids:
                add_event(
                    service=service.calendar,
                    date_str=release_date,
                    title=calendar_title,
                    calendar_id=config.google_calendar_id,
                    color_id=config.google_calendar_color_id
                )

                output_log(f"追加: {release_date} {calendar_title}")

            book.volume = volume
            book.release_date = release_date

            books_add.append((calendar_title, release_date))

    # 更新
    save_db(book_db, config.database_path)

    output_log("新しい新刊情報の取得完了")

    n_del = len(books_del)
    n_add = len(books_add)

    if n_del + n_add > 0:
        output_log("LINE通知")

        if n_del > 0:
            message_del = books_to_message(books_del)

            messages = [
                f"■カレンダーから削除（{n_del}件）",
                message_del
            ]

        else:
            messages = []

        if n_add > 0:
            message_add = books_to_message(books_add)

            messages += [
                f"■カレンダーに追加（{n_add}件）",
                message_add
            ]

        message = "\n\n".join(messages).strip()
        send_message(message, config.line_token_path)

    output_log("完了")

