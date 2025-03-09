import pytest
from unittest.mock import patch, MagicMock
from discussion_llama.engine.consensus_detector import (
    extract_key_points,
    group_similar_points,
    check_consensus_rule_based,
    ConsensusDetector
)
from discussion_llama.llm.llm_client import MockLLMClient


def test_extract_key_points_with_complex_text():
    """Test key point extraction with more complex text structures."""
    # Test with complex sentences and multiple marker words
    message = """
    This is a complex message with multiple points.
    
    First, we need to consider security implications. This is critical for our system.
    
    Second point: performance optimization is necessary for user satisfaction.
    
    The key insight here is that we need to balance both security and performance.
    
    Another important consideration is cost, which we cannot ignore.
    
    Finally, I believe that maintainability should be our guiding principle.
    """
    
    points = extract_key_points(message)
    
    assert len(points) >= 5
    assert any("security implications" in p for p in points)
    assert any("performance optimization" in p for p in points)
    assert any("balance both security and performance" in p for p in points)
    assert any("cost" in p for p in points)
    assert any("maintainability" in p for p in points)


def test_group_similar_points_with_synonyms():
    """Test grouping of points that use synonyms or related concepts."""
    points = [
        "Security is our top priority",
        "We must ensure the system is secure",
        "Data protection is essential",
        "Performance optimization is necessary",
        "The system needs to be fast and responsive",
        "Speed is critical for user experience",
        "Cost considerations cannot be ignored",
        "Budget constraints are important"
    ]
    
    groups = group_similar_points(points)
    
    # We should have 3 groups: security, performance, cost
    assert len(groups) == 3
    
    # Check that similar points using different words are grouped together
    security_group = next((g for g in groups if "security" in g[0].lower()), None)
    assert security_group is not None
    assert len(security_group) == 3
    assert any("data protection" in p.lower() for p in security_group)
    
    performance_group = next((g for g in groups if "performance" in g[0].lower()), None)
    assert performance_group is not None
    assert len(performance_group) == 3
    assert any("speed" in p.lower() for p in performance_group)
    
    cost_group = next((g for g in groups if "cost" in g[0].lower()), None)
    assert cost_group is not None
    assert len(cost_group) == 2
    assert any("budget" in p.lower() for p in cost_group)


def test_check_consensus_with_partial_agreement():
    """Test consensus detection with partial agreement among participants."""
    # Test with partial agreement (3 out of 4 agree)
    messages = [
        {"role": "role1", "content": "Security is our top priority. We need to focus on that first."},
        {"role": "role2", "content": "I agree that security is important, but we also need to consider performance."},
        {"role": "role3", "content": "Security should be our main focus, though performance is also relevant."},
        {"role": "role4", "content": "I disagree. Performance is more critical than security for our users."}
    ]
    
    # This should detect partial consensus on security being important
    consensus = check_consensus_rule_based(messages, threshold=0.75)
    assert consensus is True
    
    # With a higher threshold, it should not detect consensus
    consensus = check_consensus_rule_based(messages, threshold=0.9)
    assert consensus is False


def test_check_consensus_with_implicit_agreement():
    """Test consensus detection with implicit agreement through different wording."""
    messages = [
        {"role": "role1", "content": "Data protection must be our focus."},
        {"role": "role2", "content": "Security is the most important aspect."},
        {"role": "role3", "content": "We need to ensure our system is secure from attacks."},
        {"role": "role4", "content": "Privacy and security should be prioritized."}
    ]
    
    # All messages refer to security/protection/privacy, so consensus should be detected
    consensus = check_consensus_rule_based(messages)
    assert consensus is True


def test_consensus_detector_with_complex_discussion():
    """Test the consensus detector with a more complex discussion scenario."""
    # Create a mock LLM client
    mock_client = MockLLMClient()
    detector = ConsensusDetector(mock_client)
    
    # Test with a complex discussion where consensus is not immediately obvious
    messages = [
        {"role": "Product Manager", "content": "I think we should prioritize new features to stay competitive."},
        {"role": "Engineer", "content": "We need to focus on fixing bugs and improving stability before adding features."},
        {"role": "Designer", "content": "User experience improvements should be our focus, which includes both bug fixes and some new features."},
        {"role": "QA", "content": "Quality should be our priority, so I agree with fixing bugs first."},
        {"role": "Product Manager", "content": "I see the points about stability. Perhaps we can focus on critical bug fixes while still planning for key features."},
        {"role": "Engineer", "content": "That sounds reasonable. We can prioritize critical bugs and then move to the most important features."},
        {"role": "Designer", "content": "I agree with this balanced approach of fixing critical issues first, then adding carefully selected features."},
        {"role": "QA", "content": "This makes sense to me. Fix the critical bugs first, then add new features with proper testing."}
    ]
    
    # The first 4 messages should not show consensus
    early_messages = messages[:4]
    consensus = detector.check_consensus(early_messages, "Project priorities")
    assert consensus is False
    
    # The full conversation should show consensus on the balanced approach
    consensus = detector.check_consensus(messages, "Project priorities")
    assert consensus is True


def test_consensus_detector_with_llm_fallback():
    """Test that the consensus detector falls back to LLM when rule-based detection is uncertain."""
    # Create a mock LLM client that returns consensus
    mock_client = MockLLMClient({
        "consensus": "CONSENSUS: YES - The participants have reached agreement on prioritizing security while acknowledging performance."
    })
    
    detector = ConsensusDetector(mock_client)
    
    # Test with messages that are ambiguous for rule-based detection
    messages = [
        {"role": "role1", "content": "Security is important, but we need to balance it with performance."},
        {"role": "role2", "content": "Performance is critical, though security cannot be ignored."},
        {"role": "role3", "content": "We need both security and performance to be successful."},
        {"role": "role4", "content": "A balanced approach to security and performance is necessary."}
    ]
    
    # Force the rule-based detection to be uncertain by setting a high threshold
    with patch('discussion_llama.engine.consensus_detector.check_consensus_rule_based', return_value=None):
        consensus = detector.check_consensus(messages, "Security vs Performance")
        assert consensus is True


def test_consensus_detector_with_changing_opinions():
    """Test consensus detection when participants change their opinions during discussion."""
    mock_client = MockLLMClient()
    detector = ConsensusDetector(mock_client)
    
    # Initial disagreement
    initial_messages = [
        {"role": "role1", "content": "We should use a microservice architecture."},
        {"role": "role2", "content": "I disagree, a monolithic approach would be simpler."},
        {"role": "role3", "content": "I'm leaning toward microservices for scalability."},
        {"role": "role4", "content": "Monolithic is better for our small team."}
    ]
    
    consensus = detector.check_consensus(initial_messages, "Architecture decision")
    assert consensus is False
    
    # Later messages show changing opinions and convergence
    later_messages = initial_messages + [
        {"role": "role1", "content": "I see the points about team size. Perhaps a modular monolith would be a good compromise."},
        {"role": "role2", "content": "A modular monolith does address many of my concerns while providing some benefits of microservices."},
        {"role": "role3", "content": "I can support a modular monolith approach as it gives us flexibility to evolve later."},
        {"role": "role4", "content": "Modular monolith seems like the right balance for our current situation and future needs."}
    ]
    
    consensus = detector.check_consensus(later_messages, "Architecture decision")
    assert consensus is True


def test_consensus_detector_with_topic_specific_detection():
    """Test that consensus detection considers the discussion topic."""
    mock_client = MockLLMClient()
    detector = ConsensusDetector(mock_client)
    
    # Test with a specific topic
    messages = [
        {"role": "role1", "content": "For the authentication system, JWT is the best approach."},
        {"role": "role2", "content": "I agree that JWT works well for our authentication needs."},
        {"role": "role3", "content": "JWT with proper expiration policies would be secure for authentication."},
        {"role": "role4", "content": "JWT is industry standard for authentication and makes sense for us."}
    ]
    
    consensus = detector.check_consensus(messages, "Authentication mechanism")
    assert consensus is True
    
    # Same messages but different topic should not necessarily show consensus
    consensus = detector.check_consensus(messages, "Overall system architecture")
    assert consensus is False


def test_sentiment_analysis_for_consensus():
    """Test that sentiment analysis is used to detect agreement/disagreement."""
    # Create messages with clear sentiment indicators
    messages = [
        {"role": "role1", "content": "I strongly support using React for our frontend."},
        {"role": "role2", "content": "React is definitely the right choice for our needs."},
        {"role": "role3", "content": "I'm enthusiastic about using React for this project."},
        {"role": "role4", "content": "While I have some concerns about the learning curve, I can see why React is a good fit."}
    ]
    
    # Create a detector with sentiment analysis capability
    mock_client = MockLLMClient()
    detector = ConsensusDetector(mock_client)
    
    # Test that positive sentiment is detected as agreement
    consensus = detector.check_consensus(messages, "Frontend framework selection")
    assert consensus is True
    
    # Test with mixed sentiment
    mixed_messages = [
        {"role": "role1", "content": "I strongly support using React for our frontend."},
        {"role": "role2", "content": "React is definitely the right choice for our needs."},
        {"role": "role3", "content": "I'm not convinced React is the best option. Vue might be better."},
        {"role": "role4", "content": "I'm skeptical about React. Angular has better enterprise support."}
    ]
    
    consensus = detector.check_consensus(mixed_messages, "Frontend framework selection")
    assert consensus is False


def test_temporal_analysis_for_consensus():
    """Test that temporal analysis tracks opinion changes over time."""
    # Create a sequence of messages showing opinion evolution
    messages = [
        {"role": "role1", "content": "We should use a microservice architecture.", "timestamp": 1},
        {"role": "role2", "content": "I prefer a monolithic approach.", "timestamp": 2},
        {"role": "role1", "content": "After considering your points, a modular monolith might be better.", "timestamp": 3},
        {"role": "role2", "content": "I agree that a modular monolith is a good compromise.", "timestamp": 4}
    ]
    
    mock_client = MockLLMClient()
    detector = ConsensusDetector(mock_client)
    
    # Test that later opinions are weighted more heavily
    consensus = detector.check_consensus_with_temporal_analysis(messages, "Architecture decision")
    assert consensus is True
    
    # Test with opinions that diverge over time
    diverging_messages = [
        {"role": "role1", "content": "We should use a microservice architecture.", "timestamp": 1},
        {"role": "role2", "content": "I agree with using microservices.", "timestamp": 2},
        {"role": "role1", "content": "On second thought, I'm concerned about the complexity of microservices.", "timestamp": 3},
        {"role": "role2", "content": "I still believe microservices are the right approach.", "timestamp": 4}
    ]
    
    consensus = detector.check_consensus_with_temporal_analysis(diverging_messages, "Architecture decision")
    assert consensus is False


def test_weighted_consensus_by_expertise():
    """Test that consensus detection weights opinions based on role expertise."""
    # Create messages with roles that have different expertise levels for the topic
    messages = [
        {"role": "Frontend Developer", "content": "We should use React for the frontend."},
        {"role": "Backend Developer", "content": "I think Vue might be better, but I defer to frontend expertise."},
        {"role": "DevOps Engineer", "content": "From a deployment perspective, either framework works."},
        {"role": "UI Designer", "content": "React has better component libraries for our design system."}
    ]
    
    # Create role expertise mapping
    role_expertise = {
        "Frontend Developer": {"frontend": 0.9, "backend": 0.3, "devops": 0.2, "design": 0.6},
        "Backend Developer": {"frontend": 0.4, "backend": 0.9, "devops": 0.5, "design": 0.2},
        "DevOps Engineer": {"frontend": 0.2, "backend": 0.5, "devops": 0.9, "design": 0.1},
        "UI Designer": {"frontend": 0.7, "backend": 0.1, "devops": 0.1, "design": 0.9}
    }
    
    mock_client = MockLLMClient()
    detector = ConsensusDetector(mock_client)
    
    # Test that frontend-related consensus is detected with appropriate weighting
    consensus = detector.check_consensus_with_expertise_weighting(messages, "Frontend framework selection", role_expertise)
    assert consensus is True
    
    # Test with a backend topic where there's less consensus among experts
    backend_messages = [
        {"role": "Frontend Developer", "content": "I think we should use MongoDB for the database."},
        {"role": "Backend Developer", "content": "PostgreSQL would be a better choice for our relational data."},
        {"role": "DevOps Engineer", "content": "From an operations standpoint, PostgreSQL is more mature."},
        {"role": "UI Designer", "content": "I don't have a strong opinion on database technology."}
    ]
    
    consensus = detector.check_consensus_with_expertise_weighting(backend_messages, "Database selection", role_expertise)
    assert consensus is False


def test_improved_topic_relevance():
    """Test improved detection of topic relevance in messages."""
    # Create a detector with topic relevance capability
    mock_client = MockLLMClient()
    detector = ConsensusDetector(mock_client)
    
    # Test with on-topic messages
    on_topic_messages = [
        {"role": "role1", "content": "For user authentication, JWT with proper expiration is secure."},
        {"role": "role2", "content": "I agree that JWT works well for authentication needs."},
        {"role": "role3", "content": "JWT tokens should be stored securely and refreshed appropriately."},
        {"role": "role4", "content": "We should implement proper JWT validation on the server side."}
    ]
    
    topic_relevance = detector.calculate_topic_relevance(on_topic_messages, "Authentication mechanism")
    assert topic_relevance > 0.8
    
    # Test with off-topic messages
    off_topic_messages = [
        {"role": "role1", "content": "The UI design looks great, I like the color scheme."},
        {"role": "role2", "content": "We should optimize the database queries for better performance."},
        {"role": "role3", "content": "The deployment pipeline needs improvement."},
        {"role": "role4", "content": "We should consider adding more unit tests."}
    ]
    
    topic_relevance = detector.calculate_topic_relevance(off_topic_messages, "Authentication mechanism")
    assert topic_relevance < 0.3


def test_consensus_confidence_scoring():
    """Test that consensus detection includes a confidence score."""
    mock_client = MockLLMClient()
    detector = ConsensusDetector(mock_client)
    
    # Test with high-confidence consensus
    high_confidence_messages = [
        {"role": "role1", "content": "We should definitely use React for the frontend."},
        {"role": "role2", "content": "React is absolutely the right choice for our needs."},
        {"role": "role3", "content": "I strongly agree that React is the best option."},
        {"role": "role4", "content": "React is clearly the way to go for this project."}
    ]
    
    consensus, confidence = detector.check_consensus_with_confidence(high_confidence_messages, "Frontend framework")
    assert consensus is True
    assert confidence > 0.8
    
    # Test with low-confidence consensus
    low_confidence_messages = [
        {"role": "role1", "content": "I think React might be a good option, but I'm not entirely sure."},
        {"role": "role2", "content": "React seems reasonable, though I haven't used it much."},
        {"role": "role3", "content": "I'm leaning towards React, but I'm open to alternatives."},
        {"role": "role4", "content": "React is probably fine, though we should consider other options too."}
    ]
    
    consensus, confidence = detector.check_consensus_with_confidence(low_confidence_messages, "Frontend framework")
    assert consensus is True
    assert confidence < 0.6
    
    # Test with no consensus
    no_consensus_messages = [
        {"role": "role1", "content": "React would be my choice for the frontend."},
        {"role": "role2", "content": "I strongly prefer Vue for its simplicity."},
        {"role": "role3", "content": "Angular provides better structure for large applications."},
        {"role": "role4", "content": "Svelte offers better performance and a smaller bundle size."}
    ]
    
    consensus, confidence = detector.check_consensus_with_confidence(no_consensus_messages, "Frontend framework")
    assert consensus is False
    assert confidence > 0.7  # High confidence that there is NO consensus 