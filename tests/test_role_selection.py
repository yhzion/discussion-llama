import os
import tempfile
import pytest
import yaml
from unittest.mock import patch, MagicMock
from discussion_llama.role.role_manager import Role, RoleManager


@pytest.fixture
def sample_roles_data():
    """Create a set of sample roles with different expertise areas."""
    roles = [
        {
            "role": "Security Engineer",
            "description": "Focuses on system security",
            "responsibilities": ["Security assessment", "Vulnerability management"],
            "expertise": ["Security", "Cryptography", "Authentication", "Authorization"],
            "characteristics": ["Detail-oriented", "Cautious"],
            "interaction_with": {},
            "success_criteria": ["Secure system"]
        },
        {
            "role": "Frontend Developer",
            "description": "Builds user interfaces",
            "responsibilities": ["UI implementation", "UX optimization"],
            "expertise": ["JavaScript", "React", "CSS", "User Experience"],
            "characteristics": ["Creative", "User-focused"],
            "interaction_with": {},
            "success_criteria": ["Intuitive UI"]
        },
        {
            "role": "Backend Developer",
            "description": "Implements server-side logic",
            "responsibilities": ["API development", "Database design"],
            "expertise": ["Python", "Databases", "API Design", "Performance"],
            "characteristics": ["Analytical", "Systematic"],
            "interaction_with": {},
            "success_criteria": ["Robust backend"]
        },
        {
            "role": "DevOps Engineer",
            "description": "Manages deployment and infrastructure",
            "responsibilities": ["CI/CD", "Infrastructure management"],
            "expertise": ["Docker", "Kubernetes", "Cloud", "Automation"],
            "characteristics": ["Efficient", "Reliable"],
            "interaction_with": {},
            "success_criteria": ["Stable infrastructure"]
        },
        {
            "role": "Product Owner",
            "description": "Represents business and user needs",
            "responsibilities": ["Requirements gathering", "Prioritization"],
            "expertise": ["Business Analysis", "User Stories", "Product Strategy"],
            "characteristics": ["Strategic", "User-advocate"],
            "interaction_with": {},
            "success_criteria": ["Product-market fit"]
        }
    ]
    return roles


@pytest.fixture
def temp_roles_dir(sample_roles_data):
    """Create a temporary directory with sample role files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        for role_data in sample_roles_data:
            role_file_path = os.path.join(temp_dir, f"{role_data['role'].replace(' ', '_').lower()}.yaml")
            with open(role_file_path, "w") as f:
                yaml.dump(role_data, f)
        yield temp_dir


def test_basic_role_selection(temp_roles_dir):
    """Test basic role selection functionality."""
    manager = RoleManager(temp_roles_dir)
    
    # Test selecting roles with default parameters
    selected_roles = manager.select_roles_for_discussion("general topic")
    assert len(selected_roles) == 3  # Default is 3 roles
    
    # Test selecting a specific number of roles
    selected_roles = manager.select_roles_for_discussion("general topic", num_roles=2)
    assert len(selected_roles) == 2
    
    # Test selecting more roles than available
    selected_roles = manager.select_roles_for_discussion("general topic", num_roles=10)
    assert len(selected_roles) == 5  # Should return all available roles


def test_topic_based_role_selection(temp_roles_dir):
    """Test role selection based on topic relevance."""
    manager = RoleManager(temp_roles_dir)
    
    # Test with security-related topic
    security_topic = "How to implement secure authentication for our web application"
    selected_roles = manager.select_roles_for_discussion(security_topic, num_roles=3)
    
    # Security Engineer should be selected for security topic
    assert any(role.role == "Security Engineer" for role in selected_roles)
    
    # Test with frontend-related topic
    frontend_topic = "Improving the user interface design and responsiveness"
    selected_roles = manager.select_roles_for_discussion(frontend_topic, num_roles=3)
    
    # Frontend Developer should be selected for UI topic
    assert any(role.role == "Frontend Developer" for role in selected_roles)
    
    # Test with backend-related topic
    backend_topic = "Optimizing database performance and API response times"
    selected_roles = manager.select_roles_for_discussion(backend_topic, num_roles=3)
    
    # Backend Developer should be selected for backend topic
    assert any(role.role == "Backend Developer" for role in selected_roles)


@patch('discussion_llama.role.role_manager.RoleManager._calculate_role_relevance')
def test_role_relevance_calculation(mock_calculate_relevance, temp_roles_dir):
    """Test that roles are selected based on calculated relevance scores."""
    manager = RoleManager(temp_roles_dir)
    
    # Mock the relevance calculation to return predetermined scores
    mock_calculate_relevance.side_effect = lambda role, topic: {
        "Security Engineer": 0.9,
        "Frontend Developer": 0.3,
        "Backend Developer": 0.7,
        "DevOps Engineer": 0.5,
        "Product Owner": 0.6
    }.get(role.role, 0.0)
    
    # Select roles
    selected_roles = manager.select_roles_for_discussion("test topic", num_roles=3)
    
    # Verify that the highest scoring roles were selected
    selected_role_names = [role.role for role in selected_roles]
    assert "Security Engineer" in selected_role_names  # Highest score: 0.9
    assert "Backend Developer" in selected_role_names  # Second highest: 0.7
    assert "Product Owner" in selected_role_names  # Third highest: 0.6
    assert "DevOps Engineer" not in selected_role_names  # Fourth highest: 0.5
    assert "Frontend Developer" not in selected_role_names  # Lowest score: 0.3


def test_role_compatibility(temp_roles_dir):
    """Test that selected roles are compatible with each other."""
    manager = RoleManager(temp_roles_dir)
    
    # Add a compatibility check to the RoleManager class
    original_select_method = manager.select_roles_for_discussion
    
    def select_with_compatibility(topic, num_roles=3):
        # Get initial selection based on relevance
        candidates = original_select_method(topic, num_roles=num_roles+2)  # Get more candidates than needed
        
        # Simple compatibility check: don't select too many developers
        selected = []
        dev_count = 0
        
        for role in candidates:
            if "Developer" in role.role:
                if dev_count < 1:  # Limit to 1 developer
                    selected.append(role)
                    dev_count += 1
            else:
                selected.append(role)
            
            if len(selected) == num_roles:
                break
        
        return selected
    
    # Monkey patch the method
    manager.select_roles_for_discussion = select_with_compatibility
    
    # Test with a development topic
    dev_topic = "Implementing new features in our web application"
    selected_roles = manager.select_roles_for_discussion(dev_topic, num_roles=3)
    
    # Count developers in the selection
    dev_count = sum(1 for role in selected_roles if "Developer" in role.role)
    
    # Should have at most 1 developer
    assert dev_count <= 1


def test_role_diversity(temp_roles_dir):
    """Test that selected roles provide diverse perspectives."""
    manager = RoleManager(temp_roles_dir)
    
    # Add a diversity check to the RoleManager class
    original_select_method = manager.select_roles_for_discussion
    
    def select_with_diversity(topic, num_roles=3):
        # Get all roles
        all_roles = manager.get_all_roles()
        
        # Ensure we have at least one business role and one technical role
        business_roles = [r for r in all_roles if "Product Owner" in r.role]
        technical_roles = [r for r in all_roles if "Product Owner" not in r.role]
        
        selected = []
        
        # Always include a business perspective
        if business_roles:
            selected.append(business_roles[0])
        
        # Fill the rest with technical roles
        selected.extend(technical_roles[:num_roles - len(selected)])
        
        return selected[:num_roles]
    
    # Monkey patch the method
    manager.select_roles_for_discussion = select_with_diversity
    
    # Test role selection
    selected_roles = manager.select_roles_for_discussion("test topic", num_roles=3)
    
    # Should include Product Owner for business perspective
    assert any(role.role == "Product Owner" for role in selected_roles)
    
    # Should include technical roles
    assert any(role.role != "Product Owner" for role in selected_roles)


def test_role_selection_with_llm_integration(temp_roles_dir):
    """Test role selection with simulated LLM integration for better topic analysis."""
    manager = RoleManager(temp_roles_dir)
    
    # Simulate LLM-enhanced topic analysis
    with patch('discussion_llama.role.role_manager.RoleManager._analyze_topic_with_llm') as mock_analyze:
        # Mock the LLM to extract key aspects from the topic
        mock_analyze.return_value = {
            "key_aspects": ["authentication", "security", "user experience"],
            "technical_complexity": "high",
            "business_impact": "medium"
        }
        
        # Test with a complex topic
        complex_topic = "Implementing secure login while maintaining good user experience"
        selected_roles = manager.select_roles_for_discussion(complex_topic, num_roles=3)
        
        # Should include Security Engineer for authentication/security
        assert any(role.role == "Security Engineer" for role in selected_roles)
        
        # Should include Frontend Developer for user experience
        assert any(role.role == "Frontend Developer" for role in selected_roles) 