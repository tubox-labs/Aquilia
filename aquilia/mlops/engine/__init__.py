"""
Aquilia MLOps Execution Engine.

The engine manages the full inference pipeline per request:
preprocessing → batching → inference → postprocessing,
with metrics and tracing at each stage.
"""

from .pipeline import InferencePipeline
from .hooks import (
    before_predict,
    after_predict,
    on_error,
    on_load,
    on_unload,
    preprocess,
    postprocess,
    collect_hooks,
)

__all__ = [
    "InferencePipeline",
    "before_predict",
    "after_predict",
    "on_error",
    "on_load",
    "on_unload",
    "preprocess",
    "postprocess",
    "collect_hooks",
]
