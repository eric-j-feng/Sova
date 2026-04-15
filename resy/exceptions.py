class NoSlotsError(Exception):
    """Raised when no acceptable reservation slots are found."""


class AuthError(Exception):
    """Raised when authentication with Resy fails."""


class BookingError(Exception):
    """Raised when the final booking request fails."""


class ExhaustedRetriesError(Exception):
    """Raised when all retry attempts have been exhausted."""
