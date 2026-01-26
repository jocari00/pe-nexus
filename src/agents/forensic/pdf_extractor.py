"""PDF extraction with bounding box tracking for traceability."""

import hashlib
import logging
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional

import pdfplumber

from src.schemas.financials import BoundingBox

logger = logging.getLogger(__name__)


@dataclass
class ExtractedText:
    """Text extracted from a PDF with location information."""

    text: str
    page_number: int
    bounding_box: Optional[BoundingBox]
    confidence: float = 1.0


@dataclass
class ExtractedTable:
    """Table extracted from a PDF."""

    data: list[list[str]]
    page_number: int
    bounding_box: Optional[BoundingBox]
    headers: Optional[list[str]] = None


@dataclass
class ExtractedNumber:
    """Numeric value extracted from PDF with context."""

    value: Decimal
    raw_text: str
    context: str
    page_number: int
    bounding_box: Optional[BoundingBox]
    confidence: float = 1.0
    label: Optional[str] = None


class PDFExtractor:
    """
    PDF extraction engine with bounding box tracking.

    Features:
    - Page-by-page text extraction
    - Table detection and extraction
    - Bounding box coordinates for all extractions
    - Financial number parsing
    - Checksum generation for document integrity
    """

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        self._pdf = pdfplumber.open(self.file_path)
        self._checksum: Optional[str] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the PDF file."""
        if self._pdf:
            self._pdf.close()

    @property
    def page_count(self) -> int:
        """Get total number of pages."""
        return len(self._pdf.pages)

    @property
    def checksum(self) -> str:
        """Get SHA-256 checksum of the PDF file."""
        if self._checksum is None:
            with open(self.file_path, "rb") as f:
                self._checksum = hashlib.sha256(f.read()).hexdigest()
        return self._checksum

    def get_page_text(self, page_number: int) -> str:
        """
        Get all text from a specific page.

        Args:
            page_number: 1-indexed page number

        Returns:
            Extracted text
        """
        if page_number < 1 or page_number > self.page_count:
            raise ValueError(f"Invalid page number: {page_number}")

        page = self._pdf.pages[page_number - 1]
        return page.extract_text() or ""

    def get_all_text(self) -> list[ExtractedText]:
        """
        Extract text from all pages.

        Returns:
            List of ExtractedText objects
        """
        results = []
        for i, page in enumerate(self._pdf.pages, start=1):
            text = page.extract_text()
            if text:
                # Get page bounding box
                bbox = BoundingBox(
                    x0=page.bbox[0],
                    y0=page.bbox[1],
                    x1=page.bbox[2],
                    y1=page.bbox[3],
                )
                results.append(ExtractedText(
                    text=text,
                    page_number=i,
                    bounding_box=bbox,
                ))
        return results

    def get_tables(self, page_number: Optional[int] = None) -> list[ExtractedTable]:
        """
        Extract tables from the PDF.

        Args:
            page_number: Optional specific page (1-indexed), or None for all pages

        Returns:
            List of ExtractedTable objects
        """
        results = []

        if page_number:
            pages = [(page_number, self._pdf.pages[page_number - 1])]
        else:
            pages = list(enumerate(self._pdf.pages, start=1))

        for page_num, page in pages:
            tables = page.extract_tables()
            for table in tables:
                if table and len(table) > 0:
                    # Try to identify headers
                    headers = None
                    data = table
                    if len(table) > 1:
                        # Assume first row might be headers
                        potential_headers = table[0]
                        if all(isinstance(h, str) and h for h in potential_headers):
                            headers = potential_headers
                            data = table[1:]

                    results.append(ExtractedTable(
                        data=data,
                        page_number=page_num,
                        bounding_box=None,  # pdfplumber doesn't provide table bbox directly
                        headers=headers,
                    ))

        return results

    def extract_financial_numbers(
        self,
        page_number: Optional[int] = None,
    ) -> list[ExtractedNumber]:
        """
        Extract financial numbers from the PDF.

        Looks for patterns like:
        - $1,234,567
        - 1,234.56
        - (1,234) for negative numbers
        - 1.5M, 2.3B for millions/billions

        Args:
            page_number: Optional specific page (1-indexed)

        Returns:
            List of ExtractedNumber objects
        """
        results = []

        # Patterns for financial numbers
        patterns = [
            # Dollar amounts: $1,234,567.89
            (r'\$[\d,]+(?:\.\d{1,2})?', "currency"),
            # Parenthetical negatives: (1,234.56)
            (r'\([\d,]+(?:\.\d{1,2})?\)', "negative"),
            # Plain numbers with commas: 1,234,567
            (r'(?<![.\d])[\d,]{4,}(?:\.\d{1,2})?(?![.\d])', "number"),
            # Millions/Billions: 1.5M, 2.3B
            (r'[\d.]+[MB]', "abbreviated"),
        ]

        if page_number:
            pages = [(page_number, self._pdf.pages[page_number - 1])]
        else:
            pages = list(enumerate(self._pdf.pages, start=1))

        for page_num, page in pages:
            text = page.extract_text() or ""
            words = page.extract_words()

            for pattern, pattern_type in patterns:
                for match in re.finditer(pattern, text):
                    raw_text = match.group()
                    value = self._parse_financial_number(raw_text, pattern_type)

                    if value is not None:
                        # Get context (surrounding text)
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        context = text[start:end].strip()

                        # Try to find bounding box from words
                        bbox = self._find_word_bbox(words, raw_text)

                        results.append(ExtractedNumber(
                            value=value,
                            raw_text=raw_text,
                            context=context,
                            page_number=page_num,
                            bounding_box=bbox,
                        ))

        return results

    def _parse_financial_number(
        self,
        text: str,
        pattern_type: str,
    ) -> Optional[Decimal]:
        """Parse a financial number string to Decimal."""
        try:
            # Remove currency symbol and whitespace
            cleaned = text.strip().replace("$", "").replace(",", "")

            # Handle parenthetical negatives
            if pattern_type == "negative":
                cleaned = cleaned.replace("(", "-").replace(")", "")

            # Handle abbreviated (M/B)
            if pattern_type == "abbreviated":
                multiplier = Decimal("1")
                if cleaned.endswith("M"):
                    multiplier = Decimal("1000000")
                    cleaned = cleaned[:-1]
                elif cleaned.endswith("B"):
                    multiplier = Decimal("1000000000")
                    cleaned = cleaned[:-1]
                return Decimal(cleaned) * multiplier

            return Decimal(cleaned)

        except (InvalidOperation, ValueError):
            return None

    def _find_word_bbox(
        self,
        words: list[dict],
        target_text: str,
    ) -> Optional[BoundingBox]:
        """Find bounding box for a specific text in word list."""
        # Clean target for comparison
        target_clean = target_text.replace(",", "").replace("$", "")

        for word in words:
            word_text = word.get("text", "").replace(",", "").replace("$", "")
            if target_clean in word_text or word_text in target_clean:
                return BoundingBox(
                    x0=word["x0"],
                    y0=word["top"],
                    x1=word["x1"],
                    y1=word["bottom"],
                )

        return None

    def find_text_with_bbox(
        self,
        search_text: str,
        page_number: Optional[int] = None,
    ) -> list[tuple[int, BoundingBox, str]]:
        """
        Find text and return its bounding box.

        Args:
            search_text: Text to search for
            page_number: Optional specific page

        Returns:
            List of (page_number, bounding_box, context) tuples
        """
        results = []

        if page_number:
            pages = [(page_number, self._pdf.pages[page_number - 1])]
        else:
            pages = list(enumerate(self._pdf.pages, start=1))

        search_lower = search_text.lower()

        for page_num, page in pages:
            words = page.extract_words()
            text = page.extract_text() or ""

            # Search for the text
            for i, word in enumerate(words):
                if search_lower in word.get("text", "").lower():
                    bbox = BoundingBox(
                        x0=word["x0"],
                        y0=word["top"],
                        x1=word["x1"],
                        y1=word["bottom"],
                    )

                    # Get surrounding context
                    word_start = text.lower().find(word.get("text", "").lower())
                    if word_start >= 0:
                        start = max(0, word_start - 30)
                        end = min(len(text), word_start + len(word.get("text", "")) + 30)
                        context = text[start:end]
                    else:
                        context = word.get("text", "")

                    results.append((page_num, bbox, context))

        return results

    def extract_labeled_values(
        self,
        labels: list[str],
    ) -> dict[str, list[ExtractedNumber]]:
        """
        Extract values associated with specific labels.

        Useful for finding specific financial metrics like
        "Revenue", "EBITDA", "Net Income", etc.

        Args:
            labels: List of labels to search for

        Returns:
            Dict mapping labels to found values
        """
        results = {label: [] for label in labels}

        for page_num, page in enumerate(self._pdf.pages, start=1):
            text = page.extract_text() or ""
            words = page.extract_words()

            for label in labels:
                # Find label occurrences
                pattern = rf'{re.escape(label)}[\s:]*[\$]?([\d,]+(?:\.\d{{1,2}})?)'
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    raw_value = match.group(1)
                    value = self._parse_financial_number(raw_value, "number")

                    if value is not None:
                        # Get context
                        start = max(0, match.start() - 20)
                        end = min(len(text), match.end() + 20)
                        context = text[start:end]

                        # Try to find bbox
                        bbox = self._find_word_bbox(words, raw_value)

                        results[label].append(ExtractedNumber(
                            value=value,
                            raw_text=match.group(0),
                            context=context,
                            page_number=page_num,
                            bounding_box=bbox,
                            label=label,
                        ))

        return results

    def get_metadata(self) -> dict[str, Any]:
        """Get PDF metadata."""
        return {
            "page_count": self.page_count,
            "checksum": self.checksum,
            "metadata": self._pdf.metadata or {},
        }
