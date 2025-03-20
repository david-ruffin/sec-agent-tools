import os
from dotenv import load_dotenv
from sec_api import ExtractorApi
from typing import Literal, Dict, List
from enum import Enum

# Load environment variables
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

class FormType(Enum):
    """Form types supported by the ExtractorApi"""
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"

class SECExtractorTool:
    """Tool for extracting sections from SEC filings using the ExtractorApi."""
    
    # All available sections as per documentation
    SECTIONS_10K = {
        "1": "Business",
        "1A": "Risk Factors",
        "1B": "Unresolved Staff Comments",
        "1C": "Cybersecurity",  # Introduced in 2023
        "2": "Properties",
        "3": "Legal Proceedings",
        "4": "Mine Safety Disclosures",
        "5": "Market for Registrant's Common Equity",
        "6": "Selected Financial Data",  # Prior to February 2021
        "7": "Management's Discussion and Analysis",
        "7A": "Market Risk",
        "8": "Financial Statements",
        "9": "Changes in and Disagreements with Accountants",
        "9A": "Controls and Procedures",
        "9B": "Other Information",
        "10": "Directors and Officers",
        "11": "Executive Compensation",
        "12": "Security Ownership",
        "13": "Certain Relationships",
        "14": "Principal Accountant Fees"
    }
    
    SECTIONS_10Q = {
        # Part 1
        "part1item1": "Financial Statements",
        "part1item2": "Management's Discussion",
        "part1item3": "Market Risk",
        "part1item4": "Controls and Procedures",
        # Part 2
        "part2item1": "Legal Proceedings",
        "part2item1a": "Risk Factors",
        "part2item2": "Unregistered Sales",
        "part2item3": "Defaults",
        "part2item4": "Mine Safety",
        "part2item5": "Other Information",
        "part2item6": "Exhibits"
    }
    
    SECTIONS_8K = {
        # Item 1 - Registrant's Business and Operations
        "1-1": "Entry into Material Agreement",
        "1-2": "Termination of Material Agreement",
        "1-3": "Bankruptcy",
        "1-4": "Mine Safety",
        # Item 2 - Financial Information
        "2-1": "Completion of Acquisition",
        "2-2": "Results of Operations",
        "2-3": "Creation of Obligation",
        "2-4": "Triggering Events",
        "2-5": "Exit Costs",
        "2-6": "Material Impairments",
        # Item 3 - Securities and Trading Markets
        "3-1": "Notice of Delisting",
        "3-2": "Unregistered Sales",
        "3-3": "Material Modifications",
        # Item 4 - Matters Related to Accountants
        "4-1": "Auditor Changes",
        "4-2": "Non-Reliance on Statements",
        # Item 5 - Corporate Governance
        "5-1": "Changes in Control",
        "5-2": "Departure of Directors",
        "5-3": "Amendments to Articles",
        "5-4": "Change in Fiscal Year",
        "5-5": "Shell Status",
        "5-6": "Code of Ethics",
        # Item 6 - Asset-Backed Securities
        "6-1": "ABS Informational",
        "6-2": "Change in Trustee",
        "6-3": "Change in Credit Enhancement",
        "6-4": "Failure to Make Distribution",
        "6-5": "Securities Act Updating",
        # Item 7 - Regulation FD
        "7-1": "Regulation FD Disclosure",
        # Item 8 - Other Events
        "8-1": "Other Events",
        # Item 9 - Financial Statements and Exhibits
        "9-1": "Financial Statements and Exhibits"
    }
    
    def __init__(self, api_key: str = None):
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
            The extracted section content
        """
        return self.extractor.get_section(filing_url, section_id, output_format)

    def get_all_sections(self, 
                        filing_url: str,
                        form_type: FormType,
                        output_format: Literal["text", "html"] = "text") -> Dict[str, str]:
        """
        Extract all available sections from a filing.

        Args:
            filing_url: Full SEC.gov URL to the filing
            form_type: Type of form (10-K, 10-Q, or 8-K)
            output_format: Either "text" (cleaned) or "html" (original)

        Returns:
            Dictionary mapping section IDs to their content
        """
        sections = {}
        section_map = {
            FormType.FORM_10K: self.SECTIONS_10K,
            FormType.FORM_10Q: self.SECTIONS_10Q,
            FormType.FORM_8K: self.SECTIONS_8K
        }[form_type]
        
        for section_id in section_map.keys():
            try:
                content = self.get_section(filing_url, section_id, output_format)
                sections[section_id] = content
            except Exception as e:
                print(f"Warning: Could not extract section {section_id}: {str(e)}")
                sections[section_id] = None
                
        return sections

def test_extractor():
    """Test the ExtractorApi exactly as shown in documentation."""
    extractor = SECExtractorTool()
    
    print("\n=== Testing 10-K Sections ===")
    # Tesla 10-K filing
    filing_url_10k = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"

    # get the standardized and cleaned text of section 1A "Risk Factors"
    section_text = extractor.get_section(filing_url_10k, "1A", "text")
    print("\nRisk Factors (Section 1A) as text:")
    print(f"Length: {len(section_text)} characters")
    print(f"Preview: {section_text[:200]}...")

    # get the original HTML of section 7 "Management's Discussion and Analysis"
    section_html = extractor.get_section(filing_url_10k, "7", "html")
    print("\nManagement's Discussion (Section 7) as HTML:")
    print(f"Length: {len(section_html)} characters")
    print(f"Preview: {section_html[:200]}...")

    print("\n=== Testing 10-Q Sections ===")
    # Tesla 10-Q filing
    filing_url_10q = "https://www.sec.gov/Archives/edgar/data/1318605/000095017022006034/tsla-20220331.htm"

    # extract section 1A "Risk Factors" in part 2 as cleaned text
    section_10q = extractor.get_section(filing_url_10q, "part2item1a", "text")
    print("\nRisk Factors (Part 2 Item 1A):")
    print(f"Length: {len(section_10q)} characters")
    print(f"Preview: {section_10q[:200]}...")

    print("\n=== Testing 8-K Sections ===")
    # Example 8-K filing
    filing_url_8k = "https://www.sec.gov/Archives/edgar/data/66600/000149315222016468/form8-k.htm"

    # extract section 1.01 "Entry into Material Definitive Agreement" as cleaned text
    section_8k = extractor.get_section(filing_url_8k, "1-1", "text")
    print("\nMaterial Agreement (Section 1.01):")
    print(f"Length: {len(section_8k)} characters")
    print(f"Preview: {section_8k[:200]}...")

if __name__ == "__main__":
    test_extractor() 