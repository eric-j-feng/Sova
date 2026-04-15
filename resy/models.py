from datetime import date, datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, root_validator, validator


class ResyConfig(BaseModel):
    email: str
    password: str
    # api_key: find yours by inspecting https://resy.com in Chrome DevTools → Network tab
    api_key: str

    # Populated automatically after authenticate() is called
    token: Optional[str] = None
    payment_method_id: Optional[int] = None

    def get_authorization(self) -> str:
        return f'ResyAPI api_key="{self.api_key}"'


class ReservationRequest(BaseModel):
    venue_id: int
    party_size: int
    # Target time: hour (0–23) and minute
    ideal_hour: int
    ideal_minute: int
    # Accept slots within this many hours of the ideal time
    window_hours: float = 1.0
    # When two slots are equidistant, prefer the earlier one
    prefer_early: bool = True
    # Optionally restrict to a seating type, e.g. "Dining Room" or "Bar"
    preferred_type: Optional[str] = None
    # Provide exactly one of ideal_date or days_in_advance
    ideal_date: Optional[date] = None
    days_in_advance: Optional[int] = None

    @root_validator
    def validate_target_date(cls, values):
        has_date = values.get("ideal_date") is not None
        has_advance = values.get("days_in_advance") is not None
        if has_date and has_advance:
            raise ValueError("Provide only one of 'ideal_date' or 'days_in_advance', not both")
        if not has_date and not has_advance:
            raise ValueError("Must provide either 'ideal_date' or 'days_in_advance'")
        return values

    @property
    def target_date(self) -> date:
        if self.ideal_date:
            return self.ideal_date
        return date.today() + timedelta(days=self.days_in_advance)


class BotConfig(BaseModel):
    resy_config: ResyConfig
    reservation_request: ReservationRequest
    # If set, the bot waits until this local time before attempting to book.
    # Useful for snagging reservations the moment they drop.
    drop_hour: Optional[int] = None
    drop_minute: Optional[int] = None
    n_retries: int = 30
    seconds_between_retries: float = 0.5


# ---------------------------------------------------------------------------
# Resy API response models
# ---------------------------------------------------------------------------

class PaymentMethod(BaseModel):
    id: int


class AuthResponseBody(BaseModel):
    payment_methods: List[PaymentMethod]
    token: str


class SlotConfig(BaseModel):
    id: str
    type: str
    token: str


class SlotDate(BaseModel):
    start: datetime
    end: datetime


class Slot(BaseModel):
    config: SlotConfig
    date: SlotDate


class Venue(BaseModel):
    slots: List[Slot]


class Results(BaseModel):
    venues: List[Venue]


class FindResponseBody(BaseModel):
    results: Results


class BookToken(BaseModel):
    date_expires: datetime
    value: str


class DetailsResponseBody(BaseModel):
    book_token: BookToken


class BookResponseBody(BaseModel):
    resy_token: str
