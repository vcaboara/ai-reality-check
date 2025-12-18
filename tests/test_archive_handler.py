"""Tests for archive extraction and processing."""

import shutil

# Add src to path for imports
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.archive_handler import (
    ArchiveExtractionError,
    SecurityValidationError,
    extract_archive,
    extract_tar,
    extract_zip,
    find_supported_files,
    is_archive_file,
    process_archive,
    validate_archive_safety,
    validate_extracted_path,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    files = {}

    # Create sample PDF (just a text file named .pdf for testing)
    pdf_file = temp_dir / "document.pdf"
    pdf_file.write_text("This is a test PDF document.")
    files["pdf"] = pdf_file

    # Create sample TXT
    txt_file = temp_dir / "notes.txt"
    txt_file.write_text("These are test notes.")
    files["txt"] = txt_file

    # Create sample unsupported file
    doc_file = temp_dir / "spreadsheet.xlsx"
    doc_file.write_text("This is an Excel file.")
    files["xlsx"] = doc_file

    return files


def test_is_archive_file():
    """Test archive file detection."""
    assert is_archive_file("test.zip")
    assert is_archive_file("test.tar")
    assert is_archive_file("test.tar.gz")
    assert is_archive_file("test.tgz")
    assert is_archive_file("TEST.ZIP")  # Case insensitive

    assert not is_archive_file("test.pdf")
    assert not is_archive_file("test.txt")
    assert not is_archive_file("test.docx")


def test_validate_archive_safety_success(temp_dir):
    """Test archive size validation succeeds for small files."""
    # Create small test file
    small_file = temp_dir / "small.zip"
    small_file.write_text("small content")

    # Should not raise
    validate_archive_safety(small_file)


def test_validate_archive_safety_too_large(temp_dir):
    """Test archive size validation fails for large files."""
    # Create large test file (simulate >50MB)
    large_file = temp_dir / "large.zip"
    # Write 51MB of data
    with open(large_file, "wb") as f:
        f.write(b"x" * (51 * 1024 * 1024))

    with pytest.raises(SecurityValidationError, match="Archive too large"):
        validate_archive_safety(large_file)


def test_validate_extracted_path_success(temp_dir):
    """Test path validation succeeds for safe paths."""
    extract_to = temp_dir / "extract"
    extract_to.mkdir()

    safe_path = extract_to / "subdir" / "file.txt"

    # Should not raise
    validate_extracted_path(extract_to, safe_path)


def test_validate_extracted_path_traversal(temp_dir):
    """Test path validation detects traversal attempts."""
    extract_to = temp_dir / "extract"
    extract_to.mkdir()

    # Try to escape using ..
    dangerous_path = extract_to / ".." / ".." / "etc" / "passwd"

    with pytest.raises(SecurityValidationError, match="Path traversal detected"):
        validate_extracted_path(extract_to, dangerous_path)


def test_extract_zip_success(temp_dir, sample_files):
    """Test successful ZIP extraction."""
    # Create ZIP file
    zip_path = temp_dir / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(sample_files["pdf"], arcname="document.pdf")
        zf.write(sample_files["txt"], arcname="notes.txt")

    # Extract
    extract_to = temp_dir / "extracted"
    extract_to.mkdir()

    files = extract_zip(zip_path, extract_to)

    assert len(files) == 2
    assert (extract_to / "document.pdf").exists()
    assert (extract_to / "notes.txt").exists()


def test_extract_zip_corrupted(temp_dir):
    """Test ZIP extraction fails on corrupted file."""
    # Create corrupted ZIP
    bad_zip = temp_dir / "bad.zip"
    bad_zip.write_text("This is not a valid ZIP file")

    extract_to = temp_dir / "extracted"
    extract_to.mkdir()

    with pytest.raises(ArchiveExtractionError, match="Corrupted ZIP"):
        extract_zip(bad_zip, extract_to)


def test_extract_zip_too_many_files(temp_dir, sample_files):
    """Test ZIP extraction fails when too many files."""
    # Create ZIP with >100 files
    zip_path = temp_dir / "many.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for i in range(101):
            zf.writestr(f"file_{i}.txt", f"Content {i}")

    extract_to = temp_dir / "extracted"
    extract_to.mkdir()

    with pytest.raises(SecurityValidationError, match="Too many files"):
        extract_zip(zip_path, extract_to)


def test_extract_tar_success(temp_dir, sample_files):
    """Test successful TAR extraction."""
    # Create TAR file
    tar_path = temp_dir / "test.tar"
    with tarfile.open(tar_path, "w") as tf:
        tf.add(sample_files["pdf"], arcname="document.pdf")
        tf.add(sample_files["txt"], arcname="notes.txt")

    # Extract
    extract_to = temp_dir / "extracted"
    extract_to.mkdir()

    files = extract_tar(tar_path, extract_to)

    assert len(files) == 2
    assert (extract_to / "document.pdf").exists()
    assert (extract_to / "notes.txt").exists()


def test_extract_tar_gz_success(temp_dir, sample_files):
    """Test successful TAR.GZ extraction."""
    # Create TAR.GZ file
    tar_gz_path = temp_dir / "test.tar.gz"
    with tarfile.open(tar_gz_path, "w:gz") as tf:
        tf.add(sample_files["pdf"], arcname="document.pdf")
        tf.add(sample_files["txt"], arcname="notes.txt")

    # Extract
    extract_to = temp_dir / "extracted"
    extract_to.mkdir()

    files = extract_tar(tar_gz_path, extract_to)

    assert len(files) == 2
    assert (extract_to / "document.pdf").exists()
    assert (extract_to / "notes.txt").exists()


def test_extract_tar_corrupted(temp_dir):
    """Test TAR extraction fails on corrupted file."""
    # Create corrupted TAR
    bad_tar = temp_dir / "bad.tar"
    bad_tar.write_text("This is not a valid TAR file")

    extract_to = temp_dir / "extracted"
    extract_to.mkdir()

    with pytest.raises(ArchiveExtractionError, match="Corrupted TAR"):
        extract_tar(bad_tar, extract_to)


def test_extract_archive_unsupported_format(temp_dir):
    """Test extraction fails for unsupported format."""
    # Create file with unsupported extension
    bad_file = temp_dir / "test.rar"
    bad_file.write_text("RAR archive")

    extract_to = temp_dir / "extracted"
    extract_to.mkdir()

    with pytest.raises(ArchiveExtractionError, match="Unsupported archive format"):
        extract_archive(bad_file, extract_to)


def test_find_supported_files(temp_dir, sample_files):
    """Test finding supported files in directory."""
    # Create directory structure
    test_dir = temp_dir / "test_files"
    test_dir.mkdir()
    subdir = test_dir / "subdir"
    subdir.mkdir()

    # Copy files to test directory
    shutil.copy(sample_files["pdf"], test_dir / "doc1.pdf")
    shutil.copy(sample_files["txt"], test_dir / "notes.txt")
    shutil.copy(sample_files["xlsx"], test_dir / "data.xlsx")  # Unsupported
    shutil.copy(sample_files["pdf"], subdir / "doc2.pdf")

    # Find supported files
    files = find_supported_files(test_dir)

    # Should find 3 supported files (2 PDFs, 1 TXT), ignore XLSX
    assert len(files) == 3
    assert any(f.name == "doc1.pdf" for f in files)
    assert any(f.name == "notes.txt" for f in files)
    assert any(f.name == "doc2.pdf" for f in files)
    assert not any(f.name == "data.xlsx" for f in files)


def test_find_supported_files_nested_archive(temp_dir, sample_files):
    """Test finding files in nested archives (1 level deep)."""
    # Create inner ZIP
    inner_zip = temp_dir / "inner.zip"
    with zipfile.ZipFile(inner_zip, "w") as zf:
        zf.write(sample_files["pdf"], arcname="inner_doc.pdf")

    # Create outer directory
    outer_dir = temp_dir / "outer"
    outer_dir.mkdir()
    shutil.copy(inner_zip, outer_dir / "nested.zip")

    # Find files (should extract nested archive)
    files = find_supported_files(outer_dir)

    # Should find the PDF from nested archive
    assert len(files) == 1
    assert any("inner_doc.pdf" in str(f) for f in files)


def test_process_archive_success(temp_dir, sample_files):
    """Test complete archive processing workflow."""
    # Create ZIP with multiple files
    zip_path = temp_dir / "project.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(sample_files["pdf"], arcname="report.pdf")
        zf.write(sample_files["txt"], arcname="readme.txt")

    # Process archive
    supported_files, temp_extract_dir = process_archive(zip_path)

    try:
        assert len(supported_files) == 2
        assert any(f.name == "report.pdf" for f in supported_files)
        assert any(f.name == "readme.txt" for f in supported_files)
        assert temp_extract_dir.exists()
    finally:
        # Cleanup
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir, ignore_errors=True)


def test_process_archive_no_supported_files(temp_dir, sample_files):
    """Test processing archive with no supported files."""
    # Create ZIP with only unsupported files
    zip_path = temp_dir / "unsupported.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(sample_files["xlsx"], arcname="data.xlsx")

    # Process archive
    supported_files, temp_extract_dir = process_archive(zip_path)

    try:
        # Should return empty list but not raise
        assert len(supported_files) == 0
    finally:
        # Cleanup
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir, ignore_errors=True)


def test_process_archive_cleanup_on_error(temp_dir):
    """Test temporary directory is cleaned up on error."""
    # Create corrupted ZIP
    bad_zip = temp_dir / "bad.zip"
    bad_zip.write_text("Not a ZIP")

    with pytest.raises(ArchiveExtractionError):
        process_archive(bad_zip)

    # Check no temp directories left behind
    temp_dirs = [d for d in temp_dir.iterdir() if d.is_dir() and "archive_extract" in d.name]
    assert len(temp_dirs) == 0


def test_extract_zip_skips_large_files(temp_dir):
    """Test that large files in ZIP are skipped."""
    # Create ZIP with large file
    zip_path = temp_dir / "large.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
        # Create a large file (>10MB)
        large_content = b"x" * (11 * 1024 * 1024)
        zf.writestr("large.txt", large_content)
        zf.writestr("small.txt", "small content")

    extract_to = temp_dir / "extracted"
    extract_to.mkdir()

    # Should extract only small file
    files = extract_zip(zip_path, extract_to)

    assert len(files) == 1
    assert files[0].name == "small.txt"
    assert not (extract_to / "large.txt").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
