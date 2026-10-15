import csv
from pathlib import Path

from cli_data_importer.models import User


REQUIRED_HEADERS = {"id", "name", "email"}


def parse_csv(file_path: str | Path) -> list[User]:
    """Parse a CSV file into User records.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the CSV headers or row structure are invalid.
        csv.Error: If the CSV reader encounters a parsing error.
        ValueError: Also propagates field validation errors from User.
    """
    with open(file_path, mode="r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        headers = reader.fieldnames
        if headers is None:
            raise ValueError("CSV file is empty or missing a header row.")

        if len(headers) != len(set(headers)):
            raise ValueError("CSV contains duplicate headers.")

        missing_headers = REQUIRED_HEADERS - set(headers)
        if missing_headers:
            missing = ", ".join(sorted(missing_headers))
            raise ValueError(f"CSV is missing required headers: {missing}")

        users = []

        for row_number, row in enumerate(reader, start=2):
            # DictReader stores extra fields under the None key.
            if None in row:
                raise ValueError(f"Row {row_number} contains extra fields.")

            # A missing value is represented by None.
            missing_fields = [header for header in headers if row[header] is None]
            if missing_fields:
                raise ValueError(
                    f"Row {row_number} is missing values for: "
                    f"{', '.join(missing_fields)}."
                )

            users.append(
                User(
                    id=row["id"],
                    name=row["name"],
                    email=row["email"],
                )
            )

        return users
