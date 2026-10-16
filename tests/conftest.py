import pytest


@pytest.fixture
def csv_file(tmp_path):
    """Create a temporary CSV file for each test & Clean it up after"""

    def _create_csv(content: str):
        path = tmp_path / "users.csv"
        path.write_text(content, encoding="utf-8")
        return path

    return _create_csv
