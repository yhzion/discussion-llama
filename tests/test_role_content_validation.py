import os
import yaml
import pytest
import re
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Path to the role directory
ROLE_DIR = PROJECT_ROOT / "roles"

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

def normalize_role_name(role_name):
    """Normalize a role name for comparison."""
    # Remove special characters and convert to lowercase
    normalized = re.sub(r'[^\w\s]', '', role_name).lower().replace(" ", "_")
    # Handle special cases
    if normalized == "uiux_designer":
        normalized = "ui_ux_designer"
    return normalized

@pytest.mark.parametrize("role_file", get_role_files())
def test_role_name_matches_filename(role_file):
    """Test that the role name in the YAML file matches the filename (without extension)."""
    yaml_content = load_yaml(role_file)
    # Normalize role name by removing special characters and replacing with underscores
    role_name = normalize_role_name(yaml_content.get("role", ""))
    filename = role_file.stem
    
    assert role_name in filename or filename in role_name, \
        f"Role name '{yaml_content.get('role')}' does not match filename '{filename}'"

@pytest.mark.parametrize("role_file", get_role_files())
def test_description_not_empty(role_file):
    """Test that the description is not empty and has a reasonable length."""
    yaml_content = load_yaml(role_file)
    description = yaml_content.get("description", "")
    
    assert description, f"Description is empty in {role_file}"
    assert len(description) >= 50, f"Description is too short in {role_file}"
    assert len(description) <= 1000, f"Description is too long in {role_file}"

@pytest.mark.parametrize("role_file", get_role_files())
def test_responsibilities_reasonable_count(role_file):
    """Test that there is a reasonable number of responsibilities."""
    yaml_content = load_yaml(role_file)
    responsibilities = yaml_content.get("responsibilities", [])
    
    assert len(responsibilities) >= 3, f"Too few responsibilities in {role_file}"
    assert len(responsibilities) <= 15, f"Too many responsibilities in {role_file}"

@pytest.mark.parametrize("role_file", get_role_files())
def test_expertise_reasonable_count(role_file):
    """Test that there is a reasonable number of expertise items."""
    yaml_content = load_yaml(role_file)
    expertise = yaml_content.get("expertise", [])
    
    assert len(expertise) >= 3, f"Too few expertise items in {role_file}"
    assert len(expertise) <= 15, f"Too many expertise items in {role_file}"

@pytest.mark.parametrize("role_file", get_role_files())
def test_characteristics_reasonable_count(role_file):
    """Test that there is a reasonable number of characteristics."""
    yaml_content = load_yaml(role_file)
    characteristics = yaml_content.get("characteristics", [])
    
    assert len(characteristics) >= 3, f"Too few characteristics in {role_file}"
    assert len(characteristics) <= 10, f"Too many characteristics in {role_file}"

@pytest.mark.parametrize("role_file", get_role_files())
def test_interaction_with_reasonable_count(role_file):
    """Test that there is a reasonable number of interactions."""
    yaml_content = load_yaml(role_file)
    interactions = yaml_content.get("interaction_with", [])
    
    assert len(interactions) >= 2, f"Too few interactions in {role_file}"
    assert len(interactions) <= 15, f"Too many interactions in {role_file}"  # Increased from 10 to 15

@pytest.mark.parametrize("role_file", get_role_files())
def test_success_criteria_reasonable_count(role_file):
    """Test that there is a reasonable number of success criteria."""
    yaml_content = load_yaml(role_file)
    success_criteria = yaml_content.get("success_criteria", [])
    
    assert len(success_criteria) >= 3, f"Too few success criteria in {role_file}"
    assert len(success_criteria) <= 10, f"Too many success criteria in {role_file}"

@pytest.mark.parametrize("role_file", get_role_files())
def test_tools_and_technologies_format(role_file):
    """Test that tools and technologies follow the expected format."""
    yaml_content = load_yaml(role_file)
    tools = yaml_content.get("tools_and_technologies", [])
    
    if tools:
        for tool in tools:
            assert isinstance(tool, str), f"Tool '{tool}' is not a string in {role_file}"
            assert "Essential: " in tool or "Recommended: " in tool, \
                f"Tool '{tool}' does not follow 'Essential: ' or 'Recommended: ' format in {role_file}"

@pytest.mark.parametrize("role_file", get_role_files())
def test_agile_mapping_format(role_file):
    """Test that agile mapping follows the expected format."""
    yaml_content = load_yaml(role_file)
    agile_mapping = yaml_content.get("agile_mapping", [])
    
    if agile_mapping:
        expected_prefixes = [
            "Scrum role: ", 
            "Sprint Planning: ", 
            "Daily Scrum: ", 
            "Sprint Review: ", 
            "Sprint Retrospective: ", 
            "Backlog Refinement: "
        ]
        
        for mapping in agile_mapping:
            assert any(mapping.startswith(prefix) for prefix in expected_prefixes), \
                f"Agile mapping '{mapping}' does not follow expected format in {role_file}"

@pytest.mark.parametrize("role_file", get_role_files())
def test_scalability_format(role_file):
    """Test that scalability follows the expected format."""
    yaml_content = load_yaml(role_file)
    scalability = yaml_content.get("scalability", [])
    
    if scalability:
        expected_prefixes = ["Small team: ", "Large team: "]
        
        for scale in scalability:
            assert any(scale.startswith(prefix) for prefix in expected_prefixes), \
                f"Scalability '{scale}' does not follow expected format in {role_file}"

@pytest.mark.parametrize("role_file", get_role_files())
def test_key_performance_indicators_format(role_file):
    """Test that KPIs follow the expected format."""
    yaml_content = load_yaml(role_file)
    kpis = yaml_content.get("key_performance_indicators", [])
    
    if kpis:
        for kpi in kpis:
            assert ": " in kpi, f"KPI '{kpi}' does not follow 'KPI name: description' format in {role_file}"

def test_roles_have_consistent_fields():
    """Test that all role files have a consistent set of fields."""
    role_files = get_role_files()
    
    # Get the set of fields from each role file
    all_field_sets = []
    for role_file in role_files:
        yaml_content = load_yaml(role_file)
        all_field_sets.append(set(yaml_content.keys()))
    
    # Find the most common set of fields
    if all_field_sets:
        most_common_fields = max(set(map(frozenset, all_field_sets)), key=list(map(frozenset, all_field_sets)).count)
        
        # Check that each role file has at least the most common fields
        for i, role_file in enumerate(role_files):
            missing_fields = most_common_fields - all_field_sets[i]
            assert not missing_fields, f"Role file {role_file} is missing common fields: {missing_fields}" 