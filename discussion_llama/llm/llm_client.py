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
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text.
        Returns 'ko' for Korean, 'en' for English, or 'other'.
        """
        # Simple heuristic for Korean detection
        # Check for Korean Unicode range (AC00-D7A3 for Hangul syllables)
        korean_pattern = re.compile(r'[\uac00-\ud7a3]')
        if korean_pattern.search(text):
            return 'ko'
        
        # Simple heuristic for English detection
        english_pattern = re.compile(r'[a-zA-Z]')
        if english_pattern.search(text):
            return 'en'
        
        return 'other'
    
    def prepare_prompt_for_language(self, prompt: str, language: Optional[str] = None) -> str:
        """
        Prepare a prompt with appropriate language instructions.
        If language is not provided, it will be auto-detected.
        """
        if language is None:
            language = self.detect_language(prompt)
        
        if language == 'ko':
            # Add Korean language instruction to the prompt
            return f"다음 내용에 한국어로 응답해주세요. 자연스러운 한국어를 사용하세요.\n\n{prompt}"
        
        return prompt


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
        # Detect language and prepare prompt with appropriate instructions
        language = self.detect_language(prompt)
        prepared_prompt = self.prepare_prompt_for_language(prompt, language)
        
        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prepared_prompt,
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
    Enhanced client for Ollama with additional features like retries and streaming.
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
        Generate a response from Ollama with retry logic.
        """
        # Detect language and prepare prompt with appropriate instructions
        language = self.detect_language(prompt)
        prepared_prompt = self.prepare_prompt_for_language(prompt, language)
        
        retries = 0
        while retries <= self.max_retries:
            try:
                response = requests.post(
                    f"{self.api_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prepared_prompt,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": temperature,
                            "top_p": 0.9,
                            "context_size": 2048
                        }
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        return result.get("response", "")
                    except json.JSONDecodeError:
                        if retries == self.max_retries:
                            return f"Error: Invalid JSON response from Ollama API"
                else:
                    if retries == self.max_retries:
                        return f"Error: Ollama API returned status code {response.status_code}"
            
            except requests.exceptions.Timeout:
                if retries == self.max_retries:
                    return f"Error: Ollama API request timed out after {self.timeout} seconds"
            except requests.exceptions.ConnectionError:
                if retries == self.max_retries:
                    return f"Error: Could not connect to Ollama API at {self.api_url}"
            except Exception as e:
                if retries == self.max_retries:
                    return f"Error: {str(e)}"
            
            retries += 1
            time.sleep(self.retry_delay * (2 ** (retries - 1)))  # Exponential backoff
        
        return "Error: Maximum retries exceeded"
    
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
            prompt: The prompt to send to the LLM
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for response generation
            callback: Optional callback function that receives each chunk of the response
            
        Returns:
            The complete generated response as a string
        """
        # Detect language and prepare prompt with appropriate instructions
        language = self.detect_language(prompt)
        prepared_prompt = self.prepare_prompt_for_language(prompt, language)
        
        full_response = ""
        
        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prepared_prompt,
                    "stream": True,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                        "top_p": 0.9,
                        "context_size": 2048
                    }
                },
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line)
                            chunk = chunk_data.get("response", "")
                            full_response += chunk
                            
                            if callback:
                                callback(chunk)
                        except json.JSONDecodeError:
                            continue
            else:
                error_msg = f"Error: Ollama API returned status code {response.status_code}"
                if callback:
                    callback(error_msg)
                return error_msg
                
        except requests.exceptions.Timeout:
            error_msg = f"Error: Ollama API request timed out after {self.timeout} seconds"
            if callback:
                callback(error_msg)
            return error_msg
        except requests.exceptions.ConnectionError:
            error_msg = f"Error: Could not connect to Ollama API at {self.api_url}"
            if callback:
                callback(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            if callback:
                callback(error_msg)
            return error_msg
        
        return full_response


class MockLLMClient(LLMClient):
    """
    Mock LLM client for testing purposes.
    """
    def __init__(self, responses: Optional[Dict[str, str]] = None, **kwargs):
        super().__init__()
        self.default_responses = {
            "hello": "Hello! How can I help you today?",
            "안녕": "안녕하세요! 오늘 어떻게 도와드릴까요?",
            "introduce yourself": "I am an AI assistant designed to help with various tasks.",
            "자기소개": "저는 다양한 작업을 도와주기 위해 설계된 AI 어시스턴트입니다.",
            "what is your name": "I am a language model and don't have a personal name.",
            "이름이 뭐야": "저는 언어 모델이라 개인적인 이름은 없습니다.",
            "tell me a joke": "Why don't scientists trust atoms? Because they make up everything!",
            "농담 해줘": "왜 과학자들이 원자를 믿지 않을까요? 모든 것을 구성하기 때문이죠!",
            "what time is it": "I don't have access to real-time information like the current time.",
            "지금 몇 시야": "저는 현재 시간과 같은 실시간 정보에 접근할 수 없습니다.",
            "thank you": "You're welcome! Is there anything else I can help with?",
            "고마워": "천만에요! 제가 도와드릴 다른 일이 있을까요?",
            "goodbye": "Goodbye! Have a great day!",
            "안녕히 가세요": "안녕히 가세요! 좋은 하루 되세요!",
            "help": "I can help with answering questions, providing information, and more.",
            "도움": "질문에 답하고, 정보를 제공하는 등의 도움을 드릴 수 있습니다.",
            "weather": "I don't have access to real-time weather information.",
            "날씨": "저는 실시간 날씨 정보에 접근할 수 없습니다.",
            "who are you": "I am an AI language model designed to assist with various tasks.",
            "너는 누구야": "저는 다양한 작업을 지원하도록 설계된 AI 언어 모델입니다."
        }
        
        # 양자역학 교육용 소프트웨어 개발에 대한 역할별 응답
        self.quantum_education_responses = {
            "UI/UX Designer": [
                "양자역학 개념은 복잡하니까 시각화 도구가 중요해요. 사용자가 직관적으로 이해할 수 있게 인터페이스를 단순화해야 해요.",
                "학생들의 연령대별로 다른 UI가 필요할 것 같아요. 고등학생과 대학생용 모드를 따로 만들면 어떨까요?",
                "게이미피케이션 요소를 추가하면 학습 동기 부여에 도움이 될 것 같아요. 퀴즈나 도전 과제 같은 기능은 어떨까요?",
                "인터랙티브 시각화가 핵심이에요. 사용자가 직접 파라미터를 조정하면서 결과를 볼 수 있어야 해요.",
                "접근성도 고려해야 해요. 색맹이나 다른 장애가 있는 학생들도 사용할 수 있어야 하니까요.",
                "모바일 환경도 지원하면 좋겠어요. 학생들이 이동 중에도 학습할 수 있으니까요.",
                "사용자 피드백을 수집하는 기능도 필요해요. 어떤 부분이 이해하기 어려운지 데이터를 모을 수 있으면 좋겠어요."
            ],
            "DevOps Engineer": [
                "이런 교육용 소프트웨어는 학교 컴퓨터실 환경에서도 잘 돌아가야 해요. 시스템 요구사항을 최소화하는 게 중요해요.",
                "클라우드 기반으로 구축하면 업데이트와 배포가 쉬워질 거예요. 학교마다 설치 과정이 복잡하면 사용률이 떨어질 수 있어요.",
                "오프라인 모드도 지원해야 할 것 같아요. 인터넷 연결이 불안정한 환경도 고려해야죠.",
                "자동화된 테스트 환경이 필요해요. 새 기능을 추가할 때마다 기존 기능이 망가지지 않도록 해야죠.",
                "컨테이너화를 고려해보세요. Docker로 패키징하면 다양한 환경에서 일관되게 실행할 수 있어요.",
                "모니터링 시스템도 구축해야 해요. 사용자가 많아지면 성능 이슈가 생길 수 있으니까요.",
                "백업 및 복구 시스템도 중요해요. 학생들의 학습 데이터가 손실되지 않도록 해야죠."
            ],
            "Technical Architect / Lead Developer": [
                "양자역학 시뮬레이션은 계산량이 많아서 성능 최적화가 중요해요. 복잡한 계산은 서버 측에서 처리하는 구조가 좋겠어요.",
                "모듈식 설계가 필요해요. 기초 개념부터 고급 내용까지 단계별로 확장할 수 있는 구조로 만들어야 해요.",
                "오픈소스 라이브러리를 활용하면 개발 시간을 단축할 수 있을 거예요. Python의 QuTiP 같은 라이브러리가 도움될 것 같아요.",
                "마이크로서비스 아키텍처를 고려해볼 만해요. 기능별로 분리하면 확장성이 좋아질 거예요.",
                "데이터베이스 설계도 중요해요. 학습 데이터를 효율적으로 저장하고 분석할 수 있어야 해요.",
                "API 설계를 표준화하면 좋겠어요. 나중에 모바일 앱이나 다른 시스템과 연동하기 쉬워질 거예요.",
                "보안 아키텍처도 초기부터 고려해야 해요. 학생 데이터를 안전하게 보호할 수 있어야 하니까요."
            ]
        }
        
        # Role-specific responses for testing
        self.role_responses = {
            "Software Engineer": {
                "default": "코드 품질이 중요하다고 생각해요. 유지보수가 쉬운 코드를 작성해야 사용자 경험도 좋아질 거예요.",
                "기본": "코드 품질이 중요하다고 생각해요. 유지보수가 쉬운 코드를 작성해야 사용자 경험도 좋아질 거예요."
            },
            "Product Manager": {
                "default": "사용자 요구사항을 우선시해야 해요. 시장 조사 결과를 보면 이 기능이 꼭 필요하다고 나왔어요.",
                "기본": "사용자 요구사항을 우선시해야 해요. 시장 조사 결과를 보면 이 기능이 꼭 필요하다고 나왔어요."
            },
            "UI/UX Designer": {
                "default": "사용자 경험이 핵심이에요. 복잡한 기능도 직관적으로 사용할 수 있게 디자인해야 해요.",
                "기본": "사용자 경험이 핵심이에요. 복잡한 기능도 직관적으로 사용할 수 있게 디자인해야 해요."
            },
            "Data Scientist": {
                "default": "데이터 분석 결과를 봤는데요, 이 패턴이 중요해 보여요. 의사결정에 이 데이터를 활용하면 좋겠어요.",
                "기본": "데이터 분석 결과를 봤는데요, 이 패턴이 중요해 보여요. 의사결정에 이 데이터를 활용하면 좋겠어요."
            },
            "DevOps Engineer": {
                "default": "배포 자동화가 필요해요. CI/CD 파이프라인을 구축하면 개발 속도가 빨라질 거예요.",
                "기본": "배포 자동화가 필요해요. CI/CD 파이프라인을 구축하면 개발 속도가 빨라질 거예요."
            },
            "Security Specialist": {
                "default": "보안을 처음부터 고려해야 해요. 나중에 추가하면 비용이 많이 들고 위험할 수 있어요.",
                "기본": "보안을 처음부터 고려해야 해요. 나중에 추가하면 비용이 많이 들고 위험할 수 있어요."
            },
            "QA Engineer": {
                "default": "테스트 자동화가 중요해요. 수동 테스트만으로는 모든 버그를 잡기 어려워요.",
                "기본": "테스트 자동화가 중요해요. 수동 테스트만으로는 모든 버그를 잡기 어려워요."
            },
            "Technical Writer": {
                "default": "문서화를 잘 해야 사용자들이 쉽게 이해할 수 있어요. 복잡한 기능도 간단하게 설명해야 해요.",
                "기본": "문서화를 잘 해야 사용자들이 쉽게 이해할 수 있어요. 복잡한 기능도 간단하게 설명해야 해요."
            },
            "Project Manager": {
                "default": "일정 관리가 중요해요. 팀원들의 작업량을 고려해서 현실적인 마일스톤을 설정해야 해요.",
                "기본": "일정 관리가 중요해요. 팀원들의 작업량을 고려해서 현실적인 마일스톤을 설정해야 해요."
            },
            "Business Analyst": {
                "default": "비즈니스 목표와 기술적 해결책을 연결해야 해요. 이 기능이 어떤 비즈니스 가치를 창출하는지 명확히 해야 해요.",
                "기본": "비즈니스 목표와 기술적 해결책을 연결해야 해요. 이 기능이 어떤 비즈니스 가치를 창출하는지 명확히 해야 해요."
            },
            "Technical Architect / Lead Developer": {
                "default": "시스템 설계가 중요해요. 확장성과 유지보수성을 고려한 아키텍처를 선택해야 해요.",
                "기본": "시스템 설계가 중요해요. 확장성과 유지보수성을 고려한 아키텍처를 선택해야 해요."
            }
        }
        
        # Consensus responses for testing
        self.consensus_responses = {
            "consensus": "지금까지 논의한 내용을 정리해보면, 모두 동의할 수 있는 방향이 보이는 것 같아요.",
            "합의": "지금까지 논의한 내용을 정리해보면, 모두 동의할 수 있는 방향이 보이는 것 같아요.",
            "no_consensus": "아직 의견 차이가 있는 것 같아요. 좀 더 논의가 필요해 보여요.",
            "합의_없음": "아직 의견 차이가 있는 것 같아요. 좀 더 논의가 필요해 보여요."
        }
        
        # Custom responses provided at initialization
        self.custom_responses = responses or {}
        
        # 대화 상태 추적을 위한 변수
        self.role_turn_counts = {
            "UI/UX Designer": 0,
            "DevOps Engineer": 0,
            "Technical Architect / Lead Developer": 0,
            "Software Engineer": 0,
            "Product Manager": 0,
            "Data Scientist": 0,
            "Security Specialist": 0,
            "QA Engineer": 0,
            "Technical Writer": 0,
            "Project Manager": 0,
            "Business Analyst": 0
        }
    
    def generate_response(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Generate a mock response based on the prompt.
        """
        # Detect language
        language = self.detect_language(prompt)
        
        # Extract role from prompt
        role_match = None
        for role in self.role_responses.keys():
            if role.lower() in prompt.lower():
                role_match = role
                break
        
        # 양자역학 교육용 소프트웨어 개발 주제 감지
        is_quantum_education = "양자역학" in prompt and "교육" in prompt and "소프트웨어" in prompt
        
        # 역할이 있고 양자역학 교육 소프트웨어 주제인 경우
        if role_match and is_quantum_education and role_match in self.quantum_education_responses:
            # 해당 역할의 응답 목록에서 선택
            responses = self.quantum_education_responses[role_match]
            
            # 프롬프트의 해시값을 기반으로 응답 선택 (같은 프롬프트에 대해 항상 다른 응답 반환)
            # 이전 메시지 수를 추정하여 다른 응답 선택
            message_count = prompt.count("[")
            response_index = (hash(prompt) + message_count) % len(responses)
            return responses[response_index]
        
        # Check for role-specific prompts
        if role_match:
            if language == 'ko' and "기본" in self.role_responses[role_match]:
                return self.role_responses[role_match]["기본"]
            return self.role_responses[role_match]["default"]
        
        # Check for consensus-related prompts
        if "consensus" in prompt.lower():
            if language == 'ko':
                return self.consensus_responses["합의"]
            return self.consensus_responses["consensus"]
        
        if "no consensus" in prompt.lower() or "disagreement" in prompt.lower():
            if language == 'ko':
                return self.consensus_responses["합의_없음"]
            return self.consensus_responses["no_consensus"]
        
        # Check custom responses
        for key, response in self.custom_responses.items():
            if key.lower() in prompt.lower():
                return response
        
        # Check default responses
        for key, response in self.default_responses.items():
            if key.lower() in prompt.lower():
                return response
        
        # Generate a generic response based on language and topic
        if language == 'ko':
            # Extract topic from prompt if possible
            topic_match = re.search(r'토론 주제: ([^\n]+)', prompt)
            if topic_match:
                topic = topic_match.group(1)
                # Generate a conversational response about the topic
                responses = [
                    f"이 {topic}에 대해 좀 더 생각해 봤는데요, 핵심은 사용자 경험이라고 생각해요.",
                    f"{topic}에 관해서는 기술적 측면과 비즈니스 가치를 균형있게 고려해야 할 것 같아요.",
                    f"제 생각에는 {topic}에서 가장 중요한 건 확장성이에요. 나중에 수정하기 어려울 수 있거든요.",
                    f"{topic}은 팀 전체가 협력해야 잘 해결될 수 있을 것 같아요. 각자의 전문성이 필요해요.",
                    f"저는 {topic}에 대해 실용적인 접근이 필요하다고 봐요. 너무 복잡하게 생각하지 말고 단계적으로 진행해요."
                ]
                return responses[hash(prompt) % len(responses)]
            
            # Generic Korean responses
            generic_responses = [
                "좋은 의견이네요. 저도 대체로 동의합니다. 다만 실제 구현 시 고려할 점이 몇 가지 있을 것 같아요.",
                "흥미로운 관점이에요. 그런데 사용자 입장에서는 어떨지 한번 생각해 볼 필요가 있어요.",
                "맞아요, 그 부분이 중요하죠. 기술적으로 가능한지 먼저 확인해 보는 게 좋겠어요.",
                "전체적인 방향성에는 동의해요. 구체적인 실행 계획을 세워볼까요?",
                "좋은 지적이에요. 그 부분을 개선하면 전체 품질이 높아질 거예요."
            ]
            return generic_responses[hash(prompt) % len(generic_responses)]
        else:
            # Extract topic from prompt if possible
            topic_match = re.search(r'Discussion Topic: ([^\n]+)', prompt)
            if topic_match:
                topic = topic_match.group(1)
                # Generate a conversational response about the topic
                responses = [
                    f"I've been thinking about {topic}, and I believe user experience is the key here.",
                    f"For {topic}, we need to balance technical aspects with business value.",
                    f"In my view, scalability is the most important aspect of {topic}. It might be difficult to change later.",
                    f"{topic} requires collaboration from the entire team. We need everyone's expertise.",
                    f"I think we need a practical approach to {topic}. Let's not overcomplicate things and proceed step by step."
                ]
                return responses[hash(prompt) % len(responses)]
            
            # Generic English responses
            generic_responses = [
                "That's a good point. I mostly agree, though there are a few implementation considerations we should discuss.",
                "Interesting perspective. I think we should consider how this would work from the user's point of view.",
                "Yes, that's important. Let's first check if it's technically feasible.",
                "I agree with the overall direction. Should we create a specific action plan?",
                "Good insight. Improving that aspect would enhance the overall quality."
            ]
            return generic_responses[hash(prompt) % len(generic_responses)]


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