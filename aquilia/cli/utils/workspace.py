"""
Utility functions for finding and loading workspace configuration.
"""

from pathlib import Path
from typing import Optional


def find_workspace_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find the Aquilia workspace root by looking for workspace.py or aquilia.py.
    
    Searches upward from start_path (or cwd) until finding a workspace file.
    
    Args:
        start_path: Starting directory (defaults to cwd)
        
    Returns:
        Path to workspace root, or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()
    
    current = start_path.resolve()
    
    while current != current.parent:
        if (current / "workspace.py").exists():
            return current
        if (current / "aquilia.py").exists():
            return current
        current = current.parent
    
    return None


def get_workspace_file(workspace_root: Path) -> Optional[Path]:
    """
    Get the workspace configuration file path.
    
    Checks for workspace.py or aquilia.py (Python-native only).
    
    Args:
        workspace_root: Root directory of the workspace
        
    Returns:
        Path to workspace file, or None if not found
    """
    if (workspace_root / "workspace.py").exists():
        return workspace_root / "workspace.py"
    if (workspace_root / "aquilia.py").exists():
        return workspace_root / "aquilia.py"
    return None


def is_python_workspace(workspace_root: Path) -> bool:
    """Check if workspace uses Python format (workspace.py or aquilia.py)."""
    return (
        (workspace_root / "workspace.py").exists() or
        (workspace_root / "aquilia.py").exists()
    )
