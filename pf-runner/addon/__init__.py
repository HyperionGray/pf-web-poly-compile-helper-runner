"""
Addon system for pf-runner DSL extensions.

This module provides a clean interface for extending the pf DSL
with features that don't fit naturally into the core grammar.
"""

from .interface import AddonInterface, AddonRegistry

__all__ = ['AddonInterface', 'AddonRegistry']
