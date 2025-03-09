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

---

## 🔹 앞으로의 작업 방향
1. **토론 시뮬레이션 로직 개발**
   - 토론자 역할에 맞게 대화 생성하는 알고리즘 설계
   - 발언 순서 및 논의 방식 결정
   - 합의 판단 기준 구현

2. **프로그램 초기 버전 개발**
   - 명령형 파이썬 코드로 기본 기능 구현
   - 입력값(토론 주제)에 따라 동적으로 토론 생성
   
3. **토론 시뮬레이션 모듈 구현**
   - 역할 YAML 파일을 읽어 토론자 객체 생성
   - 토론자 간 상호작용 로직 구현
   - 토론 주제에 따른 대화 생성 및 합의 도출 알고리즘 개발

4. **사용자 인터페이스 개발**
   - 토론 주제 입력 및 결과 출력을 위한 인터페이스 구현
   - 토론 과정 시각화 기능 추가

5. **테스트 및 개선**
   - 다양한 토론 주제에 대한 테스트 수행
   - 토론 품질 및 합의 도출 과정 개선

---

다음 작업을 어떤 순서로 진행할지 말씀해 주시면 우선순위를 조정할 수 있도록 도와드리겠습니다. 😊