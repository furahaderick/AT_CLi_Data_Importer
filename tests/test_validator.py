import pytest

from cli_data_importer.exceptions import DuplicateUserError, ImporterError
from cli_data_importer.models import User
from cli_data_importer.validator import validate_users


def valid_record(**overrides):
    record = {
        "id": "1",
        "name": "Jane Doe",
        "email": "jane@example.com",
    }
    record.update(overrides)
    return record


@pytest.mark.parametrize(
    "record",
    [
        valid_record(),
        valid_record(id="42"),
        valid_record(name="Mary Jane"),
    ],
)
def test_valid_records(record):
    users = validate_users([record])

    assert len(users) == 1
    assert isinstance(users[0], User)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", ""),
        ("id", "   "),
        ("name", ""),
        ("name", "   "),
        ("email", ""),
        ("email", "   "),
        ("email", "not-an-email"),
        ("email", "user@localhost"),
        ("name", None),
        ("email", 123),
        ("id", 123),
    ],
)
def test_invalid_field_values_are_rejected(field, value):
    record = valid_record(**{field: value})

    with pytest.raises(ImporterError):
        validate_users([record])


@pytest.mark.parametrize(
    "records",
    [
        [
            valid_record(id="1"),
            valid_record(id="1", email="other@example.com"),
        ],
        [
            valid_record(id="42"),
            valid_record(id="42", name="Another Person"),
        ],
    ],
)
def test_duplicate_ids_in_batch_are_rejected(records):
    with pytest.raises(DuplicateUserError, match="duplicate user ID"):
        validate_users(records)


def test_unique_ids_are_accepted():
    records = [
        valid_record(id="1"),
        valid_record(id="2", email="john@example.com"),
    ]

    users = validate_users(records)

    assert [user.id for user in users] == ["1", "2"]


def test_missing_fields_are_rejected():
    record = {"id": "1", "name": "Jane Doe"}

    with pytest.raises(ImporterError, match="missing field"):
        validate_users([record])


def test_empty_batch_returns_empty_list():
    assert not validate_users([])
