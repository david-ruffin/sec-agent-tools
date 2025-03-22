from sec_api import XbrlApi
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional

class SECXbrlTool:
    """SEC XBRL-to-JSON Converter Tool following sec-api-python documentation"""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("SEC_API_KEY")
        if not self.api_key:
            raise ValueError("SEC API key is required. Set it in .env file.")
        self.xbrl_api = XbrlApi(self.api_key)

    def xbrl_to_json(self, 
                     htm_url: Optional[str] = None,
                     xbrl_url: Optional[str] = None,
                     accession_no: Optional[str] = None) -> Dict[str, Any]:
        """Convert XBRL to JSON using any of the three supported methods."""
        try:
            # Validate inputs
            if sum(x is not None for x in [htm_url, xbrl_url, accession_no]) != 1:
                raise ValueError("Exactly one of htm_url, xbrl_url, or accession_no must be provided")
            
            # Call appropriate API method
            if htm_url:
                return self.xbrl_api.xbrl_to_json(htm_url=htm_url)
            elif xbrl_url:
                return self.xbrl_api.xbrl_to_json(xbrl_url=xbrl_url)
            else:
                return self.xbrl_api.xbrl_to_json(accession_no=accession_no)
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

def test_documentation_examples():
    """Test the XBRL API with documentation examples."""
    xbrl_tool = SECXbrlTool()
    
    print("\n=== Testing Tesla 10-K XBRL Conversion ===")
    
    # Test with HTM URL
    htm_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
    result = xbrl_tool.xbrl_to_json(htm_url=htm_url)
    
    if result:
        print("\nSuccessfully converted Tesla 10-K XBRL")
        print("\nAvailable Statements:")
        for statement in result.keys():
            print(f"- {statement}")
            if statement == "StatementsOfIncome":
                print("\nExample Income Statement Data:")
                print(result[statement])
    else:
        print("Failed to convert Tesla 10-K XBRL")
    
    print("\n=== Testing Apple 10-K XBRL Conversion ===")
    
    # Test with XBRL URL
    xbrl_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926_htm.xml"
    result = xbrl_tool.xbrl_to_json(xbrl_url=xbrl_url)
    
    if result:
        print("\nSuccessfully converted Apple 10-K XBRL")
        print("\nAvailable Statements:")
        for statement in result.keys():
            print(f"- {statement}")
            if statement == "StatementsOfIncome":
                print("\nExample Income Statement Data:")
                print(result[statement])
    else:
        print("Failed to convert Apple 10-K XBRL")

if __name__ == "__main__":
    test_documentation_examples() 