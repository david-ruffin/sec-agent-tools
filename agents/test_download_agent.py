import pytest
import os
import shutil
from unittest.mock import Mock, patch
from download_agent import download_agent

@pytest.fixture
def cleanup():
    yield
    # Clean up test downloads after tests
    base_dir = "downloads"
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)

@pytest.fixture(autouse=True)
def mock_env_api_key():
    with patch.dict(os.environ, {"SEC_API_KEY": "mock_api_key"}):
        yield

@patch('download_agent.RenderApi')
def test_download_complete_filing(mock_render_api, cleanup):
    # Configure mock to return sample content
    mock_instance = Mock()
    mock_render_api.return_value = mock_instance
    mock_instance.get_filing.return_value = b"<html>Sample complete filing content</html>"
    
    response = download_agent(
        accession_number="0001640147-23-000089",
        file_type="complete"
    )
    
    assert response["status"] == 200
    assert response["file_path"].endswith("filing.html")
    assert os.path.exists(response["file_path"])
    assert os.path.getsize(response["file_path"]) > 0
    
    # Verify the API was called correctly
    mock_instance.get_filing.assert_called_once_with("0001640147-23-000089")

@patch('download_agent.RenderApi')
def test_download_primary_document(mock_render_api, cleanup):
    # Configure mock to return sample content
    mock_instance = Mock()
    mock_render_api.return_value = mock_instance
    mock_instance.get_filing.return_value = b"<html>Sample primary document content</html>"
    
    response = download_agent(
        accession_number="0001640147-23-000089",
        file_type="primary"
    )
    
    assert response["status"] == 200
    assert response["file_path"].endswith("primary.html")
    assert os.path.exists(response["file_path"])
    assert os.path.getsize(response["file_path"]) > 0
    
    # Verify the API was called correctly
    mock_instance.get_filing.assert_called_once_with("0001640147-23-000089")

@patch('download_agent.RenderApi')
def test_download_exhibit(mock_render_api, cleanup):
    # Configure mock to return sample content
    mock_instance = Mock()
    mock_render_api.return_value = mock_instance
    mock_instance.get_filing.return_value = b"<html>Sample exhibit content</html>"
    
    response = download_agent(
        accession_number="0001640147-23-000089",
        file_type="exhibit",
        exhibit_number="EX-10.1"
    )
    
    assert response["status"] == 200
    assert response["file_path"].endswith("EX-10.1.html")
    assert os.path.exists(response["file_path"])
    assert os.path.getsize(response["file_path"]) > 0
    
    # Verify the API was called correctly
    mock_instance.get_filing.assert_called_once_with("0001640147-23-000089", "EX-10.1")

def test_invalid_accession_number():
    response = download_agent(
        accession_number="invalid-format",
        file_type="complete"
    )
    
    assert response["status"] == 400
    assert "error" in response
    assert "invalid accession number format" in response["error"].lower()

def test_invalid_file_type():
    response = download_agent(
        accession_number="0001640147-23-000089",
        file_type="invalid"
    )
    
    assert response["status"] == 400
    assert "error" in response
    assert "invalid file type" in response["error"].lower()

def test_missing_exhibit_number():
    response = download_agent(
        accession_number="0001640147-23-000089",
        file_type="exhibit"
    )
    
    assert response["status"] == 400
    assert "error" in response
    assert "exhibit number required" in response["error"].lower()

@patch('download_agent.RenderApi')
def test_file_not_found(mock_render_api):
    # Configure mock to raise an exception
    mock_instance = Mock()
    mock_render_api.return_value = mock_instance
    mock_instance.get_filing.side_effect = Exception("Not found")
    
    response = download_agent(
        accession_number="0001640147-99-999999",
        file_type="complete"
    )
    
    assert response["status"] == 404
    assert "error" in response
    assert "not found" in response["error"].lower()

@patch('download_agent.RenderApi')
def test_rate_limit_handling(mock_render_api):
    # Configure mock to raise a rate limit exception
    mock_instance = Mock()
    mock_render_api.return_value = mock_instance
    mock_instance.get_filing.side_effect = Exception("Rate limit exceeded")
    
    response = download_agent(
        accession_number="0001640147-23-000089",
        file_type="complete"
    )
    
    assert response["status"] == 429
    assert "error" in response
    assert "rate limit" in response["error"].lower()

@patch('download_agent.RenderApi')
def test_authentication_error(mock_render_api):
    # Configure mock to raise an authentication error
    mock_instance = Mock()
    mock_render_api.return_value = mock_instance
    mock_instance.get_filing.side_effect = Exception("Invalid API key")
    
    response = download_agent(
        accession_number="0001640147-23-000089",
        file_type="complete"
    )
    
    assert response["status"] == 401
    assert "error" in response
    assert "api key" in response["error"].lower()

@patch('download_agent.RenderApi')
def test_download_interruption(mock_render_api, cleanup):
    # Configure mock to fail once then succeed
    mock_instance = Mock()
    mock_render_api.return_value = mock_instance
    mock_instance.get_filing.side_effect = [
        Exception("Connection lost"),  # First attempt fails
        b"<html>Sample content after retry</html>"  # Second attempt succeeds
    ]
    
    response = download_agent(
        accession_number="0001640147-23-000089",
        file_type="complete"
    )
    
    assert response["status"] == 200
    assert response["file_path"].endswith("filing.html")
    assert os.path.exists(response["file_path"])

@patch('download_agent.RenderApi')
def test_large_file_streaming(mock_render_api, cleanup):
    # Mock a large file response
    large_content = b"<html>" + b"x" * (10 * 1024 * 1024) + b"</html>"  # 10MB
    
    mock_instance = Mock()
    mock_render_api.return_value = mock_instance
    mock_instance.get_filing.return_value = large_content
    
    response = download_agent(
        accession_number="0001640147-23-000089",
        file_type="complete"
    )
    
    assert response["status"] == 200
    assert os.path.exists(response["file_path"])
    assert os.path.getsize(response["file_path"]) == len(large_content) 