from sec_api import ExtractorApi
import os
from dotenv import load_dotenv
import html
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List

class SECExtractorTool:
    """Enhanced SEC Extractor Tool for AI Agents"""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("SEC_API_KEY")
        if not self.api_key:
            raise ValueError("SEC API key is required. Set it in .env file.")
        self.extractor = ExtractorApi(self.api_key)
        
        # Complete section mappings from documentation
        self.SECTION_MAPPINGS = {
            "10-K": {
                "1": "Business",
                "1A": "Risk Factors",
                "1B": "Unresolved Staff Comments",
                "1C": "Cybersecurity",
                "2": "Properties",
                "3": "Legal Proceedings",
                "4": "Mine Safety",
                "5": "Market Information",
                "6": "Selected Financial",
                "7": "Management Discussion",
                "7A": "Market Risk",
                "8": "Financial Statements",
                "9": "Accountant Changes",
                "9A": "Controls",
                "9B": "Other Information",
                "10": "Directors",
                "11": "Executive Compensation",
                "12": "Security Ownership",
                "13": "Relationships",
                "14": "Accountant Fees"
            },
            "10-Q": {
                "part1item1": "Financial Statements",
                "part1item2": "Management Discussion",
                "part1item3": "Market Risk",
                "part1item4": "Controls",
                "part2item1": "Legal Proceedings",
                "part2item1a": "Risk Factors",
                "part2item2": "Unregistered Sales",
                "part2item3": "Defaults",
                "part2item4": "Mine Safety",
                "part2item5": "Other Information",
                "part2item6": "Exhibits"
            },
            "8-K": {
                "1-1": "Material Agreement",
                "1-3": "Bankruptcy",
                "4-1": "Auditor Changes",
                "4-2": "Financial Restatements",
                "5-2": "Director Changes"
            }
        }

    def clean_html(self, content: str) -> str:
        """Clean HTML content by removing tags and decoding entities."""
        if not content:
            return ""
        content = html.unescape(content)
        soup = BeautifulSoup(content, 'html.parser')
        for br in soup.find_all(['br', 'p']):
            br.replace_with('\n' + br.text)
        return soup.get_text(separator='\n').strip()

    def detect_form_type(self, section_id: str) -> str:
        """Detect form type from section ID."""
        if section_id in self.SECTION_MAPPINGS["10-K"]:
            return "10-K"
        elif section_id in self.SECTION_MAPPINGS["10-Q"]:
            return "10-Q"
        elif section_id in self.SECTION_MAPPINGS["8-K"]:
            return "8-K"
        raise ValueError(f"Invalid section ID: {section_id}")

    def get_section_description(self, form_type: str, section_id: str) -> str:
        """Get human-readable section description."""
        return self.SECTION_MAPPINGS[form_type].get(section_id, "Unknown Section")

    def get_section(self, filing_url: str, section_id: str, output_format: str = "text") -> Dict[str, Any]:
        """Get a section from a filing with metadata."""
        try:
            form_type = self.detect_form_type(section_id)
            content = self.extractor.get_section(filing_url, section_id, output_format)
            
            if not content:
                return {
                    "is_error": False,
                    "error": None,
                    "is_empty": True,
                    "is_present": False,
                    "status": "Section not found or empty",
                    "content": None,
                    "section_id": section_id,
                    "section_description": self.get_section_description(form_type, section_id),
                    "form_type": form_type,
                    "output_format": output_format
                }
            
            cleaned_content = self.clean_html(content) if output_format == "text" else content
            
            return {
                "is_error": False,
                "error": None,
                "is_empty": False,
                "is_present": True,
                "status": "Success",
                "content": cleaned_content,
                "section_id": section_id,
                "section_description": self.get_section_description(form_type, section_id),
                "form_type": form_type,
                "output_format": output_format
            }
            
        except Exception as e:
            return {
                "is_error": True,
                "error": str(e),
                "is_empty": True,
                "is_present": False,
                "status": "Error",
                "content": None,
                "section_id": section_id,
                "section_description": "Unknown",
                "form_type": "Unknown",
                "output_format": output_format
            }

    def extract_all_sections(self, filing_url: str, form_type: str) -> List[Dict[str, Any]]:
        """Extract all available sections from a filing."""
        results = []
        for section_id in self.SECTION_MAPPINGS[form_type].keys():
            result = self.get_section(filing_url, section_id)
            results.append(result)
        return results

def test_documentation_examples():
    """Test the ExtractorApi with proper text cleaning."""
    extractor = SECExtractorTool()

    print("\n=== Testing 10-K Sections ===")
    filing_url_10k = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"

    # Test Risk Factors section
    result = extractor.get_section(filing_url_10k, "1A")
    print("\nRisk Factors (Section 1A):")
    print(f"Status: {result['status']}")
    print(f"Section: {result['section_description']}")
    if result['content']:
        print(f"Content Length: {len(result['content'])} characters")

    # Test Management Discussion section
    result = extractor.get_section(filing_url_10k, "7", "html")
    print("\nManagement Discussion (Section 7):")
    print(f"Status: {result['status']}")
    print(f"Section: {result['section_description']}")
    if result['content']:
        print(f"Content Length: {len(result['content'])} characters")

    print("\n=== Testing 10-Q Sections ===")
    filing_url_10q = "https://www.sec.gov/Archives/edgar/data/1318605/000095017022006034/tsla-20220331.htm"
    
    result = extractor.get_section(filing_url_10q, "part2item1a")
    print("\nRisk Factors (Part 2 Item 1A):")
    print(f"Status: {result['status']}")
    print(f"Section: {result['section_description']}")
    if result['content']:
        print(f"Content Length: {len(result['content'])} characters")

    print("\n=== Testing 8-K Sections ===")
    filing_url_8k = "https://www.sec.gov/Archives/edgar/data/66600/000149315222016468/form8-k.htm"
    
    result = extractor.get_section(filing_url_8k, "1-1")
    print("\nMaterial Agreement (Section 1.01):")
    print(f"Status: {result['status']}")
    print(f"Section: {result['section_description']}")
    if result['content']:
        print(f"Content Length: {len(result['content'])} characters")

if __name__ == "__main__":
    test_documentation_examples() 