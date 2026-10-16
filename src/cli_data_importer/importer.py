import logging
from pathlib import Path

from cli_data_importer.exceptions import (
    DuplicateUserError,
    FileFormatError,
    ImporterError,
)
from cli_data_importer.parser import parse_users_from_csv_file
from cli_data_importer.repository import JsonUserRepository
from cli_data_importer.validator import validate_users

logger = logging.getLogger(__name__)


def import_users(
    csv_path: str | Path,
    repository: JsonUserRepository,
) -> int:
    """Import validated users into the JSON repository.

    Returns:
        Number of successfully imported users.

    Raises:
        ImporterError: If parsing, validation, or storage fails.
        DuplicateUserError: If IDs conflict within the batch or database.
    """
    csv_path = Path(csv_path)

    logger.info("User import started")
    logger.debug("Input file: %s", csv_path)

    # Parse the csv file.
    try:
        records = parse_users_from_csv_file(csv_path)
    except FileFormatError:
        logger.warning("Import rejected: CSV file structure is invalid")
        raise
    except ImporterError:
        logger.error("Import failed: could not read the input file")
        raise

    logger.info("CSV parsing completed: %d records", len(records))

    # Validate incoming records
    try:
        incoming_users = validate_users(records)
    except DuplicateUserError:
        logger.warning("Import rejected: duplicate IDs in incoming batch")
        raise
    except ImporterError:
        logger.warning("Import rejected: incoming records failed validation")
        raise

    logger.info(
        "Validation completed: %d records validated",
        len(incoming_users),
    )

    # Load existing users
    try:
        existing_users = repository.load_all()
    except ImporterError:
        logger.error("Import failed: could not load the user database")
        raise

    logger.debug("Existing records loaded: %d", len(existing_users))

    # Reject duplicate IDs
    existing_ids = {user.id for user in existing_users}
    duplicate_count = sum(user.id in existing_ids for user in incoming_users)

    if duplicate_count:
        logger.warning(
            "Import rejected: %d incoming record(s) conflict with existing user IDs",
            duplicate_count,
        )
        raise DuplicateUserError(
            f"Import rejected: {duplicate_count} incoming record(s) "
            "already exists in the database."
        )

    # Save combined users
    updated_users = [*existing_users, *incoming_users]

    try:
        repository.save_all(updated_users)
    except ImporterError:
        logger.error("Import failed: could not save the user database")
        raise

    # Report success only after the save succeeds
    imported_count = len(incoming_users)
    logger.info("User import succeeded: %d records imported", imported_count)

    return imported_count
