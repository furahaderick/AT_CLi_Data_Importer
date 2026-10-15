import pytest

from cli_data_importer.models import User
from cli_data_importer.parser import parse_csv


def test_valid_csv_with_one_record(csv_file):
    path = csv_file("id,name,email\n" + "1,Alice,alice@example.com\n")

    users = parse_csv(path)

    assert users == [User(id="1", name="Alice", email="alice@example.com")]


def test_valid_csv_with_multiple_records(csv_file):
    path = csv_file(
        "id,name,email\n" + "1,Alice,alice@example.com\n" + "2,Bob,bob@example.com\n"
    )

    users = parse_csv(path)

    assert len(users) == 2
    assert users[0].name == "Alice"
    assert users[1].name == "Bob"


def test_header_only_returns_empty_list(csv_file):
    path = csv_file("id,name,email\n")

    assert not parse_csv(path)


@pytest.mark.parametrize(
    "header",
    [
        "name,email",
        "id,email",
        "id,name",
        "username,name,email",
    ],
)
def test_missing_required_headers(csv_file, header):
    path = csv_file(header + "\n")

    with pytest.raises(ValueError, match="missing required headers"):
        parse_csv(path)


@pytest.mark.parametrize(
    "content, expected_message",
    [
        (
            "id,name,email\n" + "1,Alice\n",
            "missing values",
        ),
        (
            "id,name,email\n" + "1,Alice,alice@example.com,unexpected\n",
            "extra fields",
        ),
    ],
)
def test_malformed_rows(csv_file, content, expected_message):
    path = csv_file(content)

    with pytest.raises(ValueError, match=expected_message):
        parse_csv(path)


def test_empty_input_file(csv_file):
    path = csv_file("")

    with pytest.raises(ValueError, match="empty or missing a header"):
        parse_csv(path)


def test_missing_input_file(tmp_path):
    path = tmp_path / "does_not_exist.csv"

    with pytest.raises(FileNotFoundError):
        parse_csv(path)


def test_quoted_field_containing_comma(csv_file):
    path = csv_file("id,name,email\n" + '1,"Smith, Alice",alice@example.com\n')

    users = parse_csv(path)

    assert len(users) == 1
    assert users[0].name == "Smith, Alice"


def test_duplicate_headers_rejected(csv_file):
    path = csv_file(
        "id,name,email,email\n" + "1,Alice,alice@example.com,other@example.com\n"
    )

    with pytest.raises(ValueError, match="duplicate headers"):
        parse_csv(path)
