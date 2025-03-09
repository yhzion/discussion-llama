import os
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock
import argparse
from discussion_llama.cli.cli import run_discussion, format_message


def test_format_message():
    message = {"role": "test_role", "content": "Test message content"}
    formatted = format_message(message)
    
    assert formatted == "[test_role]: Test message content"
    
    # Test with missing fields
    message = {"content": "Test message content"}
    formatted = format_message(message)
    
    assert formatted == "[Unknown]: Test message content"
    
    message = {"role": "test_role"}
    formatted = format_message(message)
    
    assert formatted == "[test_role]: "


@patch('discussion_llama.cli.cli.RoleManager')
@patch('discussion_llama.cli.cli.create_llm_client')
@patch('discussion_llama.cli.cli.ConsensusDetector')
@patch('discussion_llama.cli.cli.DiscussionEngine')
def test_run_discussion(mock_engine_class, mock_detector_class, mock_create_llm, mock_role_manager_class):
    # Create mock objects
    mock_role_manager = MagicMock()
    mock_role_manager_class.return_value = mock_role_manager
    
    mock_role1 = MagicMock()
    mock_role1.role = "role1"
    mock_role2 = MagicMock()
    mock_role2.role = "role2"
    
    mock_role_manager.get_role.side_effect = lambda role: {"role1": mock_role1, "role2": mock_role2}.get(role)
    mock_role_manager.select_roles_for_discussion.return_value = [mock_role1, mock_role2]
    
    mock_llm_client = MagicMock()
    mock_create_llm.return_value = mock_llm_client
    
    mock_detector = MagicMock()
    mock_detector_class.return_value = mock_detector
    
    mock_engine = MagicMock()
    mock_engine_class.return_value = mock_engine
    
    # Mock the discussion result
    mock_engine.run_discussion.return_value = {
        "topic": "test topic",
        "discussion": [
            {"role": "role1", "content": "Message 1"},
            {"role": "role2", "content": "Message 2"}
        ],
        "consensus_reached": True,
        "turns": 2
    }
    
    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "output.json")
        
        # Create args
        args = argparse.Namespace(
            topic="test topic",
            roles_dir="./roles",
            roles="role1,role2",
            num_roles=3,
            max_turns=30,
            state_dir="./discussion_state",
            llm_client="mock",
            model="llama2:7b-chat-q4_0",
            output=output_file
        )
        
        # Run the discussion
        run_discussion(args)
        
        # Check that the role manager was initialized correctly
        mock_role_manager_class.assert_called_once_with("./roles")
        
        # Check that the roles were selected correctly
        mock_role_manager.get_role.assert_any_call("role1")
        mock_role_manager.get_role.assert_any_call("role2")
        
        # Check that the LLM client was created correctly
        mock_create_llm.assert_called_once_with("mock", model="llama2:7b-chat-q4_0")
        
        # Check that the consensus detector was created correctly
        mock_detector_class.assert_called_once_with(mock_llm_client)
        
        # Check that the discussion engine was created correctly
        mock_engine_class.assert_called_once_with("test topic", [mock_role1, mock_role2], "./discussion_state")
        
        # Check that the discussion was run
        mock_engine.run_discussion.assert_called_once()
        
        # Check that the output file was created
        assert os.path.exists(output_file)
        
        # Check the content of the output file
        with open(output_file, "r") as f:
            output = json.load(f)
            assert output["topic"] == "test topic"
            assert len(output["discussion"]) == 2
            assert output["consensus_reached"] is True
            assert output["turns"] == 2


@patch('discussion_llama.cli.cli.RoleManager')
def test_run_discussion_no_roles(mock_role_manager_class):
    # Create mock objects
    mock_role_manager = MagicMock()
    mock_role_manager_class.return_value = mock_role_manager
    
    # Mock that no roles are found
    mock_role_manager.get_role.return_value = None
    mock_role_manager.select_roles_for_discussion.return_value = []
    
    # Create args
    args = argparse.Namespace(
        topic="test topic",
        roles_dir="./roles",
        roles="role1,role2",
        num_roles=3,
        max_turns=30,
        state_dir="./discussion_state",
        llm_client="mock",
        model="llama2:7b-chat-q4_0",
        output=None
    )
    
    # Run the discussion
    run_discussion(args)
    
    # Check that the role manager was initialized correctly
    mock_role_manager_class.assert_called_once_with("./roles")
    
    # Check that the roles were selected correctly
    mock_role_manager.get_role.assert_any_call("role1")
    mock_role_manager.get_role.assert_any_call("role2") 