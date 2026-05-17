# Utilities API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `DataObject` | `aquilia/utils/data.py` | dict | A dictionary subclass that supports dot-notation access to its keys. |
| `PackageScanner` | `aquilia/utils/scanner.py` | object | Enhanced scanner for discovering classes in Python packages. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `join_paths` | `aquilia/utils/urls.py` | `def join_paths(*parts: str) -> str` | Robustly join URL path segments. |
| `normalize_path` | `aquilia/utils/urls.py` | `def normalize_path(path: str) -> str` | Normalize a URL path. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| None detected |  |  |

## Detailed Classes And Methods

### Class: `DataObject`

- Source: `aquilia/utils/data.py`
- Bases: `dict`
- Summary: A dictionary subclass that supports dot-notation access to its keys.

### Class: `PackageScanner`

- Source: `aquilia/utils/scanner.py`
- Bases: `object`
- Summary: Enhanced scanner for discovering classes in Python packages.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `clear_cache` | `def clear_cache(self) -> None` |  | Clear all caches. |
| `get_stats` | `def get_stats(self) -> dict[str, Any]` |  | Get scanning performance statistics. |
| `scan_package` | `def scan_package(self, package_name: str, base_class: type &#124; None = None, predicate: Callable[[type], bool] &#124; None = None, recursive: bool = False, max_depth: int = 3, use_cache: bool = True) -> list[type]` |  | Enhanced scan a package for classes matching criteria. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `join_paths` | `aquilia/utils/urls.py` | `def join_paths(*parts: str) -> str` | Robustly join URL path segments. |
| `normalize_path` | `aquilia/utils/urls.py` | `def normalize_path(path: str) -> str` | Normalize a URL path. |
