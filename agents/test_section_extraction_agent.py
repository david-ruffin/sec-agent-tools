"""
Test file for the section_extraction_agent module.
"""

from section_extraction_agent import section_extraction_agent

def test_section_extraction_agent():
    # Test with valid parameters (Apple's 10-K MD&A section)
    print("\nTesting with valid parameters (10-K MD&A section)...")
    # This is a real 10-K filing URL from Apple Inc.
    filing_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm"
    result = section_extraction_agent(filing_url, "7")  # Section 7 is MD&A
    print(f"Status: {result['status']}")
    if result['status'] == 200:
        content = result['data']  # Data is the section content as string
        print(f"Extracted content length: {len(content)} characters")
        print(f"First 100 characters: {content[:100]}...")
    else:
        print(f"Error: {result['error']}")
    
    # Test with invalid parameters (missing URL)
    print("\nTesting with invalid parameters (missing URL)...")
    result = section_extraction_agent("", "7")
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")
    
    # Test with invalid parameters (missing section)
    print("\nTesting with invalid parameters (missing section)...")
    result = section_extraction_agent(filing_url, "")
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")

if __name__ == "__main__":
    test_section_extraction_agent() 