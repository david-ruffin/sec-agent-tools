"""
Tests for SEC Filing Analysis System using real SEC API.io endpoints
"""

import pytest
from sec_agent import process_query

def test_basic_company_query():
    """Test a basic company query using real SEC API"""
    query = "Summarize the Management Discussion and Analysis section of Microsoft's 2023 10-K"
    result = process_query(query)
    
    # Basic validation
    assert result is not None
    assert "context" in result
    assert "companies" in result["context"]
    
def test_financial_data_query():
    """Test extracting financial data using real SEC API"""
    query = "What was Apple's revenue in their latest 10-Q?"
    result = process_query(query)
    
    assert result is not None
    assert "context" in result
    # The basic test should just confirm structure, not actual data
    # since we're not implementing XBRL extraction yet

def test_multi_company_comparison():
    """Test comparing multiple companies using real SEC API"""
    query = "Compare the risk factors between Microsoft and Apple's latest 10-K filings"
    result = process_query(query)
    
    assert result is not None
    assert "context" in result
    # Multi-company comparison will be implemented in a future update

if __name__ == "__main__":
    pytest.main(["-v", "test_sec_agent.py"]) 