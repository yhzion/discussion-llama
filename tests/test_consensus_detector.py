import pytest
from discussion_llama.engine.consensus_detector import (
    extract_key_points,
    group_similar_points,
    check_consensus_rule_based,
    ConsensusDetector
)
from discussion_llama.llm.llm_client import MockLLMClient


def test_extract_key_points():
    # Test with marker words
    message = "This is a test message. The important point is that we need to focus on quality. Another key aspect is performance."
    points = extract_key_points(message)
    
    assert len(points) == 2
    assert "The important point is that we need to focus on quality" in points
    assert "Another key aspect is performance" in points
    
    # Test with no marker words
    message = "This is a test message. No marker words here. Just regular sentences."
    points = extract_key_points(message)
    
    assert len(points) == 3
    assert "This is a test message" in points
    
    # Test with max_points
    message = "Important point 1. Key point 2. Critical point 3. Essential point 4."
    points = extract_key_points(message, max_points=2)
    
    assert len(points) == 2


def test_group_similar_points():
    points = [
        "We should focus on performance",
        "Performance is the most important aspect",
        "Security is critical",
        "We need to ensure the system is secure",
        "Usability is also important"
    ]
    
    groups = group_similar_points(points)
    
    # We should have 3 groups: performance, security, usability
    assert len(groups) == 3
    
    # Check that similar points are grouped together
    performance_group = next((g for g in groups if "performance" in g[0].lower()), None)
    assert performance_group is not None
    assert len(performance_group) == 2
    
    security_group = next((g for g in groups if "security" in g[0].lower()), None)
    assert security_group is not None
    assert len(security_group) == 2
    
    usability_group = next((g for g in groups if "usability" in g[0].lower()), None)
    assert usability_group is not None
    assert len(usability_group) == 1


def test_check_consensus_rule_based():
    # Test with no consensus
    messages = [
        {"role": "role1", "content": "We should focus on performance."},
        {"role": "role2", "content": "Security is more important."},
        {"role": "role3", "content": "Usability is the key."},
        {"role": "role4", "content": "Cost is the main concern."}
    ]
    
    consensus = check_consensus_rule_based(messages)
    assert consensus is False
    
    # Test with consensus
    messages = [
        {"role": "role1", "content": "Performance is important. We should optimize the code."},
        {"role": "role2", "content": "I agree that performance is key. We need faster algorithms."},
        {"role": "role3", "content": "Performance is indeed critical. Let's focus on that."},
        {"role": "role4", "content": "While security matters, I agree that performance is the main issue."}
    ]
    
    consensus = check_consensus_rule_based(messages)
    assert consensus is True
    
    # Test with too few messages
    messages = [
        {"role": "role1", "content": "Performance is important."},
        {"role": "role2", "content": "I agree."}
    ]
    
    consensus = check_consensus_rule_based(messages)
    assert consensus is False


def test_consensus_detector():
    # Create a mock LLM client that always returns consensus
    mock_client = MockLLMClient({
        "consensus": "CONSENSUS: YES - All participants agree that performance is the main concern."
    })
    
    detector = ConsensusDetector(mock_client)
    
    # Test with messages that should trigger rule-based consensus
    messages = [
        {"role": "role1", "content": "Performance is important. We should optimize the code."},
        {"role": "role2", "content": "I agree that performance is key. We need faster algorithms."},
        {"role": "role3", "content": "Performance is indeed critical. Let's focus on that."},
        {"role": "role4", "content": "While security matters, I agree that performance is the main issue."}
    ]
    
    consensus = detector.check_consensus(messages, "test topic")
    assert consensus is True
    
    # Create a mock LLM client that returns no consensus
    mock_client = MockLLMClient({
        "consensus": "CONSENSUS: NO - There are still disagreements about priorities."
    })
    
    detector = ConsensusDetector(mock_client)
    
    # Test with messages that should not trigger rule-based consensus but should use LLM
    messages = [
        {"role": "role1", "content": "We should focus on performance."},
        {"role": "role2", "content": "Security is more important."},
        {"role": "role3", "content": "Usability is the key."},
        {"role": "role4", "content": "Cost is the main concern."}
    ]
    
    consensus = detector.check_consensus(messages, "test topic")
    assert consensus is False 