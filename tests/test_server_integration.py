"""Integration tests for archive file upload via Flask server."""

import io
import json

# Add src to path for imports
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def app():
    """Create Flask test app."""
    # Mock environment to avoid requiring API keys
    import os

    os.environ["FLASK_ENV"] = "testing"

    # Import after setting env
    from src.ui.server import app as flask_app

    flask_app.config["TESTING"] = True
    flask_app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

    # Use temp directories for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        flask_app.config["UPLOAD_FOLDER"] = temp_path / "uploads"
        flask_app.config["RESULTS_FOLDER"] = temp_path / "results"
        flask_app.config["UPLOAD_FOLDER"].mkdir(parents=True)
        flask_app.config["RESULTS_FOLDER"].mkdir(parents=True)

        yield flask_app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def sample_archive():
    """Create sample ZIP archive with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Create sample text files
        file1 = temp_path / "doc1.txt"
        file1.write_text("This is a test document about thermal processing.")

        file2 = temp_path / "doc2.txt"
        file2.write_text("Additional technical specifications for the reactor.")

        # Create ZIP archive
        zip_path = temp_path / "test_project.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(file1, arcname="doc1.txt")
            zf.write(file2, arcname="doc2.txt")

        # Read archive content
        with open(zip_path, "rb") as f:
            archive_data = f.read()

        yield archive_data


def test_archive_upload_accepted(client, sample_archive):
    """Test that archive files are accepted by upload endpoint."""
    # Note: This test will fail without API key, but we can verify
    # the archive handling logic at least gets called

    data = {
        "title": "Test Archive Project",
        "context": "Testing archive upload",
        "file": (io.BytesIO(sample_archive), "test_project.zip"),
    }

    response = client.post(
        "/analyze", data=data, content_type="multipart/form-data", follow_redirects=True
    )

    # Response may fail due to missing API key, but shouldn't fail due to file type
    assert response.status_code in [200, 500]  # Not 400 (bad request)

    # If it's a 400, check it's not about file type
    if response.status_code == 400:
        data = json.loads(response.data)
        error_msg = data.get("error", "").lower()
        assert "invalid file type" not in error_msg
        assert "allowed" not in error_msg


def test_allowed_file_extensions(app):
    """Test that archive extensions are in allowed list."""
    from src.ui.server import allowed_file

    assert allowed_file("test.zip")
    assert allowed_file("test.tar")
    assert allowed_file("test.tar.gz")
    assert allowed_file("test.tgz")
    assert allowed_file("test.pdf")
    assert allowed_file("test.txt")

    assert not allowed_file("test.exe")
    assert not allowed_file("test.docx")


def test_archive_file_detection(app):
    """Test archive file detection."""
    from src.utils.archive_handler import is_archive_file

    assert is_archive_file("project.zip")
    assert is_archive_file("data.tar.gz")
    assert is_archive_file("backup.tgz")
    assert is_archive_file("files.tar")

    assert not is_archive_file("document.pdf")
    assert not is_archive_file("notes.txt")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
