import os
import json
import time
import sys
import re
import difflib
from typing import Dict, List, Any, Optional, Callable, Tuple
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
        self.deadlock_detected = False
        self.deadlock_resolution_applied = False
    
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
            "roles": [role.role for role in self.roles],
            "messages": [message.to_dict() for message in self.messages],
            "summary": self.summary,
            "turn": self.turn,
            "consensus_reached": self.consensus_reached,
            "deadlock_detected": self.deadlock_detected,
            "deadlock_resolution_applied": self.deadlock_resolution_applied
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
        state.deadlock_detected = data.get("deadlock_detected", False)
        state.deadlock_resolution_applied = data.get("deadlock_resolution_applied", False)
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
    Manages a discussion between multiple roles.
    """
    def __init__(self, topic: str, roles: List[Role], state_dir: str = "./discussion_state", 
                 llm_client: Optional[LLMClient] = None, max_turns: int = 100,
                 use_streaming: bool = False, deadlock_detection_enabled: bool = False,
                 deadlock_threshold: float = 0.85, hierarchical_mode: bool = False):
        self.topic = topic
        self.roles = roles
        self.state_manager = DiskBasedDiscussionManager(topic, roles, state_dir)
        self.llm_client = llm_client or create_llm_client()
        self.max_turns = max_turns
        self.use_streaming = use_streaming
        self.deadlock_detection_enabled = deadlock_detection_enabled
        self.deadlock_threshold = deadlock_threshold
        self.hierarchical_mode = hierarchical_mode
        
        # Initialize hierarchical structure if enabled
        if self.hierarchical_mode:
            self.role_hierarchy_map = self._build_hierarchy_map()
            self.next_speaker_override = None
        else:
            self.role_hierarchy_map = {}
            self.next_speaker_override = None
        
        self.deadlock_resolution_strategies = [
            self._introduce_new_perspective,
            self._suggest_compromise,
            self._reframe_discussion
        ]
    
    def _build_hierarchy_map(self) -> Dict[str, Dict[str, Any]]:
        """
        Build a map of the hierarchical relationships between roles.
        
        Returns:
            Dict[str, Dict[str, Any]]: A dictionary mapping role names to their hierarchy information
        """
        hierarchy_map = {}
        
        # First pass: add all roles to the map
        for role in self.roles:
            hierarchy_map[role.role] = {
                "level": role.hierarchy_level,
                "superior": role.superior,
                "subordinates": role.subordinates,
                "role_obj": role
            }
        
        # Second pass: validate and fix any inconsistencies
        for role_name, info in hierarchy_map.items():
            # Ensure superior exists if specified
            if info["superior"] and info["superior"] not in hierarchy_map:
                print(f"Warning: Superior '{info['superior']}' for role '{role_name}' not found in roles.")
                info["superior"] = ""
            
            # Ensure subordinates exist
            valid_subordinates = []
            for sub in info["subordinates"]:
                if sub in hierarchy_map:
                    valid_subordinates.append(sub)
                else:
                    print(f"Warning: Subordinate '{sub}' for role '{role_name}' not found in roles.")
            
            info["subordinates"] = valid_subordinates
            
            # Ensure bidirectional relationships
            if info["superior"] and role_name not in hierarchy_map[info["superior"]]["subordinates"]:
                hierarchy_map[info["superior"]]["subordinates"].append(role_name)
            
            for sub in info["subordinates"]:
                if hierarchy_map[sub]["superior"] != role_name:
                    hierarchy_map[sub]["superior"] = role_name
        
        return hierarchy_map

    def prepare_context(self, role: Role, max_recent_messages: int = 6) -> Dict[str, Any]:
        """
        Prepare context for a role to generate a response.
        
        Args:
            role: The role to prepare context for
            max_recent_messages: Maximum number of recent messages to include
            
        Returns:
            Dict[str, Any]: Context for the role
        """
        state = self.state_manager.load_state()
        
        # Get recent messages
        recent_messages = []
        if state.messages:
            recent_messages = state.messages[-min(max_recent_messages, len(state.messages)):]
        
        # Format messages for context
        formatted_messages = []
        for msg in recent_messages:
            formatted_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Create context
        context = {
            "topic": state.topic,
            "messages": formatted_messages,
            "current_role": role.role,
            "turn": state.turn
        }
        
        # Add hierarchical context if enabled
        if self.hierarchical_mode and role.hierarchy_level > 0:
            hierarchy_context = self._prepare_hierarchical_context(role)
            context.update(hierarchy_context)
        
        return context
    
    def _prepare_hierarchical_context(self, role: Role) -> Dict[str, Any]:
        """
        Prepare hierarchical context for a role.
        
        Args:
            role: The role to prepare hierarchical context for
            
        Returns:
            Dict[str, Any]: Hierarchical context
        """
        hierarchy_context = {
            "hierarchy_level": role.hierarchy_level,
            "superior": role.superior,
            "subordinates": role.subordinates,
            "hierarchy_guidance": ""
        }
        
        # Add specific guidance based on hierarchy level
        if role.hierarchy_level == 1:  # Top level
            hierarchy_context["hierarchy_guidance"] = (
                "As the highest-ranking participant, you should provide strategic direction "
                "and make final decisions when necessary. Guide the discussion toward consensus "
                "while considering input from all participants."
            )
        elif role.superior and not role.subordinates:  # Bottom level
            hierarchy_context["hierarchy_guidance"] = (
                f"As a team member reporting to {role.superior}, provide your expertise and perspective "
                f"while respecting the authority of higher-ranking participants. If a decision seems "
                f"beyond your authority, consider suggesting escalation to your superior."
            )
        elif role.superior and role.subordinates:  # Middle level
            hierarchy_context["hierarchy_guidance"] = (
                f"As a middle manager reporting to {role.superior} and overseeing {', '.join(role.subordinates)}, "
                f"you should balance providing your expertise with respecting the authority structure. "
                f"Support your subordinates while aligning with strategic direction from above."
            )
        
        return hierarchy_context

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
        Create a prompt for a specific role based on the discussion context.
        
        Args:
            role: The role to create a prompt for
            context: The discussion context
            
        Returns:
            A formatted prompt string
        """
        # Get the language of the topic
        topic_language = self.llm_client.detect_language(self.topic) if hasattr(self.llm_client, 'detect_language') else 'en'
        
        # Get role description
        role_description = role.get_prompt_description()
        
        # Format the prompt based on language
        if topic_language == 'ko':
            prompt = f"{role_description}\n\n"
            prompt += f"토론 주제: {self.topic}\n\n"
            
            if context.get("messages", []):
                prompt += "이전 대화:\n"
                for msg in context["messages"]:
                    prompt += f"[{msg['role']}]: {msg['content']}\n\n"
            
            if self.hierarchical_mode:
                # Add hierarchical context for Korean
                if context.get("superior"):
                    prompt += f"당신의 상급자: {context['superior']}\n"
                
                if context.get("subordinates"):
                    subordinates_str = ", ".join(context["subordinates"])
                    prompt += f"당신의 부하직원: {subordinates_str}\n"
                
                if context.get("escalated_decisions"):
                    prompt += "\n상급자에게 에스컬레이션된 결정:\n"
                    for decision in context["escalated_decisions"]:
                        prompt += f"- {decision}\n"
                
                prompt += "\n"
            
            # 더 자연스럽고 간결한 구어체 스타일의 지시사항
            prompt += "이제 당신 차례입니다. 다음 지침을 따라주세요:\n\n"
            prompt += "1. 간결하고 자연스러운 구어체로 대화하세요. 짧고 명확한 문장을 사용하세요.\n"
            prompt += "2. 당신의 역할과 전문성을 바탕으로 의견을 제시하되, 너무 형식적이거나 길게 설명하지 마세요.\n"
            prompt += "3. 다른 참가자들의 의견에 자연스럽게 반응하고, 실제 대화처럼 이어나가세요.\n"
            prompt += "4. 합의점을 찾기 위해 노력하되, 필요한 경우 명확한 의견 차이를 표현하세요.\n"
            
            if self.hierarchical_mode:
                prompt += "5. 조직 구조를 존중하되, 너무 형식적인 표현은 피하세요.\n"
            
            prompt += "\n한국어로 응답하되, 실제 회의나 대화에서 사용할 법한 자연스러운 말투를 사용하세요. 2-3문장 정도의 간결한 응답이 좋습니다.\n"
        else:
            # English or other language prompt (default)
            prompt = f"{role_description}\n\n"
            prompt += f"Discussion Topic: {self.topic}\n\n"
            
            if context.get("messages", []):
                prompt += "Previous conversation:\n"
                for msg in context["messages"]:
                    prompt += f"[{msg['role']}]: {msg['content']}\n\n"
            
            if self.hierarchical_mode:
                # Add hierarchical context
                if context.get("superior"):
                    prompt += f"Your superior: {context['superior']}\n"
                
                if context.get("subordinates"):
                    subordinates_str = ", ".join(context["subordinates"])
                    prompt += f"Your subordinates: {subordinates_str}\n"
                
                if context.get("escalated_decisions"):
                    prompt += "\nDecisions escalated to superiors:\n"
                    for decision in context["escalated_decisions"]:
                        prompt += f"- {decision}\n"
                
                prompt += "\n"
            
            # More conversational and concise style instructions
            prompt += "It's now your turn. Please follow these guidelines:\n\n"
            prompt += "1. Speak in a concise, conversational tone. Use short, clear sentences.\n"
            prompt += "2. Express opinions based on your role and expertise, but avoid being overly formal or lengthy.\n"
            prompt += "3. Respond naturally to other participants, as in a real conversation.\n"
            prompt += "4. Work toward consensus while clearly expressing differences when necessary.\n"
            
            if self.hierarchical_mode:
                prompt += "5. Respect the organizational structure, but avoid overly formal expressions.\n"
            
            prompt += "\nRespond in a natural, conversational style as you would in an actual meeting. A response of 2-3 sentences is ideal.\n"
        
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
    
    def detect_deadlock(self) -> bool:
        """
        Detect if the discussion is in a deadlock state by analyzing recent messages.
        
        A deadlock is detected when:
        1. Messages from the same role are becoming repetitive (high similarity)
        2. No progress is being made toward consensus
        3. Participants are repeating the same arguments
        
        Returns:
            bool: True if deadlock is detected, False otherwise
        """
        state = self.state_manager.load_state()
        
        # Need at least 4 messages to detect a deadlock
        if len(state.messages) < 4:
            return False
        
        # If deadlock was already detected and resolved, don't detect it again too soon
        if state.deadlock_detected and state.deadlock_resolution_applied:
            # Only check for deadlock again after at least 4 more messages
            last_resolution_index = max(
                [i for i, msg in enumerate(state.messages) 
                 if msg.role == "System" and "deadlock" in msg.content.lower()], 
                default=-1
            )
            
            if last_resolution_index != -1 and len(state.messages) - last_resolution_index < 4:
                return False
        
        # Get the last 6 messages or all if less than 6
        recent_messages = state.messages[-min(6, len(state.messages)):]
        
        # Check for repetitive content from the same role
        role_messages = {}
        for message in recent_messages:
            if message.role not in role_messages:
                role_messages[message.role] = []
            role_messages[message.role].append(message.content)
        
        # For each role, check if their messages are becoming repetitive
        for role, messages in role_messages.items():
            if len(messages) >= 2:
                # Calculate similarity between consecutive messages from the same role
                for i in range(len(messages) - 1):
                    similarity = self._calculate_text_similarity(messages[i], messages[i+1])
                    if similarity > self.deadlock_threshold:
                        return True
        
        # Check for back-and-forth pattern with little progress
        if len(recent_messages) >= 4:
            # Extract key points from each message
            key_points = [self._extract_key_points(msg.content) for msg in recent_messages]
            
            # Check if the same points are being repeated
            repeated_points = 0
            total_points = 0
            
            for i in range(len(key_points)):
                for point in key_points[i]:
                    total_points += 1
                    # Check if this point appears in previous messages
                    for j in range(max(0, i-2), i):
                        if any(self._calculate_text_similarity(point, prev_point) > 0.7 
                               for prev_point in key_points[j]):
                            repeated_points += 1
                            break
            
            # If more than 70% of points are repetitions, consider it a deadlock
            if total_points > 0 and repeated_points / total_points > 0.7:
                return True
        
        return False
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings using difflib.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            float: Similarity score between 0 and 1
        """
        # Normalize texts
        text1 = re.sub(r'\s+', ' ', text1.lower().strip())
        text2 = re.sub(r'\s+', ' ', text2.lower().strip())
        
        # Calculate similarity using difflib
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def _extract_key_points(self, text: str) -> List[str]:
        """
        Extract key points from a text.
        
        Args:
            text: The text to extract key points from
            
        Returns:
            List[str]: List of key points
        """
        # Simple implementation: split by sentences and filter
        sentences = re.split(r'[.!?]\s+', text)
        
        # Filter out short sentences and sentences without meaningful content
        key_points = [
            sentence.strip() for sentence in sentences 
            if len(sentence.strip()) > 20 and not sentence.strip().startswith("I ")
        ]
        
        return key_points
    
    def resolve_deadlock(self) -> Message:
        """
        Apply a strategy to resolve the detected deadlock.
        
        Returns:
            Message: The system message added to resolve the deadlock
        """
        state = self.state_manager.load_state()
        
        # Choose a resolution strategy
        strategy_index = state.turn % len(self.deadlock_resolution_strategies)
        resolution_strategy = self.deadlock_resolution_strategies[strategy_index]
        
        # Apply the chosen strategy
        resolution_message = resolution_strategy()
        
        # Update state
        state.add_message(resolution_message)
        state.deadlock_detected = True
        state.deadlock_resolution_applied = True
        self.state_manager.save_state(state)
        
        # Print the resolution message
        print(f"[{resolution_message.role}]: {resolution_message.content}")
        
        return resolution_message
    
    def _introduce_new_perspective(self) -> Message:
        """
        Introduce a new perspective to help break the deadlock.
        
        Returns:
            Message: System message with a new perspective
        """
        state = self.state_manager.load_state()
        
        # Create a prompt for the LLM to generate a new perspective
        prompt = (
            f"The discussion on '{state.topic}' appears to be in a deadlock. "
            f"Participants are repeating their positions without making progress. "
            f"Please suggest a completely new perspective or angle that hasn't been considered yet. "
            f"This should be a thoughtful, neutral contribution that could help move the discussion forward."
        )
        
        # Generate a new perspective using the LLM
        new_perspective = self.llm_client.generate(prompt)
        
        # Create a system message with the new perspective
        content = (
            f"I notice this discussion may be reaching a deadlock. Let me introduce a new perspective: "
            f"{new_perspective}"
        )
        
        return Message("System (Mediator)", content)
    
    def _suggest_compromise(self) -> Message:
        """
        Suggest a potential compromise to help break the deadlock.
        
        Returns:
            Message: System message with a compromise suggestion
        """
        state = self.state_manager.load_state()
        
        # Get recent messages to analyze positions
        recent_messages = state.messages[-min(10, len(state.messages)):]
        recent_content = "\n".join([f"{msg.role}: {msg.content}" for msg in recent_messages])
        
        # Create a prompt for the LLM to suggest a compromise
        prompt = (
            f"The discussion on '{state.topic}' appears to be in a deadlock. "
            f"Here are the recent messages:\n\n{recent_content}\n\n"
            f"Based on these messages, please suggest a thoughtful compromise that acknowledges "
            f"the valid points from different perspectives and offers a middle ground. "
            f"This should be a balanced suggestion that respects all viewpoints."
        )
        
        # Generate a compromise suggestion using the LLM
        compromise = self.llm_client.generate(prompt)
        
        # Create a system message with the compromise suggestion
        content = (
            f"I notice we may be at an impasse. Let me suggest a possible compromise: "
            f"{compromise}"
        )
        
        return Message("System (Mediator)", content)
    
    def _reframe_discussion(self) -> Message:
        """
        Reframe the discussion to help break the deadlock.
        
        Returns:
            Message: System message with a reframed discussion
        """
        state = self.state_manager.load_state()
        
        # Create a prompt for the LLM to reframe the discussion
        prompt = (
            f"The discussion on '{state.topic}' appears to be in a deadlock. "
            f"Please reframe the discussion by identifying the underlying interests and values "
            f"rather than the stated positions. What are the deeper needs or concerns that "
            f"might not be explicitly stated? How could the discussion be restructured to "
            f"address these underlying interests?"
        )
        
        # Generate a reframing using the LLM
        reframing = self.llm_client.generate(prompt)
        
        # Create a system message with the reframing
        content = (
            f"I notice we may be talking past each other. Let me try to reframe this discussion: "
            f"{reframing}"
        )
        
        return Message("System (Mediator)", content)
    
    def detect_escalation(self, role_name: str) -> bool:
        """
        Detect if a message from a role indicates the need for escalation to a superior.
        
        Args:
            role_name: The name of the role that sent the message
            
        Returns:
            bool: True if escalation is needed, False otherwise
        """
        if not self.hierarchical_mode:
            return False
        
        state = self.state_manager.load_state()
        
        # Need at least one message to detect escalation
        if not state.messages:
            return False
        
        # Get the last message from the specified role
        role_messages = [msg for msg in state.messages if msg.role == role_name]
        if not role_messages:
            return False
        
        last_message = role_messages[-1]
        
        # Check for escalation keywords in the message
        escalation_keywords = [
            "escalate", "refer to", "defer to", "beyond my authority",
            "need approval", "higher decision", "superior", "manager"
        ]
        
        message_lower = last_message.content.lower()
        
        # Check if any escalation keyword is in the message
        for keyword in escalation_keywords:
            if keyword in message_lower:
                # If a superior is mentioned specifically, check if it's valid
                if self.role_hierarchy_map.get(role_name, {}).get("superior", ""):
                    superior = self.role_hierarchy_map[role_name]["superior"]
                    if superior.lower() in message_lower:
                        return True
                    
                    # Generic escalation mention
                    return True
        
        return False

    def handle_escalation(self, role_name: str) -> Dict[str, Any]:
        """
        Handle escalation from a role to its superior.
        
        Args:
            role_name: The name of the role requesting escalation
            
        Returns:
            Dict[str, Any]: Information about the escalation
        """
        if not self.hierarchical_mode:
            return {"escalated": False, "reason": "Hierarchical mode not enabled"}
        
        # Check if the role exists and has a superior
        if role_name not in self.role_hierarchy_map:
            return {"escalated": False, "reason": f"Role '{role_name}' not found"}
        
        superior = self.role_hierarchy_map[role_name]["superior"]
        if not superior:
            return {"escalated": False, "reason": f"Role '{role_name}' has no superior"}
        
        # Set the next speaker to be the superior
        self.next_speaker_override = superior
        
        # Add a system message about the escalation
        state = self.state_manager.load_state()
        escalation_message = Message(
            "System",
            f"The {role_name} has escalated this matter to their superior, {superior}."
        )
        state.add_message(escalation_message)
        self.state_manager.save_state(state)
        
        # Print the escalation message
        print(f"[{escalation_message.role}]: {escalation_message.content}")
        
        return {
            "escalated": True,
            "from_role": role_name,
            "escalated_to": superior,
            "message": escalation_message.content
        }

    def get_next_speaker(self) -> str:
        """
        Determine the next speaker in the discussion based on the current state and hierarchy.
        
        Returns:
            str: The role name of the next speaker
        """
        state = self.state_manager.load_state()
        
        # If there's an override from escalation, use it
        if self.next_speaker_override:
            next_speaker = self.next_speaker_override
            self.next_speaker_override = None
            return next_speaker
        
        # Default round-robin approach if hierarchical mode is disabled
        if not self.hierarchical_mode:
            current_role_index = state.turn % len(self.roles)
            return self.roles[current_role_index].role
        
        # Hierarchical approach
        # In the first round, start with highest-ranking roles
        if state.turn < len(self.roles):
            # Sort roles by hierarchy level (ascending, so lower numbers = higher rank)
            sorted_roles = sorted(self.roles, key=lambda r: r.hierarchy_level or 999)
            return sorted_roles[state.turn].role
        
        # After first round, use a modified round-robin that respects recent speakers
        recent_speakers = []
        if len(state.messages) >= len(self.roles):
            recent_speakers = [
                msg.role for msg in state.messages[-len(self.roles):]
                if msg.role in [role.role for role in self.roles]
            ]
        
        # Find roles that haven't spoken recently
        available_roles = [role for role in self.roles if role.role not in recent_speakers]
        
        # If all roles have spoken recently, use standard round-robin
        if not available_roles:
            current_role_index = state.turn % len(self.roles)
            return self.roles[current_role_index].role
        
        # Otherwise, choose the highest-ranking available role
        sorted_available = sorted(available_roles, key=lambda r: r.hierarchy_level or 999)
        return sorted_available[0].role

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
            
            # If hierarchical mode is enabled, add an explanation
            if self.hierarchical_mode:
                hierarchy_message = Message(
                    "System",
                    "This discussion will follow a hierarchical structure where higher-ranking "
                    "participants may have more authority in decision-making. Participants may "
                    "escalate matters to their superiors when appropriate."
                )
                state.add_message(hierarchy_message)
                self.state_manager.save_state(state)
                
                print(f"[System]: {hierarchy_message.content}")
        else:
            print(f"Loaded existing discussion state with {len(state.messages)} messages.")
        
        # Run the discussion
        consensus_reached = state.consensus_reached
        
        while state.turn < self.max_turns and not consensus_reached:
            # Check for deadlock if enabled
            if self.deadlock_detection_enabled and self.detect_deadlock():
                self.resolve_deadlock()
            
            # Get the next speaker based on hierarchy or round-robin
            if self.hierarchical_mode:
                next_speaker_role = self.get_next_speaker()
                current_role = next(role for role in self.roles if role.role == next_speaker_role)
            else:
                # Standard round-robin approach
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
            
            # Check for escalation if hierarchical mode is enabled
            if self.hierarchical_mode and self.detect_escalation(current_role.role):
                self.handle_escalation(current_role.role)
            
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
            "consensus_reached": consensus_reached,
            "deadlock_detected": state.deadlock_detected,
            "deadlock_resolution_applied": state.deadlock_resolution_applied,
            "hierarchical_mode": self.hierarchical_mode
        }
        
        return result 