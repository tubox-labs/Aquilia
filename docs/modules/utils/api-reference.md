# Utils API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/utils/__init__.py` | 16 | 0 | 0 | Aquilia Utils Package |
| `aquilia/utils/data.py` | 42 | 1 | 0 | Data Utilities - Provides flexible data structures for the framework. |
| `aquilia/utils/scanner.py` | 218 | 1 | 0 | Package Scanner Utility. |
| `aquilia/utils/urls.py` | 50 | 0 | 2 | URL Utilities for Aquilia. |

## Public Exports

`PackageScanner`, `join_paths`, `normalize_path`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `DataObject` | `aquilia/utils/data.py` | dict | A dictionary subclass that supports dot-notation access to its keys. |
| `PackageScanner` | `aquilia/utils/scanner.py` | object | Enhanced scanner for discovering classes in Python packages. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `join_paths` | `aquilia/utils/urls.py` | `def join_paths(*parts: str)` | Robustly join URL path segments. |
| `normalize_path` | `aquilia/utils/urls.py` | `def normalize_path(path: str)` | Normalize a URL path. |

## Detailed Classes And Methods

### `DataObject`

- Source: `aquilia/utils/data.py`
- Bases: `dict`
- Summary: A dictionary subclass that supports dot-notation access to its keys.

### `PackageScanner`

- Source: `aquilia/utils/scanner.py`
- Bases: `object`
- Summary: Enhanced scanner for discovering classes in Python packages.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `clear_cache` | `def clear_cache(self)` | Clear all caches. |
| `get_stats` | `def get_stats(self)` | Get scanning performance statistics. |
| `scan_package` | `def scan_package(self, package_name: str, base_class: type \| None=None, predicate: Callable[[type], bool] \| None=None, recursive: bool=False, max_depth: int=3, use_cache: bool=True)` | Enhanced scan a package for classes matching criteria. |
