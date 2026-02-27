"""
Model Persistence System — Robust loading and saving for production models.

Provides abstractions and implementations for serializing model weights,
metadata, and runtime state across restarts.
"""

from __future__ import annotations

import abc
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .._types import DType, Framework

@dataclass
class ModelBundle:
    """A complete model bundle ready for persistence."""
    name: str
    version: str
    weights_path: Path
    metadata: Dict[str, Any]
    framework: str
    dtype: str

class ModelLoader(abc.ABC):
    """Abstract base class for framework-specific model loaders."""
    
    @abc.abstractmethod
    def load(self, path: Path, **kwargs) -> Any:
        """Load model from path."""
        pass

class ModelSaver(abc.ABC):
    """Abstract base class for framework-specific model savers."""
    
    @abc.abstractmethod
    def save(self, model: Any, path: Path, **kwargs) -> None:
        """Save model to path."""
        pass

# ── PyTorch Implementation ────────────────────────────────────────────────

class PyTorchModelLoader(ModelLoader):
    """Production-grade PyTorch model loader."""
    
    def load(self, path: Path, device: str = "cpu", **kwargs) -> Any:
        import torch
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        
        # Safe loading with weights_only=True if supported
        load_kwargs = {"map_location": device}
        if hasattr(torch, "load") and "weights_only" in torch.load.__code__.co_varnames:
            load_kwargs["weights_only"] = True
            
        return torch.load(path, **load_kwargs)

class PyTorchModelSaver(ModelSaver):
    """Production-grade PyTorch model saver."""
    
    def save(self, model: Any, path: Path, **kwargs) -> None:
        import torch
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use a temporary file for atomic save
        temp_path = path.with_suffix(".tmp")
        torch.save(model.state_dict() if hasattr(model, "state_dict") else model, temp_path)
        os.replace(temp_path, path)

# ── Persistence Manager ──────────────────────────────────────────────────

class ModelPersistenceManager:
    """
    Orchestrates high-level model persistence operations.
    
    Handles directory structures, versioning, and framework-agnostic dispatch.
    """
    
    def __init__(self, root_dir: str = ".models"):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self._loaders: Dict[str, ModelLoader] = {
            "pytorch": PyTorchModelLoader(),
        }
        self._savers: Dict[str, ModelSaver] = {
            "pytorch": PyTorchModelSaver(),
        }

    def register_framework(self, name: str, loader: ModelLoader, saver: ModelSaver):
        self._loaders[name] = loader
        self._savers[name] = saver

    def _get_model_dir(self, name: str, version: str) -> Path:
        return self.root_dir / name / version

    async def save_bundle(self, bundle: ModelBundle) -> Path:
        """Save a complete model bundle."""
        model_dir = self._get_model_dir(bundle.name, bundle.version)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Save metadata
        with open(model_dir / "metadata.json", "w") as f:
            json.dump({
                "name": bundle.name,
                "version": bundle.version,
                "framework": bundle.framework,
                "dtype": bundle.dtype,
                **bundle.metadata
            }, f, indent=2)
            
        # 2. Copy/Save weights
        target_weights = model_dir / bundle.weights_path.name
        if bundle.weights_path.resolve() != target_weights.resolve():
            shutil.copy2(bundle.weights_path, target_weights)
            
        return model_dir

    async def load_model(self, name: str, version: str, device: str = "cpu") -> Any:
        """Load a model by name and version."""
        model_dir = self._get_model_dir(name, version)
        metadata_path = model_dir / "metadata.json"
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"Model {name}:{version} not found in persistence")
            
        with open(metadata_path) as f:
            metadata = json.load(f)
            
        framework = metadata["framework"]
        loader = self._loaders.get(framework)
        if not loader:
            raise ValueError(f"No loader for framework: {framework}")
            
        # Find weights file (assuming first non-json file)
        weights_file = next(
            p for p in model_dir.iterdir() 
            if p.suffix != ".json" and p.is_file()
        )
        
        return loader.load(weights_file, device=device)
