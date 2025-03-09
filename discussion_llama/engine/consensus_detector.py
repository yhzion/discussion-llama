from typing import Dict, List, Any, Optional
from ..llm.llm_client import LLMClient


def extract_key_points(message: str, max_points: int = 3) -> List[str]:
    """
    Extract key points from a message using simple rule-based approach.
    In a real implementation, this would use more sophisticated NLP techniques.
    """
    sentences = message.split('.')
    key_points = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Simple heuristic: look for sentences with marker words
        if any(marker in sentence.lower() for marker in [
            "important", "key", "critical", "essential", "main", "primary",
            "crucial", "vital", "significant", "fundamental", "central",
            "agree", "consensus", "concur", "support", "endorse", "approve",
            "suggest", "propose", "recommend", "advise", "advocate"
        ]):
            key_points.append(sentence)
            if len(key_points) >= max_points:
                break
    
    # If we didn't find any key points with markers, just take the first few sentences
    if not key_points and sentences:
        key_points = [s.strip() for s in sentences[:max_points] if s.strip()]
    
    return key_points


def group_similar_points(points: List[str]) -> List[List[str]]:
    """
    Group similar points together using simple string matching.
    In a real implementation, this would use semantic similarity.
    """
    if not points:
        return []
    
    groups = []
    used_indices = set()
    
    for i, point in enumerate(points):
        if i in used_indices:
            continue
        
        current_group = [point]
        used_indices.add(i)
        
        # Find similar points
        for j, other_point in enumerate(points):
            if j in used_indices or i == j:
                continue
            
            # Simple similarity: check if there are common words
            # In a real implementation, use embedding similarity
            point_words = set(point.lower().split())
            other_words = set(other_point.lower().split())
            common_words = point_words.intersection(other_words)
            
            # If there are enough common words, consider them similar
            if len(common_words) >= min(3, len(point_words) // 3):
                current_group.append(other_point)
                used_indices.add(j)
        
        groups.append(current_group)
    
    return groups


def check_consensus_rule_based(messages: List[Dict[str, Any]], topic: str, threshold: float = 0.7) -> bool:
    """
    Check for consensus using a rule-based approach.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        topic: The discussion topic
        threshold: Threshold for agreement ratio (0.0 to 1.0)
        
    Returns:
        True if consensus is detected, False otherwise
    """
    if len(messages) < 4:  # Need at least a few messages to detect consensus
        return False
    
    # Ensure threshold is a float
    try:
        threshold = float(threshold)
    except (ValueError, TypeError):
        threshold = 0.7  # Default to 0.7 if conversion fails
    
    # 합의 키워드 찾기
    consensus_keywords = [
        "agree", "consensus", "concur", "support", "endorse", "approve",
        "same page", "aligned", "common ground", "mutual agreement"
    ]
    
    # 각 메시지에서 합의 키워드 찾기
    agreement_count = 0
    unique_roles = set()
    
    for msg in messages:
        unique_roles.add(msg["role"])
        content = msg["content"].lower()
        
        # 합의 키워드가 있는지 확인
        if any(keyword in content for keyword in consensus_keywords):
            agreement_count += 1
    
    # 합의 비율 계산
    if len(unique_roles) > 0:
        agreement_ratio = agreement_count / len(unique_roles)
        return agreement_ratio >= threshold
    
    return False


def check_consensus_with_llm(messages: List[Dict[str, Any]], topic: str, llm_client: LLMClient) -> bool:
    """
    Check for consensus using an LLM.
    """
    if len(messages) < 3:  # Need at least a few messages to detect consensus
        return False
    
    # Format messages for the prompt
    formatted_messages = ""
    for i, msg in enumerate(messages[-6:]):  # Use the most recent messages
        formatted_messages += f"[{msg['role']}]: {msg['content']}\n\n"
    
    # Create a prompt for consensus detection
    consensus_prompt = f"""
    Below is a discussion about the topic "{topic}":
    
    {formatted_messages}
    
    Based on the discussion above, has a consensus been reached among the participants?
    A consensus means that all or most participants agree on key points or a solution.
    
    Analyze the discussion carefully and respond with either:
    "CONSENSUS: YES" if there is clear agreement on main points.
    "CONSENSUS: NO" if there are still significant disagreements or unresolved issues.
    
    Provide a brief explanation for your decision.
    """
    
    # Get response from LLM
    response = llm_client.generate_response(consensus_prompt, max_tokens=150)
    
    # Check if the response indicates consensus
    return "CONSENSUS: YES" in response.upper()


class ConsensusDetector:
    """
    Detects consensus in a discussion.
    """
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client
    
    def check_consensus(self, messages: List[Dict[str, Any]], topic: str) -> bool:
        """
        Check if consensus has been reached in the discussion.
        """
        # First try rule-based approach
        rule_based_result = check_consensus_rule_based(messages, topic)
        
        # If we have an LLM client and rule-based approach is inconclusive,
        # use the LLM for a more sophisticated check
        if not rule_based_result and self.llm_client:
            return check_consensus_with_llm(messages, topic, self.llm_client)
        
        return rule_based_result 