"""
AquilaVectorDB — Document chunking.

Long documents embed badly. Every model has a context window, and text beyond it
is silently truncated — a 40-page manual becomes a vector describing its first
paragraph, and search never finds anything past page one. Worse, even within the
window, one vector averaged over many topics is close to none of them.

Chunking splits a document into passages, embeds each, and stores them as child
records linked to the parent (§3.5)::

    Parent key:  "article_101"
    Child keys:  "article_101#chunk:0", "article_101#chunk:1", ...

Each child carries a native ``ChunkInfo`` locating it in the source
(``document_key``, ``ordinal``, ``char_start``, ``char_end``), so a hit on a
chunk can always be traced back to its document and offset.

Boundaries are semantic, not arithmetic
---------------------------------------

:class:`RecursiveCharacterChunker` splits on the largest natural boundary that
fits — paragraphs, then lines, then sentences, then words, and only then raw
characters. Cutting mid-sentence produces a fragment that embeds to something
neither half means, so the separator ladder exists to make that the last resort
rather than the default.

Overlap
-------

Adjacent chunks share ``chunk_overlap`` characters. Without it, a passage
straddling a boundary is split across two vectors and matches neither well;
with it, the straddling text appears whole in at least one chunk. The cost is
storage proportional to the overlap ratio, which is why it defaults to a modest
fraction rather than half the window.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from aquilia.vectordb.faults import VectorChunkingFault

#: Separator ladder for :class:`RecursiveCharacterChunker`, widest boundary
#: first. The empty string is the terminal fallback: split anywhere.
DEFAULT_SEPARATORS: tuple[str, ...] = ("\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", "")

#: Separator used to build a child key from its parent. Chosen because elips
#: folds non-UUID keys through UUIDv5, so the literal text only has to be
#: unambiguous to humans reading a key — and ``#`` does not occur in a UUID.
CHUNK_KEY_SEPARATOR = "#chunk:"


@dataclass(frozen=True, slots=True)
class Chunk:
    """
    One fragment of a chunked document.

    Attributes:
        text: The fragment's text.
        ordinal: Zero-based position in the parent document.
        char_start: Inclusive start offset in the source text.
        char_end: Exclusive end offset in the source text.
    """

    text: str
    ordinal: int
    char_start: int
    char_end: int

    def key_for(self, parent_key: str) -> str:
        """Return the child record key for this chunk under ``parent_key``."""
        return f"{parent_key}{CHUNK_KEY_SEPARATOR}{self.ordinal}"

    def to_native(self, parent_key: str) -> Any:
        """
        Build the native ``elips.ChunkInfo`` for this fragment.

        Raises:
            VectorNotInstalledFault: When ``elips`` is not installed.
        """
        from aquilia.vectordb._compat import require_elips

        elips = require_elips()
        info = elips.ChunkInfo()
        info.document_key = parent_key
        info.ordinal = self.ordinal
        info.char_start = self.char_start
        info.char_end = self.char_end
        return info

    def __repr__(self) -> str:
        preview = self.text[:40].replace("\n", " ")
        ellipsis = "…" if len(self.text) > 40 else ""
        return f"<Chunk #{self.ordinal} [{self.char_start}:{self.char_end}] {preview!r}{ellipsis}>"


class Chunker:
    """
    Base class for chunking strategies.

    Subclasses implement :meth:`split`. The base handles validation of the
    size/overlap relationship, which is the one way a chunker can be configured
    into an infinite loop.

    Args:
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Characters shared between adjacent chunks.

    Raises:
        VectorChunkingFault: When ``chunk_size`` is not positive, or
            ``chunk_overlap`` is not smaller than it. Equal values would make
            each step advance zero characters and loop forever.
    """

    def __init__(self, *, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise VectorChunkingFault(reason=f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0:
            raise VectorChunkingFault(reason=f"chunk_overlap must be non-negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise VectorChunkingFault(
                reason=(
                    f"chunk_overlap ({chunk_overlap}) must be smaller than chunk_size "
                    f"({chunk_size}); otherwise each chunk would advance zero characters "
                    f"and chunking would never terminate."
                )
            )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[Chunk]:
        """
        Split ``text`` into chunks.

        Args:
            text: Source document text.

        Returns:
            Chunks in document order. A document shorter than ``chunk_size``
            yields exactly one chunk covering all of it.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{type(self).__name__}(chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap})"


class RecursiveCharacterChunker(Chunker):
    """
    Split on the largest natural boundary that fits.

    Walks :data:`DEFAULT_SEPARATORS` from widest to narrowest, preferring a
    paragraph break over a line break over a sentence end, and falling back to a
    hard character cut only when no separator appears within the window.

    Args:
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Characters shared between adjacent chunks.
        separators: Boundary ladder, widest first. Defaults to
            :data:`DEFAULT_SEPARATORS`.

    Example::

        chunker = RecursiveCharacterChunker(chunk_size=500, chunk_overlap=50)
        chunks = chunker.split(article_body)
    """

    def __init__(
        self,
        *,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: tuple[str, ...] | list[str] | None = None,
    ) -> None:
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.separators = tuple(separators) if separators else DEFAULT_SEPARATORS

    def split(self, text: str) -> list[Chunk]:
        """Split ``text`` on the widest separator that fits each window."""
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [Chunk(text=text, ordinal=0, char_start=0, char_end=len(text))]

        chunks: list[Chunk] = []
        start = 0
        ordinal = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            if end < len(text):
                end = self._best_boundary(text, start, end)

            piece = text[start:end]
            if piece.strip():
                chunks.append(Chunk(text=piece, ordinal=ordinal, char_start=start, char_end=end))
                ordinal += 1

            if end >= len(text):
                break

            # Step forward by at least one character even when the overlap
            # would otherwise put the next window back where this one began.
            start = max(end - self.chunk_overlap, start + 1)

        return chunks

    def _best_boundary(self, text: str, start: int, hard_end: int) -> int:
        """
        Return the widest separator boundary inside ``[start, hard_end]``.

        Searches backward from the window edge so the chunk stays within
        ``chunk_size``. A separator found in the first half of the window is
        rejected: honouring it would produce a chunk under half the target size
        and multiply the record count for no retrieval benefit.
        """
        minimum = start + self.chunk_size // 2

        for separator in self.separators:
            if not separator:
                break
            index = text.rfind(separator, minimum, hard_end)
            if index > start:
                return index + len(separator)

        return hard_end


class SentenceChunker(Chunker):
    """
    Group whole sentences up to the size budget.

    Never splits a sentence, which suits prose where a fragment embeds poorly.
    A single sentence longer than ``chunk_size`` is emitted whole rather than
    cut — exceeding the budget is the lesser evil against a fragment that means
    something different from either half.

    Args:
        chunk_size: Soft maximum characters per chunk.
        chunk_overlap: Trailing sentences repeated into the next chunk,
            measured in characters.

    Example::

        chunker = SentenceChunker(chunk_size=800, chunk_overlap=100)
    """

    #: Sentence terminator followed by whitespace. Deliberately simple: a full
    #: abbreviation-aware segmenter is a dependency, and a mis-split here costs
    #: a slightly odd boundary rather than a wrong result.
    _SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

    def split(self, text: str) -> list[Chunk]:
        """Group sentences into chunks without splitting any of them."""
        if not text:
            return []

        sentences = self._sentences(text)
        if not sentences:
            return []

        chunks: list[Chunk] = []
        ordinal = 0
        current: list[tuple[int, int, str]] = []
        current_len = 0

        for span_start, span_end, sentence in sentences:
            if current and current_len + len(sentence) > self.chunk_size:
                chunks.append(self._emit(text, current, ordinal))
                ordinal += 1
                current = self._carry_over(current)
                current_len = sum(len(s) for _, _, s in current)

            current.append((span_start, span_end, sentence))
            current_len += len(sentence)

        if current:
            chunks.append(self._emit(text, current, ordinal))

        return chunks

    def _sentences(self, text: str) -> list[tuple[int, int, str]]:
        """Return ``(start, end, sentence)`` spans, offsets into ``text``."""
        spans: list[tuple[int, int, str]] = []
        cursor = 0
        for piece in self._SENTENCE_END.split(text):
            if not piece:
                continue
            start = text.find(piece, cursor)
            if start < 0:
                start = cursor
            end = start + len(piece)
            spans.append((start, end, piece))
            cursor = end
        return spans

    def _carry_over(self, current: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
        """Return the trailing sentences that overlap into the next chunk."""
        if not self.chunk_overlap:
            return []

        carried: list[tuple[int, int, str]] = []
        length = 0
        for span in reversed(current):
            if length + len(span[2]) > self.chunk_overlap:
                break
            carried.insert(0, span)
            length += len(span[2])
        return carried

    def _emit(self, text: str, spans: list[tuple[int, int, str]], ordinal: int) -> Chunk:
        """Build one chunk covering ``spans``, reading its text from the source."""
        start = spans[0][0]
        end = spans[-1][1]
        return Chunk(text=text[start:end], ordinal=ordinal, char_start=start, char_end=end)


def parent_key_of(key: str) -> str | None:
    """
    Return the parent document key for a chunk key, or ``None``.

    Args:
        key: A record key, possibly a chunk key.

    Returns:
        The parent key when ``key`` names a chunk, otherwise ``None``.

    Example::

        parent_key_of("article_101#chunk:3")  # "article_101"
        parent_key_of("article_101")          # None
    """
    if CHUNK_KEY_SEPARATOR not in key:
        return None
    return key.split(CHUNK_KEY_SEPARATOR, 1)[0]


def is_chunk_key(key: str) -> bool:
    """Return whether ``key`` names a chunk rather than a whole document."""
    return CHUNK_KEY_SEPARATOR in key


__all__ = [
    "CHUNK_KEY_SEPARATOR",
    "DEFAULT_SEPARATORS",
    "Chunk",
    "Chunker",
    "RecursiveCharacterChunker",
    "SentenceChunker",
    "is_chunk_key",
    "parent_key_of",
]
