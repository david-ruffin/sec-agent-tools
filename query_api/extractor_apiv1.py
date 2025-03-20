import os
from dotenv import load_dotenv
from sec_api import ExtractorApi
from typing import Literal, Optional

# Load environment variables
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

class SECExtractorTool:
    """Tool for extracting sections from SEC filings using the ExtractorApi."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the ExtractorApi with the provided or environment API key."""
        self.api_key = api_key or SEC_API_KEY
        if not self.api_key:
            raise ValueError("SEC API key is required. Set it in .env or pass to constructor.")
        self.extractor = ExtractorApi(self.api_key)

    def get_section(self, 
                   filing_url: str, 
                   section_id: str, 
                   output_format: Literal["text", "html"] = "text") -> str:
        """
        Extract a section from an SEC filing.

        Args:
            filing_url: Full SEC.gov URL to the filing
            section_id: Section identifier (e.g., "1A", "7", "part2item1a", "1-1")
            output_format: Either "text" (cleaned) or "html" (original)

        Returns:
            str: The extracted section content
        """
        try:
            return self.extractor.get_section(filing_url, section_id, output_format)
        except Exception as e:
            return f"Error extracting section: {str(e)}"

def test_extractor():
    """Run test cases using documented examples."""
    extractor = SECExtractorTool()
    
    print("\n=== Testing 10-K Extraction ===")
    filing_url_10k = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
    
    # Test Risk Factors section (text format)
    print("\nExtracting Risk Factors (Section 1A) as text:")
    risk_factors = extractor.get_section(filing_url_10k, "1A", "text")
    print(f"Retrieved {len(risk_factors)} characters")
    print(f"Preview: {risk_factors[:200]}...")
    
    # Test Management Discussion section (html format)
    print("\nExtracting Management Discussion (Section 7) as HTML:")
    mgmt_discussion = extractor.get_section(filing_url_10k, "7", "html")
    print(f"Retrieved {len(mgmt_discussion)} characters")
    print(f"Preview: {mgmt_discussion[:200]}...")

    print("\n=== Testing 10-Q Extraction ===")
    filing_url_10q = "https://www.sec.gov/Archives/edgar/data/1318605/000095017022006034/tsla-20220331.htm"
    
    # Test Risk Factors section in Part 2
    print("\nExtracting Risk Factors (Part 2 Item 1A) as text:")
    risk_factors_10q = extractor.get_section(filing_url_10q, "part2item1a", "text")
    print(f"Retrieved {len(risk_factors_10q)} characters")
    print(f"Preview: {risk_factors_10q[:200]}...")

    print("\n=== Testing 8-K Extraction ===")
    filing_url_8k = "https://www.sec.gov/Archives/edgar/data/66600/000149315222016468/form8-k.htm"
    
    # Test Material Agreement section
    print("\nExtracting Material Agreement (Section 1.01) as text:")
    material_agreement = extractor.get_section(filing_url_8k, "1-1", "text")
    print(f"Retrieved {len(material_agreement)} characters")
    print(f"Preview: {material_agreement[:200]}...")

if __name__ == "__main__":
    test_extractor() 