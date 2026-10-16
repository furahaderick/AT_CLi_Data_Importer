import pytest

from cli_data_importer.exceptions import FileFormatError, ImporterError
from cli_data_importer.parser import parse_users_from_csv_file


def test_parse_one_user(csv_file):
    path = csv_file("id,name,email\n" + "1,Jane Doe,jane@example.com\n")

    records = parse_users_from_csv_file(path)

    assert records == [
        {
            "id": "1",
            "name": "Jane Doe",
            "email": "jane@example.com",
        }
    ]


def test_parse_multiple_users(csv_file):
    path = csv_file(
        "id,name,email\n"
        + "1,Jane Doe,jane@example.com\n"
        + "2,John Smith,john@example.com\n"
    )

    records = parse_users_from_csv_file(path)

    assert len(records) == 2
    assert records[0]["id"] == "1"
    assert records[1]["name"] == "John Smith"


def test_header_only_returns_empty_list(csv_file):
    path = csv_file("id,name,email\n")

    assert not parse_users_from_csv_file(path)


@pytest.mark.parametrize(
    "headers,missing",
    [
        ("name,email", "id"),
        ("id,email", "name"),
        ("id,name", "email"),
        ("id", "email, name"),
    ],
)
def test_missing_required_headers(csv_file, headers, missing):
    path = csv_file(f"{headers}\n")

    with pytest.raises(
        FileFormatError,
        match="missing required header",
    ):
        parse_users_from_csv_file(path)


@pytest.mark.parametrize(
    "row",
    [
        "1,Jane",  # Missing field
        "1,Jane,jane@example.com,extra",  # Extra field
    ],
)
def test_malformed_row_structure(csv_file, row):
    path = csv_file("id,name,email\n" + f"{row}\n")

    with pytest.raises(
        FileFormatError,
        match="Malformed CSV row",
    ):
        parse_users_from_csv_file(path)


def test_empty_file(csv_file):
    path = csv_file("")

    with pytest.raises(
        FileFormatError,
        match="CSV file is empty",
    ):
        parse_users_from_csv_file(path)


def test_missing_file(tmp_path):
    path = tmp_path / "missing.csv"

    with pytest.raises(ImporterError, match="Could not read input CSV file"):
        parse_users_from_csv_file(path)


def test_quoted_comma_in_name(csv_file):
    path = csv_file("id,name,email\n" + '1,"Doe, Jane",jane@example.com\n')

    records = parse_users_from_csv_file(path)

    assert len(records) == 1
    assert records[0]["name"] == "Doe, Jane"


def test_reordered_headers(csv_file):
    path = csv_file("email,id,name\n" + "jane@example.com,1,Jane Doe\n")

    records = parse_users_from_csv_file(path)

    assert records == [
        {
            "email": "jane@example.com",
            "id": "1",
            "name": "Jane Doe",
        }
    ]


def test_duplicate_headers_are_rejected(csv_file):
    path = csv_file("id,name,email,id\n" + "1,Jane,jane@example.com,2\n")

    with pytest.raises(
        FileFormatError,
        match="duplicate headers",
    ):
        parse_users_from_csv_file(path)
