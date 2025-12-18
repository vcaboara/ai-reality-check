"""Secure archive extraction and processing for batch file analysis.

Supports ZIP, TAR, and TAR.GZ formats with security protections against:
- Path traversal attacks
- Zip bombs (excessive file counts and sizes)
- Deeply nested archives
"""

import logging
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Security limits
MAX_ARCHIVE_SIZE_MB = 50  # Maximum archive size in MB
MAX_FILES_IN_ARCHIVE = 100  # Maximum number of files to extract
MAX_EXTRACTION_DEPTH = 1  # Maximum nesting level for archives
MAX_FILE_SIZE_MB = 10  # Maximum size for individual extracted file

SUPPORTED_ARCHIVE_EXTENSIONS = {".zip", ".tar", ".tar.gz", ".tgz"}
SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".txt", ".docx"}


class ArchiveExtractionError(Exception):
    """Raised when archive extraction fails."""

    pass


class SecurityValidationError(Exception):
    """Raised when security validation fails."""

    pass


def is_archive_file(filename: str) -> bool:
    """Check if file is a supported archive format.

    Args:
        filename: Name of the file to check

    Returns:
        True if file has supported archive extension
    """
    file_path = Path(filename)
    # Check for .tar.gz specifically
    if filename.lower().endswith(".tar.gz"):
        return True
    return file_path.suffix.lower() in SUPPORTED_ARCHIVE_EXTENSIONS


def validate_archive_safety(archive_path: Path) -> None:
    """Validate archive doesn't exceed security limits.

    Args:
        archive_path: Path to archive file

    Raises:
        SecurityValidationError: If archive fails security checks
    """
    # Check archive size
    archive_size_mb = archive_path.stat().st_size / (1024 * 1024)
    if archive_size_mb > MAX_ARCHIVE_SIZE_MB:
        raise SecurityValidationError(
            f"Archive too large: {archive_size_mb:.1f}MB exceeds {MAX_ARCHIVE_SIZE_MB}MB limit"
        )

    logger.info(f"Archive size validation passed: {archive_size_mb:.2f}MB")


def validate_extracted_path(extract_to: Path, target_path: Path) -> None:
    """Validate extraction path doesn't escape target directory (path traversal protection).

    Args:
        extract_to: Base extraction directory
        target_path: Target path to validate

    Raises:
        SecurityValidationError: If path attempts to escape extraction directory
    """
    # Resolve both paths to absolute and check containment
    extract_to_abs = extract_to.resolve()
    target_abs = target_path.resolve()

    try:
        target_abs.relative_to(extract_to_abs)
    except ValueError as err:
        raise SecurityValidationError(
            f"Path traversal detected: {target_path} attempts to escape extraction directory"
        ) from err


def extract_zip(archive_path: Path, extract_to: Path) -> list[Path]:
    """Extract ZIP archive securely.

    Args:
        archive_path: Path to ZIP file
        extract_to: Directory to extract to

    Returns:
        List of extracted file paths

    Raises:
        ArchiveExtractionError: If extraction fails
        SecurityValidationError: If security checks fail
    """
    extracted_files = []

    try:
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            # Check number of files
            if len(zip_ref.namelist()) > MAX_FILES_IN_ARCHIVE:
                raise SecurityValidationError(
                    f"Too many files in archive: {len(zip_ref.namelist())} exceeds {MAX_FILES_IN_ARCHIVE} limit"
                )

            # Extract files with safety checks
            for member in zip_ref.namelist():
                # Skip directories
                if member.endswith("/"):
                    continue

                # Validate path safety
                target_path = extract_to / member
                validate_extracted_path(extract_to, target_path)

                # Check individual file size
                file_info = zip_ref.getinfo(member)
                file_size_mb = file_info.file_size / (1024 * 1024)
                if file_size_mb > MAX_FILE_SIZE_MB:
                    logger.warning(
                        f"Skipping large file {member}: {file_size_mb:.1f}MB exceeds {MAX_FILE_SIZE_MB}MB limit"
                    )
                    continue

                # Extract the file
                zip_ref.extract(member, extract_to)
                extracted_files.append(target_path)
                logger.debug(f"Extracted: {member}")

        logger.info(f"Extracted {len(extracted_files)} files from ZIP archive")
        return extracted_files

    except zipfile.BadZipFile as e:
        raise ArchiveExtractionError(f"Corrupted ZIP file: {e}") from e
    except SecurityValidationError:
        # Re-raise security errors without wrapping
        raise
    except Exception as e:
        raise ArchiveExtractionError(f"Failed to extract ZIP: {e}") from e


def extract_tar(archive_path: Path, extract_to: Path) -> list[Path]:
    """Extract TAR/TAR.GZ archive securely.

    Args:
        archive_path: Path to TAR or TAR.GZ file
        extract_to: Directory to extract to

    Returns:
        List of extracted file paths

    Raises:
        ArchiveExtractionError: If extraction fails
        SecurityValidationError: If security checks fail
    """
    extracted_files = []

    try:
        # Determine compression mode
        if archive_path.name.endswith((".tar.gz", ".tgz")):
            mode = "r:gz"
        else:
            mode = "r"

        with tarfile.open(str(archive_path), mode) as tar_ref:  # type: ignore[call-overload]
            # Check number of files
            members = tar_ref.getmembers()
            if len(members) > MAX_FILES_IN_ARCHIVE:
                raise SecurityValidationError(
                    f"Too many files in archive: {len(members)} exceeds {MAX_FILES_IN_ARCHIVE} limit"
                )

            # Extract files with safety checks
            for member in members:
                # Skip directories and special files
                if not member.isfile():
                    continue

                # Validate path safety (tarfile uses member.name)
                target_path = extract_to / member.name
                validate_extracted_path(extract_to, target_path)

                # Check individual file size
                file_size_mb = member.size / (1024 * 1024)
                if file_size_mb > MAX_FILE_SIZE_MB:
                    logger.warning(
                        f"Skipping large file {member.name}: {file_size_mb:.1f}MB exceeds {MAX_FILE_SIZE_MB}MB limit"
                    )
                    continue

                # Extract the file
                tar_ref.extract(member, extract_to, filter="data")
                extracted_files.append(target_path)
                logger.debug(f"Extracted: {member.name}")

        logger.info(f"Extracted {len(extracted_files)} files from TAR archive")
        return extracted_files

    except tarfile.TarError as e:
        raise ArchiveExtractionError(f"Corrupted TAR file: {e}") from e
    except SecurityValidationError:
        # Re-raise security errors without wrapping
        raise
    except Exception as e:
        raise ArchiveExtractionError(f"Failed to extract TAR: {e}") from e


def extract_archive(archive_path: Path, extract_to: Path) -> list[Path]:
    """Extract archive to directory based on file type.

    Args:
        archive_path: Path to archive file
        extract_to: Directory to extract to

    Returns:
        List of extracted file paths

    Raises:
        ArchiveExtractionError: If extraction fails
        SecurityValidationError: If security checks fail
    """
    # Validate archive safety
    validate_archive_safety(archive_path)

    # Extract based on type
    filename = archive_path.name.lower()
    if filename.endswith(".zip"):
        return extract_zip(archive_path, extract_to)
    elif filename.endswith((".tar", ".tar.gz", ".tgz")):
        return extract_tar(archive_path, extract_to)
    else:
        raise ArchiveExtractionError(f"Unsupported archive format: {archive_path.name}")


def find_supported_files(directory: Path, depth: int = 0) -> list[Path]:
    """Recursively find supported document files in directory.

    Args:
        directory: Directory to search
        depth: Current recursion depth (for limiting nesting)

    Returns:
        List of paths to supported document files
    """
    supported_files: list[Path] = []

    # Limit recursion depth to prevent processing deeply nested structures
    if depth > MAX_EXTRACTION_DEPTH:
        logger.warning(f"Max extraction depth reached at {directory}")
        return supported_files

    try:
        for item in directory.iterdir():
            if item.is_file():
                # Check if it's a supported document type
                if item.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS:
                    supported_files.append(item)
                    logger.debug(f"Found supported file: {item.name}")
                # Check if it's a nested archive (1 level deep only)
                elif depth < MAX_EXTRACTION_DEPTH and is_archive_file(item.name):
                    logger.info(f"Found nested archive: {item.name} at depth {depth}")
                    # Extract nested archive
                    nested_extract_dir = item.parent / f"_extracted_{item.stem}"
                    nested_extract_dir.mkdir(exist_ok=True)
                    try:
                        extract_archive(item, nested_extract_dir)
                        # Recursively find files in nested archive
                        nested_files = find_supported_files(nested_extract_dir, depth + 1)
                        supported_files.extend(nested_files)
                    except (ArchiveExtractionError, SecurityValidationError) as e:
                        logger.warning(f"Failed to extract nested archive {item.name}: {e}")
            elif item.is_dir() and not item.name.startswith("_extracted_"):
                # Recursively search subdirectories
                supported_files.extend(find_supported_files(item, depth))

    except PermissionError as e:
        logger.warning(f"Permission denied accessing {directory}: {e}")

    return supported_files


def process_archive(archive_path: Path) -> tuple[list[Path], Path]:
    """Process archive file and return extracted document files.

    Creates temporary directory, extracts archive, and finds supported files.

    Args:
        archive_path: Path to archive file

    Returns:
        Tuple of (list of supported file paths, temp directory path)
        Caller is responsible for cleaning up temp directory

    Raises:
        ArchiveExtractionError: If extraction fails
        SecurityValidationError: If security checks fail
    """
    # Create temporary extraction directory
    temp_dir = Path(tempfile.mkdtemp(prefix="archive_extract_"))
    logger.info(f"Created temp extraction directory: {temp_dir}")

    try:
        # Extract archive
        extracted_files = extract_archive(archive_path, temp_dir)
        logger.info(f"Extracted {len(extracted_files)} files from archive")

        # Find supported document files
        supported_files = find_supported_files(temp_dir)
        logger.info(f"Found {len(supported_files)} supported files in archive")

        if not supported_files:
            logger.warning("No supported files found in archive")

        return supported_files, temp_dir

    except Exception:
        # Clean up on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
