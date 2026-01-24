import httpx
import respx

from recent_state_summarizer.fetch.qiita_api import fetch_qiita_api


class TestQiitaAPI:
    @respx.mock
    def test_fetch_qiita_api(self):
        api_response = [
            {
                "id": "abc123",
                "title": "Sample Qiita API Article 1",
                "url": "https://qiita.com/ftnext/items/abc123",
                "created_at": "2025-01-14T10:00:00+09:00",
                "updated_at": "2025-01-14T10:00:00+09:00",
                "user": {"id": "ftnext"},
            },
            {
                "id": "def456",
                "title": "Sample Qiita API Article 2",
                "url": "https://qiita.com/ftnext/items/def456",
                "created_at": "2022-10-01T19:34:17+09:00",
                "updated_at": "2022-10-08T17:23:09+09:00",
                "user": {"id": "ftnext"},
            },
        ]
        respx.get("https://qiita.com/api/v2/users/ftnext/items").mock(
            return_value=httpx.Response(
                status_code=200,
                json=api_response,
                headers={"content-type": "application/json"},
            )
        )

        result = list(
            fetch_qiita_api("https://qiita.com/api/v2/users/ftnext/items")
        )

        assert len(result) == 2
        assert result[0]["title"] == "Sample Qiita API Article 1"
        assert result[0]["url"] == "https://qiita.com/ftnext/items/abc123"
        assert result[1]["title"] == "Sample Qiita API Article 2"
        assert result[1]["url"] == "https://qiita.com/ftnext/items/def456"
