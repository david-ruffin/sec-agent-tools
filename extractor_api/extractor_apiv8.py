from sec_api import ExtractorApi
import os
from dotenv import load_dotenv

def test_documentation_examples():
    """Test the ExtractorApi exactly as shown in documentation."""
    # Initialize
    load_dotenv()
    api_key = os.getenv("SEC_API_KEY")
    if not api_key:
        raise ValueError("SEC API key is required. Set it in .env file.")
    extractor = ExtractorApi(api_key)

    print("\n=== Testing 10-K Sections ===")
    # Tesla 10-K filing
    filing_url_10k = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"

    # get the standardized and cleaned text of section 1A "Risk Factors"
    section_text = extractor.get_section(filing_url_10k, "1A", "text")
    print("\nRisk Factors (Section 1A) as text:")
    print(section_text)

    # get the original HTML of section 7 "Management's Discussion"
    section_html = extractor.get_section(filing_url_10k, "7", "html")
    print("\nManagement's Discussion (Section 7) as HTML:")
    print(section_html)

    print("\n=== Testing 10-Q Sections ===")
    # Tesla 10-Q filing
    filing_url_10q = "https://www.sec.gov/Archives/edgar/data/1318605/000095017022006034/tsla-20220331.htm"

    # extract section 1A "Risk Factors" in part 2 as cleaned text
    extracted_section_10q = extractor.get_section(filing_url_10q, "part2item1a", "text")
    print("\nRisk Factors (Part 2 Item 1A):")
    print(extracted_section_10q)

    print("\n=== Testing 8-K Sections ===")
    # Example 8-K filing
    filing_url_8k = "https://www.sec.gov/Archives/edgar/data/66600/000149315222016468/form8-k.htm"

    # extract section 1.01 "Entry into Material Definitive Agreement" as cleaned text
    extracted_section_8k = extractor.get_section(filing_url_8k, "1-1", "text")
    print("\nMaterial Agreement (Section 1.01):")
    print(extracted_section_8k)

if __name__ == "__main__":
    test_documentation_examples() 