"""Unit tests for Flask routes with mocked dependencies."""

import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path


@pytest.fixture
def client():
    """Flask test client with mocked dependencies."""
    with patch('src.ui.server.analyzer') as mock_analyzer, \
         patch('src.ui.server.selector', None), \
         patch('src.ui.server.user_preferences', {}):
        
        from src.ui.server import app
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            yield client, mock_analyzer


def test_index_route(client):
    """Test main page loads."""
    test_client, _ = client
    response = test_client.get('/')
    
    assert response.status_code == 200
    assert b'AI Reality Check' in response.data


def test_analyze_with_text(client):
    """Test text analysis endpoint."""
    test_client, mock_analyzer = client
    
    mock_analyzer.analyze.return_value = {
        'analysis': 'Test analysis result',
        'metadata': {'model': 'test'}
    }
    
    response = test_client.post('/analyze', data={
        'title': 'Test Project',
        'text': 'Test technical description',
        'context': 'Test context'
    })
    
    assert response.status_code == 200
    data = response.json
    assert data['success'] is True
    assert 'result' in data
    mock_analyzer.analyze.assert_called_once()


def test_analyze_missing_input(client):
    """Test analysis fails without input."""
    test_client, _ = client
    
    response = test_client.post('/analyze', data={'title': 'Test'})
    
    assert response.status_code == 400
    assert b'No text or file provided' in response.data


def test_chat_endpoint(client):
    """Test chat endpoint with mocked provider."""
    test_client, _ = client
    
    with patch('asmf.providers.AIProviderFactory.create_provider') as mock_create:
        mock_provider = MagicMock()
        mock_provider.analyze_text.return_value = "Mocked AI response"
        mock_create.return_value = mock_provider
        
        response = test_client.post('/chat', 
            json={
                'message': 'Test question',
                'session_id': 'test_session',
                'message_count': 1
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json
        assert 'response' in data
        assert data['response'] == "Mocked AI response"


def test_results_api(client):
    """Test results API with mocked metadata."""
    test_client, _ = client
    
    mock_metadata = [
        {'filename': 'test1.json', 'title': 'Test 1', 'timestamp': '2025-12-18T10:00:00'},
        {'filename': 'test2.json', 'title': 'Test 2', 'timestamp': '2025-12-18T11:00:00'}
    ]
    
    with patch('src.ui.server.load_metadata', return_value=mock_metadata):
        response = test_client.get('/api/results')
        
        assert response.status_code == 200
        data = response.json
        assert 'results' in data
        assert len(data['results']) == 2


def test_health_check(client):
    """Test health endpoint returns valid JSON."""
    test_client, mock_analyzer = client
    
    # Mock analyzer attributes used in health response
    mock_analyzer.domain_config.domain_name = "Test Domain"
    mock_analyzer.expert.__class__.__name__ = "MockExpert"
    
    response = test_client.get('/health')
    
    assert response.status_code == 200
    data = response.json
    assert data['status'] == 'healthy'
    assert 'domain' in data
    assert 'provider' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
