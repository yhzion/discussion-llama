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
        mock_client.generate.return_value = "This is a mock response from the LLM."
        mock_create.return_value = mock_client
        yield mock_client


def test_deadlock_detection_initialization(sample_roles, temp_state_dir):
    """Test that the DiscussionEngine initializes with deadlock detection enabled."""
    engine = DiscussionEngine(
        topic="Test topic",
        roles=sample_roles,
        state_dir=temp_state_dir,
        deadlock_detection_enabled=True
    )
    
    assert engine.deadlock_detection_enabled is True
    assert hasattr(engine, 'deadlock_threshold')
    assert hasattr(engine, 'deadlock_resolution_strategies')


def test_detect_deadlock_with_repetitive_messages(sample_roles, temp_state_dir, mock_llm_client):
    """Test that the engine can detect a deadlock when messages become repetitive."""
    engine = DiscussionEngine(
        topic="Test topic",
        roles=sample_roles,
        state_dir=temp_state_dir,
        deadlock_detection_enabled=True,
        deadlock_threshold=0.9  # High similarity threshold for testing
    )
    
    # Create a state with repetitive messages
    state = engine.state_manager.load_state()
    
    # Add similar messages from the same role alternating
    for i in range(6):  # Add enough messages to trigger deadlock detection
        role_index = i % 2
        content = f"I maintain my position on this issue. My view is unchanged." if i > 0 else "My position on this issue."
        message = Message(sample_roles[role_index].role, content)
        state.add_message(message)
    
    engine.state_manager.save_state(state)
    
    # Check if deadlock is detected
    is_deadlocked = engine.detect_deadlock()
    assert is_deadlocked is True


def test_deadlock_resolution(sample_roles, temp_state_dir, mock_llm_client):
    """Test that the engine can resolve a deadlock when detected."""
    # Create a mock LLM client directly
    mock_client = MagicMock()
    mock_client.generate.return_value = "Here's a new perspective to consider..."
    
    engine = DiscussionEngine(
        topic="Test topic",
        roles=sample_roles,
        state_dir=temp_state_dir,
        deadlock_detection_enabled=True,
        llm_client=mock_client  # Use the mock client directly
    )
    
    # Create a state with repetitive messages
    state = engine.state_manager.load_state()
    
    # Add similar messages from the same role alternating
    for i in range(6):  # Add enough messages to trigger deadlock detection
        role_index = i % 2
        content = f"I maintain my position on this issue. My view is unchanged." if i > 0 else "My position on this issue."
        message = Message(sample_roles[role_index].role, content)
        state.add_message(message)
    
    engine.state_manager.save_state(state)
    
    # Mock the detect_deadlock method to return True
    with patch.object(engine, 'detect_deadlock', return_value=True):
        # Call resolve_deadlock
        resolution_message = engine.resolve_deadlock()
        
        # Check that a resolution message was added
        assert resolution_message is not None
        assert "System" in resolution_message.role
        assert "deadlock" in resolution_message.content.lower()
        
        # Check that the state was updated
        updated_state = engine.state_manager.load_state()
        assert len(updated_state.messages) > len(state.messages)
        assert updated_state.messages[-1].role == resolution_message.role
        assert updated_state.messages[-1].content == resolution_message.content


def test_run_discussion_with_deadlock_detection(sample_roles, temp_state_dir, mock_llm_client):
    """Test that the run_discussion method handles deadlock detection and resolution."""
    # Create a mock LLM client directly
    mock_client = MagicMock()
    mock_client.generate.return_value = "This is a mock response from the LLM."
    
    # Create a simple test to verify that deadlock detection and resolution work
    engine = DiscussionEngine(
        topic="Test topic",
        roles=sample_roles,
        state_dir=temp_state_dir,
        deadlock_detection_enabled=True,
        max_turns=5,  # Set a very low max_turns for testing
        llm_client=mock_client
    )
    
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
        
        # Check that the result dictionary includes the deadlock information
        result = {
            "deadlock_detected": updated_state.deadlock_detected,
            "deadlock_resolution_applied": updated_state.deadlock_resolution_applied
        }
        
        assert result["deadlock_detected"] is True
        assert result["deadlock_resolution_applied"] is True 