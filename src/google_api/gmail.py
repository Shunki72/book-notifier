import base64

from bs4 import BeautifulSoup
from email.header import decode_header, make_header
from googleapiclient.discovery import Resource
from html import unescape


def _decode(data: str) -> str:
    return (
        base64
        .urlsafe_b64decode(data + "=" * (-len(data) % 4))
        .decode("utf-8", "replace")
    )


def _subject(payload: dict) -> str:
    raw = next(
        (
            h["value"]
            for h in payload.get("headers", [])
            if h["name"].lower() == "subject"
        ),
        ""
    )
    return str(make_header(decode_header(raw)))


def _body(payload: dict) -> str:
    texts = []

    def walk(part: dict) -> None:
        mime = part.get("mimeType", "")
        data = part.get("body", dict()).get("data")

        if data and mime in {"text/plain", "text/html"}:
            value = _decode(data)

            if mime == "text/html":
                value = (
                    BeautifulSoup(value, "html.parser")
                    .get_text("\n")
                )

            texts.append(value)

        for child in part.get("parts", []):
            walk(child)

    walk(payload)

    return unescape("\n".join(texts)).replace("\r", "")


def fetch_notices(
    service: Resource,
    query: str,
    max_results: int
) -> list[dict]:
    """
    メールを取得する。
    """
    response = (
        service
        .users()
        .messages()
        .list(
            userId="me",
            q=query,
            maxResults=max_results
        )
        .execute()
    )

    notices = []

    for item in response.get("messages", []):
        message_id = item["id"]

        message = (
            service
            .users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full"
            )
            .execute()
        )

        payload = message.get("payload", dict())

        subject = _subject(payload)
        body = _body(payload)

        notices.append(
            {
                "id": message_id,
                "subject": subject,
                "body": body
            }
        )

    return notices


def mark_as_read(
    service: Resource,
    message_ids: list[str]
) -> None:
    """
    既読にする。
    """
    for message_id in message_ids:
        (
            service
            .users()
            .messages()
            .modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]}
            )
        )

