"""
AquilaVectorDB — EQL, the string filter syntax.

A small, closed expression language for filters that arrive as *text* — a CLI
``--where``, a saved view, an admin search box. It exists because the two Python
syntaxes cannot cross a process boundary: ``Doc.views >= 10`` is an object graph,
and a config file can only carry a string.

Grammar (precedence low to high)::

    or_expr   := and_expr ('OR' and_expr)*
    and_expr  := not_expr ('AND' not_expr)*
    not_expr  := 'NOT' not_expr | primary
    primary   := '(' or_expr ')' | comparison
    comparison:= FIELD OP literal | FIELD 'BETWEEN' literal 'AND' literal
    OP        := '=' | '==' | '!=' | '>' | '>=' | '<' | '<='
               | 'IN' | 'NOT IN' | 'CONTAINS' | 'STARTSWITH' | 'ENDSWITH'
               | 'IS NULL' | 'IS NOT NULL'
    literal   := number | string | boolean | 'null'
               | '[' literal,* ']' | '(' literal,* ')'

Keywords are case-insensitive; field names are not.

Design constraints
------------------

**No ``eval``.** A hand-written tokenizer and recursive-descent parser, because
EQL strings arrive from operators and config files. ``eval`` on that input is a
remote code execution hole, and no amount of sanitizing makes it one that closes.

**Compiles to :class:`VF`, not to a native filter.** EQL is a *front end*: it
produces the same node tree the keyword and expression syntaxes produce, so all
three inherit one compiler, one push-down analysis, and one residual path. A
lookup that cannot be pushed down behaves identically no matter which syntax
spelled it.

Example::

    from aquilia.vectordb.eql import parse_eql

    node = parse_eql("source = 'docs' AND views >= 10")
    hits = await Doc.vectors.filter(node).search("release")
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from aquilia.vectordb.faults import VectorEQLFault
from aquilia.vectordb.filters import VF

__all__ = ["parse_eql"]

#: Comparison operators, longest-first so ``>=`` wins over ``>`` and
#: ``NOT IN`` over ``IN`` during tokenization.
_OPERATORS: tuple[tuple[str, str], ...] = (
    ("IS NOT NULL", "isnull_false"),
    ("IS NULL", "isnull_true"),
    ("NOT IN", "not_in"),
    ("STARTSWITH", "startswith"),
    ("ENDSWITH", "endswith"),
    ("CONTAINS", "contains"),
    ("IN", "in"),
    (">=", "gte"),
    ("<=", "lte"),
    ("!=", "ne"),
    ("==", "exact"),
    ("=", "exact"),
    (">", "gt"),
    ("<", "lt"),
)

_TOKEN_RE = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<lparen>\()
  | (?P<rparen>\))
  | (?P<lbracket>\[)
  | (?P<rbracket>\])
  | (?P<comma>,)
  | (?P<string>'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")
  | (?P<number>-?\d+\.\d+|-?\d+)
  | (?P<op>>=|<=|!=|==|=|>|<)
  | (?P<word>[A-Za-z_][A-Za-z0-9_.]*)
    """,
    re.VERBOSE,
)

_KEYWORDS = {
    "AND",
    "OR",
    "NOT",
    "IN",
    "IS",
    "NULL",
    "CONTAINS",
    "STARTSWITH",
    "ENDSWITH",
    "BETWEEN",
    "TRUE",
    "FALSE",
}


@dataclass(frozen=True, slots=True)
class _Token:
    kind: str
    value: Any
    pos: int


def _tokenize(source: str) -> list[_Token]:
    """Split ``source`` into tokens, or fault with the offending offset."""
    tokens: list[_Token] = []
    pos = 0
    while pos < len(source):
        match = _TOKEN_RE.match(source, pos)
        if match is None:
            raise VectorEQLFault(
                expression=source,
                reason=f"unexpected character {source[pos]!r}",
                position=pos,
            )
        kind = match.lastgroup or ""
        text = match.group()
        pos = match.end()

        if kind == "ws":
            continue
        if kind == "string":
            tokens.append(_Token("literal", _unquote(text), match.start()))
        elif kind == "number":
            tokens.append(_Token("literal", float(text) if "." in text else int(text), match.start()))
        elif kind == "word":
            upper = text.upper()
            if upper in _KEYWORDS:
                tokens.append(_Token("keyword", upper, match.start()))
            else:
                tokens.append(_Token("field", text, match.start()))
        else:
            tokens.append(_Token(kind, text, match.start()))
    return tokens


def _unquote(text: str) -> str:
    """Strip surrounding quotes and resolve backslash escapes."""
    body = text[1:-1]
    return re.sub(r"\\(.)", r"\1", body)


class _Parser:
    """Recursive-descent parser over the token stream."""

    def __init__(self, source: str, tokens: list[_Token]) -> None:
        self.source = source
        self.tokens = tokens
        self.index = 0

    # ── Stream helpers ───────────────────────────────────────────────────

    def peek(self) -> _Token | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def next(self) -> _Token:
        token = self.peek()
        if token is None:
            raise VectorEQLFault(
                expression=self.source,
                reason="unexpected end of expression",
                position=len(self.source),
            )
        self.index += 1
        return token

    def accept_keyword(self, *words: str) -> bool:
        token = self.peek()
        if token and token.kind == "keyword" and token.value in words:
            self.index += 1
            return True
        return False

    def expect(self, kind: str, label: str) -> _Token:
        token = self.next()
        if token.kind != kind:
            raise VectorEQLFault(
                expression=self.source,
                reason=f"expected {label}, got {token.value!r}",
                position=token.pos,
            )
        return token

    # ── Grammar ──────────────────────────────────────────────────────────

    def parse(self) -> VF:
        node = self.or_expr()
        remaining = self.peek()
        if remaining is not None:
            raise VectorEQLFault(
                expression=self.source,
                reason=f"unexpected trailing {remaining.value!r}",
                position=remaining.pos,
            )
        return node

    def or_expr(self) -> VF:
        node = self.and_expr()
        while self.accept_keyword("OR"):
            node = node | self.and_expr()
        return node

    def and_expr(self) -> VF:
        node = self.not_expr()
        while self.accept_keyword("AND"):
            node = node & self.not_expr()
        return node

    def not_expr(self) -> VF:
        if self.accept_keyword("NOT"):
            return ~self.not_expr()
        return self.primary()

    def primary(self) -> VF:
        token = self.peek()
        if token and token.kind == "lparen":
            self.next()
            node = self.or_expr()
            self.expect("rparen", "')'")
            return node
        return self.comparison()

    def comparison(self) -> VF:
        field = self.expect("field", "a field name")
        lookup = self.operator()

        if lookup == "isnull_true":
            return VF(**{f"{field.value}__isnull": True})
        if lookup == "isnull_false":
            return VF(**{f"{field.value}__isnull": False})
        if lookup == "ne":
            return ~VF(**{f"{field.value}__exact": self.literal()})
        if lookup == "not_in":
            return ~VF(**{f"{field.value}__in": self.literal()})
        if lookup == "range":
            # BETWEEN lo AND hi — the `AND` here is part of the operator, not a
            # conjunction, so it is consumed before the boolean parser can see it.
            low = self.literal()
            if not self.accept_keyword("AND"):
                token = self.peek()
                raise VectorEQLFault(
                    expression=self.source,
                    reason="expected AND after the lower bound of BETWEEN",
                    position=token.pos if token else len(self.source),
                )
            return VF(**{f"{field.value}__range": (low, self.literal())})

        return VF(**{f"{field.value}__{lookup}": self.literal()})

    def operator(self) -> str:
        """Consume one comparison operator, including multi-word forms."""
        token = self.next()

        if token.kind == "op":
            for text, lookup in _OPERATORS:
                if text == token.value:
                    return lookup

        if token.kind == "keyword":
            if token.value == "IS":
                negated = self.accept_keyword("NOT")
                if not self.accept_keyword("NULL"):
                    raise VectorEQLFault(
                        expression=self.source,
                        reason="expected NULL after IS",
                        position=token.pos,
                    )
                return "isnull_false" if negated else "isnull_true"
            if token.value == "NOT":
                if self.accept_keyword("IN"):
                    return "not_in"
                raise VectorEQLFault(
                    expression=self.source,
                    reason="expected IN after NOT",
                    position=token.pos,
                )
            if token.value in {"IN", "CONTAINS", "STARTSWITH", "ENDSWITH", "BETWEEN"}:
                return {
                    "IN": "in",
                    "CONTAINS": "contains",
                    "STARTSWITH": "startswith",
                    "ENDSWITH": "endswith",
                    "BETWEEN": "range",
                }[token.value]

        raise VectorEQLFault(
            expression=self.source,
            reason=f"expected a comparison operator, got {token.value!r}",
            position=token.pos,
        )

    def literal(self) -> Any:
        token = self.next()

        if token.kind == "literal":
            return token.value
        if token.kind == "keyword":
            if token.value == "TRUE":
                return True
            if token.value == "FALSE":
                return False
            if token.value == "NULL":
                return None
        if token.kind in ("lbracket", "lparen"):
            # Both bracket styles are accepted for lists: `IN ['a', 'b']` reads
            # as Python, `IN ('a', 'b')` as SQL, and rejecting either would be a
            # syntax trap with no upside.
            closing = "rbracket" if token.kind == "lbracket" else "rparen"
            symbol = "]" if token.kind == "lbracket" else ")"

            items: list[Any] = []
            nxt = self.peek()
            if nxt is not None and nxt.kind == closing:
                self.next()
                return items
            while True:
                items.append(self.literal())
                nxt = self.next()
                if nxt.kind == closing:
                    return items
                if nxt.kind != "comma":
                    raise VectorEQLFault(
                        expression=self.source,
                        reason=f"expected ',' or '{symbol}' in list, got {nxt.value!r}",
                        position=nxt.pos,
                    )

        raise VectorEQLFault(
            expression=self.source,
            reason=f"expected a literal value, got {token.value!r}",
            position=token.pos,
        )


def parse_eql(expression: str) -> VF:
    """
    Parse an EQL string into a :class:`VF` filter tree.

    Args:
        expression: The EQL source, e.g. ``"source = 'docs' AND views >= 10"``.

    Returns:
        A :class:`VF` node, usable anywhere a filter node is accepted.

    Raises:
        VectorEQLFault: On any tokenization or parse failure. The fault carries
            the character ``position``, so a CLI can point at the offending
            column rather than reporting "invalid filter".

    Example::

        parse_eql("NOT (draft = true OR views < 10)")
        parse_eql("tags CONTAINS 'python' AND lang IN ['en', 'fr']")
    """
    if not expression or not expression.strip():
        raise VectorEQLFault(expression=expression, reason="expression is empty", position=0)

    tokens = _tokenize(expression)
    if not tokens:
        raise VectorEQLFault(expression=expression, reason="expression has no tokens", position=0)

    return _Parser(expression, tokens).parse()
