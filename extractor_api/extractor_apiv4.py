from sec_api import ExtractorApi
import os
from dotenv import load_dotenv

class SECExtractorTool:
    """
    Tool for extracting sections from SEC filings using the ExtractorApi.
    Implements exact functionality from sec-api-python documentation.
    """
    
    def __init__(self, api_key: str = None):
        """Initialize with API key from environment or parameter."""
        load_dotenv()
        self.api_key = api_key or os.getenv("SEC_API_KEY")
        if not self.api_key:
            raise ValueError("SEC API key is required. Set it in .env or pass to constructor.")
        self.extractor = ExtractorApi(self.api_key)

    def get_section(self, filing_url: str, section_id: str, output_format: str = "text") -> str:
        """
        Extract a section from an SEC filing.
        
        Args:
            filing_url (str): URL of the SEC filing
            section_id (str): Section identifier (e.g., "1A" for 10-K Risk Factors)
            output_format (str): "text" for cleaned text, "html" for original HTML
            
        Returns:
            str: The extracted section content
        """
        return self.extractor.get_section(filing_url, section_id, output_format)

def test_documentation_examples():
    """Test all examples from the sec-api-python documentation."""
    print("\nTesting SEC Extractor API Documentation Examples")
    print("=" * 50)
    
    extractor = SECExtractorTool()
    
    # 10-K Examples (Tesla)
    print("\n1. Testing 10-K Examples:")
    print("-" * 30)
    filing_url_10k = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
    
    # Example 1: Risk Factors (text)
    print("\nExample 1a: Getting Risk Factors (Section 1A) as text")
    section_text = extractor.get_section(filing_url_10k, "1A", "text")
    print(f"Retrieved {len(section_text) if section_text else 0} characters")
    print("First 500 characters:" if section_text else "No content retrieved")
    if section_text:
        print(section_text[:500] + "...")
    
    # Example 2: MD&A (html)
    print("\nExample 1b: Getting MD&A (Section 7) as HTML")
    section_html = extractor.get_section(filing_url_10k, "7", "html")
    print(f"Retrieved {len(section_html) if section_html else 0} characters")
    print("First 500 characters:" if section_html else "No content retrieved")
    if section_html:
        print(section_html[:500] + "...")
    
    # 10-Q Example (Tesla)
    print("\n2. Testing 10-Q Example:")
    print("-" * 30)
    filing_url_10q = "https://www.sec.gov/Archives/edgar/data/1318605/000095017022006034/tsla-20220331.htm"
    
    # Example: Risk Factors
    print("\nGetting Risk Factors (Part 2, Item 1A) as text")
    extracted_section_10q = extractor.get_section(filing_url_10q, "part2item1a", "text")
    print(f"Retrieved {len(extracted_section_10q) if extracted_section_10q else 0} characters")
    print("First 500 characters:" if extracted_section_10q else "No content retrieved")
    if extracted_section_10q:
        print(extracted_section_10q[:500] + "...")
    
    # 8-K Example
    print("\n3. Testing 8-K Example:")
    print("-" * 30)
    filing_url_8k = "https://www.sec.gov/Archives/edgar/data/66600/000149315222016468/form8-k.htm"
    
    # Example: Material Agreement
    print("\nGetting Entry into Material Agreement (Section 1-1) as text")
    extracted_section_8k = extractor.get_section(filing_url_8k, "1-1", "text")
    print(f"Retrieved {len(extracted_section_8k) if extracted_section_8k else 0} characters")
    print("First 500 characters:" if extracted_section_8k else "No content retrieved")
    if extracted_section_8k:
        print(extracted_section_8k[:500] + "...")

if __name__ == "__main__":
    test_documentation_examples() 