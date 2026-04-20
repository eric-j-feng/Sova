import json
import logging
from datetime import datetime
from typing import List

from requests import HTTPError, Session

from resy.exceptions import AuthError, BookingError
from resy.models import (
    AuthResponseBody,
    BookResponseBody,
    DetailsResponseBody,
    FindResponseBody,
    ResyConfig,
    Slot,
)

logger = logging.getLogger(__name__)

RESY_BASE_URL = "https://api.resy.com"
# (connect_timeout, read_timeout) in seconds — short enough to fail fast and retry
REQUEST_TIMEOUT = (3.0, 10.0)


def _build_session(config: ResyConfig) -> Session:
    session = Session()
    token = config.token or ""
    session.headers.update(
        {
            "Authorization": config.get_authorization(),
            "X-Resy-Auth-Token": token,
            "X-Resy-Universal-Auth": token,
            "Origin": "https://resy.com",
            "X-Origin": "https://resy.com",
            "Referrer": "https://resy.com/",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
    )
    return session


class ResyClient:
    def __init__(self, config: ResyConfig):
        self.config = config
        self.session = _build_session(config)

    def authenticate(self) -> None:
        """Exchange email/password for an auth token and payment method ID."""
        url = f"{RESY_BASE_URL}/3/auth/password"
        resp = self.session.post(
            url,
            data={"email": self.config.email, "password": self.config.password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=REQUEST_TIMEOUT,
        )
        if not resp.ok:
            raise AuthError(f"Authentication failed [{resp.status_code}]: {resp.text}")

        body = AuthResponseBody(**resp.json())
        self.config.token = body.token
        if body.payment_methods:
            self.config.payment_method_id = body.payment_methods[0].id
        else:
            raise AuthError("No payment methods found on this account — add one at resy.com")

        # Propagate the new token to all future requests
        self.session.headers.update(
            {
                "X-Resy-Auth-Token": body.token,
                "X-Resy-Universal-Auth": body.token,
            }
        )
        logger.info("Authenticated successfully (payment method id: %s)", self.config.payment_method_id)

    def find_slots(self, venue_id: int, party_size: int, day: str) -> List[Slot]:
        """Return available slots for the venue on the given day (YYYY-MM-DD)."""
        url = f"{RESY_BASE_URL}/4/find"
        params = {
            "lat": "0",
            "long": "0",
            "day": day,
            "party_size": party_size,
            "venue_id": venue_id,
        }
        logger.info("[%s] Searching for slots on %s for %d...", datetime.now().strftime("%H:%M:%S"), day, party_size)
        resp = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if not resp.ok:
            raise HTTPError(f"Find failed [{resp.status_code}]: {resp.text}")

        body = FindResponseBody(**resp.json())
        venues = body.results.venues
        if not venues:
            return []
        return venues[0].slots

    def get_booking_token(self, config_token: str, party_size: int, day: str) -> str:
        """Fetch the time-limited book_token needed to complete a booking."""
        url = f"{RESY_BASE_URL}/3/details"
        params = {
            "config_id": config_token,
            "party_size": party_size,
            "day": day,
        }
        resp = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if not resp.ok:
            raise HTTPError(f"Details failed [{resp.status_code}]: {resp.text}")

        body = DetailsResponseBody(**resp.json())
        return body.book_token.value

    def book(self, book_token: str, payment_method_id: int) -> str:
        """Confirm the reservation. Returns the resy_token on success."""
        url = f"{RESY_BASE_URL}/3/book"
        data = {
            "book_token": book_token,
            # The API expects this as a JSON string inside the form body
            "struct_payment_method": json.dumps({"id": payment_method_id}),
            "source_id": "resy.com-venue-details",
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://widgets.resy.com",
            "X-Origin": "https://widgets.resy.com",
            "Referrer": "https://widgets.resy.com/",
            "Cache-Control": "no-cache",
        }
        resp = self.session.post(url, data=data, headers=headers, timeout=REQUEST_TIMEOUT)
        if not resp.ok:
            raise BookingError(f"Booking failed [{resp.status_code}]: {resp.text}")

        body = BookResponseBody(**resp.json())
        logger.info("Booking confirmed — resy_token: %s", body.resy_token)
        return body.resy_token
