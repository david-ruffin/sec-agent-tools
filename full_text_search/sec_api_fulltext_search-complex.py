import os
from dotenv import load_dotenv
from sec_api import FullTextSearchApi
import json

# Load environment variables
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

if not SEC_API_KEY:
    print("ERROR: SEC_API_KEY environment variable is not set")
    exit(1)

print(f"Using API Key (first 5 chars): {SEC_API_KEY[:5]}...")

# Initialize API client
fullTextSearchApi = FullTextSearchApi(api_key=SEC_API_KEY)

# Example directly from the documentation
def test_exact_example():
    print("\n=== Testing example directly from documentation ===")
    query = {
        "query": '"LPCN 1154"',
        "formTypes": ['8-K', '10-Q'],
        "startDate": '2021-01-01',
        "endDate": '2021-06-14',
    }
    
    print(f"Running query: {query}")
    
    try:
        filings = fullTextSearchApi.get_filings(query)
        
        # Print total number of results
        total = filings.get('total', {}).get('value', 0)
        print(f"Total results: {total}")
        
        # Print first result if available
        if 'filings' in filings and filings['filings']:
            print("\nFirst result:")
            filing = filings['filings'][0]
            
            # Print all available keys
            print(f"Available keys: {list(filing.keys())}")
            
            # Print some common fields
            print(f"Company Name: {filing.get('companyName')}")
            print(f"Ticker: {filing.get('ticker')}")
            print(f"Form Type: {filing.get('formType')}")
            print(f"Filed At: {filing.get('filedAt')}")
            print(f"Excerpt: {filing.get('excerpt')}")
            print(f"Filing URL: {filing.get('linkToFilingDetails') or filing.get('linkToHtml')}")
            
            # Save full result to file for inspection
            with open('sec_api_sample.json', 'w') as f:
                json.dump(filings, f, indent=2)
            print("\nFull results saved to 'sec_api_sample.json'")
        else:
            print("No results found")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

# Another example with more commonly available terms
def test_common_terms():
    print("\n=== Testing with common search terms ===")
    query = {
        "query": '"revenue growth"',
        "formTypes": ['10-K'],
        "startDate": '2022-01-01',
        "endDate": '2023-12-31',
    }
    
    print(f"Running query: {query}")
    
    try:
        filings = fullTextSearchApi.get_filings(query)
        
        # Print total number of results
        total = filings.get('total', {}).get('value', 0)
        print(f"Total results: {total}")
        
        # Print first result if available
        if 'filings' in filings and filings['filings']:
            print("\nFirst result:")
            filing = filings['filings'][0]
            
            # Print all available keys
            print(f"Available keys: {list(filing.keys())}")
            
            # Print some common fields
            print(f"Company Name: {filing.get('companyName')}")
            print(f"Ticker: {filing.get('ticker')}")
            print(f"Form Type: {filing.get('formType')}")
            print(f"Filed At: {filing.get('filedAt')}")
            
            # Save full result to file for inspection
            with open('sec_api_revenue.json', 'w') as f:
                json.dump(filings, f, indent=2)
            print("\nFull results saved to 'sec_api_revenue.json'")
        else:
            print("No results found")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_exact_example()
    test_common_terms()
    
    print("\nDiagnostic tests completed. Check the output above and JSON files for details.")