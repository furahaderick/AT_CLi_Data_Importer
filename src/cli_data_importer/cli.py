"""Command-line interface for the user CSV importer."""

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from cli_data_importer.exceptions import ImporterError
from cli_data_importer.importer import import_users
from cli_data_importer.repository import JsonUserRepository

DEFAULT_OUTPUT = Path("data/users.json")

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Import users from a CSV file into a JSON database.",
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=(f"Path to the destination JSON database (default: {DEFAULT_OUTPUT})."),
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return an appropriate process exit code."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    parser = create_parser()
    args = parser.parse_args(argv)

    repository = JsonUserRepository(args.output)

    try:
        imported_count = import_users(args.input, repository)
    except ImporterError as exc:
        print(f"Import failed: {exc}")
        logger.debug("Import failure details", exc_info=True)
        return 1

    print(f"Successfully imported {imported_count} user(s).")
    print(f"Database: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
