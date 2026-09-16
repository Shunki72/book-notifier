import json

from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)
from pathlib import Path


def send_message(text: str, token_path: Path) -> None:
    """
    LINEでメッセージを送る。
    """
    data = json.loads(token_path.read_text(encoding="utf-8"))

    config = Configuration(
        access_token=data["channel_access_token"]
    )

    with ApiClient(config) as api_client:
        (
            MessagingApi(api_client)
            .push_message(
                PushMessageRequest(
                    to=data["user_id"],
                    messages=[TextMessage(text=text)]
                )
            )
        )

