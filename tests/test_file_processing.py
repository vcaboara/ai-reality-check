"""Unit tests for file processing helper functions."""

import tempfile
from pathlib import Path

import pytest

from src.ui.server import (
    extract_text_from_file,
    extract_text_with_header,
    process_multiple_files,
)


@pytest.fixture
def temp_text_file():
    """Create a temporary text file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("This is test content.\nLine 2 of content.")
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_pdf_file():
    """Create a temporary PDF file with text."""
    from pypdf import PdfWriter, PageObject
    from pypdf.generic import RectangleObject
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        temp_path = Path(f.name)
    
    # Create a simple PDF with text
    writer = PdfWriter()
    page = PageObject.create_blank_page(width=200, height=200)
    writer.add_page(page)
    
    with open(temp_path, 'wb') as pdf_file:
        writer.write(pdf_file)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


def test_extract_text_from_file_txt(temp_text_file):
    """Test extracting text from a TXT file."""
    text = extract_text_from_file(temp_text_file)
    
    assert "This is test content." in text
    assert "Line 2 of content." in text


def test_extract_text_from_file_pdf(temp_pdf_file):
    """Test extracting text from a PDF file."""
    # Should not raise error even if PDF has no extractable text
    text = extract_text_from_file(temp_pdf_file)
    assert isinstance(text, str)


def test_extract_text_from_file_unsupported():
    """Test that unsupported file types raise ValueError."""
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text_from_file(temp_path)
    finally:
        temp_path.unlink()


def test_extract_text_with_header_included(temp_text_file):
    """Test extracting text with header."""
    text = extract_text_with_header(temp_text_file, include_header=True)
    
    assert f"--- File: {temp_text_file.name} ---" in text
    assert "This is test content." in text


def test_extract_text_with_header_excluded(temp_text_file):
    """Test extracting text without header."""
    text = extract_text_with_header(temp_text_file, include_header=False)
    
    assert "--- File:" not in text
    assert "This is test content." in text


def test_process_multiple_files_success(temp_text_file):
    """Test processing multiple files successfully."""
    # Create second temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("Second file content.")
        temp_path2 = Path(f.name)
    
    try:
        result = process_multiple_files([temp_text_file, temp_path2])
        
        assert temp_text_file.name in result
        assert temp_path2.name in result
        assert "This is test content." in result
        assert "Second file content." in result
    finally:
        temp_path2.unlink()


def test_process_multiple_files_with_failures(temp_text_file, caplog):
    """Test processing files with some failures."""
    # Create an unsupported file
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        bad_file = Path(f.name)
    
    try:
        # Should succeed with valid file, log warning for bad file
        result = process_multiple_files([temp_text_file, bad_file])
        
        assert "This is test content." in result
        assert "Failed to extract text" in caplog.text
    finally:
        bad_file.unlink()


def test_process_multiple_files_all_fail():
    """Test processing files when all fail."""
    # Create only unsupported files
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        bad_file = Path(f.name)
    
    try:
        with pytest.raises(ValueError, match="Could not extract text from any files"):
            process_multiple_files([bad_file])
    finally:
        bad_file.unlink()


def test_process_multiple_files_empty_list():
    """Test processing empty file list."""
    with pytest.raises(ValueError, match="Could not extract text from any files"):
        process_multiple_files([])


def test_extract_text_preserves_encoding(temp_text_file):
    """Test that text extraction preserves UTF-8 encoding."""
    # Create file with special characters
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("Special chars: é ñ ü 中文")
        special_file = Path(f.name)
    
    try:
        text = extract_text_from_file(special_file)
        assert "é ñ ü 中文" in text
    finally:
        special_file.unlink()
