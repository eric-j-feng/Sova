#!/usr/bin/env python3
"""
Sova — Resy reservation bot

Usage:
    python main.py config.json

The bot will:
  1. Authenticate with your Resy credentials
  2. Optionally wait until a reservation drop time
  3. Poll for an available slot matching your preferences
  4. Book it automatically

See config.example.json for the full configuration schema.
"""
import argparse
import json
import logging
import sys
from pathlib import Path

from resy.bot import ResyBot
from resy.exceptions import AuthError, BookingError, ExhaustedRetriesError
from resy.models import BotConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sova",
        description="Resy reservation bot — snipe hard-to-get restaurant reservations",
    )
    parser.add_argument("config", help="Path to bot config JSON file (see config.example.json)")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        logger.error("Config file not found: %s", config_path)
        sys.exit(1)

    with open(config_path) as f:
        raw = json.load(f)

    try:
        config = BotConfig(**raw)
    except Exception as exc:
        logger.error("Invalid config: %s", exc)
        sys.exit(1)

    bot = ResyBot(config)

    try:
        resy_token = bot.run()
        print(f"\nReservation confirmed! Resy token: {resy_token}")
    except AuthError as exc:
        logger.error("Auth error: %s", exc)
        sys.exit(1)
    except ExhaustedRetriesError as exc:
        logger.error("%s", exc)
        sys.exit(1)
    except BookingError as exc:
        logger.error("Booking error: %s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
