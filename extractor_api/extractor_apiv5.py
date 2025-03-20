from sec_api import ExtractorApi
import os
from dotenv import load_dotenv
from typing import Dict, Optional, Union

class SECExtractorTool:
    """Tool for extracting sections from SEC filings using the ExtractorApi."""
    
    # Section mappings from documentation
    SECTIONS = {
        '10-K': {
            '1': 'Business',
            '1A': 'Risk Factors',
            '1B': 'Unresolved Staff Comments',
            '1C': 'Cybersecurity',
            '2': 'Properties',
            '3': 'Legal Proceedings',
            '4': 'Mine Safety Disclosures',
            '5': 'Market Information',
            '6': 'Selected Financial Data',
            '7': 'Management Discussion',
            '7A': 'Market Risk',
            '8': 'Financial Statements',
            '9': 'Accountant Changes',
            '9A': 'Controls and Procedures',
            '9B': 'Other Information',
            '10': 'Directors and Officers',
            '11': 'Executive Compensation',
            '12': 'Security Ownership',
            '13': 'Related Transactions',
            '14': 'Principal Accountant Fees'
        },
        '10-Q': {
            'part1item1': 'Financial Statements',
            'part1item2': 'Management Discussion',
            'part1item3': 'Market Risk',
            'part1item4': 'Controls and Procedures',
            'part2item1': 'Legal Proceedings',
            'part2item1a': 'Risk Factors',
            'part2item2': 'Unregistered Sales',
            'part2item3': 'Defaults',
            'part2item4': 'Mine Safety',
            'part2item5': 'Other Information',
            'part2item6': 'Exhibits'
        },
        '8-K': {
            '1-1': 'Entry into Material Agreement',
            '4-1': 'Auditor Changes',
            '4-2': 'Financial Restatements',
            '5-2': 'Director Changes'
        }
    }
    
    def __init__(self, api_key: str = None):
        """Initialize with API key from environment or parameter."""
        load_dotenv()
        self.api_key = api_key or os.getenv("SEC_API_KEY")
        if not self.api_key:
            raise ValueError("SEC API key is required. Set it in .env or pass to constructor.")
        self.extractor = ExtractorApi(self.api_key)

    def get_section(self, filing_url: str, section_id: str, output_format: str = "text") -> Dict:
        """
        Extract a section from an SEC filing with enhanced response format.
        
        Args:
            filing_url (str): URL of the SEC filing
            section_id (str): Section identifier (e.g., "1A" for 10-K Risk Factors)
            output_format (str): "text" for cleaned text, "html" for original HTML
            
        Returns:
            dict: {
                'content': str,           # The section content
                'section_id': str,        # The section ID used
                'section_name': str,      # Human-readable section name
                'form_type': str,         # Detected form type
                'success': bool,          # Whether extraction succeeded
                'error': Optional[str]    # Error message if any
            }
        """
        try:
            # Detect form type from section_id format
            form_type = self._detect_form_type(section_id)
            
            # Get section name
            section_name = self._get_section_name(form_type, section_id)
            
            # Extract content
            content = self.extractor.get_section(filing_url, section_id, output_format)
            
            return {
                'content': content,
                'section_id': section_id,
                'section_name': section_name,
                'form_type': form_type,
                'success': True,
                'error': None
            }
        except Exception as e:
            return {
                'content': None,
                'section_id': section_id,
                'section_name': self._get_section_name(self._detect_form_type(section_id), section_id),
                'form_type': self._detect_form_type(section_id),
                'success': False,
                'error': str(e)
            }

    def _detect_form_type(self, section_id: str) -> str:
        """Detect form type from section ID format."""
        if section_id.startswith('part'):
            return '10-Q'
        elif '-' in section_id:
            return '8-K'
        return '10-K'

    def _get_section_name(self, form_type: str, section_id: str) -> str:
        """Get human-readable section name."""
        return self.SECTIONS.get(form_type, {}).get(section_id, 'Unknown Section')

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
    result = extractor.get_section(filing_url_10k, "1A", "text")
    print(f"Success: {result['success']}")
    print(f"Form Type: {result['form_type']}")
    print(f"Section Name: {result['section_name']}")
    if result['content']:
        print(f"Content Length: {len(result['content'])} characters")
        print("First 500 characters:")
        print(result['content'][:500] + "...")
    
    # Example 2: MD&A (html)
    print("\nExample 1b: Getting MD&A (Section 7) as HTML")
    result = extractor.get_section(filing_url_10k, "7", "html")
    print(f"Success: {result['success']}")
    print(f"Form Type: {result['form_type']}")
    print(f"Section Name: {result['section_name']}")
    if result['content']:
        print(f"Content Length: {len(result['content'])} characters")
        print("First 500 characters:")
        print(result['content'][:500] + "...")
    
    # 10-Q Example (Tesla)
    print("\n2. Testing 10-Q Example:")
    print("-" * 30)
    filing_url_10q = "https://www.sec.gov/Archives/edgar/data/1318605/000095017022006034/tsla-20220331.htm"
    
    # Example: Risk Factors
    print("\nGetting Risk Factors (Part 2, Item 1A) as text")
    result = extractor.get_section(filing_url_10q, "part2item1a", "text")
    print(f"Success: {result['success']}")
    print(f"Form Type: {result['form_type']}")
    print(f"Section Name: {result['section_name']}")
    if result['content']:
        print(f"Content Length: {len(result['content'])} characters")
        print("First 500 characters:")
        print(result['content'][:500] + "...")
    
    # 8-K Example
    print("\n3. Testing 8-K Example:")
    print("-" * 30)
    filing_url_8k = "https://www.sec.gov/Archives/edgar/data/66600/000149315222016468/form8-k.htm"
    
    # Example: Material Agreement
    print("\nGetting Entry into Material Agreement (Section 1-1) as text")
    result = extractor.get_section(filing_url_8k, "1-1", "text")
    print(f"Success: {result['success']}")
    print(f"Form Type: {result['form_type']}")
    print(f"Section Name: {result['section_name']}")
    if result['content']:
        print(f"Content Length: {len(result['content'])} characters")
        print("First 500 characters:")
        print(result['content'][:500] + "...")

if __name__ == "__main__":
    test_documentation_examples() 