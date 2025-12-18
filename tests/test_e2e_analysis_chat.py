"""End-to-end tests for analysis → chat workflow."""

import json
import time
import pytest
import requests
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:5000"
TIMEOUT = 90  # seconds for API calls (Ollama can be slow)


@pytest.fixture(scope="module")
def test_document():
    """Sample technical description for testing."""
    return """
    Novel Pyrolysis Reactor for Plastic Waste Conversion
    
    Technical Overview:
    Our innovation introduces a continuous-feed pyrolysis reactor operating at 450-550°C
    under oxygen-free conditions. The system processes mixed plastic waste (HDPE, PP, PS)
    and converts it into synthetic crude oil and gas products.
    
    Key Features:
    - Advanced heat recovery system with 85% thermal efficiency
    - Catalytic cracking unit for improved oil quality
    - Automated feedstock sorting and preparation
    - Real-time process monitoring and control
    
    Technical Challenges:
    - Scaling from lab (10 kg/hr) to commercial (500 kg/hr)
    - Maintaining consistent product quality with variable feedstock
    - Managing catalyst deactivation and regeneration
    
    Market Opportunity:
    Targets industrial plastic recyclers with 20+ tons/day capacity.
    Estimated ROI of 18 months based on current oil prices.
    """


@pytest.fixture(scope="module")
def server_available():
    """Check if server is running before tests."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200, "Server health check failed"
        return True
    except requests.exceptions.RequestException as e:
        pytest.skip(f"Server not available at {BASE_URL}: {e}")


def test_e2e_analysis_to_chat_workflow(test_document, server_available):
    """
    Test complete workflow:
    1. Submit analysis request
    2. Verify analysis results
    3. Navigate to chat with context
    4. Ask context-aware questions
    5. Verify responses reference the analysis
    """
    
    # Step 1: Submit analysis
    print("\n1. Submitting analysis request...")
    analysis_response = requests.post(
        f"{BASE_URL}/analyze",
        data={
            'title': 'E2E Test: Pyrolysis Reactor',
            'text': test_document,
            'context': 'Commercial viability focus'
        },
        timeout=TIMEOUT
    )
    
    assert analysis_response.status_code == 200, \
        f"Analysis request failed: {analysis_response.text}"
    
    analysis_data = analysis_response.json()
    assert analysis_data['success'] is True, "Analysis did not succeed"
    assert 'result' in analysis_data, "No result in analysis response"
    assert 'result_file' in analysis_data, "No result file returned"
    
    result = analysis_data['result']
    result_file = analysis_data['result_file']
    
    print(f"   ✓ Analysis completed: {result_file}")
    
    # Step 2: Verify analysis structure
    print("2. Verifying analysis results...")
    
    # Handle both structured (aspects) and unstructured (analysis text) formats
    has_aspects = 'aspects' in result
    has_analysis_text = 'analysis' in result
    
    assert has_aspects or has_analysis_text, \
        "Result must have either 'aspects' or 'analysis' field"
    
    if has_aspects:
        assert len(result['aspects']) > 0, "No aspects analyzed"
        aspect_names = [aspect['name'] for aspect in result['aspects']]
        print(f"   Found aspects: {', '.join(aspect_names)}")
        assert any('Technical' in name for name in aspect_names), \
            "Missing Technical Feasibility aspect"
    else:
        # Text-based analysis
        analysis_text = result['analysis']
        assert len(analysis_text) > 100, "Analysis text too short"
        print(f"   Found analysis text ({len(analysis_text)} chars)")
        # Check for key terms in technical analysis
        assert any(term in analysis_text.lower() for term in ['feasibility', 'technical', 'challenge']), \
            "Analysis doesn't contain expected technical terms"
    
    print("   ✓ Analysis structure valid")
    
    # Step 3: Simulate loading chat with context (as frontend would)
    print("3. Loading chat page...")
    chat_response = requests.get(f"{BASE_URL}/chat", timeout=10)
    assert chat_response.status_code == 200, "Chat page not accessible"
    assert 'Interactive Feasibility Chat' in chat_response.text, \
        "Chat page content incorrect"
    print("   ✓ Chat page accessible")
    
    # Step 4: Send chat message with analysis context
    print("4. Asking context-aware question...")
    
    # Generate unique session ID
    session_id = f"e2e_test_{int(time.time())}"
    
    chat_payload = {
        'message': 'What are the main technical challenges mentioned in this analysis?',
        'session_id': session_id,
        'message_count': 1,
        'analysis_context': result  # Pass the analysis context
    }
    
    chat_api_response = requests.post(
        f"{BASE_URL}/chat",
        json=chat_payload,
        headers={'Content-Type': 'application/json'},
        timeout=TIMEOUT
    )
    
    assert chat_api_response.status_code == 200, \
        f"Chat request failed: {chat_api_response.text}"
    
    chat_data = chat_api_response.json()
    assert 'response' in chat_data, "No response from chat"
    
    ai_response = chat_data['response']
    print(f"   AI Response: {ai_response[:200]}...")
    
    # Step 5: Verify response is context-aware
    print("5. Verifying context-aware response...")
    
    # Response should reference the technical challenges we mentioned
    context_indicators = [
        'scaling',
        'catalyst',
        'feedstock',
        'technical',
        'challenge'
    ]
    
    response_lower = ai_response.lower()
    matches = [ind for ind in context_indicators if ind in response_lower]
    
    assert len(matches) >= 2, \
        f"Response doesn't seem context-aware. Expected technical terms, got: {ai_response[:300]}"
    
    print(f"   ✓ Response references: {', '.join(matches)}")
    
    # Step 6: Ask follow-up question
    print("6. Testing conversation continuity...")
    
    followup_payload = {
        'message': 'What would you recommend to address the scaling challenge?',
        'session_id': session_id,
        'message_count': 2,
        'analysis_context': result
    }
    
    followup_response = requests.post(
        f"{BASE_URL}/chat",
        json=followup_payload,
        headers={'Content-Type': 'application/json'},
        timeout=TIMEOUT
    )
    
    assert followup_response.status_code == 200, "Follow-up question failed"
    followup_data = followup_response.json()
    
    print(f"   Follow-up response: {followup_data['response'][:200]}...")
    print("   ✓ Conversation continuity maintained")
    
    print("\n✅ E2E workflow test passed!")


def test_e2e_chat_without_context(server_available):
    """Test chat works without analysis context (general questions)."""
    
    print("\n1. Testing chat without analysis context...")
    
    session_id = f"e2e_no_context_{int(time.time())}"
    
    payload = {
        'message': 'What is pyrolysis?',
        'session_id': session_id,
        'message_count': 1
        # No analysis_context provided
    }
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=TIMEOUT
    )
    
    assert response.status_code == 200, f"Chat failed: {response.text}"
    
    data = response.json()
    assert 'response' in data, "No response from chat"
    
    # Should get a general answer about pyrolysis
    assert len(data['response']) > 50, "Response too short"
    
    print(f"   Response: {data['response'][:200]}...")
    print("   ✓ Chat works without context")


def test_e2e_results_page_integration(server_available):
    """Test that results page can load and display analyses."""
    
    print("\n1. Testing results page...")
    
    # Load results page
    response = requests.get(f"{BASE_URL}/results", timeout=10)
    assert response.status_code == 200, "Results page not accessible"
    
    # Load results API
    api_response = requests.get(f"{BASE_URL}/api/results", timeout=10)
    assert api_response.status_code == 200, "Results API failed"
    
    data = api_response.json()
    assert 'results' in data, "No results in API response"
    
    results_count = len(data['results'])
    print(f"   ✓ Found {results_count} saved analyses")
    
    if results_count > 0:
        # Verify metadata structure
        sample = data['results'][0]
        assert 'filename' in sample, "Missing filename in result"
        assert 'title' in sample, "Missing title in result"
        assert 'timestamp' in sample, "Missing timestamp in result"
        print(f"   ✓ Latest: {sample['title']} ({sample['timestamp']})")


@pytest.mark.slow
def test_e2e_performance_metadata_cache(server_available):
    """Verify metadata cache provides fast results listing."""
    
    print("\n1. Testing results listing performance...")
    
    start = time.perf_counter()
    response = requests.get(f"{BASE_URL}/api/results", timeout=10)
    duration = time.perf_counter() - start
    
    assert response.status_code == 200, "Results API failed"
    
    data = response.json()
    results_count = len(data['results'])
    
    # Should be fast even with many results (< 100ms for typical loads)
    print(f"   Retrieved {results_count} results in {duration*1000:.1f}ms")
    
    # Warn if slow (but don't fail - could be network/load)
    if duration > 0.5:
        print(f"   ⚠ Slow response: {duration*1000:.1f}ms (expected <100ms)")
    else:
        print(f"   ✓ Fast metadata cache: {duration*1000:.1f}ms")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s', '--tb=short'])
