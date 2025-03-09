import pytest
import requests
import time
from discussion_llama.llm import EnhancedOllamaClient

# Check if Ollama server is available
def is_ollama_available():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

# Skip all tests if Ollama is not available
pytestmark = pytest.mark.skipif(
    not is_ollama_available(),
    reason="Ollama server is not available at http://localhost:11434"
)


@pytest.fixture(scope="module")
def ollama_client():
    return EnhancedOllamaClient(
        model="llama2:7b-chat-q4_0",  # Use a model that's likely to be available
        max_retries=2,
        retry_delay=1.0,
        timeout=30
    )


class TestRealOllamaIntegration:
    
    def test_basic_response_generation(self, ollama_client):
        """Test that we can generate a basic response from Ollama."""
        prompt = "What is the capital of France?"
        response = ollama_client.generate_response(prompt, max_tokens=100)
        
        # Check that we got a non-error response
        assert not response.startswith("Error")
        # The response should mention Paris
        assert "Paris" in response
    
    def test_streaming_response(self, ollama_client):
        """Test that streaming response works."""
        prompt = "Count from 1 to 5."
        
        chunks = []
        def collect_chunk(chunk):
            chunks.append(chunk)
        
        response = ollama_client.generate_streaming_response(
            prompt, 
            max_tokens=100,
            callback=collect_chunk
        )
        
        # Check that we got a non-error response
        assert not response.startswith("Error")
        # Check that we received multiple chunks
        assert len(chunks) > 1
        # The full response should be the concatenation of all chunks
        assert "".join(chunks) == response
        # The response should contain the numbers 1 through 5
        for num in range(1, 6):
            assert str(num) in response
    
    def test_temperature_affects_output(self, ollama_client):
        """Test that different temperature values produce different outputs."""
        prompt = "Write a short poem about AI."
        
        # Generate two responses with different temperatures
        response1 = ollama_client.generate_response(prompt, temperature=0.1, max_tokens=100)
        time.sleep(1)  # Add a small delay to ensure different seeds
        response2 = ollama_client.generate_response(prompt, temperature=1.0, max_tokens=100)
        
        # The responses should be different
        assert response1 != response2
    
    def test_retry_mechanism(self, ollama_client):
        """
        Test that the retry mechanism works.
        This is a bit tricky to test with a real server, so we'll just verify
        that a normal request succeeds.
        """
        prompt = "Hello, how are you?"
        response = ollama_client.generate_response(prompt, max_tokens=50)
        
        # Check that we got a non-error response
        assert not response.startswith("Error")
        assert len(response) > 0 