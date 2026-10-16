import pytest

from cli_data_importer.cli import DEFAULT_OUTPUT, create_parser, main
from cli_data_importer.exceptions import FileFormatError, ImporterError


def test_valid_command_line_arguments_are_accepted(tmp_path):
    input_path = tmp_path / "users.csv"
    output_path = tmp_path / "users.json"

    args = create_parser().parse_args(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert args.input == input_path
    assert args.output == output_path


def test_input_argument_is_required():
    with pytest.raises(SystemExit) as exc_info:
        create_parser().parse_args([])

    assert exc_info.value.code == 2


def test_output_defaults_to_documented_path():
    args = create_parser().parse_args(["--input", "users.csv"])

    assert args.output == DEFAULT_OUTPUT
    assert str(args.output) == "data/users.json"


def test_successful_import_prints_summary(tmp_path, mocker, capsys):
    input_path = tmp_path / "users.csv"
    output_path = tmp_path / "users.json"

    repository_mock = mocker.patch("cli_data_importer.cli.JsonUserRepository")
    import_mock = mocker.patch(
        "cli_data_importer.cli.import_users",
        return_value=3,
    )

    exit_code = main(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Successfully imported 3 user(s)." in captured.out
    assert f"Database: {output_path}" in captured.out

    repository_mock.assert_called_once_with(output_path)
    import_mock.assert_called_once_with(
        input_path,
        repository_mock.return_value,
    )


def test_successful_import_uses_default_output(tmp_path, mocker, capsys):
    input_path = tmp_path / "users.csv"

    repository_mock = mocker.patch("cli_data_importer.cli.JsonUserRepository")
    import_mock = mocker.patch(
        "cli_data_importer.cli.import_users",
        return_value=1,
    )

    exit_code = main(["--input", str(input_path)])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Successfully imported 1 user(s)." in captured.out
    repository_mock.assert_called_once_with(DEFAULT_OUTPUT)
    import_mock.assert_called_once_with(
        input_path,
        repository_mock.return_value,
    )


def test_invalid_csv_prints_useful_error(tmp_path, mocker, capsys):
    input_path = tmp_path / "invalid.csv"

    mocker.patch("cli_data_importer.cli.JsonUserRepository")
    mocker.patch(
        "cli_data_importer.cli.import_users",
        side_effect=FileFormatError("CSV is missing required header(s): email."),
    )

    exit_code = main(["--input", str(input_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Import failed:" in captured.out
    assert "missing required header" in captured.out
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err


def test_missing_input_file_prints_useful_error(tmp_path, mocker, capsys):
    input_path = tmp_path / "missing.csv"

    mocker.patch("cli_data_importer.cli.JsonUserRepository")
    mocker.patch(
        "cli_data_importer.cli.import_users",
        side_effect=ImporterError(
            f"Could not read input CSV file '{input_path}': file not found"
        ),
    )

    exit_code = main(["--input", str(input_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Import failed:" in captured.out
    assert str(input_path) in captured.out
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    "error",
    [
        ImporterError("Database read failed"),
        ImporterError("Database write failed"),
    ],
)
def test_import_failure_returns_nonzero_exit_code(tmp_path, mocker, capsys, error):
    input_path = tmp_path / "users.csv"

    mocker.patch("cli_data_importer.cli.JsonUserRepository")
    mocker.patch(
        "cli_data_importer.cli.import_users",
        side_effect=error,
    )

    exit_code = main(["--input", str(input_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Import failed:" in captured.out
    assert str(error) in captured.out


def test_import_failure_does_not_print_success(tmp_path, mocker, capsys):
    input_path = tmp_path / "users.csv"

    mocker.patch("cli_data_importer.cli.JsonUserRepository")
    mocker.patch(
        "cli_data_importer.cli.import_users",
        side_effect=ImporterError("Import failed"),
    )

    exit_code = main(["--input", str(input_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Successfully imported" not in captured.out
