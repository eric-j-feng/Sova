from datetime import datetime, timedelta
from typing import List, Optional

from resy.exceptions import NoSlotsError
from resy.models import ReservationRequest, Slot


def select_slot(slots: List[Slot], request: ReservationRequest) -> Slot:
    """
    Pick the best slot from a sorted list based on the reservation request.

    Strategy:
    - Only consider slots within `window_hours` of the ideal time.
    - If `preferred_type` is set, only consider slots of that type.
    - Among qualifying slots, prefer the one closest to the ideal time.
    - Break ties using `prefer_early`.
    """
    window = timedelta(hours=request.window_hours)
    ideal = datetime(
        request.target_date.year,
        request.target_date.month,
        request.target_date.day,
        request.ideal_hour,
        request.ideal_minute,
    )
    min_time = ideal - window
    max_time = ideal + window

    best_slot: Optional[Slot] = None
    best_diff: Optional[timedelta] = None

    for slot in slots:
        start = slot.date.start
        if start < min_time or start > max_time:
            continue
        if request.preferred_type and slot.config.type != request.preferred_type:
            continue

        diff = abs(start - ideal)
        if best_diff is None:
            best_slot, best_diff = slot, diff
        elif diff < best_diff:
            best_slot, best_diff = slot, diff
        elif diff == best_diff:
            # Tie-break: prefer the earlier slot if prefer_early, else later
            if request.prefer_early and start < best_slot.date.start:
                best_slot = slot
            elif not request.prefer_early and start > best_slot.date.start:
                best_slot = slot

    if best_slot is None:
        raise NoSlotsError(
            f"No slots found within {request.window_hours}h of "
            f"{request.ideal_hour:02d}:{request.ideal_minute:02d}"
            + (f" (type: {request.preferred_type})" if request.preferred_type else "")
        )

    return best_slot
