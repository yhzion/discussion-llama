import os
import json
import yaml
import pytest
import jsonschema
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Path to the schema file
SCHEMA_PATH = PROJECT_ROOT / "roles" / "role_schema.json"

# Path to the role directory
ROLE_DIR = PROJECT_ROOT / "roles"

def load_schema():
    """Load the JSON schema from the schema file."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_role_files():
    """Get all YAML files in the role directory except the template."""
    role_files = []
    for file in os.listdir(ROLE_DIR):
        if file.endswith(".yaml") and file != "role_template.yaml":
            role_files.append(ROLE_DIR / file)
    return role_files

def load_yaml(file_path):
    """Load a YAML file and return its contents."""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_schema_exists():
    """Test that the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

def test_role_directory_exists():
    """Test that the role directory exists."""
    assert ROLE_DIR.exists(), f"Role directory not found at {ROLE_DIR}"

def test_role_files_exist():
    """Test that there are role files in the role directory."""
    role_files = get_role_files()
    assert len(role_files) > 0, "No role files found in the role directory"

@pytest.mark.parametrize("role_file", get_role_files())
def test_role_file_valid_yaml(role_file):
    """Test that each role file is valid YAML."""
    try:
        yaml_content = load_yaml(role_file)
        assert yaml_content is not None, f"Failed to load YAML from {role_file}"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in {role_file}: {e}")

@pytest.mark.parametrize("role_file", get_role_files())
def test_role_file_conforms_to_schema(role_file):
    """Test that each role file conforms to the schema."""
    schema = load_schema()
    yaml_content = load_yaml(role_file)
    
    try:
        jsonschema.validate(instance=yaml_content, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Schema validation failed for {role_file}: {e}")

def test_all_required_fields_present():
    """Test that all required fields are present in each role file."""
    schema = load_schema()
    required_fields = schema.get("required", [])
    
    for role_file in get_role_files():
        yaml_content = load_yaml(role_file)
        for field in required_fields:
            assert field in yaml_content, f"Required field '{field}' missing in {role_file}"
            
            # Check if the field is an array and has at least one item if minItems is specified
            if schema["properties"][field].get("type") == "array" and schema["properties"][field].get("minItems", 0) > 0:
                min_items = schema["properties"][field].get("minItems", 0)
                assert isinstance(yaml_content[field], list), f"Field '{field}' should be an array in {role_file}"
                assert len(yaml_content[field]) >= min_items, f"Field '{field}' should have at least {min_items} items in {role_file}"

def test_no_additional_properties():
    """Test that no additional properties are present in each role file."""
    schema = load_schema()
    allowed_properties = set(schema.get("properties", {}).keys())
    
    for role_file in get_role_files():
        yaml_content = load_yaml(role_file)
        file_properties = set(yaml_content.keys())
        
        unexpected_properties = file_properties - allowed_properties
        assert not unexpected_properties, f"Unexpected properties {unexpected_properties} in {role_file}" 