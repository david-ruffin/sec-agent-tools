"""
Test file for the filing_search_agent module.

Tests all functionality defined in filing_search_agent_plan.md including:
- Query language features
- Real-time streaming (verification of "not implemented" status)
- File downloading
- Error handling
"""

from datetime import datetime, timedelta
from filing_search_agent import filing_search_agent

def print_result(result, test_name):
    """Helper to print test results in a consistent format."""
    print(f"\n{test_name}:")
    print(f"Status: {result['status']}")
    if result['status'] == 200:
        if 'filings' in result['data']:
            print(f"Found {len(result['data']['filings'])} filings")
            if result['data']['filings']:
                print("First filing:", result['data']['filings'][0]['formType'])
        else:
            print("Data:", result['data'])
    else:
        print(f"Error: {result['error']}")

def test_query_language_features():
    """Test all query language features defined in the plan."""
    
    # Test field query
    field_query = {
        "query": "ticker:AAPL AND formType:\"10-K\"",
        "from": "0",
        "size": "1",
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    result = filing_search_agent(field_query)
    print_result(result, "Field Query Test (ticker and formType)")
    
    # Test boolean operators
    bool_query = {
        "query": "formType:\"10-K\" AND NOT ticker:AAPL",
        "from": "0",
        "size": "1"
    }
    result = filing_search_agent(bool_query)
    print_result(result, "Boolean Operators Test (AND, NOT)")
    
    # Test date range
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    date_query = {
        "query": f"filedAt:[{yesterday} TO *]",
        "from": "0",
        "size": "1"
    }
    result = filing_search_agent(date_query)
    print_result(result, "Date Range Test")
    
    # Test wildcard
    wildcard_query = {
        "query": "companyName:Micro*",
        "from": "0",
        "size": "1"
    }
    result = filing_search_agent(wildcard_query)
    print_result(result, "Wildcard Test")

def test_pagination():
    """Test pagination functionality."""
    
    # Test with different page sizes
    pagination_query = {
        "query": "formType:\"10-K\"",
        "from": "0",
        "size": "5"
    }
    result = filing_search_agent(pagination_query)
    print_result(result, "Pagination Test (size=5)")
    
    # Test with offset
    offset_query = {
        "query": "formType:\"10-K\"",
        "from": "5",
        "size": "5"
    }
    result = filing_search_agent(offset_query)
    print_result(result, "Pagination Test (offset=5)")

def test_error_cases():
    """Test all error scenarios."""
    
    # Test invalid query syntax
    invalid_query = {
        "query": "ticker:AAPL AND AND formType:\"10-K\"",  # Double AND
        "from": "0",
        "size": "1"
    }
    result = filing_search_agent(invalid_query)
    print_result(result, "Invalid Query Syntax Test")
    
    # Test missing required parameter
    result = filing_search_agent(None)
    print_result(result, "Missing Query Test")
    
    # Test invalid field name
    invalid_field = {
        "query": "invalidField:value",
        "from": "0",
        "size": "1"
    }
    result = filing_search_agent(invalid_field)
    print_result(result, "Invalid Field Test")
    
    # Test invalid pagination
    invalid_pagination = {
        "query": "formType:\"10-K\"",
        "from": "-1",  # Invalid offset
        "size": "1"
    }
    result = filing_search_agent(invalid_pagination)
    print_result(result, "Invalid Pagination Test")

def test_real_time_streaming():
    """Test real-time streaming functionality (verification of not implemented status)."""
    
    # Test stream_mode parameter
    result = filing_search_agent(
        query={"query": "formType:\"8-K\""},  # Basic query for streaming
        stream_mode=True
    )
    print_result(result, "Real-Time Streaming Not Implemented Test")
    
    # Verify correct status code (501 Not Implemented)
    if result['status'] == 501:
        print("✓ Correctly returned 501 Not Implemented status")
    else:
        print("✗ Expected status 501, got", result['status'])
    
    # Verify informative error message
    if result['error'] and "not implemented" in result['error'].lower():
        print("✓ Includes helpful error message about implementation")
    else:
        print("✗ Missing or uninformative error message")

def test_file_downloading():
    """Test file downloading functionality."""
    
    # Find a recent 10-K filing to download
    query = {
        "query": "formType:\"10-K\"",
        "from": "0",
        "size": "1",
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    
    # Test original format download
    result = filing_search_agent(
        query=query,
        download_format="original"
    )
    print_result(result, "Original Format Download Test")
    if result['status'] == 200 and 'downloadedContent' in result['data']:
        print("Successfully downloaded original content")
    
    # Test unsupported format (HTML was removed as it's not available)
    result = filing_search_agent(
        query=query,
        download_format="html"
    )
    print_result(result, "Unsupported Format Test (HTML)")
    if result['status'] == 400 and 'unsupported' in result['error'].lower():
        print("✓ Correctly returns error for unsupported formats")
    
    # Test invalid format
    result = filing_search_agent(
        query=query,
        download_format="invalid"
    )
    print_result(result, "Invalid Format Download Test")
    if result['status'] == 400:
        print("✓ Correctly returns error for invalid formats")

def test_filing_search_agent():
    """Run all tests."""
    print("\nRunning Filing Search Agent Tests...")
    print("=" * 50)
    
    test_query_language_features()
    test_pagination()
    test_error_cases()
    test_real_time_streaming()
    test_file_downloading()
    
    print("\nTests completed.")

if __name__ == "__main__":
    test_filing_search_agent() 