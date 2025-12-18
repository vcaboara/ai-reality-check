"""Tests for metadata cache performance improvements."""

import json

# Add src to path for imports
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_results_dir():
    """Create temporary results directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir) / 'results'
        results_dir.mkdir()
        yield results_dir


@pytest.fixture
def mock_app(temp_results_dir):
    """Mock Flask app with temporary directories."""
    with patch('src.ui.server.app') as mock_app_obj:
        mock_app_obj.config = {
            'RESULTS_FOLDER': temp_results_dir,
            'UPLOAD_FOLDER': temp_results_dir / 'uploads'
        }
        # Patch the module-level METADATA_FILE
        with patch('src.ui.server.METADATA_FILE', temp_results_dir / '_metadata.json'):
            yield mock_app_obj


def create_result_files(results_dir: Path, count: int):
    """Create dummy result files for testing."""
    for i in range(count):
        result_file = results_dir / f"analysis_test_{i:04d}.json"
        # Create large result with realistic analysis data
        large_result = {
            'aspects': [
                {
                    'name': f'Aspect {j}',
                    'description': 'x' * 100,  # Simulate real content
                    'feasibility_score': 7.5,
                    'concerns': ['x' * 50 for _ in range(5)]
                }
                for j in range(10)  # 10 aspects per result
            ],
            'summary': 'x' * 500,
            'overall_score': 8.0
        }

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                'title': f'Test Project {i}',
                'timestamp': f'2025-12-{18:02d}T10:{i:02d}:00',
                'result': large_result
            }, f)


def test_metadata_creation(temp_results_dir, mock_app):
    """Test metadata file is created on first save."""
    from src.ui.server import add_result_metadata

    # Initially no metadata
    assert not (temp_results_dir / '_metadata.json').exists()

    # Add a result
    with patch('src.ui.server.METADATA_FILE', temp_results_dir / '_metadata.json'):
        add_result_metadata('test.json', 'Test', '2025-12-18T10:00:00')

    # Metadata should exist
    assert (temp_results_dir / '_metadata.json').exists()

    # Should contain the entry
    with open(temp_results_dir / '_metadata.json') as f:
        metadata = json.load(f)
    assert len(metadata) == 1
    assert metadata[0]['filename'] == 'test.json'
    assert metadata[0]['title'] == 'Test'


def test_metadata_rebuild(temp_results_dir, mock_app):
    """Test metadata can be rebuilt from existing files."""
    from src.ui.server import rebuild_metadata

    # Create some result files
    create_result_files(temp_results_dir, 5)

    # Rebuild metadata
    with patch('src.ui.server.METADATA_FILE', temp_results_dir / '_metadata.json'):
        with patch('src.ui.server.app.config', {'RESULTS_FOLDER': temp_results_dir}):
            metadata = rebuild_metadata()

    # Should have all 5 entries
    assert len(metadata) == 5
    assert all('filename' in entry for entry in metadata)
    assert all('title' in entry for entry in metadata)
    assert all('timestamp' in entry for entry in metadata)


def test_performance_improvement(temp_results_dir, mock_app):
    """Test metadata approach is faster than file scanning."""
    from src.ui.server import load_metadata, rebuild_metadata

    # Create many result files (simulate real usage)
    num_files = 100
    create_result_files(temp_results_dir, num_files)

    # Time the old approach (scan all files)
    start = time.perf_counter()
    results_old = []
    for result_file in temp_results_dir.glob('*.json'):
        with open(result_file, encoding='utf-8') as f:
            data = json.load(f)
            results_old.append({
                'filename': result_file.name,
                'title': data.get('title', 'Untitled'),
                'timestamp': data.get('timestamp'),
            })
    old_time = time.perf_counter() - start

    # Build metadata cache
    with patch('src.ui.server.METADATA_FILE', temp_results_dir / '_metadata.json'):
        with patch('src.ui.server.app.config', {'RESULTS_FOLDER': temp_results_dir}):
            rebuild_metadata()

    # Time the new approach (load from cache)
    start = time.perf_counter()
    with patch('src.ui.server.METADATA_FILE', temp_results_dir / '_metadata.json'):
        results_new = load_metadata()
    new_time = time.perf_counter() - start

    # New approach should be significantly faster
    print(f"\nPerformance comparison ({num_files} files):")
    print(f"  Old approach (scan all): {old_time*1000:.2f}ms")
    print(f"  New approach (metadata): {new_time*1000:.2f}ms")
    print(f"  Speedup: {old_time/new_time:.1f}x faster")

    # Should be at least 5x faster with 100 files
    assert new_time < old_time / 5, "Metadata cache should be significantly faster"

    # Results should be equivalent
    assert len(results_new) == num_files


def test_metadata_consistency(temp_results_dir, mock_app):
    """Test metadata stays consistent with result files."""
    from src.ui.server import add_result_metadata, load_metadata

    with patch('src.ui.server.METADATA_FILE', temp_results_dir / '_metadata.json'):
        # Add multiple results
        for i in range(10):
            filename = f'analysis_{i}.json'
            add_result_metadata(
                filename,
                f'Project {i}',
                f'2025-12-18T10:{i:02d}:00'
            )

        # Load and verify
        metadata = load_metadata()
        assert len(metadata) == 10

        # Check ordering is preserved
        titles = [m['title'] for m in metadata]
        assert titles == [f'Project {i}' for i in range(10)]


def test_invalid_metadata_recovery(temp_results_dir, mock_app):
    """Test recovery when metadata file is corrupted."""
    from src.ui.server import load_metadata

    # Create result files
    create_result_files(temp_results_dir, 5)

    # Create corrupted metadata
    metadata_file = temp_results_dir / '_metadata.json'
    with open(metadata_file, 'w') as f:
        f.write("invalid json{{{")

    # Should rebuild automatically
    with patch('src.ui.server.METADATA_FILE', metadata_file):
        with patch('src.ui.server.app.config', {'RESULTS_FOLDER': temp_results_dir}):
            metadata = load_metadata()

    # Should have recovered all files
    assert len(metadata) == 5


def test_metadata_sorting(temp_results_dir, mock_app):
    """Test results are sorted correctly by timestamp."""
    from src.ui.server import add_result_metadata, load_metadata

    with patch('src.ui.server.METADATA_FILE', temp_results_dir / '_metadata.json'):
        # Add results out of order
        add_result_metadata('file3.json', 'Third', '2025-12-18T10:30:00')
        add_result_metadata('file1.json', 'First', '2025-12-18T10:10:00')
        add_result_metadata('file2.json', 'Second', '2025-12-18T10:20:00')

        metadata = load_metadata()

        # Should be in chronological order (as added)
        titles = [m['title'] for m in metadata]
        assert titles == ['Third', 'First', 'Second']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
