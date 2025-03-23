import pytest
import os
from unittest.mock import Mock, patch
from edgar_entities_agent import edgar_entities_agent

@pytest.fixture(autouse=True)
def mock_env_api_key():
    with patch.dict(os.environ, {"SEC_API_KEY": "mock_api_key"}):
        yield

@patch('edgar_entities_agent.EdgarEntitiesApi')
def test_get_entity_data_by_cik(mock_entities_api):
    # Configure mock to return sample data
    mock_instance = Mock()
    mock_entities_api.return_value = mock_instance
    
    mock_response = {
        "total": 1,
        "data": [
            {
                "cik": "1318605",
                "irsNumber": "123456789",
                "stateOfIncorporation": "DE",
                "fiscalYearEnd": "1231",
                "sicCode": "3711",
                "currentAuditor": "PricewaterhouseCoopers LLP",
                "latestICFRAuditDate": "2023-12-31T00:00:00.000Z",
                "filerCategory": "Large Accelerated Filer",
                "cikUpdatedAt": "2023-12-31T00:00:00.000Z"
            }
        ]
    }
    mock_instance.get_data.return_value = mock_response
    
    search_request = {
        "query": "cik:1318605",
        "from": "0",
        "size": "50",
        "sort": [{"cikUpdatedAt": {"order": "desc"}}]
    }
    
    response = edgar_entities_agent(search_request)
    assert response["status"] == 200
    assert "data" in response
    assert len(response["data"]) > 0
    assert response["data"][0]["cik"] == "1318605"
    
    # Verify API was called with correct parameters
    mock_instance.get_data.assert_called_once_with(search_request)

@patch('edgar_entities_agent.EdgarEntitiesApi')
def test_get_entity_data_by_state(mock_entities_api):
    # Configure mock to return sample data
    mock_instance = Mock()
    mock_entities_api.return_value = mock_instance
    
    mock_response = {
        "total": 2,
        "data": [
            {
                "cik": "1318605",
                "stateOfIncorporation": "DE",
                "cikUpdatedAt": "2023-12-31T00:00:00.000Z"
            },
            {
                "cik": "789012",
                "stateOfIncorporation": "DE",
                "cikUpdatedAt": "2023-11-30T00:00:00.000Z"
            }
        ]
    }
    mock_instance.get_data.return_value = mock_response
    
    search_request = {
        "query": "stateOfIncorporation:DE",
        "from": "0",
        "size": "50"
    }
    
    response = edgar_entities_agent(search_request)
    assert response["status"] == 200
    assert "data" in response
    assert len(response["data"]) > 0
    assert all(item["stateOfIncorporation"] == "DE" for item in response["data"])
    
    # Verify API was called with correct parameters
    mock_instance.get_data.assert_called_once_with(search_request)

@patch('edgar_entities_agent.EdgarEntitiesApi')
def test_get_entity_data_by_sic_code(mock_entities_api):
    # Configure mock to return sample data
    mock_instance = Mock()
    mock_entities_api.return_value = mock_instance
    
    mock_response = {
        "total": 2,
        "data": [
            {
                "cik": "1318605",
                "sicCode": "7370",
                "cikUpdatedAt": "2023-12-31T00:00:00.000Z"
            },
            {
                "cik": "789012",
                "sicCode": "7370",
                "cikUpdatedAt": "2023-11-30T00:00:00.000Z"
            }
        ]
    }
    mock_instance.get_data.return_value = mock_response
    
    search_request = {
        "query": "sicCode:7370",
        "from": "0",
        "size": "50",
        "sort": [{"fiscalYearEnd": {"order": "asc"}}]
    }
    
    response = edgar_entities_agent(search_request)
    assert response["status"] == 200
    assert "data" in response
    assert len(response["data"]) > 0
    assert all(item["sicCode"] == "7370" for item in response["data"])
    
    # Verify API was called with correct parameters
    mock_instance.get_data.assert_called_once_with(search_request)

@patch('edgar_entities_agent.EdgarEntitiesApi')
def test_pagination(mock_entities_api):
    # Configure mock for first page
    mock_instance = Mock()
    mock_entities_api.return_value = mock_instance
    
    mock_first_page = {
        "total": 20,
        "data": [{"cik": f"10000{i}", "stateOfIncorporation": "DE"} for i in range(10)]
    }
    
    mock_second_page = {
        "total": 20,
        "data": [{"cik": f"20000{i}", "stateOfIncorporation": "DE"} for i in range(10)]
    }
    
    mock_instance.get_data.side_effect = [mock_first_page, mock_second_page]
    
    # Test first page
    first_page = edgar_entities_agent({
        "query": "stateOfIncorporation:DE",
        "from": "0",
        "size": "10"
    })
    
    # Test second page
    second_page = edgar_entities_agent({
        "query": "stateOfIncorporation:DE",
        "from": "10",
        "size": "10"
    })
    
    assert first_page["status"] == 200
    assert second_page["status"] == 200
    assert len(first_page["data"]) == 10
    assert len(second_page["data"]) == 10
    assert first_page["data"] != second_page["data"]
    
    # Verify API was called twice with different parameters
    assert mock_instance.get_data.call_count == 2

def test_invalid_query():
    # Use a query format that fails the regex pattern check
    search_request = {
        "query": "invalid*field",
        "from": "0",
        "size": "50"
    }
    
    response = edgar_entities_agent(search_request)
    assert response["status"] == 400
    assert "error" in response

@patch('edgar_entities_agent.EdgarEntitiesApi')
def test_rate_limit_handling(mock_entities_api):
    # Configure mock to raise a rate limit exception
    mock_instance = Mock()
    mock_entities_api.return_value = mock_instance
    mock_instance.get_data.side_effect = Exception("Rate limit exceeded")
    
    response = edgar_entities_agent({
        "query": "cik:1318605",
        "from": "0",
        "size": "50"
    })
    
    assert response["status"] == 429
    assert "error" in response
    assert "rate limit" in response["error"].lower()

@patch('edgar_entities_agent.EdgarEntitiesApi')
def test_authentication_error(mock_entities_api):
    # Configure mock to raise an authentication error
    mock_instance = Mock()
    mock_entities_api.return_value = mock_instance
    mock_instance.get_data.side_effect = Exception("Invalid API key")
    
    response = edgar_entities_agent({
        "query": "cik:1318605",
        "from": "0",
        "size": "50"
    })
    
    assert response["status"] == 401
    assert "error" in response
    assert "api key" in response["error"].lower()

@patch('edgar_entities_agent.EdgarEntitiesApi')
def test_empty_result(mock_entities_api):
    # Configure mock to return empty results
    mock_instance = Mock()
    mock_entities_api.return_value = mock_instance
    mock_instance.get_data.return_value = {"total": 0, "data": []}
    
    search_request = {
        "query": "cik:999999999",
        "from": "0",
        "size": "50"
    }
    
    response = edgar_entities_agent(search_request)
    assert response["status"] == 200
    assert "data" in response
    assert len(response["data"]) == 0

def test_malformed_request():
    search_request = {
        "invalid_key": "value"
    }
    
    response = edgar_entities_agent(search_request)
    assert response["status"] == 400
    assert "error" in response 