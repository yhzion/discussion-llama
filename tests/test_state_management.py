import os
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock
from discussion_llama.role.role_manager import Role
from discussion_llama.engine.discussion_engine import (
    Message, 
    DiscussionState, 
    DiskBasedDiscussionManager
)


@pytest.fixture
def sample_roles():
    """Create sample roles for testing."""
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
    """Create a temporary directory for state files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_message_serialization():
    """Test message serialization and deserialization."""
    # Create a message with metadata
    original_message = Message(
        "test_role", 
        "Test message content", 
        {"sentiment": "positive", "key_points": ["point1", "point2"]}
    )
    
    # Convert to dict
    message_dict = original_message.to_dict()
    
    # Convert back to Message
    reconstructed_message = Message.from_dict(message_dict)
    
    # Verify all fields match
    assert reconstructed_message.role == original_message.role
    assert reconstructed_message.content == original_message.content
    assert reconstructed_message.metadata == original_message.metadata
    assert reconstructed_message.timestamp == original_message.timestamp


def test_discussion_state_serialization(sample_roles):
    """Test discussion state serialization and deserialization."""
    # Create a state with messages
    original_state = DiscussionState("test topic", sample_roles)
    original_state.add_message(Message("role1", "Message 1"))
    original_state.add_message(Message("role2", "Message 2"))
    original_state.summary = "This is a summary of the discussion."
    original_state.turn = 2
    original_state.consensus_reached = True
    
    # Convert to dict
    state_dict = original_state.to_dict()
    
    # Convert back to DiscussionState
    reconstructed_state = DiscussionState.from_dict(state_dict, sample_roles)
    
    # Verify all fields match
    assert reconstructed_state.topic == original_state.topic
    assert len(reconstructed_state.messages) == len(original_state.messages)
    assert reconstructed_state.messages[0].role == original_state.messages[0].role
    assert reconstructed_state.messages[0].content == original_state.messages[0].content
    assert reconstructed_state.summary == original_state.summary
    assert reconstructed_state.turn == original_state.turn
    assert reconstructed_state.consensus_reached == original_state.consensus_reached


def test_disk_based_discussion_manager_save_load(sample_roles, temp_state_dir):
    """Test saving and loading discussion state from disk."""
    manager = DiskBasedDiscussionManager("test topic", sample_roles, temp_state_dir)
    
    # Create a state with messages
    state = DiscussionState("test topic", sample_roles)
    state.add_message(Message("role1", "Message 1"))
    state.add_message(Message("role2", "Message 2"))
    state.summary = "This is a summary of the discussion."
    state.turn = 2
    state.consensus_reached = True
    
    # Save the state
    manager.save_state(state)
    
    # Check that the file was created
    state_file_path = os.path.join(temp_state_dir, "state.json")
    assert os.path.exists(state_file_path)
    
    # Load the state
    loaded_state = manager.load_state()
    
    # Verify all fields match
    assert loaded_state.topic == state.topic
    assert len(loaded_state.messages) == len(state.messages)
    assert loaded_state.messages[0].role == state.messages[0].role
    assert loaded_state.messages[0].content == state.messages[0].content
    assert loaded_state.summary == state.summary
    assert loaded_state.turn == state.turn
    assert loaded_state.consensus_reached == state.consensus_reached


def test_disk_based_discussion_manager_no_existing_state(sample_roles, temp_state_dir):
    """Test loading when no state file exists."""
    manager = DiskBasedDiscussionManager("test topic", sample_roles, temp_state_dir)
    
    # Load the state (should create a new one)
    loaded_state = manager.load_state()
    
    # Verify default values
    assert loaded_state.topic == "test topic"
    assert len(loaded_state.messages) == 0
    assert loaded_state.summary == ""
    assert loaded_state.turn == 0
    assert loaded_state.consensus_reached is False


def test_disk_based_discussion_manager_invalid_state_file(sample_roles, temp_state_dir):
    """Test loading when state file is invalid."""
    # Create an invalid state file
    state_file_path = os.path.join(temp_state_dir, "state.json")
    with open(state_file_path, "w") as f:
        f.write("This is not valid JSON")
    
    manager = DiskBasedDiscussionManager("test topic", sample_roles, temp_state_dir)
    
    # Load the state (should create a new one)
    loaded_state = manager.load_state()
    
    # Verify default values
    assert loaded_state.topic == "test topic"
    assert len(loaded_state.messages) == 0
    assert loaded_state.summary == ""
    assert loaded_state.turn == 0
    assert loaded_state.consensus_reached is False


def test_disk_based_discussion_manager_backup(sample_roles, temp_state_dir):
    """Test that backups are created when saving state."""
    manager = DiskBasedDiscussionManager("test topic", sample_roles, temp_state_dir)
    
    # Create and save multiple states
    for i in range(3):
        state = DiscussionState("test topic", sample_roles)
        state.add_message(Message("role1", f"Message {i}"))
        state.turn = i
        manager.save_state(state)
    
    # Check that backup files were created
    files = os.listdir(temp_state_dir)
    backup_files = [f for f in files if f.startswith("state_backup_")]
    
    # Should have at least 2 backup files (original gets renamed to backup)
    assert len(backup_files) >= 2


def test_discussion_state_add_multiple_messages(sample_roles):
    """Test adding multiple messages to the discussion state."""
    state = DiscussionState("test topic", sample_roles)
    
    # Add multiple messages
    messages = [
        Message("role1", "Message 1"),
        Message("role2", "Message 2"),
        Message("role1", "Message 3"),
        Message("role2", "Message 4")
    ]
    
    for message in messages:
        state.add_message(message)
    
    # Verify all messages were added
    assert len(state.messages) == 4
    assert state.messages[0].content == "Message 1"
    assert state.messages[1].content == "Message 2"
    assert state.messages[2].content == "Message 3"
    assert state.messages[3].content == "Message 4"


def test_discussion_state_get_messages_by_role(sample_roles):
    """Test getting messages by role."""
    state = DiscussionState("test topic", sample_roles)
    
    # Add messages from different roles
    state.add_message(Message("role1", "Message 1 from role1"))
    state.add_message(Message("role2", "Message 2 from role2"))
    state.add_message(Message("role1", "Message 3 from role1"))
    state.add_message(Message("role2", "Message 4 from role2"))
    state.add_message(Message("role1", "Message 5 from role1"))
    
    # Get messages by role
    role1_messages = state.get_messages_by_role("role1")
    role2_messages = state.get_messages_by_role("role2")
    
    # Verify correct messages were retrieved
    assert len(role1_messages) == 3
    assert all(msg.role == "role1" for msg in role1_messages)
    
    assert len(role2_messages) == 2
    assert all(msg.role == "role2" for msg in role2_messages)


def test_discussion_state_get_last_n_messages(sample_roles):
    """Test getting the last N messages."""
    state = DiscussionState("test topic", sample_roles)
    
    # Add multiple messages
    for i in range(10):
        state.add_message(Message(f"role{i%2+1}", f"Message {i}"))
    
    # Get last 5 messages
    last_messages = state.get_last_n_messages(5)
    
    # Verify correct messages were retrieved
    assert len(last_messages) == 5
    assert last_messages[0].content == "Message 5"
    assert last_messages[4].content == "Message 9"


def test_discussion_state_get_message_history(sample_roles):
    """Test getting formatted message history."""
    state = DiscussionState("test topic", sample_roles)
    
    # Add multiple messages
    state.add_message(Message("role1", "Hello, I'm role1"))
    state.add_message(Message("role2", "Hi, I'm role2"))
    state.add_message(Message("role1", "Let's discuss the topic"))
    
    # Get formatted history
    history = state.get_message_history()
    
    # Verify format
    assert len(history) == 3
    assert history[0]["role"] == "role1"
    assert history[0]["content"] == "Hello, I'm role1"
    assert history[1]["role"] == "role2"
    assert history[1]["content"] == "Hi, I'm role2"
    assert history[2]["role"] == "role1"
    assert history[2]["content"] == "Let's discuss the topic" 