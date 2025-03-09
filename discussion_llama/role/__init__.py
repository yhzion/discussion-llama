"""
Role management module for Discussion-Llama.

This module provides tools for loading and managing role definitions.
"""

from .role_manager import Role, RoleManager, load_roles_from_yaml

__all__ = ['Role', 'RoleManager', 'load_roles_from_yaml'] 