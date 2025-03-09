import os
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock
from discussion_llama.role.role_manager import Role
from discussion_llama.engine.discussion_engine import (
    Message, 
    DiscussionState, 
    DiskBasedDiscussionManager, 
    DiscussionEngine
)


@pytest.fixture
def hierarchical_roles():
    """Create a set of roles with hierarchical relationships."""
    ceo_data = {
        "role": "CEO",
        "description": "Chief Executive Officer",
        "responsibilities": ["Strategic leadership", "Decision making"],
        "expertise": ["Business strategy", "Leadership"],
        "characteristics": ["Decisive", "Visionary"],
        "interaction_with": {},
        "success_criteria": ["Company growth"],
        "hierarchy_level": 1,  # Top level
        "subordinates": ["CTO", "CFO", "COO"]
    }
    
    cto_data = {
        "role": "CTO",
        "description": "Chief Technology Officer",
        "responsibilities": ["Technology strategy", "Technical leadership"],
        "expertise": ["Technology", "Engineering"],
        "characteristics": ["Innovative", "Technical"],
        "interaction_with": {},
        "success_criteria": ["Technical innovation"],
        "hierarchy_level": 2,  # Second level
        "superior": "CEO",
        "subordinates": ["Engineering Manager", "Product Manager"]
    }
    
    cfo_data = {
        "role": "CFO",
        "description": "Chief Financial Officer",
        "responsibilities": ["Financial strategy", "Budgeting"],
        "expertise": ["Finance", "Accounting"],
        "characteristics": ["Analytical", "Detail-oriented"],
        "interaction_with": {},
        "success_criteria": ["Financial health"],
        "hierarchy_level": 2,  # Second level
        "superior": "CEO",
        "subordinates": []
    }
    
    engineering_manager_data = {
        "role": "Engineering Manager",
        "description": "Manager of engineering team",
        "responsibilities": ["Team management", "Project delivery"],
        "expertise": ["Software development", "Team leadership"],
        "characteristics": ["Organized", "Supportive"],
        "interaction_with": {},
        "success_criteria": ["Project success"],
        "hierarchy_level": 3,  # Third level
        "superior": "CTO",
        "subordinates": ["Software Engineer"]
    }
    
    software_engineer_data = {
        "role": "Software Engineer",
        "description": "Software developer",
        "responsibilities": ["Code development", "Testing"],
        "expertise": ["Programming", "Problem solving"],
        "characteristics": ["Detail-oriented", "Logical"],
        "interaction_with": {},
        "success_criteria": ["Code quality"],
        "hierarchy_level": 4,  # Fourth level
        "superior": "Engineering Manager",
        "subordinates": []
    }
    
    return [
        Role(ceo_data),
        Role(cto_data),
        Role(cfo_data),
        Role(engineering_manager_data),
        Role(software_engineer_data)
    ]


@pytest.fixture
def temp_state_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_llm_client():
    with patch('discussion_llama.llm.llm_client.create_llm_client') as mock_create:
        mock_client = MagicMock()
        mock_client.generate.return_value = "Mock response"
        mock_create.return_value = mock_client
        yield mock_client


def test_role_hierarchy_attributes(hierarchical_roles):
    """Test that roles have the correct hierarchy attributes."""
    # Find roles by their role names
    ceo = next(role for role in hierarchical_roles if role.role == "CEO")
    cto = next(role for role in hierarchical_roles if role.role == "CTO")
    engineering_manager = next(role for role in hierarchical_roles if role.role == "Engineering Manager")
    software_engineer = next(role for role in hierarchical_roles if role.role == "Software Engineer")
    
    # Check hierarchy levels
    assert ceo.hierarchy_level == 1
    assert cto.hierarchy_level == 2
    assert engineering_manager.hierarchy_level == 3
    assert software_engineer.hierarchy_level == 4
    
    # Check superior-subordinate relationships
    assert "CTO" in ceo.subordinates
    assert cto.superior == "CEO"
    assert engineering_manager.superior == "CTO"
    assert "Engineering Manager" in cto.subordinates
    assert "Software Engineer" in engineering_manager.subordinates
    assert software_engineer.superior == "Engineering Manager"


def test_hierarchical_discussion_engine_initialization(hierarchical_roles, temp_state_dir):
    """Test that the DiscussionEngine initializes with hierarchical roles."""
    engine = DiscussionEngine(
        topic="Test topic",
        roles=hierarchical_roles,
        state_dir=temp_state_dir,
        hierarchical_mode=True
    )
    
    assert engine.hierarchical_mode is True
    assert hasattr(engine, 'role_hierarchy_map')
    
    # Check that the role hierarchy map was created correctly
    hierarchy_map = engine.role_hierarchy_map
    assert "CEO" in hierarchy_map
    assert hierarchy_map["CEO"]["level"] == 1
    assert "CTO" in hierarchy_map["CEO"]["subordinates"]
    
    assert "CTO" in hierarchy_map
    assert hierarchy_map["CTO"]["superior"] == "CEO"
    assert "Engineering Manager" in hierarchy_map["CTO"]["subordinates"]


def test_hierarchical_turn_management(hierarchical_roles, temp_state_dir, mock_llm_client):
    """Test that the discussion engine respects hierarchy in turn management."""
    engine = DiscussionEngine(
        topic="Test topic",
        roles=hierarchical_roles,
        state_dir=temp_state_dir,
        hierarchical_mode=True
    )
    
    # Run a few turns of the discussion
    with patch.object(engine, 'check_consensus', return_value=False):
        # Run for a limited number of turns for testing
        engine.max_turns = 10
        result = engine.run_discussion()
        
        # Get the sequence of speakers
        speakers = [msg["role"] for msg in result["discussion"] if msg["role"] != "System"]
        
        # Check that higher-level roles generally speak before lower-level roles
        # This is a simplified check - in reality, the pattern would be more complex
        ceo_indices = [i for i, role in enumerate(speakers) if role == "CEO"]
        cto_indices = [i for i, role in enumerate(speakers) if role == "CTO"]
        engineer_indices = [i for i, role in enumerate(speakers) if role == "Software Engineer"]
        
        # CEO should speak before engineers in the first round
        if ceo_indices and engineer_indices:
            assert min(ceo_indices) < min(engineer_indices)


def test_hierarchical_prompt_generation(hierarchical_roles, temp_state_dir):
    """Test that prompts include hierarchical information."""
    engine = DiscussionEngine(
        topic="Test topic",
        roles=hierarchical_roles,
        state_dir=temp_state_dir,
        hierarchical_mode=True
    )
    
    # Get roles
    ceo = next(role for role in hierarchical_roles if role.role == "CEO")
    software_engineer = next(role for role in hierarchical_roles if role.role == "Software Engineer")
    
    # Generate context for CEO
    ceo_context = engine.prepare_context(ceo)
    
    # Generate context for Software Engineer
    engineer_context = engine.prepare_context(software_engineer)
    
    # Create prompts
    ceo_prompt = engine.create_prompt_for_role(ceo, ceo_context)
    engineer_prompt = engine.create_prompt_for_role(software_engineer, engineer_context)
    
    # Check that hierarchical information is included in the prompts
    assert "subordinates" in ceo_prompt.lower()
    assert "cto" in ceo_prompt.lower()
    
    assert "superior" in engineer_prompt.lower()
    assert "engineering manager" in engineer_prompt.lower()


def test_decision_escalation(hierarchical_roles, temp_state_dir, mock_llm_client):
    """Test that decisions can be escalated up the hierarchy."""
    engine = DiscussionEngine(
        topic="Test topic",
        roles=hierarchical_roles,
        state_dir=temp_state_dir,
        hierarchical_mode=True
    )
    
    # Create a state with a message that requires escalation
    state = engine.state_manager.load_state()
    
    # Add a message from a lower-level role requesting escalation
    escalation_message = Message(
        "Software Engineer", 
        "This decision is beyond my authority. I need to escalate this to my manager."
    )
    state.add_message(escalation_message)
    
    # Save the state
    engine.state_manager.save_state(state)
    
    # Mock the detect_escalation method to return True
    with patch.object(engine, 'detect_escalation', return_value=True):
        # Call handle_escalation
        escalation_result = engine.handle_escalation("Software Engineer")
        
        # Check that escalation was handled correctly
        assert escalation_result is not None
        assert escalation_result["escalated_to"] == "Engineering Manager"
        
        # Check that the next speaker is the superior
        next_speaker = engine.get_next_speaker()
        assert next_speaker == "Engineering Manager" 