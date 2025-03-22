import html
from sec_api import ExtractorApi
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

class SECExtractorTool:
    """Tool for extracting ALL sections from SEC filings using the ExtractorApi."""
    
    def __init__(self, api_key: str = None):
        """Initialize the ExtractorApi with the provided or environment API key."""
        self.api_key = api_key or SEC_API_KEY
        if not self.api_key:
            raise ValueError("SEC API key is required. Set it in .env or pass to constructor.")
        self.extractor = ExtractorApi(self.api_key)

    def get_section(self, filing_url: str, section_id: str, output_format: str = "text") -> str:
        """Extract a section from an SEC filing and decode HTML entities."""
        content = self.extractor.get_section(filing_url, section_id, output_format)
        return html.unescape(content) if content else content

def test_all_sections():
    """Test extracting ALL sections from example filings in the documentation."""
    extractor = SECExtractorTool()
    
    print("\n=== Testing ALL 10-K Sections ===")
    # Tesla 10-K filing from documentation
    filing_url_10k = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
    
    # All 10-K sections as listed in documentation
    sections_10k = [
        "1",    # Business
        "1A",   # Risk Factors
        "1B",   # Unresolved Staff Comments
        "1C",   # Cybersecurity (introduced in 2023)
        "2",    # Properties
        "3",    # Legal Proceedings
        "4",    # Mine Safety Disclosures
        "5",    # Market for Registrant's Common Equity
        "6",    # Selected Financial Data (prior to February 2021)
        "7",    # Management's Discussion and Analysis
        "7A",   # Market Risk
        "8",    # Financial Statements
        "9",    # Changes in and Disagreements with Accountants
        "9A",   # Controls and Procedures
        "9B",   # Other Information
        "10",   # Directors and Officers
        "11",   # Executive Compensation
        "12",   # Security Ownership
        "13",   # Certain Relationships
        "14"    # Principal Accountant Fees
    ]
    
    print("\nTesla 10-K Sections:")
    for section_id in sections_10k:
        try:
            content = extractor.get_section(filing_url_10k, section_id, "text")
            if not content:
                print(f"Section {section_id}: Empty (0 characters)")
                continue
            print(f"Section {section_id}: {len(content)} characters")
            print(f"Full content:\n{content}\n")
            print("-" * 80 + "\n")  # Separator between sections
        except Exception as e:
            print(f"Section {section_id}: Not present in filing - {str(e)}\n")
    
    print("\n=== Testing ALL 10-Q Sections ===")
    # Tesla 10-Q filing from documentation
    filing_url_10q = "https://www.sec.gov/Archives/edgar/data/1318605/000095017022006034/tsla-20220331.htm"
    
    # All 10-Q sections as listed in documentation
    sections_10q = [
        # Part 1
        "part1item1",  # Financial Statements
        "part1item2",  # Management's Discussion
        "part1item3",  # Market Risk
        "part1item4",  # Controls and Procedures
        # Part 2
        "part2item1",  # Legal Proceedings
        "part2item1a", # Risk Factors
        "part2item2",  # Unregistered Sales
        "part2item3",  # Defaults
        "part2item4",  # Mine Safety
        "part2item5",  # Other Information
        "part2item6"   # Exhibits
    ]
    
    print("\nTesla 10-Q Sections:")
    for section_id in sections_10q:
        try:
            content = extractor.get_section(filing_url_10q, section_id, "text")
            if not content:
                print(f"Section {section_id}: Empty (0 characters)")
                continue
            print(f"Section {section_id}: {len(content)} characters")
            print(f"Full content:\n{content}\n")
            print("-" * 80 + "\n")  # Separator between sections
        except Exception as e:
            print(f"Section {section_id}: Not present in filing - {str(e)}\n")
    
    print("\n=== Testing 8-K Sections ===")
    # Example 8-K filing from documentation
    filing_url_8k = "https://www.sec.gov/Archives/edgar/data/66600/000149315222016468/form8-k.htm"
    
    # Test the exact example from documentation
    print("\n8-K Sections:")
    try:
        # Extract section 1.01 "Entry into Material Definitive Agreement" as cleaned text
        content = extractor.get_section(filing_url_8k, "1-1", "text")
        if not content:
            print("Section 1-1 (Entry into Material Agreement): Empty (0 characters)")
        else:
            print(f"Section 1-1 (Entry into Material Agreement): {len(content)} characters")
            print(f"Full content:\n{content}\n")
            print("-" * 80 + "\n")  # Separator between sections
    except Exception as e:
        print(f"Section 1-1 (Entry into Material Agreement): Not present in filing - {str(e)}\n")

if __name__ == "__main__":
    test_all_sections() 