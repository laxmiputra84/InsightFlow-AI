"""
Chunking Engine for InsightFlow AI RAG Pipeline.
Splits extracted document sections into semantically meaningful chunks
with configurable chunk size and overlap, while preserving page and row citations.
"""
from typing import List, Dict, Any
from app.services.rag.text_extractor import ExtractedChunkSection

DEFAULT_CHUNK_SIZE = 600
DEFAULT_CHUNK_OVERLAP = 120


class DocumentChunk:
    def __init__(
        self,
        chunk_index: int,
        content: str,
        page_number: int = 1,
        metadata: Dict[str, Any] = None,
    ):
        self.chunk_index = chunk_index
        self.content = content.strip()
        self.page_number = page_number
        self.char_count = len(self.content)
        self.metadata = metadata or {}


class DocumentChunker:
    """
    Splits text sections using recursive boundary splitting (paragraphs, sentences, words).
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self.chunk_size = max(100, chunk_size)
        self.chunk_overlap = max(0, min(chunk_overlap, self.chunk_size // 2))

    def chunk_sections(self, sections: List[ExtractedChunkSection]) -> List[DocumentChunk]:
        """
        Chunks multiple document sections (e.g., pages or row batches),
        preserving citation location identifiers.
        """
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        for section in sections:
            section_text = section.text.strip()
            if not section_text:
                continue

            # If section fits within chunk size, keep it whole
            if len(section_text) <= self.chunk_size:
                chunks.append(DocumentChunk(
                    chunk_index=global_chunk_idx,
                    content=section_text,
                    page_number=section.page_number,
                    metadata=section.metadata,
                ))
                global_chunk_idx += 1
                continue

            # Otherwise, split using sliding window with natural boundaries
            sub_texts = self._split_text(section_text)
            for sub_text in sub_texts:
                if sub_text.strip():
                    chunks.append(DocumentChunk(
                        chunk_index=global_chunk_idx,
                        content=sub_text.strip(),
                        page_number=section.page_number,
                        metadata=section.metadata,
                    ))
                    global_chunk_idx += 1

        return chunks

    def _split_text(self, text: str) -> List[str]:
        """
        Recursive natural boundary splitting with chunk overlap.
        """
        separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]
        return self._recursive_split(text, separators)

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]

        if not separators:
            # Force hard split if no separators left
            return self._hard_split(text)

        sep = separators[0]
        remaining_seps = separators[1:]
        parts = text.split(sep)

        result_chunks: List[str] = []
        current_chunk = ""

        for part in parts:
            candidate = f"{current_chunk}{sep}{part}" if current_chunk else part
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    result_chunks.append(current_chunk)
                    # Handle overlap by taking tail of current chunk
                    if self.chunk_overlap > 0 and len(current_chunk) > self.chunk_overlap:
                        overlap_start = len(current_chunk) - self.chunk_overlap
                        current_chunk = current_chunk[overlap_start:] + sep + part
                    else:
                        current_chunk = part
                else:
                    # Part itself is larger than chunk_size, recurse with next separator
                    deeper_chunks = self._recursive_split(part, remaining_seps)
                    result_chunks.extend(deeper_chunks[:-1])
                    current_chunk = deeper_chunks[-1] if deeper_chunks else ""

        if current_chunk:
            result_chunks.append(current_chunk)

        return result_chunks

    def _hard_split(self, text: str) -> List[str]:
        step = self.chunk_size - self.chunk_overlap
        return [text[i : i + self.chunk_size] for i in range(0, len(text), step)]
