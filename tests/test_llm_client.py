import pytest
from unittest.mock import patch, MagicMock
from discussion_llama.llm.llm_client import (
    LLMClient,
    MockLLMClient,
    OllamaClient,
    create_llm_client
)


def test_llm_client_base_class():
    client = LLMClient()
    
    # The base class should raise NotImplementedError
    with pytest.raises(NotImplementedError):
        client.generate_response("test prompt")


def test_mock_llm_client():
    # Test with default response
    client = MockLLMClient()
    response = client.generate_response("test prompt")
    
    assert response == "This is a mock response from the LLM."
    
    # Test with custom responses
    client = MockLLMClient({
        "hello": "Hello, world!",
        "test": "This is a test response."
    })
    
    response = client.generate_response("hello there")
    assert response == "Hello, world!"
    
    response = client.generate_response("this is a test")
    assert response == "This is a test response."
    
    # Test with prompt that doesn't match any predefined responses
    response = client.generate_response("something else")
    assert response == "This is a mock response from the LLM."


@patch('requests.post')
def test_ollama_client_success(mock_post):
    # Mock the response from Ollama
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "This is a response from Ollama."}
    mock_post.return_value = mock_response
    
    client = OllamaClient()
    response = client.generate_response("test prompt")
    
    assert response == "This is a response from Ollama."
    mock_post.assert_called_once()
    
    # Check that the request was made with the correct parameters
    args, kwargs = mock_post.call_args
    assert args[0] == "http://localhost:11434/api/generate"
    assert kwargs["json"]["model"] == "llama2:7b-chat-q4_0"
    assert kwargs["json"]["prompt"] == "test prompt"
    assert kwargs["json"]["options"]["num_predict"] == 512
    assert kwargs["json"]["options"]["temperature"] == 0.7


@patch('requests.post')
def test_ollama_client_error(mock_post):
    # Mock an error response from Ollama
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response
    
    client = OllamaClient()
    response = client.generate_response("test prompt")
    
    assert "Error: 500" in response
    assert "Internal Server Error" in response


@patch('requests.post')
def test_ollama_client_exception(mock_post):
    # Mock an exception when making the request
    mock_post.side_effect = Exception("Connection error")
    
    client = OllamaClient()
    response = client.generate_response("test prompt")
    
    assert "Error generating response" in response
    assert "Connection error" in response


def test_create_llm_client():
    # Test creating a mock client
    client = create_llm_client("mock")
    assert isinstance(client, MockLLMClient)
    
    # Test creating an Ollama client
    client = create_llm_client("ollama", model="mistral:7b-instruct-v0.2-q4_0")
    assert isinstance(client, OllamaClient)
    assert client.model == "mistral:7b-instruct-v0.2-q4_0"
    
    # Test with unknown client type
    with pytest.raises(ValueError):
        create_llm_client("unknown") 