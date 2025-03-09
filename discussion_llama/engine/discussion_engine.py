import os
import json
import time
from typing import Dict, List, Any, Optional
from ..role.role_manager import Role
from ..llm.llm_client import LLMClient, create_llm_client
from .consensus_detector import check_consensus_rule_based


class Message:
    """
    Represents a message in a discussion.
    """
    def __init__(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary.
        """
        return {
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a message from a dictionary.
        """
        msg = cls(data["role"], data["content"], data.get("metadata", {}))
        msg.timestamp = data.get("timestamp", time.time())
        return msg


class DiscussionState:
    """
    Represents the state of a discussion.
    """
    def __init__(self, topic: str, roles: List[Role]):
        self.topic = topic
        self.roles = roles
        self.messages: List[Message] = []
        self.summary = ""
        self.turn = 0
        self.consensus_reached = False
        self.metadata: Dict[str, Any] = {}
    
    def add_message(self, message: Message) -> None:
        """
        Add a message to the discussion.
        """
        self.messages.append(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the discussion state to a dictionary.
        """
        return {
            "topic": self.topic,
            "roles": [role.to_dict() for role in self.roles],
            "messages": [msg.to_dict() for msg in self.messages],
            "summary": self.summary,
            "turn": self.turn,
            "consensus_reached": self.consensus_reached,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], roles: List[Role]) -> 'DiscussionState':
        """
        Create a discussion state from a dictionary.
        """
        state = cls(data["topic"], roles)
        state.messages = [Message.from_dict(msg) for msg in data.get("messages", [])]
        state.summary = data.get("summary", "")
        state.turn = data.get("turn", 0)
        state.consensus_reached = data.get("consensus_reached", False)
        state.metadata = data.get("metadata", {})
        return state


class DiskBasedDiscussionManager:
    """
    Manages the discussion state using disk-based storage.
    """
    def __init__(self, topic: str, roles: List[Role], temp_dir: str = "./discussion_state"):
        self.topic = topic
        self.roles = roles
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    
    def save_state(self, state: DiscussionState) -> None:
        """
        Save the discussion state to disk.
        """
        state_dict = state.to_dict()
        with open(f"{self.temp_dir}/state.json", "w", encoding="utf-8") as f:
            json.dump(state_dict, f, ensure_ascii=False, indent=2)
    
    def load_state(self) -> DiscussionState:
        """
        Load the discussion state from disk.
        """
        try:
            with open(f"{self.temp_dir}/state.json", "r", encoding="utf-8") as f:
                state_dict = json.load(f)
                return DiscussionState.from_dict(state_dict, self.roles)
        except FileNotFoundError:
            return DiscussionState(self.topic, self.roles)


class DiscussionEngine:
    """
    Core engine for managing discussions.
    """
    def __init__(self, topic: str, roles: List[Role], state_dir: str = "./discussion_state", llm_client: Optional[LLMClient] = None):
        self.topic = topic
        self.roles = roles
        self.state_manager = DiskBasedDiscussionManager(topic, roles, state_dir)
        self.state = self.state_manager.load_state()
        self.max_turns = 30  # Default maximum number of turns
        self.llm_client = llm_client or create_llm_client("mock")
    
    def prepare_context(self, role: Role, max_recent_messages: int = 6) -> Dict[str, Any]:
        """
        Prepare the context for a role's turn.
        """
        if len(self.state.messages) <= max_recent_messages:
            return {
                "full_context": self.state.messages,
                "summary": ""
            }
        
        recent_messages = self.state.messages[-max_recent_messages:]
        older_messages = self.state.messages[:-max_recent_messages]
        
        # In a real implementation, this would use an LLM to generate a summary
        # For now, we'll just use a placeholder
        summary = f"Previous discussion with {len(older_messages)} messages about {self.topic}"
        
        return {
            "full_context": recent_messages,
            "summary": summary
        }
    
    def compress_context(self) -> None:
        """
        Compress the discussion context to save memory.
        """
        if len(self.state.messages) > 6:  # Keep the most recent 6 messages
            older_messages = self.state.messages[:-6]
            
            # In a real implementation, this would use an LLM to generate a summary
            # For now, we'll just use a placeholder
            summary = f"Summary of {len(older_messages)} previous messages about {self.topic}"
            
            self.state.summary = summary
            self.state.messages = self.state.messages[-6:]
    
    def check_consensus(self) -> bool:
        """
        Check if consensus has been reached in the discussion.
        """
        # 메시지를 딕셔너리 형태로 변환
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in self.state.messages
        ]
        
        # 규칙 기반 합의 감지 사용
        return check_consensus_rule_based(messages)
    
    def create_prompt_for_role(self, role: Role, context: Dict[str, Any]) -> str:
        """
        Create a prompt for a role based on the context.
        """
        # Get role description
        role_description = role.get_prompt_description()
        
        # Format recent messages
        formatted_messages = ""
        for msg in context["full_context"]:
            formatted_messages += f"[{msg.role}]: {msg.content}\n\n"
        
        # Create the prompt
        prompt = f"""
{role_description}

Topic for discussion: {self.topic}

{context["summary"]}

Recent messages:
{formatted_messages}

Based on your role and the discussion so far, provide your perspective on the topic.
Keep your response concise and focused on the most important points.
"""
        
        return prompt
    
    def generate_response(self, role: Role, context: Dict[str, Any]) -> str:
        """
        Generate a response for a role based on the context.
        """
        prompt = self.create_prompt_for_role(role, context)
        
        # 디버깅을 위해 프롬프트 출력
        print(f"\nPrompt for {role.role}:")
        print("-" * 40)
        print(prompt)
        print("-" * 40)
        
        # Use the LLM client to generate a response
        response = self.llm_client.generate_response(prompt, max_tokens=512, temperature=0.7)
        
        return response
    
    def run_discussion(self) -> Dict[str, Any]:
        """
        Run the discussion until consensus is reached or max turns is hit.
        """
        turn = self.state.turn
        consensus_reached = self.state.consensus_reached
        
        while turn < self.max_turns and not consensus_reached:
            # Determine the current role
            current_role_index = turn % len(self.roles)
            current_role = self.roles[current_role_index]
            
            # Prepare context for this turn
            context = self.prepare_context(current_role)
            
            # Generate response using LLM
            response = self.generate_response(current_role, context)
            
            # Add the message to the discussion
            self.state.add_message(Message(current_role.role, response))
            
            # Compress context if needed
            self.compress_context()
            
            # Update turn counter
            turn += 1
            self.state.turn = turn
            
            # Save state
            self.state_manager.save_state(self.state)
            
            # Check for consensus
            if (turn % len(self.roles) == 0):  # Check after each round
                consensus_reached = self.check_consensus()
                self.state.consensus_reached = consensus_reached
        
        # Return the final state
        return {
            "topic": self.topic,
            "discussion": [msg.to_dict() for msg in self.state.messages],
            "consensus_reached": self.state.consensus_reached,
            "turns": self.state.turn
        } 