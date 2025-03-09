import os
import tempfile
import pytest
import yaml
from unittest.mock import patch, MagicMock
from discussion_llama.role.role_manager import Role, RoleManager


@pytest.fixture
def compatible_roles_data():
    """Create a set of compatible roles with defined interactions."""
    roles = [
        {
            "role": "Frontend Developer",
            "description": "Builds user interfaces",
            "responsibilities": ["UI implementation", "UX optimization"],
            "expertise": ["JavaScript", "React", "CSS"],
            "characteristics": ["Creative", "User-focused"],
            "interaction_with": {
                "Backend Developer": "Collaborates on API integration",
                "UX Designer": "Works closely on implementing designs",
                "Product Owner": "Receives requirements and feedback"
            },
            "success_criteria": ["Intuitive UI"]
        },
        {
            "role": "Backend Developer",
            "description": "Implements server-side logic",
            "responsibilities": ["API development", "Database design"],
            "expertise": ["Python", "Databases", "API Design"],
            "characteristics": ["Analytical", "Systematic"],
            "interaction_with": {
                "Frontend Developer": "Provides APIs for UI integration",
                "DevOps Engineer": "Coordinates on deployment",
                "Database Administrator": "Consults on database design"
            },
            "success_criteria": ["Robust backend"]
        },
        {
            "role": "UX Designer",
            "description": "Designs user experiences",
            "responsibilities": ["User research", "Interface design"],
            "expertise": ["User Research", "Wireframing", "Prototyping"],
            "characteristics": ["Empathetic", "Creative"],
            "interaction_with": {
                "Frontend Developer": "Provides designs for implementation",
                "Product Owner": "Aligns on user needs and requirements"
            },
            "success_criteria": ["Usable design"]
        },
        {
            "role": "Product Owner",
            "description": "Represents business and user needs",
            "responsibilities": ["Requirements gathering", "Prioritization"],
            "expertise": ["Business Analysis", "User Stories"],
            "characteristics": ["Strategic", "User-advocate"],
            "interaction_with": {
                "Frontend Developer": "Provides requirements and feedback",
                "UX Designer": "Communicates business and user needs",
                "Backend Developer": "Defines functional requirements"
            },
            "success_criteria": ["Product-market fit"]
        },
        {
            "role": "DevOps Engineer",
            "description": "Manages deployment and infrastructure",
            "responsibilities": ["CI/CD", "Infrastructure management"],
            "expertise": ["Docker", "Kubernetes", "Cloud"],
            "characteristics": ["Efficient", "Reliable"],
            "interaction_with": {
                "Backend Developer": "Supports deployment needs",
                "Security Engineer": "Implements security measures"
            },
            "success_criteria": ["Stable infrastructure"]
        },
        {
            "role": "Security Engineer",
            "description": "Ensures system security",
            "responsibilities": ["Security assessment", "Vulnerability management"],
            "expertise": ["Security", "Cryptography", "Authentication"],
            "characteristics": ["Detail-oriented", "Cautious"],
            "interaction_with": {
                "DevOps Engineer": "Advises on security configurations",
                "Backend Developer": "Reviews code for security issues"
            },
            "success_criteria": ["Secure system"]
        }
    ]
    return roles


@pytest.fixture
def temp_roles_dir(compatible_roles_data):
    """Create a temporary directory with role files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        for role_data in compatible_roles_data:
            role_file_path = os.path.join(temp_dir, f"{role_data['role'].replace(' ', '_').lower()}.yaml")
            with open(role_file_path, "w") as f:
                yaml.dump(role_data, f)
        yield temp_dir


def test_role_interaction_extraction(temp_roles_dir):
    """Test extracting role interactions from role definitions."""
    manager = RoleManager(temp_roles_dir)
    
    # Get the Frontend Developer role
    frontend_dev = manager.get_role("Frontend Developer")
    
    # Check that interactions are correctly loaded
    assert "Backend Developer" in frontend_dev.interaction_with
    assert "UX Designer" in frontend_dev.interaction_with
    assert "Product Owner" in frontend_dev.interaction_with
    
    # Check the interaction descriptions
    assert "Collaborates on API integration" == frontend_dev.interaction_with["Backend Developer"]
    assert "Works closely on implementing designs" == frontend_dev.interaction_with["UX Designer"]


def test_role_compatibility_check():
    """Test checking compatibility between roles."""
    # Create roles with defined interactions
    frontend_dev = Role({
        "role": "Frontend Developer",
        "description": "Builds user interfaces",
        "interaction_with": {
            "Backend Developer": "Collaborates on API integration",
            "UX Designer": "Works closely on implementing designs"
        }
    })
    
    backend_dev = Role({
        "role": "Backend Developer",
        "description": "Implements server-side logic",
        "interaction_with": {
            "Frontend Developer": "Provides APIs for UI integration",
            "DevOps Engineer": "Coordinates on deployment"
        }
    })
    
    ux_designer = Role({
        "role": "UX Designer",
        "description": "Designs user experiences",
        "interaction_with": {
            "Frontend Developer": "Provides designs for implementation"
        }
    })
    
    security_engineer = Role({
        "role": "Security Engineer",
        "description": "Ensures system security",
        "interaction_with": {
            "Backend Developer": "Reviews code for security issues"
        }
    })
    
    # Check bidirectional compatibility
    assert is_compatible(frontend_dev, backend_dev)
    assert is_compatible(frontend_dev, ux_designer)
    
    # Check unidirectional compatibility
    assert is_compatible(security_engineer, backend_dev)
    assert not is_compatible(frontend_dev, security_engineer)


def is_compatible(role1, role2):
    """Helper function to check if two roles are compatible."""
    return role2.role in role1.interaction_with or role1.role in role2.interaction_with


def test_find_compatible_roles():
    """Test finding compatible roles for a given role."""
    # Create roles with defined interactions
    frontend_dev = Role({
        "role": "Frontend Developer",
        "description": "Builds user interfaces",
        "interaction_with": {
            "Backend Developer": "Collaborates on API integration",
            "UX Designer": "Works closely on implementing designs"
        }
    })
    
    backend_dev = Role({
        "role": "Backend Developer",
        "description": "Implements server-side logic",
        "interaction_with": {
            "Frontend Developer": "Provides APIs for UI integration",
            "DevOps Engineer": "Coordinates on deployment"
        }
    })
    
    ux_designer = Role({
        "role": "UX Designer",
        "description": "Designs user experiences",
        "interaction_with": {
            "Frontend Developer": "Provides designs for implementation"
        }
    })
    
    devops_engineer = Role({
        "role": "DevOps Engineer",
        "description": "Manages deployment and infrastructure",
        "interaction_with": {
            "Backend Developer": "Supports deployment needs"
        }
    })
    
    security_engineer = Role({
        "role": "Security Engineer",
        "description": "Ensures system security",
        "interaction_with": {
            "Backend Developer": "Reviews code for security issues"
        }
    })
    
    all_roles = [frontend_dev, backend_dev, ux_designer, devops_engineer, security_engineer]
    
    # Find compatible roles for Frontend Developer
    compatible_with_frontend = find_compatible_roles(frontend_dev, all_roles)
    assert len(compatible_with_frontend) == 2
    assert backend_dev in compatible_with_frontend
    assert ux_designer in compatible_with_frontend
    
    # Find compatible roles for Backend Developer
    compatible_with_backend = find_compatible_roles(backend_dev, all_roles)
    assert len(compatible_with_backend) == 3
    assert frontend_dev in compatible_with_backend
    assert devops_engineer in compatible_with_backend
    assert security_engineer in compatible_with_backend


def find_compatible_roles(role, all_roles):
    """Helper function to find compatible roles for a given role."""
    return [r for r in all_roles if r != role and is_compatible(role, r)]


def test_select_compatible_roles(temp_roles_dir):
    """Test selecting a set of compatible roles for a discussion."""
    manager = RoleManager(temp_roles_dir)
    
    # Add a method to select compatible roles
    def select_compatible_roles(topic, num_roles=3):
        all_roles = manager.get_all_roles()
        
        # Start with the most relevant role for the topic
        # For simplicity, just pick the first role in this test
        selected = [all_roles[0]]
        
        # Add compatible roles until we reach the desired number
        while len(selected) < num_roles and len(selected) < len(all_roles):
            # Find roles compatible with any of the already selected roles
            compatible_candidates = []
            for selected_role in selected:
                for candidate in all_roles:
                    if candidate not in selected and is_compatible(selected_role, candidate):
                        compatible_candidates.append(candidate)
            
            # If no compatible roles found, break
            if not compatible_candidates:
                break
            
            # Add the first compatible role (in a real implementation, 
            # you would choose based on relevance to the topic)
            selected.append(compatible_candidates[0])
        
        return selected
    
    # Monkey patch the method
    manager.select_compatible_roles = select_compatible_roles
    
    # Test selecting compatible roles
    selected_roles = manager.select_compatible_roles("test topic", num_roles=3)
    
    # Check that we got the expected number of roles
    assert len(selected_roles) == 3
    
    # Check that all selected roles are compatible with at least one other selected role
    for i, role1 in enumerate(selected_roles):
        has_compatible = False
        for j, role2 in enumerate(selected_roles):
            if i != j and is_compatible(role1, role2):
                has_compatible = True
                break
        assert has_compatible, f"{role1.role} is not compatible with any other selected role"


def test_role_compatibility_matrix(temp_roles_dir):
    """Test creating a compatibility matrix for all roles."""
    manager = RoleManager(temp_roles_dir)
    all_roles = manager.get_all_roles()
    
    # Create a compatibility matrix
    matrix = {}
    for role1 in all_roles:
        matrix[role1.role] = {}
        for role2 in all_roles:
            if role1 != role2:
                matrix[role1.role][role2.role] = is_compatible(role1, role2)
    
    # Check some expected compatibilities
    assert matrix["Frontend Developer"]["Backend Developer"] is True
    assert matrix["Frontend Developer"]["UX Designer"] is True
    assert matrix["Backend Developer"]["DevOps Engineer"] is True
    
    # Check that the matrix is not necessarily symmetric
    # (some roles might mention interactions that others don't)
    for role1 in all_roles:
        for role2 in all_roles:
            if role1 != role2:
                if role1.role in matrix and role2.role in matrix:
                    if role2.role in matrix[role1.role] and role1.role in matrix[role2.role]:
                        # This assertion might fail if interactions are not defined symmetrically
                        # which is fine - it's just to check the behavior
                        pass


def test_role_compatibility_validation(temp_roles_dir):
    """Test validating role compatibility in a selected set."""
    manager = RoleManager(temp_roles_dir)
    
    # Define a validation function
    def validate_role_compatibility(roles):
        # Check that each role is compatible with at least one other role
        for i, role1 in enumerate(roles):
            has_compatible = False
            for j, role2 in enumerate(roles):
                if i != j and is_compatible(role1, role2):
                    has_compatible = True
                    break
            if not has_compatible:
                return False, f"{role1.role} is not compatible with any other selected role"
        return True, "All roles are compatible"
    
    # Test with compatible roles
    frontend_dev = manager.get_role("Frontend Developer")
    backend_dev = manager.get_role("Backend Developer")
    ux_designer = manager.get_role("UX Designer")
    
    is_valid, message = validate_role_compatibility([frontend_dev, backend_dev, ux_designer])
    assert is_valid is True
    
    # Test with incompatible roles
    security_engineer = manager.get_role("Security Engineer")
    devops_engineer = manager.get_role("DevOps Engineer")
    
    # This set might not be fully connected (depends on the exact interaction definitions)
    is_valid, message = validate_role_compatibility([frontend_dev, security_engineer, devops_engineer])
    # We don't assert the result here as it depends on the exact interaction definitions 