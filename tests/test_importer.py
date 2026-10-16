# pylint: disable=redefined-outer-name

import pytest

from cli_data_importer.exceptions import DuplicateUserError, ImporterError
from cli_data_importer.importer import import_users
from cli_data_importer.models import User


@pytest.fixture
def csv_path(tmp_path):
    """Create a temporary CSV file path."""
    return tmp_path / "users.csv"


@pytest.fixture
def parser_records():
    """Return raw records as produced by the CSV parser."""
    return [
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


@pytest.fixture
def incoming_users():
    """Return validated User objects."""
    return [
        User("1", "Jane Doe", "jane@example.com"),
        User("2", "John Smith", "john@example.com"),
    ]


@pytest.fixture
def repository(mocker):
    """Provide a mocked repository."""
    repo = mocker.Mock()
    repo.load_all.return_value = []
    repo.save_all.return_value = None
    return repo


def test_import_valid_batch_into_empty_database(
    mocker,
    csv_path,
    repository,
    parser_records,
    incoming_users,
):
    parse_mock = mocker.patch(
        "cli_data_importer.importer.parse_users_from_csv_file",
        return_value=parser_records,
    )
    validate_mock = mocker.patch(
        "cli_data_importer.importer.validate_users",
        return_value=incoming_users,
    )

    result = import_users(csv_path, repository)

    assert result == 2
    parse_mock.assert_called_once_with(csv_path)
    validate_mock.assert_called_once_with(parser_records)
    repository.load_all.assert_called_once_with()
    repository.save_all.assert_called_once_with(incoming_users)


def test_import_new_users_alongside_existing_users(
    mocker,
    csv_path,
    repository,
    parser_records,
    incoming_users,
):
    existing_users = [User("existing-1", "Existing User", "existing@example.com")]
    repository.load_all.return_value = existing_users

    mocker.patch(
        "cli_data_importer.importer.parse_users_from_csv_file",
        return_value=parser_records,
    )
    mocker.patch(
        "cli_data_importer.validator.validate_users",
        return_value=incoming_users,
    )

    result = import_users(csv_path, repository)

    assert result == len(incoming_users)
    repository.save_all.assert_called_once_with(existing_users + incoming_users)


def test_duplicate_id_already_in_database_is_rejected(
    mocker,
    csv_path,
    repository,
    parser_records,
    incoming_users,
):
    repository.load_all.return_value = [
        User("1", "Existing Jane", "existing@example.com")
    ]

    mocker.patch(
        "cli_data_importer.importer.parse_users_from_csv_file",
        return_value=parser_records,
    )
    mocker.patch(
        "cli_data_importer.validator.validate_users",
        return_value=incoming_users,
    )

    with pytest.raises(
        DuplicateUserError,
        match="already exists",
    ):
        import_users(csv_path, repository)

    repository.save_all.assert_not_called()


def test_duplicate_ids_within_incoming_batch_are_rejected(
    mocker,
    csv_path,
    repository,
    parser_records,
):
    mocker.patch(
        "cli_data_importer.importer.parse_users_from_csv_file",
        return_value=parser_records,
    )
    mocker.patch(
        "cli_data_importer.importer.validate_users",
        side_effect=DuplicateUserError("Duplicate ID in batch"),
    )

    with pytest.raises(
        DuplicateUserError,
        match="Duplicate ID in batch",
    ):
        import_users(csv_path, repository)

    repository.load_all.assert_not_called()
    repository.save_all.assert_not_called()


def test_invalid_record_does_not_modify_existing_data(
    mocker,
    csv_path,
    repository,
    parser_records,
):
    existing_users = [User("existing-1", "Existing User", "existing@example.com")]
    repository.load_all.return_value = existing_users

    mocker.patch(
        "cli_data_importer.importer.parse_users_from_csv_file",
        return_value=parser_records,
    )
    mocker.patch(
        "cli_data_importer.importer.validate_users",
        side_effect=ImporterError("Invalid email"),
    )

    with pytest.raises(ImporterError, match="Invalid email"):
        import_users(csv_path, repository)

    repository.load_all.assert_not_called()
    repository.save_all.assert_not_called()


def test_parsing_failure_does_not_validate_or_access_repository(
    mocker,
    csv_path,
    repository,
):
    parse_mock = mocker.patch(
        "cli_data_importer.importer.parse_users_from_csv_file",
        side_effect=ImporterError("Invalid CSV"),
    )
    validate_mock = mocker.patch(
        "cli_data_importer.validator.validate_users",
    )

    with pytest.raises(ImporterError, match="Invalid CSV"):
        import_users(csv_path, repository)

    parse_mock.assert_called_once_with(csv_path)
    validate_mock.assert_not_called()
    repository.load_all.assert_not_called()
    repository.save_all.assert_not_called()


def test_validation_failure_does_not_save(
    mocker,
    csv_path,
    repository,
    parser_records,
):
    mocker.patch(
        "cli_data_importer.importer.parse_users_from_csv_file",
        return_value=parser_records,
    )
    mocker.patch(
        "cli_data_importer.importer.validate_users",
        side_effect=ImporterError("Invalid user data"),
    )

    with pytest.raises(ImporterError, match="Invalid user data"):
        import_users(csv_path, repository)

    repository.load_all.assert_not_called()
    repository.save_all.assert_not_called()


def test_repository_read_failure_prevents_saving(
    mocker,
    csv_path,
    repository,
    parser_records,
    incoming_users,
):
    mocker.patch(
        "cli_data_importer.importer.parse_users_from_csv_file",
        return_value=parser_records,
    )
    mocker.patch(
        "cli_data_importer.validator.validate_users",
        return_value=incoming_users,
    )
    repository.load_all.side_effect = ImporterError("Database read failed")

    with pytest.raises(
        ImporterError,
        match="Database read failed",
    ):
        import_users(csv_path, repository)

    repository.save_all.assert_not_called()


def test_repository_write_failure_is_propagated(
    mocker,
    csv_path,
    repository,
    parser_records,
    incoming_users,
):
    mocker.patch(
        "cli_data_importer.importer.parse_users_from_csv_file",
        return_value=parser_records,
    )
    mocker.patch(
        "cli_data_importer.validator.validate_users",
        return_value=incoming_users,
    )
    repository.save_all.side_effect = ImporterError("Database write failed")

    with pytest.raises(
        ImporterError,
        match="Database write failed",
    ):
        import_users(csv_path, repository)

    repository.save_all.assert_called_once_with(incoming_users)


def test_empty_batch_returns_zero(
    mocker,
    csv_path,
    repository,
):
    mocker.patch(
        "cli_data_importer.importer.parse_users_from_csv_file",
        return_value=[],
    )
    mocker.patch(
        "cli_data_importer.validator.validate_users",
        return_value=[],
    )

    result = import_users(csv_path, repository)

    assert result == 0
    repository.load_all.assert_called_once_with()
    repository.save_all.assert_called_once_with([])


def test_successful_import_returns_count_after_save(
    mocker,
    csv_path,
    repository,
    parser_records,
    incoming_users,
):
    mocker.patch(
        "cli_data_importer.importer.parse_users_from_csv_file",
        return_value=parser_records,
    )
    mocker.patch(
        "cli_data_importer.validator.validate_users",
        return_value=incoming_users,
    )

    result = import_users(csv_path, repository)

    assert result == len(incoming_users)
    repository.save_all.assert_called_once_with(incoming_users)
