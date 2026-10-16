# CLI Data Importer

A command-line tool for importing user records from CSV files into a JSON database with validation and duplicate detection.

## What It Does

The CLI Data Importer reads user data from a CSV file, validates each record, and stores valid users in a JSON database. It enforces data integrity by rejecting malformed records and preventing duplicate user IDs.

## Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)

## Poetry Setup

Install Poetry if not already installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

## Installation

Clone the repository and install dependencies:

```bash
poetry install
```

## CSV Format

### Required Headers

The CSV file must contain exactly these three headers:

- `id` - Unique user identifier (required, non-empty string)
- `name` - User's full name (required, non-empty string)
- `email` - User's email address (required, non-empty string, valid email format)

### Validation Rules

- All three fields must be present in every record
- All fields must be strings and cannot be blank
- Email must match standard email format (e.g., user@example.com)
- CSV must not contain duplicate headers
- Each row must have the same number of fields as headers

## Running an Import

Activate the virtual environment and run the CLI:

```bash
poetry run python -m cli_data_importer.cli --input path/to/users.csv
```

Specify a custom output file:

```bash
poetry run python -m cli_data_importer.cli --input path/to/users.csv --output path/to/database.json
```

The default output location is `data/users.json`.

## Data Storage

User records are stored as a JSON array in the specified output file. Each record contains:

```json
{
	"id": "user_id",
	"name": "User Name",
	"email": "user@example.com"
}
```

## Error Handling

### Duplicates

The import is rejected if:

- Duplicate user IDs exist within the incoming CSV batch
- Any incoming user ID already exists in the database

### Malformed Records

The entire import is rejected if any record is malformed:

- Missing required fields
- Fields are not strings
- Fields are blank/empty
- Invalid email format
- CSV structure is invalid (e.g., wrong column count, duplicate headers)

The tool reports the specific record number and validation error.

## Testing

Run all tests:

```bash
poetry run pytest
```

Generate coverage report:

```bash
poetry run coverage run -m pytest
poetry run coverage report
```

For an HTML coverage report:

```bash
poetry run coverage html
```

## Code Quality

Run all code quality checks using pre-commit:

```bash
poetry run pre-commit run --all-files
```

This runs:

- Ruff linter with auto-fix
- Ruff formatter (Black-compatible)
- mypy type checker
- Basic file checks (trailing whitespace, YAML validation, etc.)

Install pre-commit hooks to run automatically on each commit:

```bash
poetry run pre-commit install
```
