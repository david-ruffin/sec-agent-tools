"""
Test file for the full_text_search_agent module.
"""

from full_text_search_agent import full_text_search_agent

def test_full_text_search_agent():
    # Test with valid parameters (searching for a specific phrase in 10-K/10-Q)
    print("\nTesting with valid parameters (searching for 'artificial intelligence')...")
    query = {
        "query": '"artificial intelligence"',
        "formTypes": ["10-K", "10-Q"],
        "startDate": "2023-01-01",
        "endDate": "2023-12-31"
    }
    result = full_text_search_agent(query)
    print(f"Status: {result['status']}")
    if result['status'] == 200:
        filings = result['data'].get('filings', [])
        print(f"Found {len(filings)} filings containing the phrase")
        if filings:
            print(f"First filing: {filings[0].get('companyName', 'N/A')} - {filings[0].get('formType', 'N/A')}")
    else:
        print(f"Error: {result['error']}")
    
    # Test with invalid parameters (missing query)
    print("\nTesting with invalid parameters (missing query)...")
    result = full_text_search_agent({})
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")
    
    # Test with None query
    print("\nTesting with None query...")
    result = full_text_search_agent(None)
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")

if __name__ == "__main__":
    test_full_text_search_agent() 