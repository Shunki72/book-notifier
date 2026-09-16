from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pathlib import Path


API_VERSION_PAIRS = [
    ("chat", "v1"),
    ("calendar", "v3"),
    ("gmail", "v1")
]


class GoogleAPI:

    def __init__(
        self,
        credentials_path: str | Path,
        token_path: str | Path,
        scopes: list[str]
    ):
        self.credentials_path = Path(credentials_path).resolve()
        self.token_path = Path(token_path).resolve()
        self.scopes = [ str(scope) for scope in scopes ]

        self._authenticate()


    def _apis(self) -> set[str]:
        def _api(scope: str) -> str:
            api = scope.removeprefix("https://www.googleapis.com/auth/")
            api = api.split(".")[0]
            return api

        return { _api(scope) for scope in self.scopes }


    def _credentials(self) -> Credentials:
        credentials = None

        if self.token_path.exists():
            credentials = Credentials.from_authorized_user_file(
                self.token_path,
                self.scopes
            )

        if (
            credentials
            and credentials.expired
            and credentials.refresh_token
        ):
            credentials.refresh(Request())

        if not credentials or not credentials.valid:
            if not self.credentials_path.exists():
                raise FileNotFoundError(
                    "Google OAuth認証情報がありません: "
                    f"{self.credentials_path}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path,
                self.scopes
            )

            credentials = flow.run_local_server(port=0)

            self.token_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            self.token_path.write_text(
                credentials.to_json(),
                encoding="utf-8"
            )

        return credentials


    def _authenticate(self) -> None:
        apis = self._apis()
        credentials = self._credentials()

        for api, version in API_VERSION_PAIRS:
            if api in apis:
                self.__setattr__(
                    api,
                    build(
                        api,
                        version,
                        credentials=credentials,
                        cache_discovery=False
                    )
                )

