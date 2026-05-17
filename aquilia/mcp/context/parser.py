"""Parsers that extract compact source metadata without executing code."""

from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path

from ..models import SourceAnchor, SourceFile
from ..security import redact_secrets


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def _first_doc_line(node: ast.AST) -> str:
    doc = ast.get_docstring(node) or ""
    return doc.strip().splitlines()[0][:220] if doc.strip() else ""


def _python_source(path: Path, rel: str, text: str) -> SourceFile:
    anchors: list[SourceAnchor] = []
    symbols: list[str] = []
    imports: list[str] = []
    sections: list[dict[str, object]] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None

    if tree is not None:
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif node.module:
                    imports.append("." * node.level + node.module)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", getattr(node, "lineno", 1))
                sections.append(
                    {
                        "name": node.name,
                        "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                        "line": getattr(node, "lineno", 1),
                        "end_line": end,
                        "summary": _first_doc_line(node),
                    }
                )
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = "class" if isinstance(node, ast.ClassDef) else "function"
                symbols.append(node.name)
                anchors.append(
                    SourceAnchor(
                        path=rel,
                        line=getattr(node, "lineno", 1),
                        kind=kind,
                        name=node.name,
                        summary=_first_doc_line(node),
                    )
                )
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in {"manifest", "workspace"}:
                        symbols.append(target.id)
                        anchors.append(
                            SourceAnchor(path=rel, line=getattr(node, "lineno", 1), kind="assignment", name=target.id)
                        )

    doc_summary = ""
    if tree is not None:
        doc_summary = _first_doc_line(tree)
    if not doc_summary:
        for line in text.splitlines():
            stripped = line.strip(" #")
            if stripped and not stripped.startswith(("from ", "import ")):
                doc_summary = stripped[:220]
                break

    keywords = sorted(set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", rel + " " + " ".join(symbols) + " " + " ".join(imports))))[:80]
    return SourceFile(
        path=rel,
        kind="python",
        title=path.name,
        summary=doc_summary,
        symbols=symbols[:200],
        anchors=anchors[:200],
        keywords=keywords,
        imports=sorted(set(imports))[:100],
        sections=sections[:120],
        content_hash=_hash_text(text),
        size=len(text.encode("utf-8", errors="replace")),
        text=redact_secrets(text[:60_000]),
    )


def _markdown_source(path: Path, rel: str, text: str) -> SourceFile:
    anchors: list[SourceAnchor] = []
    sections: list[dict[str, object]] = []
    title = path.stem
    for lineno, line in enumerate(text.splitlines(), start=1):
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            if heading:
                if not anchors:
                    title = heading
                anchors.append(SourceAnchor(path=rel, line=lineno, kind="heading", name=heading, summary=heading))
                sections.append({"name": heading, "kind": "heading", "line": lineno, "summary": heading})
    summary = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            summary = stripped[:220]
            break
    keywords = sorted(set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", rel + " " + title)))[:80]
    return SourceFile(
        path=rel,
        kind="markdown",
        title=title,
        summary=summary,
        anchors=anchors[:200],
        keywords=keywords,
        sections=sections[:120],
        content_hash=_hash_text(text),
        size=len(text.encode("utf-8", errors="replace")),
        text=redact_secrets(text[:60_000]),
    )


def parse_source_file(root: Path, path: Path, *, max_bytes: int = 256_000) -> SourceFile:
    rel = path.relative_to(root).as_posix()
    raw = path.read_bytes()
    if len(raw) > max_bytes:
        raw = raw[:max_bytes]
    text = raw.decode("utf-8", errors="replace")
    if path.suffix == ".md":
        return _markdown_source(path, rel, text)
    return _python_source(path, rel, text)
