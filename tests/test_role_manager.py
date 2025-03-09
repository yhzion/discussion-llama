import os
import tempfile
import pytest
import yaml
from discussion_llama.role.role_manager import Role, RoleManager, load_roles_from_yaml


@pytest.fixture
def sample_role_data():
    return {
        "role": "test_role",
        "description": "A test role for unit testing",
        "responsibilities": ["Test responsibility 1", "Test responsibility 2"],
        "expertise": ["Testing", "Python"],
        "characteristics": ["Thorough", "Detail-oriented"],
        "interaction_with": {"other_role": "Collaborates on testing"},
        "success_criteria": ["All tests pass", "Good code coverage"]
    }


@pytest.fixture
def temp_roles_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_role_initialization(sample_role_data):
    role = Role(sample_role_data)
    
    assert role.role == "test_role"
    assert role.description == "A test role for unit testing"
    assert len(role.responsibilities) == 2
    assert "Testing" in role.expertise
    assert "Thorough" in role.characteristics
    assert "other_role" in role.interaction_with
    assert "All tests pass" in role.success_criteria


def test_role_prompt_description(sample_role_data):
    role = Role(sample_role_data)
    prompt = role.get_prompt_description()
    
    assert "You are a test_role" in prompt
    assert "A test role for unit testing" in prompt
    assert "Test responsibility 1" in prompt
    assert "Testing" in prompt
    assert "Thorough" in prompt


def test_role_manager_load_roles(temp_roles_dir, sample_role_data):
    # Create a test role file
    role_file_path = os.path.join(temp_roles_dir, "test_role.yaml")
    with open(role_file_path, "w") as f:
        yaml.dump(sample_role_data, f)
    
    # Create another test role file
    another_role_data = sample_role_data.copy()
    another_role_data["role"] = "another_role"
    another_role_file_path = os.path.join(temp_roles_dir, "another_role.yaml")
    with open(another_role_file_path, "w") as f:
        yaml.dump(another_role_data, f)
    
    # Test loading roles
    manager = RoleManager(temp_roles_dir)
    
    assert len(manager.roles) == 2
    assert "test_role" in manager.roles
    assert "another_role" in manager.roles
    
    # Test getting a specific role
    role = manager.get_role("test_role")
    assert role is not None
    assert role.role == "test_role"
    
    # Test getting all roles
    all_roles = manager.get_all_roles()
    assert len(all_roles) == 2
    
    # Test selecting roles for discussion
    selected_roles = manager.select_roles_for_discussion("test topic", 1)
    assert len(selected_roles) == 1


def test_load_roles_from_yaml(temp_roles_dir, sample_role_data):
    # Create a test role file
    role_file_path = os.path.join(temp_roles_dir, "test_role.yaml")
    with open(role_file_path, "w") as f:
        yaml.dump(sample_role_data, f)
    
    # Test the utility function
    roles = load_roles_from_yaml(temp_roles_dir)
    
    assert len(roles) == 1
    assert roles[0].role == "test_role" 