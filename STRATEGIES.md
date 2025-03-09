# 메모리 효율적인 토론 시스템 구현 전략

## 개요

이 문서는 제한된 메모리 환경에서 Ollama의 경량화 모델을 사용하여 토론 시스템을 효율적으로 구현하는 방법을 설명합니다. 한 번에 하나의 요청만 처리하는 환경에서 최적의 성능을 내기 위한 전략을 제시합니다.

## 1. 순차적 턴 기반 처리 아키텍처

### 1.1 롤링 컨텍스트 윈도우

```
User Topic → Role 1 → Role 2 → Role 3 → ... → Consensus Check
```

- **제한된 컨텍스트 유지**:
  - 가장 최근 N개의 대화만 전체 컨텍스트로 유지 (예: 최근 6개 메시지)
  - 이전 논의 내용은 요약본으로 압축하여 보관
  - 각 프롬프트에 요약본을 포함시켜 대화의 연속성 유지

- **구현 예시**:
  ```python
  def prepare_context(discussion_history, max_recent_messages=6):
      if len(discussion_history) <= max_recent_messages:
          return {
              "full_context": discussion_history,
              "summary": ""
          }
      
      recent_messages = discussion_history[-max_recent_messages:]
      older_messages = discussion_history[:-max_recent_messages]
      
      # 이전 메시지 요약 (경량화된 방식으로)
      summary = summarize_messages(older_messages)
      
      return {
          "full_context": recent_messages,
          "summary": summary
      }
  ```

### 1.2 컨텍스트 압축 기법

- **점진적 요약 방식**:
  - 각 턴이 끝날 때마다 대화 내용을 요약하여 압축
  - 요약은 핵심 포인트와 주요 의견만 포함하도록 설계
  - 다음 턴에는 압축된 이력과 최근 교환 내용만 전달

- **구현 예시**:
  ```python
  def compress_context(context):
      if len(context["discussion"]) > 6:  # 최근 3턴(6개 메시지) 유지
          older_messages = context["discussion"][:-6]
          
          # 간단한 요약 프롬프트 생성
          summary_prompt = f"""
          다음 토론 내용을 3-4문장으로 간결하게 요약하세요:
          {format_messages(older_messages)}
          """
          
          # 요약을 위한 경량화된 호출
          summary = call_ollama_with_minimal_context(summary_prompt, max_tokens=100)
          
          context["summary"] = summary
          context["discussion"] = context["discussion"][-6:]
      
      return context
  ```

### 1.3 디스크 기반 상태 관리

- **메모리 대신 디스크 활용**:
  - 대화 상태를 메모리가 아닌 디스크에 저장
  - 현재 역할의 턴에 필요한 정보만 로드
  - 각 턴 사이에 상태를 JSON 형태로 저장

- **구현 예시**:
  ```python
  class DiskBasedDiscussionManager:
      def __init__(self, topic, roles, temp_dir="./discussion_state"):
          self.topic = topic
          self.roles = roles
          self.temp_dir = temp_dir
          os.makedirs(temp_dir, exist_ok=True)
          
      def save_context(self, context):
          with open(f"{self.temp_dir}/context.json", "w") as f:
              json.dump(context, f)
      
      def load_context(self):
          try:
              with open(f"{self.temp_dir}/context.json", "r") as f:
                  return json.load(f)
          except FileNotFoundError:
              return {"discussion": [], "summary": "", "turn": 0}
  ```

## 2. 퓨샷 프롬프트 엔지니어링 최적화

### 2.1 역할별 템플릿 설계

- **역할 특화 프롬프트**:
  - 각 역할에 맞는 템플릿 생성 (YAML 정의 활용)
  - 2-3개의 예시 응답을 포함하여 역할의 관점 시연
  - 압축된 현재 토론 컨텍스트 포함

- **템플릿 예시**:
  ```
  당신은 {role_name}입니다.
  
  역할 설명: {role_description}
  주요 책임: {responsibilities}
  전문 분야: {expertise}
  
  이전 토론 요약: {discussion_summary}
  
  최근 대화:
  {recent_messages}
  
  예시 응답:
  1. "{example_response_1}"
  2. "{example_response_2}"
  
  위 역할과 토론 맥락을 고려하여, 주제 "{topic}"에 대한 당신의 의견을 150단어 이내로 제시하세요.
  ```

### 2.2 지시사항 최적화

- **명확한 제약 설정**:
  - 응답 길이 제한에 대한 명확한 지시 (예: 150단어 이내)
  - 가장 관련성 높은 포인트에만 집중하도록 유도
  - 응답 형식 명확히 지정 (예: 주장, 근거, 제안 순서로)

- **구현 예시**:
  ```python
  def create_prompt_for_role(role, context, topic):
      # 역할 정보 로드
      role_info = load_role_yaml(role)
      
      # 최근 메시지와 요약 포맷팅
      recent_messages = format_messages(context["discussion"])
      
      # 역할별 예시 응답 (미리 준비된 것 사용)
      examples = get_example_responses_for_role(role)
      
      prompt = f"""
      당신은 {role_info['role']}입니다.
      
      역할 설명: {role_info['description']}
      주요 책임: {', '.join(role_info['responsibilities'])}
      전문 분야: {', '.join(role_info['expertise'])}
      
      이전 토론 요약: {context['summary']}
      
      최근 대화:
      {recent_messages}
      
      예시 응답:
      1. "{examples[0]}"
      2. "{examples[1]}"
      
      위 역할과 토론 맥락을 고려하여, 주제 "{topic}"에 대한 당신의 의견을 다음 형식으로 150단어 이내로 제시하세요:
      
      1. 주장: (핵심 의견)
      2. 근거: (주장을 뒷받침하는 1-2개 근거)
      3. 제안: (구체적인 제안사항)
      """
      
      return prompt
  ```

## 3. Ollama 최적화 방법

### 3.1 모델 선택 및 설정

- **경량화 모델 선택**:
  - `llama2:7b-chat-q4_0` - 기본적인 대화 능력과 낮은 메모리 요구사항
  - `mistral:7b-instruct-v0.2-q4_0` - 지시 따르기에 최적화된 경량 모델
  - `phi-2:q4_0` - 매우 작은 크기의 모델로 기본적인 대화 가능

- **컨텍스트 크기 제한**:
  ```bash
  ollama run llama2:7b-chat-q4_0 --context-size 2048
  ```

### 3.2 API 활용 최적화

- **REST API 호출 예시**:
  ```python
  import requests
  import json
  
  def call_ollama(prompt, model="llama2:7b-chat-q4_0", max_tokens=512):
      response = requests.post(
          'http://localhost:11434/api/generate',
          json={
              "model": model,
              "prompt": prompt,
              "stream": False,
              "options": {
                  "num_predict": max_tokens,
                  "temperature": 0.7,
                  "top_p": 0.9,
                  "context_size": 2048  # 컨텍스트 크기 제한
              }
          }
      )
      
      if response.status_code == 200:
          return response.json()["response"]
      else:
          return f"Error: {response.status_code}, {response.text}"
  ```

### 3.3 배치 처리 최적화

- **저활동 시간대 배치 처리**:
  - 시스템 사용량이 적은 시간에 여러 턴을 한 번에 처리
  - 배치 크기를 메모리 상황에 맞게 동적으로 조절

- **구현 예시**:
  ```python
  def batch_process_turns(topic, roles, start_turn, batch_size=3):
      context = load_context()
      results = []
      
      for i in range(batch_size):
          current_turn = start_turn + i
          if current_turn >= MAX_TURNS:
              break
              
          current_role = roles[current_turn % len(roles)]
          prompt = create_prompt_for_role(current_role, context, topic)
          response = call_ollama(prompt)
          
          # 컨텍스트 업데이트
          context["discussion"].append({"role": current_role, "content": response})
          context = compress_context(context)
          
          results.append({"role": current_role, "response": response})
          
          # 합의 확인
          if check_consensus(context["discussion"]):
              break
      
      save_context(context)
      return results
  ```

## 4. 합의 감지 최적화

### 4.1 경량화된 합의 감지 알고리즘

- **키워드 기반 접근법**:
  - 각 메시지에서 핵심 키워드/주장 추출
  - 동일하거나 유사한 키워드의 빈도 계산
  - 임계값 이상의 동의가 있으면 합의로 판단

- **구현 예시**:
  ```python
  def extract_key_points(message, max_points=3):
      # 간단한 규칙 기반 키워드 추출
      sentences = message.split('.')
      key_points = []
      
      for sentence in sentences:
          if any(marker in sentence.lower() for marker in ["주장", "제안", "동의", "중요", "핵심"]):
              key_points.append(sentence.strip())
              if len(key_points) >= max_points:
                  break
                  
      return key_points
  
  def check_consensus(recent_messages, threshold=0.7):
      if len(recent_messages) < 4:  # 최소 2명 이상의 의견 필요
          return False
          
      # 키포인트 추출
      all_points = []
      for msg in recent_messages:
          points = extract_key_points(msg["content"])
          all_points.extend(points)
      
      # 유사 포인트 그룹화 및 빈도 계산
      point_groups = group_similar_points(all_points)
      
      # 가장 많이 언급된 포인트의 동의율 계산
      if point_groups and len(recent_messages) > 0:
          top_point_count = max(len(group) for group in point_groups)
          agreement_ratio = top_point_count / len(recent_messages)
          return agreement_ratio >= threshold
      
      return False
  ```

### 4.2 합의 감지를 위한 명시적 프롬프트

- **합의 확인 전용 프롬프트**:
  - 주기적으로 현재까지의 토론 내용을 바탕으로 합의 여부 확인
  - 명시적인 합의 조건 제시 (예: "모든 참가자가 동의한 핵심 포인트가 있는가?")

- **구현 예시**:
  ```python
  def check_consensus_with_llm(discussion_history, topic):
      # 최근 모든 참가자의 메시지 추출
      recent_messages = get_latest_message_from_each_role(discussion_history)
      
      consensus_prompt = f"""
      다음은 "{topic}" 주제에 대한 토론의 최근 각 참가자별 의견입니다:
      
      {format_messages(recent_messages)}
      
      위 토론에서 모든 참가자가 동의하는 핵심 포인트가 있는지 분석하세요.
      합의가 이루어졌다면 "합의: 예"로 시작하고 합의된 내용을 설명하세요.
      합의가 이루어지지 않았다면 "합의: 아니오"로 시작하고 주요 이견을 설명하세요.
      """
      
      response = call_ollama(consensus_prompt, max_tokens=150)
      
      # 응답에서 합의 여부 추출
      return response.startswith("합의: 예")
  ```

## 5. 전체 시스템 구현 예시

### 5.1 기본 구현 흐름

```python
def run_discussion(topic, roles_yaml_dir, max_turns=30):
    # 1. 역할 정보 로드
    roles = load_roles_from_yaml(roles_yaml_dir)
    
    # 2. 디스크 기반 상태 관리자 초기화
    discussion_manager = DiskBasedDiscussionManager(topic, roles)
    
    # 3. 토론 진행
    turn = 0
    consensus_reached = False
    
    while turn < max_turns and not consensus_reached:
        # 현재 상태 로드
        context = discussion_manager.load_context()
        
        # 현재 역할 결정
        current_role_index = turn % len(roles)
        current_role = roles[current_role_index]
        
        # 프롬프트 생성
        prompt = create_prompt_for_role(current_role, context, topic)
        
        # Ollama 호출
        response = call_ollama(prompt)
        
        # 응답 저장
        context["discussion"].append({
            "role": current_role["role"],
            "content": response
        })
        
        # 컨텍스트 압축
        context = discussion_manager.compress_context(context)
        context["turn"] = turn + 1
        
        # 상태 저장
        discussion_manager.save_context(context)
        
        # 합의 확인 (매 역할이 한 번씩 발언한 후)
        if (turn + 1) % len(roles) == 0:
            consensus_reached = check_consensus(context["discussion"])
        
        turn += 1
    
    # 4. 결과 반환
    final_context = discussion_manager.load_context()
    return {
        "topic": topic,
        "discussion": final_context["discussion"],
        "consensus_reached": consensus_reached,
        "turns": turn
    }
```

### 5.2 메모리 사용량 모니터링

```python
def monitor_memory_usage():
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        "rss": memory_info.rss / (1024 * 1024),  # MB 단위
        "vms": memory_info.vms / (1024 * 1024)   # MB 단위
    }

def log_memory_usage(stage):
    memory = monitor_memory_usage()
    print(f"Memory usage at {stage}: RSS={memory['rss']:.2f}MB, VMS={memory['vms']:.2f}MB")
```

## 6. 추가 최적화 방안

### 6.1 모델 양자화 활용

- Ollama에서 제공하는 양자화된 모델 활용 (q4_0, q4_1, q5_0, q5_1, q8_0)
- 정확도와 메모리 사용량 간의 균형점 찾기

### 6.2 프롬프트 길이 최적화

- 각 역할 설명에서 꼭 필요한 정보만 포함
- 예시 응답은 짧고 명확하게 구성
- 토론 요약은 핵심 포인트만 간결하게 유지

### 6.3 비동기 처리 활용

- 디스크 I/O와 모델 추론을 비동기적으로 처리
- 다음 턴 준비 작업을 현재 턴 처리와 병렬로 진행

## 결론

제한된 메모리 환경에서도 효과적인 토론 시스템을 구현하기 위해서는 다음 전략을 조합하여 사용하는 것이 효과적입니다:

1. 순차적 턴 기반 처리로 한 번에 하나의 역할만 메모리에 로드
2. 롤링 컨텍스트 윈도우와 컨텍스트 압축을 통한 메모리 사용량 최소화
3. 디스크 기반 상태 관리로 메모리 부담 감소
4. 역할별 최적화된 퓨샷 프롬프트로 효율적인 응답 유도
5. Ollama의 경량화 모델과 컨텍스트 크기 제한 활용
6. 경량화된 합의 감지 알고리즘 구현

이러한 접근 방식을 통해 제한된 메모리 환경에서도 품질 높은 토론 시스템을 구현할 수 있습니다.
