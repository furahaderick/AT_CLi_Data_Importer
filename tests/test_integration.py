# pylint: disable=redefined-outer-name

import json

import pytest

from cli_data_importer.exceptions import (
    DuplicateUserError,
    FileFormatError,
    ImporterError,
)
from cli_data_importer.importer import import_users
from cli_data_importer.repository import JsonUserRepository


@pytest.fixture
def import_files(tmp_path):
    """Prepare temporary CSV and JSON paths."""
    return {
        "directory": tmp_path,
        "csv": tmp_path / "users.csv",
        "database": tmp_path / "users.json",
    }


def test_import_valid_csv_into_json(import_files):
    import_files["csv"].write_text(
        "id,name,email\n"
        + "1,Jane Doe,jane@example.com\n"
        + "2,John Smith,john@example.com\n",
        encoding="utf-8",
    )

    repository = JsonUserRepository(import_files["database"])

    imported_count = import_users(import_files["csv"], repository)

    assert imported_count == 2

    saved_records = json.loads(import_files["database"].read_text(encoding="utf-8"))
    assert saved_records == [
        {
            "id": "1",
            "name": "Jane Doe",
            "email": "jane@example.com",
        },
        {
            "id": "2",
            "name": "John Smith",
            "email": "john@example.com",
        },
    ]


def test_second_import_preserves_existing_users(import_files):
    repository = JsonUserRepository(import_files["database"])

    import_files["csv"].write_text(
        "id,name,email\n" + "1,Jane Doe,jane@example.com\n",
        encoding="utf-8",
    )
    assert import_users(import_files["csv"], repository) == 1

    import_files["csv"].write_text(
        "id,name,email\n" + "2,John Smith,john@example.com\n",
        encoding="utf-8",
    )
    assert import_users(import_files["csv"], repository) == 1

    saved_records = json.loads(import_files["database"].read_text(encoding="utf-8"))

    assert [record["id"] for record in saved_records] == ["1", "2"]
    assert saved_records[0]["name"] == "Jane Doe"
    assert saved_records[1]["name"] == "John Smith"


def test_duplicate_id_fails_without_changing_database(import_files):
    repository = JsonUserRepository(import_files["database"])

    import_files["csv"].write_text(
        "id,name,email\n" + "1,Jane Doe,jane@example.com\n",
        encoding="utf-8",
    )
    import_users(import_files["csv"], repository)

    original_database = import_files["database"].read_bytes()

    import_files["csv"].write_text(
        "id,name,email\n" + "1,Another Jane,another@example.com\n",
        encoding="utf-8",
    )

    with pytest.raises(DuplicateUserError):
        import_users(import_files["csv"], repository)

    assert import_files["database"].read_bytes() == original_database


def test_malformed_csv_fails_without_changing_database(import_files):
    repository = JsonUserRepository(import_files["database"])

    import_files["csv"].write_text(
        "id,name,email\n" + "1,Jane Doe,jane@example.com\n",
        encoding="utf-8",
    )
    import_users(import_files["csv"], repository)

    original_database = import_files["database"].read_bytes()

    import_files["csv"].write_text(
        "id,name,email\n" + "2,John Smith\n",
        encoding="utf-8",
    )

    with pytest.raises(FileFormatError, match="Malformed CSV row"):
        import_users(import_files["csv"], repository)

    assert import_files["database"].read_bytes() == original_database


def test_missing_input_file_fails_without_changing_database(import_files):
    repository = JsonUserRepository(import_files["database"])

    import_files["csv"].write_text(
        "id,name,email\n" + "1,Jane Doe,jane@example.com\n",
        encoding="utf-8",
    )
    import_users(import_files["csv"], repository)

    original_database = import_files["database"].read_bytes()
    missing_csv = import_files["directory"] / "missing.csv"

    with pytest.raises(ImporterError, match="Could not read input CSV file"):
        import_users(missing_csv, repository)

    assert import_files["database"].read_bytes() == original_database
