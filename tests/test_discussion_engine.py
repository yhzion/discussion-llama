import os
import tempfile
import json
import pytest
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


def test_message_creation():
    message = Message("test_role", "Test message content")
    
    assert message.role == "test_role"
    assert message.content == "Test message content"
    assert message.metadata == {}
    assert message.timestamp is not None


def test_message_to_dict():
    message = Message("test_role", "Test message content", {"key": "value"})
    message_dict = message.to_dict()
    
    assert message_dict["role"] == "test_role"
    assert message_dict["content"] == "Test message content"
    assert message_dict["metadata"] == {"key": "value"}
    assert "timestamp" in message_dict


def test_message_from_dict():
    message_dict = {
        "role": "test_role",
        "content": "Test message content",
        "metadata": {"key": "value"},
        "timestamp": 1234567890.0
    }
    
    message = Message.from_dict(message_dict)
    
    assert message.role == "test_role"
    assert message.content == "Test message content"
    assert message.metadata == {"key": "value"}
    assert message.timestamp == 1234567890.0


def test_discussion_state(sample_roles):
    state = DiscussionState("test topic", sample_roles)
    
    assert state.topic == "test topic"
    assert len(state.roles) == 2
    assert state.messages == []
    assert state.summary == ""
    assert state.turn == 0
    assert state.consensus_reached is False


def test_discussion_state_add_message(sample_roles):
    state = DiscussionState("test topic", sample_roles)
    message = Message("role1", "Test message")
    
    state.add_message(message)
    
    assert len(state.messages) == 1
    assert state.messages[0].role == "role1"
    assert state.messages[0].content == "Test message"


def test_discussion_state_to_dict(sample_roles):
    state = DiscussionState("test topic", sample_roles)
    message = Message("role1", "Test message")
    state.add_message(message)
    
    state_dict = state.to_dict()
    
    assert state_dict["topic"] == "test topic"
    assert len(state_dict["roles"]) == 2
    assert len(state_dict["messages"]) == 1
    assert state_dict["messages"][0]["role"] == "role1"
    assert state_dict["turn"] == 0
    assert state_dict["consensus_reached"] is False


def test_disk_based_discussion_manager(sample_roles, temp_state_dir):
    manager = DiskBasedDiscussionManager("test topic", sample_roles, temp_state_dir)
    
    # Create a state
    state = DiscussionState("test topic", sample_roles)
    message = Message("role1", "Test message")
    state.add_message(message)
    
    # Save the state
    manager.save_state(state)
    
    # Check that the file was created
    assert os.path.exists(os.path.join(temp_state_dir, "state.json"))
    
    # Load the state
    loaded_state = manager.load_state()
    
    # Check that the loaded state matches the original
    assert loaded_state.topic == "test topic"
    assert len(loaded_state.messages) == 1
    assert loaded_state.messages[0].role == "role1"
    assert loaded_state.messages[0].content == "Test message"


def test_discussion_engine_initialization(sample_roles, temp_state_dir):
    engine = DiscussionEngine("test topic", sample_roles, temp_state_dir)
    
    assert engine.topic == "test topic"
    assert len(engine.roles) == 2
    assert engine.state is not None
    assert engine.max_turns == 30


def test_discussion_engine_prepare_context(sample_roles, temp_state_dir):
    engine = DiscussionEngine("test topic", sample_roles, temp_state_dir)
    
    # Add some messages
    for i in range(10):
        engine.state.add_message(Message(f"role{i%2+1}", f"Message {i}"))
    
    # Prepare context
    context = engine.prepare_context(sample_roles[0])
    
    # Check that we get the most recent messages
    assert len(context["full_context"]) == 6
    assert context["full_context"][0].content == "Message 4"
    assert context["full_context"][-1].content == "Message 9"
    assert context["summary"] != ""


def test_discussion_engine_compress_context(sample_roles, temp_state_dir):
    engine = DiscussionEngine("test topic", sample_roles, temp_state_dir)
    
    # Add some messages
    for i in range(10):
        engine.state.add_message(Message(f"role{i%2+1}", f"Message {i}"))
    
    # Compress context
    engine.compress_context()
    
    # Check that we kept only the most recent messages
    assert len(engine.state.messages) == 6
    assert engine.state.messages[0].content == "Message 4"
    assert engine.state.messages[-1].content == "Message 9"
    assert engine.state.summary != ""


def test_discussion_engine_run_discussion(sample_roles, temp_state_dir):
    engine = DiscussionEngine("test topic", sample_roles, temp_state_dir)
    engine.max_turns = 5  # Limit to 5 turns for testing
    
    # Run the discussion
    result = engine.run_discussion()
    
    # Check the result
    assert result["topic"] == "test topic"
    assert len(result["discussion"]) == 5
    assert result["consensus_reached"] is False
    assert result["turns"] == 5 