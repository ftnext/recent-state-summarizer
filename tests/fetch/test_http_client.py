import email.utils
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import respx
from httpx import Response

from recent_state_summarizer.fetch import http_client

URL = "https://example.com/resource"


@pytest.fixture
def recorded_sleeps(monkeypatch):
    sleeps = []
    monkeypatch.setattr(http_client, "_sleep", sleeps.append)
    return sleeps


@respx.mock
def test_retry_after_seconds_sleeps_then_retries(recorded_sleeps):
    respx.get(URL).mock(
        side_effect=[
            Response(429, headers={"Retry-After": "30"}),
            Response(200, text="ok"),
        ]
    )

    response = http_client.get(URL)

    assert response.status_code == 200
    assert recorded_sleeps == [30.0]


@respx.mock
def test_retry_after_http_date_sleeps_then_retries(recorded_sleeps):
    retry_after_at = datetime.now(timezone.utc) + timedelta(seconds=30)
    respx.get(URL).mock(
        side_effect=[
            Response(
                429,
                headers={
                    "Retry-After": email.utils.format_datetime(retry_after_at)
                },
            ),
            Response(200, text="ok"),
        ]
    )

    response = http_client.get(URL)

    assert response.status_code == 200
    assert len(recorded_sleeps) == 1
    assert 25 <= recorded_sleeps[0] <= 30


@respx.mock
def test_missing_retry_after_uses_exponential_backoff(recorded_sleeps):
    respx.get(URL).mock(
        side_effect=[
            Response(429),
            Response(429),
            Response(429),
            Response(200, text="ok"),
        ]
    )

    response = http_client.get(URL)

    assert response.status_code == 200
    assert recorded_sleeps == [1.0, 2.0, 4.0]


@respx.mock
def test_retry_after_over_limit_raises_without_sleeping(
    recorded_sleeps, caplog
):
    respx.get(URL).mock(
        return_value=Response(429, headers={"Retry-After": "3600"})
    )

    with caplog.at_level("WARNING"):
        with pytest.raises(httpx.HTTPStatusError):
            http_client.get(URL)

    assert recorded_sleeps == []
    assert "3600" in caplog.text


@respx.mock
def test_invalid_retry_after_falls_back_to_backoff(recorded_sleeps, caplog):
    respx.get(URL).mock(
        side_effect=[
            Response(429, headers={"Retry-After": "soon"}),
            Response(200, text="ok"),
        ]
    )

    with caplog.at_level("WARNING"):
        response = http_client.get(URL)

    assert response.status_code == 200
    assert recorded_sleeps == [1.0]
    assert "soon" in caplog.text


@respx.mock
def test_max_attempts_reached_raises_http_status_error(recorded_sleeps):
    respx.get(URL).mock(return_value=Response(429))

    with pytest.raises(httpx.HTTPStatusError):
        http_client.get(URL)

    assert len(recorded_sleeps) == http_client.MAX_ATTEMPTS - 1


@respx.mock
def test_200_is_returned_without_retry(recorded_sleeps):
    respx.get(URL).mock(return_value=Response(200, text="ok"))

    response = http_client.get(URL)

    assert response.status_code == 200
    assert recorded_sleeps == []


@respx.mock
def test_404_is_returned_without_retry_or_raising(recorded_sleeps):
    respx.get(URL).mock(return_value=Response(404))

    response = http_client.get(URL)

    assert response.status_code == 404
    assert recorded_sleeps == []
