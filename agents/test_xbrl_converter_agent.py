"""
Test file for the xbrl_converter_agent module.
"""

from xbrl_converter_agent import xbrl_converter_agent

def print_xbrl_result(result: dict, method: str):
    """Helper function to print XBRL conversion results."""
    print(f"\nTesting {method}...")
    print(f"Status: {result['status']}")
    if result['status'] == 200:
        data = result['data']
        # Print available financial statements
        statements = [k for k in data.keys() if k.startswith('StatementsOf') or k.startswith('Balance')]
        print(f"Available statements: {statements}")
        # Print a sample from first statement if available
        if statements:
            first_statement = data[statements[0]]
            print(f"\nSample from {statements[0]}:")
            # Get first fact from first statement
            first_item = next(iter(first_statement.items()))
            print(f"{first_item[0]}: {first_item[1]}")
    else:
        print(f"Error: {result['error']}")

def test_xbrl_converter_agent():
    # Test with HTM URL (Apple's 10-K)
    htm_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926.htm"
    result = xbrl_converter_agent(htm_url=htm_url)
    print_xbrl_result(result, "HTM URL method")
    
    # Test with XBRL URL (Tesla's 10-K)
    xbrl_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231_htm.xml"
    result = xbrl_converter_agent(xbrl_url=xbrl_url)
    print_xbrl_result(result, "XBRL URL method")
    
    # Test with accession number
    result = xbrl_converter_agent(accession_no="0001564590-21-004599")
    print_xbrl_result(result, "Accession number method")
    
    # Test error cases
    print("\nTesting with no parameters...")
    result = xbrl_converter_agent()
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")
    
    print("\nTesting with invalid URL...")
    result = xbrl_converter_agent(htm_url="https://invalid.url")
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")

if __name__ == "__main__":
    test_xbrl_converter_agent() 