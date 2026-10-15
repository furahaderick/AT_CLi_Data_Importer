import csv
from pathlib import Path

from cli_data_importer.exceptions import FileFormatError
from cli_data_importer.models import User


REQUIRED_HEADERS = {"id", "name", "email"}


def parse_users_from_csv_file(file_path: str | Path) -> list[User]:
    """Parse a CSV file and return its records as User objects.

    Raises:
        FileNotFoundError: If the input file does not exist.
        PermissionError: If the file cannot be accessed due to permissions.
        FileFormatError: If the CSV structure is invalid.
        ValueError: If a field value fails User validation.
    """
    users: list[User] = []

    try:
        with open(file_path, mode="r", newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.reader(csv_file, strict=True)

            try:
                headers = next(reader)
            except StopIteration:
                raise FileFormatError(
                    "CSV file is empty; expected headers: id, name, email."
                )

            if len(headers) != len(set(headers)):
                raise FileFormatError("CSV contains duplicate headers.")

            missing_headers = REQUIRED_HEADERS - set(headers)
            if missing_headers:
                missing = ", ".join(sorted(missing_headers))
                raise FileFormatError(f"CSV is missing required header(s): {missing}.")

            for row in reader:
                row_number = reader.line_num

                if len(row) != len(headers):
                    raise FileFormatError(
                        f"Malformed CSV row ending at line {row_number}: "
                        f"expected {len(headers)} fields, got {len(row)}."
                    )

                record = dict(zip(headers, row))

                try:
                    user = User(
                        id=record["id"],
                        name=record["name"],
                        email=record["email"],
                    )
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid user data on CSV row {row_number}: {exc}"
                    ) from exc

                users.append(user)

    except csv.Error as exc:
        raise FileFormatError(f"Invalid CSV format: {exc}") from exc

    return users
