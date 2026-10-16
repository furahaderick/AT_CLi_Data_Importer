import json
import os
import tempfile
from pathlib import Path
from collections.abc import Iterable

from cli_data_importer.exceptions import DuplicateUserError, ImporterError
from cli_data_importer.models import User


class JsonUserRepository:
    """Persist User records in a JSON file."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    def load_all(self) -> list[User]:
        """Load all users, returning an empty list if the file is absent."""
        if not self.file_path.exists():
            return []

        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            raise ImporterError(
                f"Database contains invalid JSON: {self.file_path}"
            ) from exc
        except OSError as exc:
            raise ImporterError(
                f"Could not read database '{self.file_path}': {exc}"
            ) from exc

        if not isinstance(data, list):
            raise ImporterError(
                "Invalid database format: expected a JSON list of users."
            )

        users: list[User] = []
        seen_ids: set[str] = set()
        required_fields = {"id", "name", "email"}

        for index, record in enumerate(data):
            if not isinstance(record, dict):
                raise ImporterError(
                    f"Invalid database record at index {index}: "
                    "expected a JSON object."
                )

            if not required_fields.issubset(record):
                missing = required_fields - record.keys()
                raise ImporterError(
                    f"Invalid database record at index {index}: "
                    f"missing fields {', '.join(sorted(missing))}."
                )

            try:
                user = User(
                    id=record["id"],
                    name=record["name"],
                    email=record["email"],
                )
            except (TypeError, ValueError) as exc:
                raise ImporterError(
                    f"Invalid user in database at index {index}: {exc}"
                ) from exc

            if user.id in seen_ids:
                raise DuplicateUserError(
                    f"Database contains duplicate user ID '{user.id}'."
                )

            seen_ids.add(user.id)
            users.append(user)

        return users

    def save_all(self, users: Iterable[User]) -> None:
        """Atomically replace the database with the supplied users."""
        records = []
        seen_ids: set[str] = set()

        for user in users:
            if not isinstance(user, User):
                raise ImporterError("Cannot save a record that is not a User instance.")

            if user.id in seen_ids:
                raise DuplicateUserError(f"Cannot save duplicate user ID '{user.id}'.")

            seen_ids.add(user.id)

            records.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                }
            )

        temp_path = None

        try:
            # Create the destination directory if it doesn't exist.
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            # Keep the temporary file in the destination directory.
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=self.file_path.parent,
                prefix=f".{self.file_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)
                json.dump(records, temp_file, indent=2, ensure_ascii=False)
                temp_file.write("\n")

            # Replace the database only after writing succeeds.
            os.replace(temp_path, self.file_path)
            temp_path = None

        except (OSError, TypeError, ValueError) as exc:
            raise ImporterError(
                f"Could not save database '{self.file_path}': {exc}"
            ) from exc

        finally:
            # Clean up a temporary file if writing or replacement failed.
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
