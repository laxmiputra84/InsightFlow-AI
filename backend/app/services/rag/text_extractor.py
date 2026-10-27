"""
Text Extraction Module for InsightFlow AI RAG Pipeline.
Supports PDF (pypdf), TXT (UTF-8 / Latin-1), and CSV (structured tabular text).
Handles empty, corrupted, or invalid documents with clear descriptive error messages.
Tracks page numbers for PDFs and row ranges for CSVs for accurate citation tracking.
"""
import io
import csv
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("insightflow.rag.extractor")


class ExtractedChunkSection:
    def __init__(self, text: str, page_number: int = 1, metadata: Dict[str, Any] = None):
        self.text = text
        self.page_number = page_number
        self.metadata = metadata or {}


class TextExtractor:
    """
    Extracts text from supported document types with page and row location tracking.
    """

    @classmethod
    def extract(cls, file_bytes: bytes, filename: str, content_type: str = "") -> List[ExtractedChunkSection]:
        """
        Extracts content into sections tagged with page or row metadata.
        Returns a list of ExtractedChunkSection items.
        """
        if not file_bytes or len(file_bytes.strip()) == 0:
            raise ValueError(f"Uploaded file '{filename}' is empty (0 bytes).")

        lower_name = filename.lower()

        if lower_name.endswith(".pdf") or "pdf" in content_type.lower():
            return cls._extract_pdf(file_bytes, filename)
        elif lower_name.endswith(".csv") or "csv" in content_type.lower() or "spreadsheet" in content_type.lower():
            return cls._extract_csv(file_bytes, filename)
        elif lower_name.endswith(".txt") or "text/plain" in content_type.lower():
            return cls._extract_txt(file_bytes, filename)
        else:
            raise ValueError(
                f"Unsupported document format for '{filename}'. Supported formats are: PDF (.pdf), Plain Text (.txt), and CSV (.csv)."
            )

    @classmethod
    def _extract_pdf(cls, file_bytes: bytes, filename: str) -> List[ExtractedChunkSection]:
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            sections: List[ExtractedChunkSection] = []

            if len(reader.pages) == 0:
                raise ValueError(f"PDF document '{filename}' contains 0 pages.")

            total_extracted_chars = 0
            for page_idx, page in enumerate(reader.pages):
                page_num = page_idx + 1
                try:
                    page_text = page.extract_text() or ""
                except Exception as pe:
                    logger.warning(f"Error extracting page {page_num} in '{filename}': {pe}")
                    page_text = ""

                cleaned = page_text.strip()
                if cleaned:
                    total_extracted_chars += len(cleaned)
                    sections.append(ExtractedChunkSection(
                        text=cleaned,
                        page_number=page_num,
                        metadata={"total_pages": len(reader.pages), "page": page_num}
                    ))

            if total_extracted_chars == 0:
                raise ValueError(
                    f"PDF document '{filename}' has {len(reader.pages)} page(s) but contains no extractable text (e.g., scanned images or empty pages)."
                )

            return sections
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse PDF '{filename}': {e}", exc_info=True)
            raise ValueError(f"Corrupted or invalid PDF file '{filename}': {str(e)}")

    @classmethod
    def _extract_txt(cls, file_bytes: bytes, filename: str) -> List[ExtractedChunkSection]:
        # Try UTF-8 decoding, fallback to latin-1
        text = None
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                text = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise ValueError(f"Unable to decode text document '{filename}'. Unsupported text encoding.")

        cleaned = text.strip()
        if not cleaned:
            raise ValueError(f"Text document '{filename}' is empty.")

        return [ExtractedChunkSection(text=cleaned, page_number=1, metadata={"format": "txt"})]

    @classmethod
    def _extract_csv(cls, file_bytes: bytes, filename: str) -> List[ExtractedChunkSection]:
        # Decode CSV bytes
        text = None
        for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
            try:
                text = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise ValueError(f"Unable to decode CSV document '{filename}'. Unsupported encoding.")

        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            raise ValueError(f"CSV document '{filename}' is empty.")

        try:
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)
        except Exception as ce:
            raise ValueError(f"Invalid CSV structure in '{filename}': {str(ce)}")

        if not rows or len(rows) < 1:
            raise ValueError(f"CSV document '{filename}' contains no rows.")

        headers = [h.strip() for h in rows[0]]
        data_rows = rows[1:]

        if not data_rows:
            # Only header row
            return [ExtractedChunkSection(
                text=f"CSV Table Headers: {', '.join(headers)} (No data rows)",
                page_number=1,
                metadata={"format": "csv", "headers": headers, "total_rows": 0}
            )]

        # Group CSV rows into readable batches (e.g., 20 rows per chunk section)
        # to ensure high retrieval relevance and meaningful context
        batch_size = 20
        sections: List[ExtractedChunkSection] = []

        for batch_idx in range(0, len(data_rows), batch_size):
            batch = data_rows[batch_idx : batch_idx + batch_size]
            batch_num = (batch_idx // batch_size) + 1
            start_row = batch_idx + 1
            end_row = batch_idx + len(batch)

            row_lines = []
            for r_idx, row in enumerate(batch):
                row_items = []
                for h_idx, val in enumerate(row):
                    header = headers[h_idx] if h_idx < len(headers) else f"Col{h_idx+1}"
                    row_items.append(f"{header}: {val.strip()}")
                row_lines.append(f"Row {start_row + r_idx}: {', '.join(row_items)}")

            batch_text = (
                f"CSV Dataset: {filename} (Rows {start_row} to {end_row} of {len(data_rows)})\n"
                f"Schema: {', '.join(headers)}\n" + "\n".join(row_lines)
            )

            sections.append(ExtractedChunkSection(
                text=batch_text,
                page_number=batch_num,  # Corresponds to row batch for citations
                metadata={
                    "format": "csv",
                    "headers": headers,
                    "start_row": start_row,
                    "end_row": end_row,
                    "total_rows": len(data_rows),
                }
            ))

        return sections
