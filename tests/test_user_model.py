import pytest

from cli_data_importer.models import User


def test_valid_user():
    """Ensure a user is created successfully with valid inputs."""
    user = User(id="usr_123", name="Alice Smith", email="alice@example.com")

    assert user.id == "usr_123"
    assert user.name == "Alice Smith"
    assert user.email == "alice@example.com"


@pytest.mark.parametrize(
    "invalid_id, expected_msg",
    [
        ("", "User ID must be present and non-empty."),
        ("   ", "User ID must be present and non-empty."),
    ],
)
def test_invalid_id_raises_value_error(invalid_id, expected_msg):
    """Ensure empty or whitespace-only IDs raise a ValueError."""
    with pytest.raises(ValueError, match=expected_msg):
        User(id=invalid_id, name="Alice", email="alice@example.com")


@pytest.mark.parametrize(
    "invalid_name, expected_msg",
    [
        ("", "Name must be present and non-empty."),
        ("   ", "Name must be present and non-empty."),
    ],
)
def test_invalid_name_raises_value_error(invalid_name, expected_msg):
    """Ensure empty or whitespace-only names raise a ValueError."""
    with pytest.raises(ValueError, match=expected_msg):
        User(id="usr_123", name=invalid_name, email="alice@example.com")


@pytest.mark.parametrize(
    "invalid_email, expected_msg",
    [
        ("", "Email must be present and non-empty."),
        ("   ", "Email must be present and non-empty."),
        ("alice", "Invalid email format"),
        ("alice@", "Invalid email format"),
        ("@example.com", "Invalid email format"),
        ("alice@example", "Invalid email format"),
        ("://example.com", "Invalid email format"),
    ],
)
def test_invalid_email_raises_value_error(invalid_email, expected_msg):
    """Ensure empty, malformed, or missing emails raise a ValueError."""
    with pytest.raises(ValueError, match=expected_msg):
        User(id="usr_123", name="Alice", email=invalid_email)


def test_slots_are_enforced():
    """Ensure slots=True prevents arbitrary attributes from being added."""
    user = User(id="usr_123", name="Alice", email="alice@example.com")

    with pytest.raises(AttributeError):
        setattr(user, "age", 30)
