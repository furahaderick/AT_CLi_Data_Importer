from collections.abc import Iterable, Mapping

from cli_data_importer.exceptions import DuplicateUserError, ImporterError
from cli_data_importer.models import EMAIL_REGEX, User

REQUIRED_FIELDS = ("id", "name", "email")


def validate_users(
    records: Iterable[Mapping[str, object]],
) -> list[User]:
    """Validate user records and return User objects.

    Raises:
        ImporterError: If a field is missing, has an invalid type,
            is blank, or contains an invalid email.
        DuplicateUserError: If IDs are repeated within the batch.
    """
    users: list[User] = []
    seen_ids: set[str] = set()

    for row_number, record in enumerate(records, start=1):
        missing = [field for field in REQUIRED_FIELDS if field not in record]
        if missing:
            raise ImporterError(
                f"Record {row_number}: missing field(s): {', '.join(missing)}."
            )

        values: dict[str, str] = {}

        for field in REQUIRED_FIELDS:
            value = record[field]

            if not isinstance(value, str):
                raise ImporterError(f"Record {row_number}: '{field}' must be a string.")

            if not value.strip():
                raise ImporterError(
                    f"Record {row_number}: '{field}' must not be blank."
                )

            values[field] = value

        email = values["email"]
        if not EMAIL_REGEX.fullmatch(email):
            raise ImporterError(
                f"Record {row_number}: invalid email format: '{email}'."
            )

        user_id = values["id"]
        if user_id in seen_ids:
            raise DuplicateUserError(
                f"Record {row_number}: duplicate user ID '{user_id}'."
            )

        seen_ids.add(user_id)

        users.append(
            User(
                id=user_id,
                name=values["name"],
                email=email,
            )
        )

    return users
