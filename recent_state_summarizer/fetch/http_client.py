import logging
import time

import httpx
from tenacity import Retrying, stop_after_attempt, wait_exponential
from urllib3.exceptions import InvalidHeader
from urllib3.util import Retry

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 4
MAX_RETRY_AFTER_SECONDS = 60
INITIAL_BACKOFF_SECONDS = 1


def _retry_after_seconds(response: httpx.Response) -> float | None:
    retry_after = response.headers.get("Retry-After")
    if retry_after is None:
        return None
    try:
        return Retry().parse_retry_after(retry_after)
    except InvalidHeader:
        logger.warning(
            "Could not parse Retry-After header %r, falling back to "
            "exponential backoff",
            retry_after,
        )
        return None


def _should_retry(retry_state) -> bool:
    response = retry_state.outcome.result()
    if response.status_code != httpx.codes.TOO_MANY_REQUESTS:
        return False
    retry_after = _retry_after_seconds(response)
    return retry_after is None or retry_after <= MAX_RETRY_AFTER_SECONDS


def _wait(retry_state) -> float:
    response = retry_state.outcome.result()
    retry_after = _retry_after_seconds(response)
    if retry_after is not None:
        return retry_after
    return wait_exponential(
        multiplier=INITIAL_BACKOFF_SECONDS, max=MAX_RETRY_AFTER_SECONDS
    )(retry_state)


def _log_before_sleep(retry_state) -> None:
    logger.info(
        "Waiting %s seconds before retry attempt %s",
        retry_state.next_action.sleep,
        retry_state.attempt_number + 1,
    )


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


def get(url: str, **kwargs) -> httpx.Response:
    retrying = Retrying(
        retry=_should_retry,
        wait=_wait,
        stop=stop_after_attempt(MAX_ATTEMPTS),
        before_sleep=_log_before_sleep,
        sleep=_sleep,
        retry_error_callback=lambda retry_state: retry_state.outcome.result(),
    )
    response = retrying(httpx.get, url, **kwargs)
    if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
        retry_after = _retry_after_seconds(response)
        if retry_after is not None and retry_after > MAX_RETRY_AFTER_SECONDS:
            logger.warning(
                "Giving up on %s: Retry-After is %s seconds, which "
                "exceeds the %s second limit",
                url,
                retry_after,
                MAX_RETRY_AFTER_SECONDS,
            )
        else:
            logger.warning(
                "Giving up on %s: still 429 after %s attempts",
                url,
                MAX_ATTEMPTS,
            )
        response.raise_for_status()
    return response
