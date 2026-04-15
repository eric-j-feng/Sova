import logging
import time
from datetime import datetime

from resy.client import ResyClient
from resy.exceptions import ExhaustedRetriesError, NoSlotsError
from resy.models import BotConfig
from resy.selectors import select_slot

logger = logging.getLogger(__name__)


class ResyBot:
    def __init__(self, config: BotConfig):
        self.config = config
        self.client = ResyClient(config.resy_config)

    def run(self) -> str:
        """
        Authenticate, optionally wait for drop time, then book with retries.
        Returns the resy_token confirming the reservation.
        """
        logger.info("Sova Resy bot starting up...")
        self.client.authenticate()

        if self.config.drop_hour is not None and self.config.drop_minute is not None:
            self._wait_for_drop_time()

        return self._book_with_retries()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _wait_for_drop_time(self) -> None:
        drop = datetime.now().replace(
            hour=self.config.drop_hour,
            minute=self.config.drop_minute,
            second=0,
            microsecond=0,
        )
        logger.info("Waiting for drop time: %s", drop.strftime("%H:%M"))
        last_log = datetime.now()
        while datetime.now() < drop:
            now = datetime.now()
            if (now - last_log).total_seconds() >= 10:
                remaining = int((drop - now).total_seconds())
                logger.info("%ds until drop time...", remaining)
                last_log = now
            time.sleep(0.05)
        logger.info("Drop time reached — booking now!")

    def _book_with_retries(self) -> str:
        req = self.config.reservation_request
        day = req.target_date.isoformat()

        for attempt in range(1, self.config.n_retries + 1):
            try:
                return self._attempt_booking(day)
            except NoSlotsError as exc:
                logger.info(
                    "Attempt %d/%d — %s", attempt, self.config.n_retries, exc
                )
                if attempt < self.config.n_retries:
                    time.sleep(self.config.seconds_between_retries)

        raise ExhaustedRetriesError(
            f"No suitable slot found after {self.config.n_retries} attempts"
        )

    def _attempt_booking(self, day: str) -> str:
        req = self.config.reservation_request

        slots = self.client.find_slots(req.venue_id, req.party_size, day)
        if not slots:
            raise NoSlotsError("API returned no slots for this venue/date")

        slot = select_slot(slots, req)
        logger.info(
            "Selected slot: %s (%s)",
            slot.date.start.strftime("%Y-%m-%d %H:%M"),
            slot.config.type,
        )

        book_token = self.client.get_booking_token(slot.config.token, req.party_size, day)
        return self.client.book(book_token, self.config.resy_config.payment_method_id)
