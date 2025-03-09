import pytest
import json
import time
from unittest.mock import patch, MagicMock, call
import requests
from discussion_llama.llm.llm_client import OllamaClient, EnhancedOllamaClient


@pytest.fixture
def mock_successful_response():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Test response"}
    return mock_response


@pytest.fixture
def mock_stream_response():
    class MockStreamResponse:
        def __init__(self, responses):
            self.status_code = 200
            self.responses = responses
            self.iter_index = 0
        
        def iter_lines(self):
            for resp in self.responses:
                yield json.dumps(resp).encode('utf-8')
    
    stream_data = [
        {"response": "This ", "done": False},
        {"response": "is ", "done": False},
        {"response": "a ", "done": False},
        {"response": "streamed ", "done": False},
        {"response": "response.", "done": True}
    ]
    
    return MockStreamResponse(stream_data)


class TestEnhancedOllamaClient:
    
    def test_init(self):
        client = EnhancedOllamaClient(
            model="llama2:7b-chat-q4_0",
            api_url="http://localhost:11434",
            max_retries=3,
            retry_delay=1.0,
            timeout=30
        )
        
        assert client.model == "llama2:7b-chat-q4_0"
        assert client.api_url == "http://localhost:11434"
        assert client.max_retries == 3
        assert client.retry_delay == 1.0
        assert client.timeout == 30
    
    @patch('requests.post')
    def test_generate_response_success(self, mock_post, mock_successful_response):
        mock_post.return_value = mock_successful_response
        
        client = EnhancedOllamaClient()
        response = client.generate_response("test prompt")
        
        assert response == "Test response"
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_generate_response_with_retry(self, mock_post):
        # First call fails with a 500 error, second call succeeds
        mock_error_response = MagicMock()
        mock_error_response.status_code = 500
        mock_error_response.text = "Internal Server Error"
        
        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"response": "Success after retry"}
        
        mock_post.side_effect = [mock_error_response, mock_success_response]
        
        client = EnhancedOllamaClient(max_retries=3, retry_delay=0.1)
        response = client.generate_response("test prompt")
        
        assert response == "Success after retry"
        assert mock_post.call_count == 2
    
    @patch('requests.post')
    def test_generate_response_max_retries_exceeded(self, mock_post):
        # All calls fail with a 500 error
        mock_error_response = MagicMock()
        mock_error_response.status_code = 500
        mock_error_response.text = "Internal Server Error"
        
        mock_post.return_value = mock_error_response
        
        client = EnhancedOllamaClient(max_retries=3, retry_delay=0.1)
        response = client.generate_response("test prompt")
        
        assert "Error: 500" in response
        assert "Internal Server Error" in response
        assert mock_post.call_count == 4  # Initial attempt + 3 retries
    
    @patch('requests.post')
    def test_generate_response_timeout(self, mock_post):
        # Mock a timeout exception
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        client = EnhancedOllamaClient(max_retries=2, retry_delay=0.1)
        response = client.generate_response("test prompt")
        
        assert "Error generating response" in response
        assert "Request timed out" in response
        assert mock_post.call_count == 3  # Initial attempt + 2 retries
    
    @patch('requests.post')
    def test_generate_streaming_response(self, mock_post, mock_stream_response):
        mock_post.return_value = mock_stream_response
        
        client = EnhancedOllamaClient()
        response = client.generate_streaming_response("test prompt")
        
        assert response == "This is a streamed response."
    
    @patch('requests.post')
    def test_generate_streaming_response_with_callback(self, mock_post, mock_stream_response):
        mock_post.return_value = mock_stream_response
        
        collected_chunks = []
        
        def callback(chunk):
            collected_chunks.append(chunk)
        
        client = EnhancedOllamaClient()
        response = client.generate_streaming_response("test prompt", callback=callback)
        
        assert response == "This is a streamed response."
        assert collected_chunks == ["This ", "is ", "a ", "streamed ", "response."]
    
    @patch('requests.post')
    def test_generate_streaming_response_error(self, mock_post):
        # Mock an error response
        mock_error_response = MagicMock()
        mock_error_response.status_code = 500
        mock_error_response.text = "Internal Server Error"
        
        mock_post.return_value = mock_error_response
        
        client = EnhancedOllamaClient()
        response = client.generate_streaming_response("test prompt")
        
        assert "Error: 500" in response
        assert "Internal Server Error" in response
    
    @patch('time.sleep')
    @patch('requests.post')
    def test_exponential_backoff(self, mock_post, mock_sleep):
        # All calls fail with a 429 rate limit error
        mock_error_response = MagicMock()
        mock_error_response.status_code = 429
        mock_error_response.text = "Rate limit exceeded"
        
        mock_post.return_value = mock_error_response
        
        client = EnhancedOllamaClient(max_retries=3, retry_delay=1.0)
        response = client.generate_response("test prompt")
        
        assert "Error: 429" in response
        assert "Rate limit exceeded" in response
        assert mock_post.call_count == 4  # Initial attempt + 3 retries
        
        # Check that sleep was called with exponential backoff
        mock_sleep.assert_has_calls([
            call(1.0),  # First retry
            call(2.0),  # Second retry
            call(4.0)   # Third retry
        ]) 