import pytest
import json
from unittest.mock import patch, MagicMock
import requests
from discussion_llama.llm.llm_client import OllamaClient

# Test different model configurations
@pytest.mark.parametrize("model_name", [
    "llama2:7b-chat-q4_0",
    "mistral:7b-instruct-v0.2-q4_0",
    "gemma:7b-instruct-q4_0"
])
@patch('requests.post')
def test_ollama_client_different_models(mock_post, model_name):
    # Mock the response from Ollama
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": f"Response from {model_name}"}
    mock_post.return_value = mock_response
    
    client = OllamaClient(model=model_name)
    response = client.generate_response("test prompt")
    
    assert response == f"Response from {model_name}"
    mock_post.assert_called_once()
    
    # Check that the request was made with the correct model
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["model"] == model_name

@pytest.mark.parametrize("temperature", [0.1, 0.5, 0.7, 1.0])
@patch('requests.post')
def test_ollama_client_temperature(mock_post, temperature):
    # Mock the response from Ollama
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Test response"}
    mock_post.return_value = mock_response
    
    client = OllamaClient()
    response = client.generate_response("test prompt", temperature=temperature)
    
    # Check that the temperature was set correctly
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["options"]["temperature"] == temperature

@pytest.mark.parametrize("max_tokens", [100, 512, 1024, 2048])
@patch('requests.post')
def test_ollama_client_max_tokens(mock_post, max_tokens):
    # Mock the response from Ollama
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Test response"}
    mock_post.return_value = mock_response
    
    client = OllamaClient()
    response = client.generate_response("test prompt", max_tokens=max_tokens)
    
    # Check that the max_tokens was set correctly
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["options"]["num_predict"] == max_tokens

@patch('requests.post')
def test_ollama_client_custom_api_url(mock_post):
    # Mock the response from Ollama
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Test response"}
    mock_post.return_value = mock_response
    
    custom_url = "http://custom-ollama-server:11434"
    client = OllamaClient(api_url=custom_url)
    response = client.generate_response("test prompt")
    
    # Check that the request was made to the custom URL
    args, kwargs = mock_post.call_args
    assert args[0] == f"{custom_url}/api/generate"

@patch('requests.post')
def test_ollama_client_timeout_handling(mock_post):
    # Mock a timeout exception
    mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
    
    client = OllamaClient()
    response = client.generate_response("test prompt")
    
    assert "Error generating response" in response
    assert "Request timed out" in response

@patch('requests.post')
def test_ollama_client_connection_error(mock_post):
    # Mock a connection error
    mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
    
    client = OllamaClient()
    response = client.generate_response("test prompt")
    
    assert "Error generating response" in response
    assert "Connection refused" in response

@patch('requests.post')
def test_ollama_client_json_error(mock_post):
    # Mock a response with invalid JSON
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_post.return_value = mock_response
    
    client = OllamaClient()
    response = client.generate_response("test prompt")
    
    assert "Error generating response" in response
    assert "Invalid JSON" in response

# Test for handling rate limiting
@patch('requests.post')
def test_ollama_client_rate_limit(mock_post):
    # Mock a rate limit response
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Rate limit exceeded"
    mock_post.return_value = mock_response
    
    client = OllamaClient()
    response = client.generate_response("test prompt")
    
    assert "Error: 429" in response
    assert "Rate limit exceeded" in response 