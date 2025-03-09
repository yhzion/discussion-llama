#!/usr/bin/env python
"""
토론 시뮬레이션을 실행하는 스크립트입니다.
"""

import os
import sys
import argparse
from discussion_llama.role.role_manager import RoleManager
from discussion_llama.engine.discussion_engine import DiscussionEngine
from discussion_llama.llm.llm_client import create_llm_client
from discussion_llama.engine.consensus_detector import ConsensusDetector

def main():
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description="Run a discussion simulation")
    parser.add_argument("topic", help="The topic for discussion")
    parser.add_argument("--roles", help="Comma-separated list of role names to include")
    parser.add_argument("--num-roles", type=int, default=3, help="Number of roles to include (if not specified)")
    parser.add_argument("--max-turns", type=int, default=10, help="Maximum number of turns")
    parser.add_argument("--llm-client", default="mock", choices=["mock", "ollama", "enhanced_ollama"], 
                        help="LLM client to use")
    parser.add_argument("--model", default="llama2:7b-chat-q4_0", help="Model to use (for Ollama)")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum number of retries for LLM requests")
    parser.add_argument("--retry-delay", type=float, default=1.0, help="Delay between retries for LLM requests")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for LLM requests in seconds")
    parser.add_argument("--output", help="Output file for discussion results (JSON)")
    parser.add_argument("--stream", action="store_true", help="Use streaming for response generation (enhanced_ollama only)")
    parser.add_argument("--language", choices=["auto", "en", "ko"], default="auto", 
                        help="Language for the discussion (auto, en, ko). Default is auto-detect.")
    args = parser.parse_args()
    
    # 역할 디렉토리 경로
    roles_dir = "./roles"
    
    # 역할 관리자 초기화
    try:
        role_manager = RoleManager(roles_dir)
    except Exception as e:
        print(f"Error initializing RoleManager: {e}")
        sys.exit(1)
    
    # 역할 선택
    if args.roles:
        # 지정된 역할 사용
        role_names = args.roles.split(",")
        selected_roles = []
        for role_name in role_names:
            role = role_manager.get_role(role_name)
            if role:
                selected_roles.append(role)
            else:
                print(f"Warning: Role '{role_name}' not found")
    else:
        # 주제에 기반한 역할 자동 선택
        selected_roles = role_manager.select_roles_for_discussion(args.topic, args.num_roles)
    
    if not selected_roles:
        print("Error: No valid roles selected for discussion")
        sys.exit(1)
    
    # LLM 클라이언트 생성
    llm_kwargs = {"model": args.model}
    
    # Add enhanced_ollama specific parameters
    if args.llm_client == "enhanced_ollama":
        llm_kwargs.update({
            "max_retries": args.max_retries,
            "retry_delay": args.retry_delay,
            "timeout": args.timeout
        })
    
    llm_client = create_llm_client(args.llm_client, **llm_kwargs)
    
    # 언어 감지
    if args.language == "auto":
        detected_language = llm_client.detect_language(args.topic) if hasattr(llm_client, 'detect_language') else 'en'
    else:
        detected_language = args.language
    
    # 언어에 따른 메시지 출력
    if detected_language == 'ko':
        print(f"\n🚀 주제에 대한 토론을 시작합니다: {args.topic}")
        print(f"👥 참가자: {', '.join(role.role for role in selected_roles)}")
        print("-" * 80)
    else:
        print(f"\n🚀 Starting discussion on topic: {args.topic}")
        print(f"👥 Participants: {', '.join(role.role for role in selected_roles)}")
        print("-" * 80)
    
    # 합의 감지기 생성
    consensus_detector = ConsensusDetector(llm_client)
    
    # 토론 엔진 생성 및 실행
    state_dir = "./discussion_state"
    os.makedirs(state_dir, exist_ok=True)
    
    # LLM 클라이언트를 DiscussionEngine에 전달
    engine = DiscussionEngine(args.topic, selected_roles, state_dir, llm_client=llm_client)
    engine.max_turns = args.max_turns
    
    # 스트리밍 옵션 설정
    engine.use_streaming = args.stream and args.llm_client == "enhanced_ollama"
    
    # 토론 실행
    result = engine.run_discussion()
    
    # 결과 표시
    if detected_language == 'ko':
        print("\n📝 토론 요약:")
        print("-" * 80)
        
        for message in result["discussion"]:
            print(f"[{message['role']}]: {message['content']}")
            print("-" * 80)
        
        print(f"\n🏁 토론이 {result['turns']}턴 후 종료되었습니다.")
        if result["consensus_reached"]:
            print("✅ 합의에 도달했습니다!")
        else:
            print("❌ 합의에 도달하지 못했습니다.")
        
        # 결과 저장
        if args.output:
            import json
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n💾 결과가 {args.output}에 저장되었습니다.")
    else:
        print("\n📝 Discussion Summary:")
        print("-" * 80)
        
        for message in result["discussion"]:
            print(f"[{message['role']}]: {message['content']}")
            print("-" * 80)
        
        print(f"\n🏁 Discussion ended after {result['turns']} turns.")
        if result["consensus_reached"]:
            print("✅ Consensus was reached!")
        else:
            print("❌ No consensus was reached.")
        
        # 결과 저장
        if args.output:
            import json
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Results saved to {args.output}")

if __name__ == "__main__":
    main() 