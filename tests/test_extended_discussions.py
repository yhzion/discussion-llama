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
def sample_roles():
    role1_data = {
        "role": "role1",
        "description": "Test role 1",
        "responsibilities": ["Responsibility 1"],
        "expertise": ["Expertise 1"],
        "characteristics": ["Characteristic 1"],
        "interaction_with": {},
        "success_criteria": ["Success 1"]
    }
    
    role2_data = {
        "role": "role2",
        "description": "Test role 2",
        "responsibilities": ["Responsibility 2"],
        "expertise": ["Expertise 2"],
        "characteristics": ["Characteristic 2"],
        "interaction_with": {},
        "success_criteria": ["Success 2"]
    }
    
    return [Role(role1_data), Role(role2_data)]


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


def test_extended_discussion_initialization(sample_roles, temp_state_dir):
    """Test that the DiscussionEngine can be initialized with a high max_turns value."""
    engine = DiscussionEngine(
        topic="Test topic",
        roles=sample_roles,
        state_dir=temp_state_dir,
        max_turns=10000
    )
    
    assert engine.max_turns == 10000


def test_extended_discussion_run(sample_roles, temp_state_dir, mock_llm_client):
    """Test that the discussion engine can handle a large number of turns."""
    # Mock the consensus check to return True after a specific number of turns
    original_check_consensus = DiscussionEngine.check_consensus
    
    def mock_check_consensus(self):
        state = self.state_manager.load_state()
        # Return True after 150 turns to simulate consensus
        return state.turn >= 150
    
    with patch.object(DiscussionEngine, 'check_consensus', mock_check_consensus):
        engine = DiscussionEngine(
            topic="Test topic",
            roles=sample_roles,
            state_dir=temp_state_dir,
            max_turns=10000
        )
        
        # Run the discussion
        result = engine.run_discussion()
        
        # Check that the discussion ran for the expected number of turns
        assert result["turns"] == 150
        assert result["consensus_reached"] is True
        assert len(result["discussion"]) > 150  # Including system messages


def test_extended_discussion_with_deadlock_resolution(sample_roles, temp_state_dir, mock_llm_client):
    """Test that extended discussions can handle deadlocks properly."""
    # Create a mock LLM client directly
    mock_client = MagicMock()
    mock_client.generate.return_value = "This is a mock response from the LLM."
    
    # Create a simple test to verify that deadlock detection and resolution work with extended discussions
    engine = DiscussionEngine(
        topic="Test topic",
        roles=sample_roles,
        state_dir=temp_state_dir,
        deadlock_detection_enabled=True,
        max_turns=10000,  # Set a high max_turns for extended discussions
        llm_client=mock_client
    )
    
    # Verify that the max_turns is set correctly
    assert engine.max_turns == 10000
    
    # Create a state with a message
    state = engine.state_manager.load_state()
    message = Message(sample_roles[0].role, "Initial message")
    state.add_message(message)
    engine.state_manager.save_state(state)
    
    # Directly call detect_deadlock and resolve_deadlock
    with patch.object(engine, 'detect_deadlock', return_value=True):
        # Call resolve_deadlock
        resolution_message = engine.resolve_deadlock()
        
        # Check that a resolution message was added
        assert resolution_message is not None
        assert "System" in resolution_message.role
        assert "deadlock" in resolution_message.content.lower()
        
        # Check that the state was updated
        updated_state = engine.state_manager.load_state()
        assert updated_state.deadlock_detected is True
        assert updated_state.deadlock_resolution_applied is True


def test_discussion_state_persistence_with_high_turn_count(sample_roles, temp_state_dir):
    """Test that the discussion state can be properly saved and loaded with a high turn count."""
    # Create a discussion state with a high turn count
    state = DiscussionState(topic="Test topic", roles=sample_roles)
    state.turn = 5000
    
    # Add some messages
    for i in range(10):
        role_index = i % 2
        message = Message(sample_roles[role_index].role, f"Message {i}")
        state.add_message(message)
    
    # Save the state
    manager = DiskBasedDiscussionManager("Test topic", sample_roles, temp_state_dir)
    manager.save_state(state)
    
    # Load the state
    loaded_state = manager.load_state()
    
    # Check that the turn count was preserved
    assert loaded_state.turn == 5000
    assert len(loaded_state.messages) == 10 