from datetime import datetime, timedelta
from googleapiclient.discovery import Resource
from zoneinfo import ZoneInfo


def find_events(
    service: Resource,
    date_str: str,
    title: str,
    calendar_id: str,
    timezone: str
) -> list[str]:
    """
    予定を検索する。
    """
    target_date = datetime.strptime(date_str, "%Y年%m月%d日").date()

    # 開始日時（当日0時）
    start_date = datetime.combine(
        target_date,
        datetime.min.time(),
        tzinfo=ZoneInfo(timezone)
    )

    # 終了日時（翌日0時）
    end_date = start_date + timedelta(days=1)

    result = (
        service
        .events()
        .list(
            calendarId=calendar_id,
            timeMin=start_date.isoformat(),
            timeMax=end_date.isoformat(),
            singleEvents=True,
            showDeleted=False
        )
        .execute()
    )

    return [
        event["id"]
        for event in result.get("items", [])
        if event.get("summary", "").strip() == title
    ]


def add_event(
    service: Resource,
    date_str: str,
    title: str,
    calendar_id: str,
    color_id: str
) -> None:
    """
    予定を登録する。
    """
    start_date = datetime.strptime(date_str, "%Y年%m月%d日").date()
    end_date = start_date + timedelta(days=1)

    # 登録内容
    event_body = {
        "summary": title,
        "start": {"date": start_date.isoformat()},
        "end": {"date": end_date.isoformat()},
        "colorId": color_id
    }

    (
        service
        .events()
        .insert(
            calendarId=calendar_id,
            body=event_body
        )
        .execute()
    )


def delete_events(
    service: Resource,
    event_ids: list[str],
    calendar_id: str
) -> None:
    """
    予定を削除する。
    """
    for event_id in event_ids:
        (
            service
            .events()
            .delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendUpdates="none"
            )
            .execute()
        )

