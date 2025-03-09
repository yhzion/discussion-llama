# 🚀 프로그램 개요 및 진행상황 정리

## 🔹 프로그램 개요
이 프로그램은 **토론 주제를 입력하면, 여러 역할을 가진 토론자들이 대화를 나누며 결론을 도출하는 시스템**입니다.  
특징적인 요소는 **토론자들의 역할(Role) 정의**와 **합의에 의해 자동으로 대화를 종료하는 실험적 접근 방식**입니다.

### 📌 주요 요구사항
1. **입력값**: 토론 주제
2. **출력값**: 토론자 간 대화 기록 (합의가 이루어지면 종료)
3. **토론자 구성**:
   - 역할별로 전문성을 갖춘 가상의 인물이 참여
   - 소프트웨어 개발 관련 역할들을 포함
4. **토론 흐름**:
   - 순차적 혹은 자유로운 방식으로 발언 가능
   - 특정 키워드나 조건이 만족되면 합의 도출 후 대화 종료

---

## 🔹 현재 진행상황

✅ **역할(Role) 정의를 위한 YAML 파일 구조 설계 완료**  
- `role` 디렉토리 아래 각 역할별 YAML 파일 생성  
- **YAML 파일 구조**
  - `role`: 역할 이름
  - `description`: 역할의 개요
  - `responsibilities`: 주요 책임
  - `expertise`: 요구되는 기술/지식
  - `characteristics`: 요구되는 성향/특성
  - `interaction_with`: 협업 대상
  - `success_criteria`: 성공 기준
  - 그 외 선택적 필드: `tools_and_technologies`, `decision_authority`, `scalability`, `agile_mapping`, `knowledge_sharing`, `career_path`, `remote_work_considerations`, `key_performance_indicators`

✅ **모든 역할별 YAML 파일 작성 완료**
- `product_owner_pm.yaml` (기획자)
- `ui_ux_designer.yaml` (UI/UX 디자이너)
- `backend_developer.yaml` (백엔드 개발자)
- `frontend_developer.yaml` (프론트엔드 개발자)
- `fullstack_developer.yaml` (풀스택 개발자)
- `qa_engineer.yaml` (QA 엔지니어)
- `devops_engineer.yaml` (DevOps 엔지니어)
- `data_engineer.yaml` (데이터 엔지니어)
- `security_engineer.yaml` (보안 엔지니어)
- `project_manager.yaml` (프로젝트 매니저)
- `technical_architect.yaml` (기술 아키텍트)
- `content_strategist.yaml` (콘텐츠 전략가)
- `product_analyst.yaml` (제품 분석가)
- `user_researcher.yaml` (사용자 연구원)

✅ **역할 정의 검증을 위한 테스트 인프라 구축 완료**
- `tests/test_role_schema_validation.py`: 역할 YAML 파일이 스키마에 맞게 작성되었는지 검증
- `tests/test_role_cross_references.py`: 역할 간 상호작용 참조가 올바르게 되어 있는지 검증
- `tests/test_role_content_validation.py`: 역할 내용이 일관성 있게 작성되었는지 검증
- 테스트 자동화를 위한 pytest 설정 완료

✅ **개발 환경 설정 완료**
- 필요한 패키지 의존성 정의 (`requirements.txt`)
- 테스트 커버리지 측정을 위한 설정 완료

✅ **핵심 시스템 아키텍처 설계 및 구현 완료**
- 시스템 아키텍처 다이어그램 설계
- 주요 컴포넌트 간 상호작용 정의
- 모듈 구조 설계 및 구현

✅ **역할 관리 시스템 구현 완료**
- `Role` 클래스 구현 (YAML 파일에서 역할 정의 로드)
- `RoleManager` 클래스 구현 (역할 관리 및 선택)
- 역할 선택 알고리즘 기본 구현

✅ **토론 엔진 기본 구현 완료**
- `Message` 클래스 구현 (토론 메시지 표현)
- `DiscussionState` 클래스 구현 (토론 상태 관리)
- `DiskBasedDiscussionManager` 구현 (디스크 기반 상태 관리)
- `DiscussionEngine` 클래스 구현 (토론 흐름 관리)
- 컨텍스트 압축 및 관리 기능 구현

✅ **LLM 통합 기본 구현 완료**
- `LLMClient` 인터페이스 정의
- `OllamaClient` 구현 (Ollama API 연동)
- `MockLLMClient` 구현 (테스트용 모의 클라이언트)
- 역할별 프롬프트 생성 기능 구현
- `EnhancedOllamaClient` 구현 (재시도 메커니즘, 스트리밍 지원, 오류 처리 개선)

✅ **합의 감지 알고리즘 구현 완료**
- 규칙 기반 합의 감지 알고리즘 구현
- 키워드 기반 합의 감지 기능 구현
- LLM 기반 합의 감지 기능 기본 구현
- 감정 분석(Sentiment Analysis)을 통한 합의 감지 기능 구현
- 시간적 분석(Temporal Analysis)을 통한 의견 변화 추적 기능 구현
- 역할별 전문성 가중치를 적용한 합의 감지 기능 구현
- 주제 관련성 개선을 통한 합의 감지 정확도 향상
- 합의 감지 신뢰도 점수 기능 구현

✅ **명령줄 인터페이스 구현 완료**
- 토론 주제 및 역할 지정 기능
- 토론 결과 출력 및 저장 기능
- 다양한 옵션 지원 (LLM 선택, 최대 턴 수 등)

✅ **테스트 코드 작성 완료**
- 역할 관리 시스템 테스트
- 토론 엔진 테스트
- LLM 클라이언트 테스트
- 합의 감지 알고리즘 테스트
- CLI 테스트

---

## 🔹 앞으로의 작업 방향
1. **LLM 통합 개선**
   - ✅ 실제 Ollama 서버와의 통합 개선
   - ✅ 스트리밍 응답 지원 추가
   - ✅ 재시도 메커니즘 및 오류 처리 개선
   - 다양한 LLM 모델 지원 추가
   - 프롬프트 엔지니어링 최적화

2. **합의 감지 알고리즘 개선**
   - 더 정교한 합의 감지 알고리즘 개발
   - 토론 주제에 따른 맞춤형 합의 기준 설정
   - 합의 품질 평가 메트릭 개발

3. **역할 선택 알고리즘 개선**
   - 토론 주제에 더 적합한 역할 선택 알고리즘 개발
   - 역할 간 상호작용 최적화
   - 동적 역할 조정 기능 추가

4. **웹 인터페이스 개발**
   - 웹 기반 사용자 인터페이스 설계 및 구현
   - 실시간 토론 시각화 기능
   - 사용자 개입 기능 추가

5. **성능 최적화**
   - 메모리 사용량 최적화
   - 토큰 사용량 최적화
   - 응답 생성 속도 개선

6. **문서화 및 배포**
   - 코드 문서화 개선
   - 사용자 가이드 작성
   - 배포 파이프라인 구축

---

## 🔹 프로그램 실행 방법 및 오류 해결

### 프로그램 실행 방법

1. **환경 설정**
   ```bash
   # 저장소 클론
   git clone https://github.com/yourusername/discussion-llama.git
   cd discussion-llama

   # 가상 환경 생성 (권장)
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate

   # 의존성 설치
   pip install -r requirements.txt

   # 개발 모드로 패키지 설치
   pip install -e .
   ```

2. **run_discussion.py 스크립트 사용**
   ```bash
   # 기본 사용법
   python run_discussion.py "토론 주제"

   # 특정 역할 지정
   python run_discussion.py "토론 주제" --roles "product_owner_pm,backend_developer,security_engineer"

   # Ollama 사용 (실제 LLM 통합)
   python run_discussion.py "토론 주제" --llm-client ollama --model llama2:7b-chat-q4_0

   # 향상된 Ollama 클라이언트 사용 (스트리밍 지원)
   python run_discussion.py "토론 주제" --llm-client enhanced_ollama --model llama2:7b-chat-q4_0 --stream

   # 결과를 파일로 저장
   python run_discussion.py "토론 주제" --output results.json
   ```

3. **명령줄 인터페이스 사용** (패키지 설치 후)
   ```bash
   # 기본 사용법
   discussion-llama "토론 주제"

   # 추가 옵션 사용
   discussion-llama "토론 주제" --roles "product_owner_pm,backend_developer,security_engineer" --llm-client ollama
   ```

### 주요 명령줄 옵션

| 옵션 | 설명 | 기본값 |
|--------|-------------|---------|
| `--roles` | 포함할 역할 이름 (쉼표로 구분) | 주제 기반 자동 선택 |
| `--num-roles` | 포함할 역할 수 (지정되지 않은 경우) | 3 |
| `--max-turns` | 최대 턴 수 | 10 |
| `--llm-client` | 사용할 LLM 클라이언트 (mock, ollama, enhanced_ollama) | mock |
| `--model` | 사용할 모델 (Ollama용) | llama2:7b-chat-q4_0 |
| `--max-retries` | LLM 요청 최대 재시도 횟수 | 3 |
| `--retry-delay` | LLM 요청 재시도 간 지연 시간 | 1.0 |
| `--timeout` | LLM 요청 타임아웃 (초) | 30 |
| `--output` | 토론 결과 저장 파일 (JSON) | None |
| `--stream` | 응답 생성에 스트리밍 사용 (enhanced_ollama만 해당) | False |

### Ollama 사용하기

실제 언어 모델로 Discussion-Llama를 사용하려면 Ollama를 설치하고 실행해야 합니다:

1. [ollama.ai](https://ollama.ai/)에서 Ollama 설치
2. Ollama 서버 시작
3. 사용할 모델 다운로드:
   ```bash
   ollama pull llama2:7b-chat-q4_0
   ```
4. Ollama 클라이언트로 Discussion-Llama 실행:
   ```bash
   python run_discussion.py "토론 주제" --llm-client ollama --model llama2:7b-chat-q4_0
   ```

### 오류 해결

#### 1. AttributeError: 'list' object has no attribute 'lower'

이 오류는 `role_manager.py` 파일의 `_calculate_role_relevance` 메서드에서 발생합니다. 역할의 expertise 필드가 문자열 리스트인데, 코드에서는 단일 문자열로 처리하려고 했기 때문입니다.

**해결 방법**:
`role_manager.py` 파일에서 expertise와 responsibilities를 처리하는 부분에 `isinstance(expertise, str)` 검사를 추가하여 문자열인 경우에만 `lower()` 메서드를 호출하도록 수정했습니다.

```python
# 수정 전
for expertise in role.expertise:
    expertise_keywords.update(re.findall(r'\b\w+\b', expertise.lower()))

# 수정 후
for expertise in role.expertise:
    if isinstance(expertise, str):  # 문자열인지 확인
        expertise_keywords.update(re.findall(r'\b\w+\b', expertise.lower()))
```

#### 2. 이전 토론 상태 로드 문제

프로그램을 여러 번 실행하면 이전 토론 상태가 로드되어 새로운 토론이 제대로 시작되지 않을 수 있습니다.

**해결 방법**:
새로운 토론을 시작하기 전에 토론 상태 디렉토리를 비웁니다:
```bash
rm -rf discussion_state/* && python run_discussion.py "토론 주제" --llm-client enhanced_ollama --model llama2:7b-chat-q4_0
```

---

다음 작업을 어떤 순서로 진행할지 말씀해 주시면 우선순위를 조정할 수 있도록 도와드리겠습니다. 😊