import requests
from typing import Dict, Any, Optional, List, Callable
import re
import time
import json


class LLMClient:
    """
    Client for interacting with Language Models.
    This is a base class that should be extended for specific LLM providers.
    """
    def __init__(self):
        pass
    
    def generate_response(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Generate a response from the LLM.
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement generate_response")


class OllamaClient(LLMClient):
    """
    Client for interacting with Ollama LLMs.
    """
    def __init__(self, model: str = "llama2:7b-chat-q4_0", api_url: str = "http://localhost:11434"):
        super().__init__()
        self.model = model
        self.api_url = api_url
    
    def generate_response(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Generate a response from Ollama.
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                        "top_p": 0.9,
                        "context_size": 2048  # Context size limit
                    }
                }
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                return f"Error: {response.status_code}, {response.text}"
        except Exception as e:
            return f"Error generating response: {str(e)}"


class EnhancedOllamaClient(OllamaClient):
    """
    Enhanced client for interacting with Ollama LLMs.
    Includes retry mechanism, streaming support, and better error handling.
    """
    def __init__(
        self, 
        model: str = "llama2:7b-chat-q4_0", 
        api_url: str = "http://localhost:11434",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 30
    ):
        super().__init__(model, api_url)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
    
    def generate_response(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Generate a response from Ollama with retry mechanism.
        """
        retries = 0
        while True:
            try:
                response = requests.post(
                    f"{self.api_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": temperature,
                            "top_p": 0.9,
                            "context_size": 2048  # Context size limit
                        }
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json()["response"]
                elif response.status_code == 429:  # Rate limit
                    if retries < self.max_retries:
                        wait_time = self.retry_delay * (2 ** retries)  # Exponential backoff
                        time.sleep(wait_time)
                        retries += 1
                        continue
                    else:
                        return f"Error: {response.status_code}, {response.text}"
                else:
                    if retries < self.max_retries:
                        time.sleep(self.retry_delay)
                        retries += 1
                        continue
                    else:
                        return f"Error: {response.status_code}, {response.text}"
            
            except requests.exceptions.Timeout:
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
                    retries += 1
                    continue
                else:
                    return f"Error generating response: Request timed out after {self.timeout} seconds"
            
            except requests.exceptions.ConnectionError as e:
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
                    retries += 1
                    continue
                else:
                    return f"Error generating response: Connection error - {str(e)}"
            
            except Exception as e:
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
                    retries += 1
                    continue
                else:
                    return f"Error generating response: {str(e)}"
    
    def generate_streaming_response(
        self, 
        prompt: str, 
        max_tokens: int = 512, 
        temperature: float = 0.7,
        callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Generate a streaming response from Ollama.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            callback: Optional callback function that receives each chunk of text
            
        Returns:
            The complete generated text
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                        "top_p": 0.9,
                        "context_size": 2048  # Context size limit
                    }
                },
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code != 200:
                return f"Error: {response.status_code}, {response.text}"
            
            # Process the streaming response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        chunk_data = json.loads(line.decode('utf-8'))
                        chunk_text = chunk_data.get("response", "")
                        full_response += chunk_text
                        
                        if callback:
                            callback(chunk_text)
                        
                        if chunk_data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
            
            return full_response
        
        except Exception as e:
            return f"Error generating streaming response: {str(e)}"


class MockLLMClient(LLMClient):
    """
    Mock LLM client for testing purposes.
    """
    def __init__(self, responses: Optional[Dict[str, str]] = None, **kwargs):
        super().__init__()
        self.responses = responses or {}
        self.default_response = "This is a mock response from the LLM."
        # 추가 매개변수 무시 (model 등)
        
        # 역할별 기본 응답 설정
        self.role_responses = {
            "Security Engineer": {
                "authentication": """
As a Security Engineer, I recommend implementing a multi-factor authentication (MFA) system with the following components:

1. Strong password requirements (minimum length, complexity)
2. Time-based one-time passwords (TOTP) as a second factor
3. Rate limiting to prevent brute force attacks
4. Account lockout after multiple failed attempts
5. Secure password storage using bcrypt or Argon2 with proper salting
6. HTTPS for all authentication endpoints
7. Session management with secure, HttpOnly cookies
8. Regular security audits and penetration testing

We should also implement proper logging for all authentication attempts to detect suspicious activities.
                """,
                "consensus": """
As a Security Engineer, I agree with the approach outlined by both the Backend Developer and Product Owner. 

I support the use of JWT for stateless authentication and OAuth 2.0 for third-party integration. The dedicated authentication microservice will help isolate security concerns, and Redis for rate limiting aligns with my recommendation.

I also concur with the Product Owner that we need to balance security with user experience. Making MFA optional but strongly encouraged is a good compromise, and supporting biometric authentication for mobile is an excellent addition.

We have reached a good consensus on the core components of our authentication system, combining strong security practices with a user-friendly approach.
                """
            },
            "Backend Developer": {
                "authentication": """
From a Backend Developer perspective, I would implement the authentication system using:

1. JWT (JSON Web Tokens) for stateless authentication
2. OAuth 2.0 for third-party authentication if needed
3. A dedicated authentication microservice
4. Redis for session storage and rate limiting
5. Database encryption for sensitive user data
6. Proper error handling that doesn't reveal sensitive information
7. Input validation and sanitization to prevent injection attacks

I'll work closely with the Security Engineer to ensure we follow best practices for password hashing and storage.
                """,
                "consensus": """
As a Backend Developer, I agree with both the Security Engineer and Product Owner on our authentication approach.

I support implementing the strong security measures recommended by the Security Engineer, including MFA, rate limiting, and secure password storage. These align well with my proposed JWT and OAuth implementation.

I also concur with the Product Owner's focus on user experience. We can implement the social login options alongside our email/password system, and the password recovery flow is an essential feature I'll prioritize.

We seem to have reached a consensus on balancing security with usability, creating a system that's both secure and user-friendly.
                """
            },
            "Product Owner": {
                "authentication": """
As the Product Owner, I want to balance security with user experience in our authentication system:

1. We should offer both email/password and social login options
2. The MFA should be optional but strongly encouraged
3. We need a clear password recovery flow
4. User onboarding should explain security features
5. Analytics should track authentication success/failure rates
6. We should implement progressive security based on user behavior and risk assessment
7. Mobile app should support biometric authentication

I agree with the security recommendations but want to ensure we don't create too much friction for users.
                """,
                "consensus": """
As the Product Owner, I'm pleased to see we've reached a consensus on our authentication system approach.

I agree with the Security Engineer's recommendations for strong security measures, including MFA and proper password storage. These are essential for protecting our users' data.

I also support the Backend Developer's technical implementation choices, particularly the JWT approach and dedicated authentication microservice, which will provide both security and scalability.

We've found common ground in balancing security with usability, offering multiple authentication options while maintaining strong protection. This consensus gives us a clear direction for implementation that meets both security requirements and user needs.
                """
            },
            "Frontend Developer": {
                "authentication": """
As a Frontend Developer, I'll focus on implementing:

1. Clean and intuitive login/registration forms
2. Client-side validation for immediate feedback
3. Clear error messages without revealing sensitive information
4. Secure storage of tokens in memory or secure storage
5. Automatic session refresh mechanisms
6. Loading states and error handling for authentication flows
7. Responsive design for authentication on all devices
8. Accessibility compliance for all authentication interfaces

I'll work with the UX team to ensure the authentication flow is seamless while maintaining security.
                """,
                "consensus": """
As a Frontend Developer, I agree with the approach outlined by the team.

I support the Security Engineer's recommendations for MFA and secure session management, which I'll implement in the frontend with proper token handling and secure storage.

I concur with the Backend Developer's JWT approach, which works well with modern frontend frameworks, and I'll ensure our client-side implementation integrates seamlessly with the authentication microservice.

I also agree with the Product Owner's focus on user experience. I'll implement the social login options and biometric authentication for mobile, ensuring the interface is intuitive while maintaining security.

We've reached a good consensus that balances security requirements with a smooth user experience.
                """
            },
            "Technical Architect": {
                "authentication": """
From an architectural perspective, I recommend:

1. Implementing an identity provider service separate from the main application
2. Using OpenID Connect for authentication and authorization
3. Implementing a token-based architecture with short-lived access tokens and longer refresh tokens
4. Designing for horizontal scalability of the authentication services
5. Planning for future authentication methods (biometrics, WebAuthn)
6. Ensuring cross-service authentication with proper API gateway integration
7. Implementing proper key management and rotation policies

This approach will give us flexibility while maintaining security and performance.
                """,
                "consensus": """
As the Technical Architect, I believe we've reached a consensus on our authentication system architecture.

I agree with the Security Engineer's focus on MFA and secure storage, which aligns with my recommendation for a robust identity provider service.

I support the Backend Developer's proposal for JWT and a dedicated authentication microservice, which fits perfectly with my token-based architecture recommendation.

I also concur with the Product Owner's emphasis on user experience and multiple authentication options, which our architecture can accommodate through OpenID Connect and support for various authentication methods.

We have found common ground that satisfies our security requirements, technical implementation needs, and user experience goals.
                """
            }
        }
    
    def generate_response(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Generate a mock response.
        """
        # Check if we have a predefined response for this prompt
        for key, response in self.responses.items():
            if key in prompt:
                return response
        
        # 이전 메시지 수 확인 (합의 응답 생성 여부 결정)
        message_count = prompt.count("[")  # 대략적인 메시지 수 추정
        
        # 특정 턴 이후에는 합의 응답 생성
        use_consensus = message_count >= 4  # 최소 2턴(4개 메시지) 이후 합의 응답 생성
        
        # Try to determine the role from the prompt
        role = None
        
        # 프롬프트에서 "You are a [Role]" 패턴 찾기
        role_match = re.search(r"You are a ([^\.]+)", prompt)
        if role_match:
            role_name = role_match.group(1).strip()
            # 정확한 역할 이름 찾기
            for known_role in self.role_responses.keys():
                if role_name in known_role or known_role in role_name:
                    role = known_role
                    break
        
        # 역할을 찾지 못했다면 프롬프트 전체에서 찾기
        if not role:
            for role_name in self.role_responses.keys():
                if role_name in prompt:
                    role = role_name
                    break
        
        # 주제 키워드 찾기
        topic_keyword = "authentication" if "authentication" in prompt.lower() else None
        
        # 역할과 주제를 모두 찾았다면 해당 응답 반환
        if role and topic_keyword:
            if use_consensus and "consensus" in self.role_responses[role]:
                return self.role_responses[role]["consensus"].strip()
            elif topic_keyword in self.role_responses[role]:
                return self.role_responses[role][topic_keyword].strip()
        
        # 역할만 찾았다면 해당 역할의 첫 번째 응답 반환
        if role and self.role_responses[role]:
            if use_consensus and "consensus" in self.role_responses[role]:
                return self.role_responses[role]["consensus"].strip()
            else:
                first_topic = next(iter(self.role_responses[role]))
                return self.role_responses[role][first_topic].strip()
        
        # Otherwise return the default response
        return self.default_response


def create_llm_client(client_type: str = "mock", **kwargs) -> LLMClient:
    """
    Create an LLM client based on the specified type.
    
    Args:
        client_type: Type of client to create ("mock", "ollama", or "enhanced_ollama")
        **kwargs: Additional arguments to pass to the client constructor
        
    Returns:
        An instance of LLMClient
        
    Raises:
        ValueError: If the client_type is not recognized
    """
    if client_type == "mock":
        return MockLLMClient(**kwargs)
    elif client_type == "ollama":
        return OllamaClient(**kwargs)
    elif client_type == "enhanced_ollama":
        return EnhancedOllamaClient(**kwargs)
    else:
        raise ValueError(f"Unknown client type: {client_type}") 