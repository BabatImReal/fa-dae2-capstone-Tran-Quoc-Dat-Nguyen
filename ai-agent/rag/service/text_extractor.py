"""
Text extraction utilities for various document formats.
"""

import logging
from pathlib import Path

from docx import Document
import fitz  # PyMuPDF
import pdfplumber

logger = logging.getLogger(__name__)


class TextExtractor:
    """Base class for text extraction."""

    def extract(self, file_path: str) -> str:
        """Extract text from a document."""
        raise NotImplementedError


class PDFPlumberExtractor(TextExtractor):
    """PDF text extraction using pdfplumber (recommended)."""

    def extract(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num} ---\n{page_text}\n"
                    else:
                        logger.warning(f"No text found on page {page_num}")

            logger.info(f"Extracted {len(text)} characters from {file_path}")
            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise


class PyMuPDFExtractor(TextExtractor):
    """PDF text extraction using PyMuPDF (for complex PDFs)."""

    def extract(self, file_path: str) -> str:
        """Extract text from PDF using PyMuPDF."""
        try:
            doc = fitz.open(file_path)
            text = ""

            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                if page_text:
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                else:
                    logger.warning(f"No text found on page {page_num + 1}")

            doc.close()
            logger.info(f"Extracted {len(text)} characters from {file_path}")
            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise


class DocxExtractor(TextExtractor):
    """Word document text extraction using python-docx."""

    def extract(self, file_path: str) -> str:
        """Extract text from Word document."""
        try:
            doc = Document(file_path)
            text = ""

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"

            logger.info(f"Extracted {len(text)} characters from {file_path}")
            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise


class TxtExtractor(TextExtractor):
    """Plain text file extraction."""

    def extract(self, file_path: str) -> str:
        """Extract text from plain text file."""
        try:
            with open(file_path, encoding="utf-8") as file:
                text = file.read()

            logger.info(f"Extracted {len(text)} characters from {file_path}")
            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise


def get_extractor(file_path: str) -> TextExtractor:
    """Get the appropriate extractor for a file based on its extension."""
    file_ext = Path(file_path).suffix.lower()

    extractors = {
        ".pdf": PDFPlumberExtractor(),
        ".docx": DocxExtractor(),
        ".doc": DocxExtractor(),
        ".txt": TxtExtractor(),
    }

    if file_ext in extractors:
        return extractors[file_ext]
    else:
        # Default to PDF extractor for unknown extensions
        logger.warning(f"Unknown file extension {file_ext}, defaulting to PDF extractor")
        return PDFPlumberExtractor()


def extract_text(file_path: str, extractor_type: str = "auto") -> str:
    """
    Extract text from a document file.

    Args:
        file_path: Path to the document file
        extractor_type: Type of extractor to use ("auto", "pdfplumber", "pymupdf")

    Returns:
        Extracted text as string
    """
    if extractor_type == "auto":
        extractor = get_extractor(file_path)
    elif extractor_type == "pdfplumber":
        extractor = PDFPlumberExtractor()
    elif extractor_type == "pymupdf":
        extractor = PyMuPDFExtractor()
    else:
        raise ValueError(f"Unknown extractor type: {extractor_type}")

    return extractor.extract(file_path)