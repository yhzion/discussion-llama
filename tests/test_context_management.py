import pytest
from unittest.mock import patch, MagicMock
from discussion_llama.role.role_manager import Role
from discussion_llama.engine.discussion_engine import (
    Message, 
    DiscussionState, 
    DiscussionEngine
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
def discussion_engine(sample_roles, tmp_path):
    """Create a discussion engine for testing."""
    return DiscussionEngine("test topic", sample_roles, str(tmp_path))


def test_prepare_context_empty_discussion(discussion_engine, sample_roles):
    """Test preparing context for an empty discussion."""
    # Prepare context for the first role
    context = discussion_engine.prepare_context(sample_roles[0])
    
    # Check that the context contains the expected fields
    assert "role" in context
    assert "topic" in context
    assert "full_context" in context
    assert "summary" in context
    
    # Check that the role and topic are correct
    assert context["role"] == sample_roles[0]
    assert context["topic"] == "test topic"
    
    # Check that the context is empty
    assert len(context["full_context"]) == 0
    assert context["summary"] == ""


def test_prepare_context_with_messages(discussion_engine, sample_roles):
    """Test preparing context with existing messages."""
    # Add some messages to the discussion
    for i in range(5):
        discussion_engine.state.add_message(Message(f"role{i%2+1}", f"Message {i}"))
    
    # Prepare context for the first role
    context = discussion_engine.prepare_context(sample_roles[0])
    
    # Check that the context contains all messages
    assert len(context["full_context"]) == 5
    assert context["full_context"][0].content == "Message 0"
    assert context["full_context"][4].content == "Message 4"


def test_prepare_context_with_many_messages(discussion_engine, sample_roles):
    """Test preparing context with many messages (exceeding context window)."""
    # Add many messages to the discussion
    for i in range(20):
        discussion_engine.state.add_message(Message(f"role{i%2+1}", f"Message {i}"))
    
    # Set a small context window size for testing
    discussion_engine.max_context_messages = 10
    
    # Prepare context for the first role
    context = discussion_engine.prepare_context(sample_roles[0])
    
    # Check that the context is limited to the most recent messages
    assert len(context["full_context"]) == 10
    assert context["full_context"][0].content == "Message 10"
    assert context["full_context"][9].content == "Message 19"
    
    # Check that the summary is not empty (should contain earlier messages)
    assert context["summary"] != ""


def test_compress_context(discussion_engine, sample_roles):
    """Test compressing the context when it gets too large."""
    # Add many messages to the discussion
    for i in range(20):
        discussion_engine.state.add_message(Message(f"role{i%2+1}", f"Message {i}"))
    
    # Set a small context window size for testing
    discussion_engine.max_context_messages = 10
    
    # Compress the context
    discussion_engine.compress_context()
    
    # Check that the state now has fewer messages
    assert len(discussion_engine.state.messages) == 10
    assert discussion_engine.state.messages[0].content == "Message 10"
    assert discussion_engine.state.messages[9].content == "Message 19"
    
    # Check that the summary is not empty
    assert discussion_engine.state.summary != ""


def test_generate_prompt(discussion_engine, sample_roles):
    """Test generating a prompt for a role."""
    # Add some messages to the discussion
    for i in range(3):
        discussion_engine.state.add_message(Message(f"role{i%2+1}", f"Message {i}"))
    
    # Generate a prompt for the first role
    prompt = discussion_engine.generate_prompt(sample_roles[0])
    
    # Check that the prompt contains the role description
    assert "You are a role1" in prompt
    assert "Test role 1" in prompt
    
    # Check that the prompt contains the topic
    assert "test topic" in prompt
    
    # Check that the prompt contains the messages
    assert "Message 0" in prompt
    assert "Message 1" in prompt
    assert "Message 2" in prompt


@patch('discussion_llama.engine.discussion_engine.DiscussionEngine._summarize_messages')
def test_summarize_messages_called(mock_summarize, discussion_engine, sample_roles):
    """Test that _summarize_messages is called when compressing context."""
    # Add many messages to the discussion
    for i in range(20):
        discussion_engine.state.add_message(Message(f"role{i%2+1}", f"Message {i}"))
    
    # Set a small context window size for testing
    discussion_engine.max_context_messages = 10
    
    # Mock the summarize method to return a fixed summary
    mock_summarize.return_value = "This is a summary of the discussion."
    
    # Compress the context
    discussion_engine.compress_context()
    
    # Check that _summarize_messages was called
    mock_summarize.assert_called_once()
    
    # Check that the summary was set
    assert discussion_engine.state.summary == "This is a summary of the discussion."


def test_context_with_summary(discussion_engine, sample_roles):
    """Test that the context includes the summary when available."""
    # Add some messages and set a summary
    for i in range(5):
        discussion_engine.state.add_message(Message(f"role{i%2+1}", f"Message {i}"))
    discussion_engine.state.summary = "This is a pre-existing summary."
    
    # Prepare context
    context = discussion_engine.prepare_context(sample_roles[0])
    
    # Check that the summary is included
    assert context["summary"] == "This is a pre-existing summary."


def test_token_counting(discussion_engine, sample_roles):
    """Test that token counting is considered when preparing context."""
    # Mock the token counting method to return a fixed number
    with patch('discussion_llama.engine.discussion_engine.DiscussionEngine._count_tokens', return_value=100):
        # Add many messages
        for i in range(20):
            discussion_engine.state.add_message(Message(f"role{i%2+1}", f"Message {i}"))
        
        # Set a token limit
        discussion_engine.max_tokens = 1000
        
        # Prepare context
        context = discussion_engine.prepare_context(sample_roles[0])
        
        # With each message at 100 tokens, we should get at most 10 messages
        assert len(context["full_context"]) <= 10


def test_context_with_role_specific_information(discussion_engine, sample_roles):
    """Test that the context includes role-specific information."""
    # Prepare context for each role
    context1 = discussion_engine.prepare_context(sample_roles[0])
    context2 = discussion_engine.prepare_context(sample_roles[1])
    
    # Check that each context has the correct role
    assert context1["role"] == sample_roles[0]
    assert context2["role"] == sample_roles[1]
    
    # Generate prompts for each role
    prompt1 = discussion_engine.generate_prompt(sample_roles[0])
    prompt2 = discussion_engine.generate_prompt(sample_roles[1])
    
    # Check that each prompt has role-specific information
    assert "You are a role1" in prompt1
    assert "Responsibility 1" in prompt1
    assert "Expertise 1" in prompt1
    
    assert "You are a role2" in prompt2
    assert "Responsibility 2" in prompt2
    assert "Expertise 2" in prompt2


def test_context_with_turn_information(discussion_engine, sample_roles):
    """Test that the context includes turn information."""
    # Set the turn number
    discussion_engine.state.turn = 5
    
    # Prepare context
    context = discussion_engine.prepare_context(sample_roles[0])
    
    # Check that the turn information is included
    prompt = discussion_engine.generate_prompt(sample_roles[0])
    assert "Turn 5" in prompt or "turn 5" in prompt.lower()


def test_context_with_consensus_information(discussion_engine, sample_roles):
    """Test that the context includes consensus information."""
    # Set consensus status
    discussion_engine.state.consensus_reached = True
    
    # Prepare context
    context = discussion_engine.prepare_context(sample_roles[0])
    
    # Check that the consensus information is included
    prompt = discussion_engine.generate_prompt(sample_roles[0])
    assert "consensus" in prompt.lower()
    assert "reached" in prompt.lower() 