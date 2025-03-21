"""
Test file for SEC-API tools based on official documentation examples
"""

import os
import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")
assert SEC_API_KEY, "SEC_API_KEY must be set in .env file"

# Import tools
from query_api.queryapi_toolv5 import search_sec_filings as query_search
from extractor_api.extractor_apiv9 import SECExtractorTool
from edgar_entities_api.edgar_entities_apiv2 import SECEdgarEntitiesAPI
from xbrl_api.xbrl_apiv1 import SECXbrlTool

# Test Query API
def test_query_api():
    """Test Query API using example from SEC-API docs"""
    query = "ticker:TSLA AND formType:\"10-K\" AND filedAt:[2020-01-01 TO 2020-12-31]"
    
    result = query_search(query)
    assert result is not None
    assert isinstance(result, dict)
    assert 'filings' in result

# Test Extractor API
def test_extractor_api():
    """Test Extractor API using example from SEC-API docs"""
    extractor = SECExtractorTool()
    filing_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
    
    result = extractor.get_section(filing_url, "1A")  # Risk Factors section
    assert result is not None
    assert isinstance(result, dict)
    assert 'content' in result

# Test EDGAR Entities API
def test_entities_api():
    """Test EDGAR Entities API using example from SEC-API docs"""
    entities_api = SECEdgarEntitiesAPI()
    result = entities_api.get_entity_data("ticker:TSLA")
    
    assert result is not None
    assert isinstance(result, dict)

# Test XBRL API
def test_xbrl_api():
    """Test XBRL API using example from SEC-API docs"""
    xbrl_tool = SECXbrlTool()
    htm_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
    
    result = xbrl_tool.xbrl_to_json(htm_url=htm_url)
    assert result is not None
    assert isinstance(result, dict)

if __name__ == "__main__":
    pytest.main([__file__]) 