# pylint: disable=redefined-outer-name

import json

import pytest

import cli_data_importer.repository as repository_module
from cli_data_importer.exceptions import DuplicateUserError, ImporterError
from cli_data_importer.models import User
from cli_data_importer.repository import JsonUserRepository


@pytest.fixture
def repository(tmp_path):
    return JsonUserRepository(tmp_path / "users.json")


@pytest.fixture
def sample_users():
    return [
        User("1", "Jane Doe", "jane@example.com"),
        User("2", "John Smith", "john@example.com"),
    ]


def test_load_valid_database(repository, sample_users):
    repository.file_path.write_text(
        json.dumps(
            [
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
        ),
        encoding="utf-8",
    )

    assert repository.load_all() == sample_users


def test_missing_database_returns_empty_list(repository):
    assert repository.load_all() == []


def test_save_and_read_back(repository, sample_users):
    repository.save_all(sample_users)

    assert repository.load_all() == sample_users


def test_saved_json_uses_expected_keys(repository, sample_users):
    repository.save_all(sample_users)

    data = json.loads(repository.file_path.read_text(encoding="utf-8"))

    assert data[0] == {
        "id": "1",
        "name": "Jane Doe",
        "email": "jane@example.com",
    }


def test_invalid_json_is_rejected(repository):
    repository.file_path.write_text(
        '{"id": "1", invalid}',
        encoding="utf-8",
    )

    with pytest.raises(ImporterError, match="invalid JSON"):
        repository.load_all()


def test_invalid_user_record_is_rejected(repository):
    repository.file_path.write_text(
        json.dumps(
            [
                {
                    "id": "1",
                    "name": "",
                    "email": "jane@example.com",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ImporterError, match="Invalid user"):
        repository.load_all()


def test_duplicate_ids_in_database_are_rejected(repository):
    repository.file_path.write_text(
        json.dumps(
            [
                {
                    "id": "1",
                    "name": "Jane Doe",
                    "email": "jane@example.com",
                },
                {
                    "id": "1",
                    "name": "Another Person",
                    "email": "other@example.com",
                },
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        DuplicateUserError,
        match="duplicate user ID",
    ):
        repository.load_all()


def test_duplicate_ids_cannot_be_saved(repository):
    users = [
        User("1", "Jane Doe", "jane@example.com"),
        User("1", "Another Person", "other@example.com"),
    ]

    with pytest.raises(
        DuplicateUserError,
        match="duplicate user ID",
    ):
        repository.save_all(users)

    assert not repository.file_path.exists()


def test_empty_collection_can_be_saved(repository):
    repository.save_all([])

    assert repository.load_all() == []


def test_unwritable_destination_raises_importer_error(tmp_path, sample_users, mocker):

    repo = JsonUserRepository(tmp_path / "users.json")

    replace_mock = mocker.patch.object(
        repository_module.os,
        "replace",
        side_effect=OSError("simulated write failure"),
    )

    with pytest.raises(
        ImporterError,
        match="Could not save database",
    ):
        repo.save_all(sample_users)

    replace_mock.assert_called_once()
    assert not repo.file_path.exists()

    # A failed replacement should clean up the temporary file.
    assert not list(tmp_path.glob(".users.json.*.tmp"))


def test_unreadable_database_raises_importer_error(tmp_path, mocker):
    repo = JsonUserRepository(tmp_path / "users.json")
    repo.file_path.write_text("[]", encoding="utf-8")

    mocker.patch.object(
        type(repo.file_path),
        "open",
        side_effect=PermissionError("simulated read failure"),
    )

    with pytest.raises(
        ImporterError,
        match="Could not read database",
    ):
        repo.load_all()


def test_non_list_json_is_rejected(repository):
    repository.file_path.write_text(
        json.dumps({"id": "1"}),
        encoding="utf-8",
    )

    with pytest.raises(
        ImporterError,
        match="expected a JSON list",
    ):
        repository.load_all()


def test_missing_required_key_is_rejected(repository):
    repository.file_path.write_text(
        json.dumps(
            [
                {
                    "id": "1",
                    "name": "Jane Doe",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ImporterError,
        match="missing fields email",
    ):
        repository.load_all()
