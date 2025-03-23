"""
Test file for the Mapping API agent.

This file contains tests for all functionalities of the Mapping API:
1. Company resolution by identifier (name, ticker, cik, cusip)
2. Listing companies by exchange, sector, and industry
3. Error handling for all methods
"""

from mapping_agent import company_resolution_agent, list_companies_agent

def test_company_resolution_agent():
    """Test the company resolution functionality."""
    print("\n===== Testing Company Resolution =====")
    
    # Test with company name
    print("\nTesting with company name...")
    result = company_resolution_agent(
        identifier_type="name",
        identifier_value="Apple"
    )
    print(f"Status: {result['status']}")
    if result['status'] == 200:
        print(f"Found {len(result['data'])} companies")
        if result['data'] and len(result['data']) > 0:
            print(f"First company: {result['data'][0]['name']} ({result['data'][0]['ticker']})")
    else:
        print(f"Error: {result['error']}")
    
    # Test with ticker
    print("\nTesting with ticker...")
    result = company_resolution_agent(
        identifier_type="ticker",
        identifier_value="AAPL"
    )
    print(f"Status: {result['status']}")
    if result['status'] == 200:
        print(f"Found {len(result['data'])} companies")
        if result['data'] and len(result['data']) > 0:
            print(f"Company: {result['data'][0]['name']} (CIK: {result['data'][0]['cik']})")
    else:
        print(f"Error: {result['error']}")
    
    # Test with CIK
    print("\nTesting with CIK...")
    result = company_resolution_agent(
        identifier_type="cik",
        identifier_value="320193"  # Apple Inc.
    )
    print(f"Status: {result['status']}")
    if result['status'] == 200:
        print(f"Found {len(result['data'])} companies")
        if result['data'] and len(result['data']) > 0:
            print(f"Company: {result['data'][0]['name']} (Ticker: {result['data'][0]['ticker']})")
    else:
        print(f"Error: {result['error']}")
    
    # Test with CUSIP (if supported)
    print("\nTesting with CUSIP...")
    result = company_resolution_agent(
        identifier_type="cusip",
        identifier_value="037833100"  # Apple Inc.
    )
    print(f"Status: {result['status']}")
    if result['status'] == 200:
        print(f"Found {len(result['data'])} companies")
        if result['data'] and len(result['data']) > 0:
            print(f"Company: {result['data'][0]['name']} (Ticker: {result['data'][0]['ticker']})")
    else:
        print(f"Error: {result['error']}")
    
    # Test with invalid identifier type
    print("\nTesting with invalid identifier type...")
    result = company_resolution_agent(
        identifier_type="invalid",
        identifier_value="value"
    )
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")
    
    # Test with missing identifier value
    print("\nTesting with missing identifier value...")
    result = company_resolution_agent(
        identifier_type="ticker",
        identifier_value=None
    )
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")

def test_list_companies_agent():
    """Test the company listing functionality."""
    print("\n===== Testing Company Listing =====")
    
    # Test listing by exchange
    print("\nTesting listing by exchange...")
    result = list_companies_agent(
        list_type="exchange",
        list_value="NASDAQ"
    )
    print(f"Status: {result['status']}")
    if result['status'] == 200:
        print(f"Found {len(result['data'])} companies")
        if result['data'] and len(result['data']) > 0:
            print(f"First few companies: {[company['name'] for company in result['data'][:3]]}")
    else:
        print(f"Error: {result['error']}")
    
    # Test listing by sector
    print("\nTesting listing by sector...")
    result = list_companies_agent(
        list_type="sector",
        list_value="Technology"
    )
    print(f"Status: {result['status']}")
    if result['status'] == 200:
        print(f"Found {len(result['data'])} companies")
        if result['data'] and len(result['data']) > 0:
            print(f"First few companies: {[company['name'] for company in result['data'][:3]]}")
    else:
        print(f"Error: {result['error']}")
    
    # Test listing by industry
    print("\nTesting listing by industry...")
    result = list_companies_agent(
        list_type="industry",
        list_value="Software"
    )
    print(f"Status: {result['status']}")
    if result['status'] == 200:
        print(f"Found {len(result['data'])} companies")
        if result['data'] and len(result['data']) > 0:
            print(f"First few companies: {[company['name'] for company in result['data'][:3]]}")
    else:
        print(f"Error: {result['error']}")
    
    # Test with invalid list type
    print("\nTesting with invalid list type...")
    result = list_companies_agent(
        list_type="invalid",
        list_value="value"
    )
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")
    
    # Test with missing list value
    print("\nTesting with missing list value...")
    result = list_companies_agent(
        list_type="exchange",
        list_value=None
    )
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")

if __name__ == "__main__":
    test_company_resolution_agent()
    test_list_companies_agent()