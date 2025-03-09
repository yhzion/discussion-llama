"""
Discussion engine module for Discussion-Llama.

This module provides the core functionality for running discussions.
"""

from .discussion_engine import Message, DiscussionState, DiskBasedDiscussionManager, DiscussionEngine
from .consensus_detector import ConsensusDetector, extract_key_points, group_similar_points

__all__ = [
    'Message', 
    'DiscussionState', 
    'DiskBasedDiscussionManager', 
    'DiscussionEngine',
    'ConsensusDetector',
    'extract_key_points',
    'group_similar_points'
] 