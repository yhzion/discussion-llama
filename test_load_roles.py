#!/usr/bin/env python
"""
간단한 스크립트로 역할 파일을 로드하고 정보를 출력합니다.
"""

import os
import sys
from discussion_llama.role.role_manager import RoleManager

def main():
    # 역할 디렉토리 경로
    roles_dir = "./roles"
    
    # 역할 관리자 초기화
    try:
        role_manager = RoleManager(roles_dir)
    except Exception as e:
        print(f"Error initializing RoleManager: {e}")
        sys.exit(1)
    
    # 모든 역할 가져오기
    roles = role_manager.get_all_roles()
    
    print(f"Found {len(roles)} roles:")
    print("-" * 50)
    
    # 각 역할 정보 출력
    for i, role in enumerate(roles, 1):
        print(f"{i}. {role.role}")
        print(f"   Description: {role.description[:100]}...")
        print(f"   Responsibilities: {len(role.responsibilities)} items")
        print(f"   Expertise: {len(role.expertise)} items")
        print(f"   Characteristics: {len(role.characteristics)} items")
        
        # interaction_with 필드 처리 - 딕셔너리 또는 리스트 형식 모두 지원
        if hasattr(role, 'interaction_with'):
            if isinstance(role.interaction_with, dict):
                interactions = ', '.join(role.interaction_with.keys())
            elif isinstance(role.interaction_with, list):
                interactions = ', '.join([str(item) for item in role.interaction_with])
            else:
                interactions = str(role.interaction_with)
            print(f"   Interacts with: {interactions}")
        else:
            print("   Interacts with: Not specified")
            
        print("-" * 50)
    
    # 토론 주제에 대한 역할 선택 예시
    topic = "How to implement a secure authentication system"
    selected_roles = role_manager.select_roles_for_discussion(topic, 3)
    
    print(f"\nSelected roles for topic '{topic}':")
    for role in selected_roles:
        print(f"- {role.role}")

if __name__ == "__main__":
    main() 