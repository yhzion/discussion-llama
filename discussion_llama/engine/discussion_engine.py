import os
import json
import time
import sys
from typing import Dict, List, Any, Optional, Callable
from ..role.role_manager import Role
from ..llm.llm_client import LLMClient, create_llm_client, EnhancedOllamaClient
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
    
    def add_message(self, message: Message) -> None:
        """
        Add a message to the discussion.
        """
        self.messages.append(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the state to a dictionary.
        """
        return {
            "topic": self.topic,
            "roles": [role.role for role in self.roles],
            "messages": [message.to_dict() for message in self.messages],
            "summary": self.summary,
            "turn": self.turn,
            "consensus_reached": self.consensus_reached
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], roles: List[Role]) -> 'DiscussionState':
        """
        Create a state from a dictionary.
        """
        state = cls(data["topic"], roles)
        state.messages = [Message.from_dict(msg) for msg in data["messages"]]
        state.summary = data.get("summary", "")
        state.turn = data.get("turn", 0)
        state.consensus_reached = data.get("consensus_reached", False)
        return state


class DiskBasedDiscussionManager:
    """
    Manages discussion state using disk-based storage.
    """
    def __init__(self, topic: str, roles: List[Role], temp_dir: str = "./discussion_state"):
        self.topic = topic
        self.roles = roles
        self.temp_dir = temp_dir
        self.state_file = os.path.join(temp_dir, f"{self._sanitize_filename(topic)}.json")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a string to be used as a filename."""
        return "".join(c if c.isalnum() else "_" for c in filename)
    
    def save_state(self, state: DiscussionState) -> None:
        """
        Save the discussion state to disk.
        """
        os.makedirs(self.temp_dir, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load_state(self) -> DiscussionState:
        """
        Load the discussion state from disk.
        """
        if not os.path.exists(self.state_file):
            return DiscussionState(self.topic, self.roles)
        
        with open(self.state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return DiscussionState.from_dict(data, self.roles)


class DiscussionEngine:
    """
    Engine for running discussions.
    """
    def __init__(self, topic: str, roles: List[Role], state_dir: str = "./discussion_state", llm_client: Optional[LLMClient] = None):
        self.topic = topic
        self.roles = roles
        self.state_manager = DiskBasedDiscussionManager(topic, roles, state_dir)
        self.llm_client = llm_client or create_llm_client("mock")
        self.max_turns = 10
        self.use_streaming = False
        self.stream_callback = None
    
    def prepare_context(self, role: Role, max_recent_messages: int = 6) -> Dict[str, Any]:
        """
        Prepare the context for a role's turn.
        """
        state = self.state_manager.load_state()
        
        if len(state.messages) <= max_recent_messages:
            return {
                "full_context": state.messages,
                "summary": ""
            }
        
        recent_messages = state.messages[-max_recent_messages:]
        older_messages = state.messages[:-max_recent_messages]
        
        # In a real implementation, this would use an LLM to generate a summary
        # For now, we'll just use a placeholder
        summary = f"Summary of {len(older_messages)} previous messages about {self.topic}"
        
        return {
            "recent_messages": recent_messages,
            "summary": summary
        }
    
    def compress_context(self) -> None:
        """
        Compress the discussion context to save memory.
        """
        state = self.state_manager.load_state()
        
        if len(state.messages) > 6:  # Keep the most recent 6 messages
            older_messages = state.messages[:-6]
            
            # In a real implementation, this would use an LLM to generate a summary
            # For now, we'll just use a placeholder
            summary = f"Summary of {len(older_messages)} previous messages about {self.topic}"
            
            state.summary = summary
            state.messages = state.messages[-6:]
            self.state_manager.save_state(state)
    
    def check_consensus(self) -> bool:
        """
        Check if consensus has been reached.
        """
        state = self.state_manager.load_state()
        
        # Need at least one message from each role to check for consensus
        if state.turn < len(self.roles):
            return False
        
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in state.messages
        ]
        
        # Use rule-based consensus detection
        return check_consensus_rule_based(messages, self.topic)
    
    def create_prompt_for_role(self, role: Role, context: Dict[str, Any]) -> str:
        """
        Create a prompt for a role based on the context.
        """
        prompt = f"""You are a {role.role} participating in a discussion about '{self.topic}'.

Your role description:
{role.description}

Your responsibilities:
"""
        
        # Handle responsibilities (might be a list of lists or a list of strings)
        if role.responsibilities:
            if isinstance(role.responsibilities[0], list):
                for resp_group in role.responsibilities:
                    prompt += f"- {', '.join(resp_group)}\n"
            else:
                prompt += f"- {', '.join(role.responsibilities)}\n"
        
        prompt += "\nYour expertise:\n"
        
        # Handle expertise (might be a list of lists or a list of strings)
        if role.expertise:
            if isinstance(role.expertise[0], list):
                for exp_group in role.expertise:
                    prompt += f"- {', '.join(exp_group)}\n"
            else:
                prompt += f"- {', '.join(role.expertise)}\n"
        
        prompt += "\nYour characteristics:\n"
        
        # Handle characteristics (might be a list of lists or a list of strings)
        if role.characteristics:
            if isinstance(role.characteristics[0], list):
                for char_group in role.characteristics:
                    prompt += f"- {', '.join(char_group)}\n"
            else:
                prompt += f"- {', '.join(role.characteristics)}\n"
        
        prompt += "\n"
        
        # Add summary of older messages if available
        if "summary" in context and context["summary"]:
            prompt += f"\nSummary of previous discussion:\n{context['summary']}\n\n"
        
        # Add recent messages
        prompt += "\nRecent messages:\n"
        
        messages = context.get("recent_messages", context.get("full_context", []))
        for msg in messages:
            prompt += f"[{msg.role}]: {msg.content}\n\n"
        
        prompt += f"\nNow, as the {role.role}, provide your perspective on the topic. Be concise but thorough."
        
        return prompt
    
    def generate_response(self, role: Role, context: Dict[str, Any]) -> str:
        """
        Generate a response for a role.
        """
        prompt = self.create_prompt_for_role(role, context)
        
        # Print role name before generating response if streaming is enabled
        if self.use_streaming:
            print(f"\n[{role.role}]: ", end="", flush=True)
            
            # Define callback for streaming
            def stream_callback(chunk: str):
                print(chunk, end="", flush=True)
                if self.stream_callback:
                    self.stream_callback(role.role, chunk)
            
            # Check if we're using EnhancedOllamaClient with streaming support
            if isinstance(self.llm_client, EnhancedOllamaClient):
                response = self.llm_client.generate_streaming_response(
                    prompt, 
                    max_tokens=512, 
                    temperature=0.7,
                    callback=stream_callback
                )
                print()  # Add newline after streaming completes
                return response
        
        # Fall back to non-streaming response generation
        response = self.llm_client.generate_response(prompt, max_tokens=512, temperature=0.7)
        return response
    
    def run_discussion(self) -> Dict[str, Any]:
        """
        Run the discussion until consensus is reached or max turns is reached.
        """
        # Try to load existing state
        state = self.state_manager.load_state()
        
        # Print welcome message if this is a new discussion
        if not state.messages:
            welcome_message = Message(
                "System", 
                f"Welcome to the discussion on '{self.topic}'. "
                f"Participants: {', '.join(role.role for role in self.roles)}."
            )
            state.add_message(welcome_message)
            self.state_manager.save_state(state)
            
            print(f"[System]: {welcome_message.content}")
        else:
            print(f"Loaded existing discussion state with {len(state.messages)} messages.")
        
        # Run the discussion
        consensus_reached = state.consensus_reached
        
        while state.turn < self.max_turns and not consensus_reached:
            # Get the current role
            current_role_index = state.turn % len(self.roles)
            current_role = self.roles[current_role_index]
            
            # Prepare context for the current role
            context = self.prepare_context(current_role)
            
            # Generate response
            response = self.generate_response(current_role, context)
            
            # Create and add message
            message = Message(current_role.role, response)
            state.add_message(message)
            state.turn += 1
            
            # Save state
            self.state_manager.save_state(state)
            
            # Print message if not streaming (streaming already printed it)
            if not self.use_streaming:
                print(f"[{message.role}]: {message.content}")
            
            # Check for consensus
            consensus_reached = self.check_consensus()
            state.consensus_reached = consensus_reached
            self.state_manager.save_state(state)
            
            if consensus_reached:
                break
            
            # Compress context if needed
            if state.turn % 3 == 0:
                self.compress_context()
        
        # Create result
        result = {
            "topic": state.topic,
            "participants": [role.role for role in state.roles],
            "discussion": [message.to_dict() for message in state.messages],
            "turns": state.turn,
            "consensus_reached": consensus_reached
        }
        
        return result 