"""
Interface definition for pf-runner addons.

Addons provide extensible functionality for features that don't fit
cleanly into the core DSL grammar, such as polyglot language support
and advanced build system integration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AddonInterface(ABC):
    """
    Base interface for pf-runner addons.
    
    Each addon must implement this interface to be compatible with
    the pf-runner execution engine.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of this addon."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Return the version of this addon."""
        pass
    
    @abstractmethod
    def can_handle(self, operation: str, args: Dict[str, Any]) -> bool:
        """
        Check if this addon can handle the given operation.
        
        Args:
            operation: The operation name (e.g., 'polyglot', 'build')
            args: Dictionary of arguments for the operation
            
        Returns:
            True if this addon can handle the operation, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self, operation: str, args: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """
        Execute the operation with the given arguments.
        
        Args:
            operation: The operation name
            args: Dictionary of arguments for the operation
            context: Execution context (environment, params, etc.)
            
        Returns:
            The result of the operation (implementation-specific)
        """
        pass
    
    def validate(self, operation: str, args: Dict[str, Any]) -> Optional[str]:
        """
        Validate operation arguments before execution.
        
        Args:
            operation: The operation name
            args: Dictionary of arguments for the operation
            
        Returns:
            None if valid, error message string if invalid
        """
        return None


class AddonRegistry:
    """
    Registry for managing pf-runner addons.
    
    Provides centralized management and discovery of available addons.
    """
    
    def __init__(self):
        self._addons: Dict[str, AddonInterface] = {}
    
    def register(self, addon: AddonInterface) -> None:
        """
        Register an addon with the registry.
        
        Args:
            addon: The addon instance to register
        """
        self._addons[addon.name] = addon
    
    def unregister(self, name: str) -> None:
        """
        Unregister an addon from the registry.
        
        Args:
            name: The name of the addon to unregister
        """
        if name in self._addons:
            del self._addons[name]
    
    def get(self, name: str) -> Optional[AddonInterface]:
        """
        Get an addon by name.
        
        Args:
            name: The name of the addon
            
        Returns:
            The addon instance if found, None otherwise
        """
        return self._addons.get(name)
    
    def find_handler(self, operation: str, args: Dict[str, Any]) -> Optional[AddonInterface]:
        """
        Find an addon that can handle the given operation.
        
        Args:
            operation: The operation name
            args: Dictionary of arguments for the operation
            
        Returns:
            The first addon that can handle the operation, or None
        """
        for addon in self._addons.values():
            if addon.can_handle(operation, args):
                return addon
        return None
    
    def list_addons(self) -> List[AddonInterface]:
        """
        Get a list of all registered addons.
        
        Returns:
            List of all registered addon instances
        """
        return list(self._addons.values())
