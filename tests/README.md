# Role Schema Validation Tests

This directory contains tests to validate that the YAML files in the `role` directory conform to the schema defined in `role_schema.json`.

## Test Files

- `test_role_schema_validation.py`: Validates that each YAML file conforms to the JSON schema.
- `test_role_content_validation.py`: Validates the content of each YAML file for consistency and completeness.
- `test_role_cross_references.py`: Validates cross-references between roles in the "interaction_with" section.
- `run_tests.py`: A script to run all the tests and generate a report.

## Running the Tests

You can run the tests using pytest directly:

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run a specific test file
pytest tests/test_role_schema_validation.py
```

Or you can use the provided `run_tests.py` script:

```bash
# Run all tests
./tests/run_tests.py

# Run tests with verbose output
./tests/run_tests.py -v

# Run tests and generate a coverage report
./tests/run_tests.py -r
```

## Test Coverage

The tests cover the following aspects of the role YAML files:

1. **Schema Validation**:
   - Validates that each YAML file conforms to the JSON schema.
   - Checks that all required fields are present.
   - Ensures no additional properties are present.

2. **Content Validation**:
   - Checks that the role name matches the filename.
   - Validates that the description is not empty and has a reasonable length.
   - Ensures that there is a reasonable number of responsibilities, expertise items, characteristics, interactions, and success criteria.
   - Checks that tools and technologies, agile mapping, scalability, and KPIs follow the expected format.

3. **Cross-Reference Validation**:
   - Validates that all roles referenced in the "interaction_with" section exist as actual role files.
   - Checks that role references are bidirectional (if A references B, B should reference A).
   - Ensures that interactions follow the expected format.
   - Validates that interaction verbs are consistent across roles.

## Adding New Tests

To add a new test, create a new test file in the `tests` directory with a name starting with `test_`. The test file should contain functions with names starting with `test_`. These functions will be automatically discovered and run by pytest.

## Requirements

The tests require the following Python packages:

- pytest
- pyyaml
- jsonschema

These dependencies are listed in the `requirements.txt` file at the root of the project. 