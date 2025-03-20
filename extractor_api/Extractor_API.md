# SEC ExtractorAPI Documentation

## Overview

The SEC ExtractorAPI Tool provides programmatic access to extract specific sections from SEC filings (10-K, 10-Q, 8-K) using the SEC-API.io service. This implementation is specifically designed for use with Langchain AI agents, providing structured responses and comprehensive error handling.

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required packages:
   ```bash
   pip install sec-api python-dotenv beautifulsoup4
   ```
3. Set up your SEC API key in a `.env` file:
   ```
   SEC_API_KEY=your_api_key_here
   ```

## Usage Examples

### Basic Usage
```python
from extractor_apiv9 import SECExtractorTool

# Initialize the tool
extractor = SECExtractorTool()

# Extract a section with metadata
result = extractor.get_section(
    filing_url="https://www.sec.gov/Archives/edgar/data/...",
    section_id="1A",
    output_format="text"
)

# Access the results
if not result["is_error"]:
    print(f"Section: {result['section_description']}")
    print(f"Content: {result['content']}")
else:
    print(f"Error: {result['error']}")
```

### Extract All Sections
```python
# Extract all sections from a 10-K filing
results = extractor.extract_all_sections(
    filing_url="https://www.sec.gov/Archives/edgar/data/...",
    form_type="10-K"
)

for result in results:
    if result["is_present"]:
        print(f"{result['section_description']}: {len(result['content'])} chars")
```

## Response Format

All methods return a structured dictionary containing:
```python
{
    "is_error": bool,          # True if an error occurred
    "error": str,              # Error message if applicable
    "is_empty": bool,          # True if section is empty
    "is_present": bool,        # True if section exists in filing
    "status": str,             # Human-readable status
    "content": str,            # Section content
    "section_id": str,         # Section identifier
    "section_description": str, # Human-readable section description
    "form_type": str,          # Form type (10-K, 10-Q, 8-K)
    "output_format": str       # Output format used (text/html)
}
```

## Supported Form Types and Sections

### Form 10-K Sections
```python
{
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
}
```

### Form 10-Q Sections
```python
{
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
}
```

### Form 8-K Sections
```python
{
    "1-1": "Material Agreement",
    "1-3": "Bankruptcy",
    "4-1": "Auditor Changes",
    "4-2": "Financial Restatements",
    "5-2": "Director Changes"
}
```

## Features

1. **Structured Response Format**
   - Consistent JSON response format
   - Clear error and status messages
   - Content validation
   - Section metadata

2. **HTML Processing**
   - Automatic HTML entity decoding
   - Tag removal while preserving structure
   - Proper newline handling
   - Table structure preservation

3. **Error Handling**
   - API key validation
   - Section ID validation
   - Empty section detection
   - Network error handling
   - Invalid URL handling

4. **Form Type Detection**
   - Automatic form type detection from section ID
   - Section validation against known mappings
   - Human-readable section descriptions

5. **Batch Processing**
   - Extract all sections from a filing
   - Parallel processing support
   - Progress tracking

## Example URLs for Testing

```python
# Tesla 10-K (2020)
filing_url_10k = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"

# Tesla 10-Q (2022 Q1)
filing_url_10q = "https://www.sec.gov/Archives/edgar/data/1318605/000095017022006034/tsla-20220331.htm"

# Example 8-K
filing_url_8k = "https://www.sec.gov/Archives/edgar/data/66600/000149315222016468/form8-k.htm"
```

## Implementation History

### Version 9 (Current - Final)
- Added complete section mappings for all form types
- Implemented structured response format
- Added form type detection
- Enhanced HTML cleaning
- Added batch extraction support
- Fixed dotenv loading issues
- Added comprehensive error handling
- Added human-readable section descriptions
- Added content validation
- Added example URLs for testing

## Contributing

Feel free to submit issues and enhancement requests!

## Section Availability Analysis

Based on our test results with Tesla's filings:

### 10-K Sections (2020 Annual Report)
- **Present with Content** (15 sections):
  - Business (Section 1)
  - Risk Factors (1A)
  - Properties (2)
  - Legal Proceedings (3)
  - Market Information (5)
  - Selected Financial Data (6)
  - Management Discussion (7)
  - Market Risk (7A)
  - Financial Statements (8)
  - Controls (9A)
  - Directors (10)
  - Executive Compensation (11)
  - Security Ownership (12)
  - Relationships (13)
  - Accountant Fees (14)

- **Present but Empty** (4 sections):
  - Unresolved Staff Comments (1B)
  - Mine Safety (4)
  - Accountant Changes (9)
  - Other Information (9B)

- **Not Present** (1 section):
  - Cybersecurity (1C) - Expected as this was introduced in 2023

### 10-Q Sections (2022 Q1)
- **Present with Content** (6 sections):
  - Financial Statements (Part 1, Item 1)
  - Management Discussion (Part 1, Item 2)
  - Market Risk (Part 1, Item 3)
  - Controls (Part 1, Item 4)
  - Legal Proceedings (Part 2, Item 1)
  - Risk Factors (Part 2, Item 1A)

- **Present but Empty** (5 sections):
  - Unregistered Sales (Part 2, Item 2)
  - Defaults (Part 2, Item 3)
  - Mine Safety (Part 2, Item 4)
  - Other Information (Part 2, Item 5)
  - Exhibits (Part 2, Item 6)

### 8-K Sections
- **Present with Content** (1 section):
  - Material Agreement (1.01)

- **Not Present** (4 sections):
  - Bankruptcy (1.03)
  - Auditor Changes (4.01)
  - Financial Restatements (4.02)
  - Director Changes (5.02)

## Missing Features & Future Enhancements

1. **Additional 8-K Items Support**:
   - Need to add support for all 8-K items (currently only supporting 5)
   - Add validation for item combinations
   - Support for multi-item 8-K filings

2. **Enhanced HTML Output**:
   - Better HTML cleaning and formatting
   - Support for tables and special characters
   - CSS styling options

3. **Content Validation**:
   - Improved empty section detection
   - Section cross-referencing validation
   - Content structure validation

4. **Performance Enhancements**:
   - Batch extraction support
   - Caching for frequently accessed sections
   - Parallel processing

5. **Additional Features**:
   - Content summarization
   - Export to various formats (PDF, JSON)
   - Section comparison tools
   - Historical version tracking

## Error Handling

The tool now includes comprehensive error handling:
- API key validation
- Section ID validation
- Content presence validation
- Exception handling for API calls
- Descriptive error messages
- Form type detection
- Empty section detection

## Response Format

The tool now returns a structured dictionary containing:
```python
{
    "is_error": bool,          # True if an error occurred
    "error": str,              # Error message if applicable
    "is_empty": bool,          # True if section is empty
    "is_present": bool,        # True if section exists in filing
    "status": str,             # Human-readable status
    "content": str,            # Section content
    "section_id": str,         # Section identifier
    "section_description": str, # Human-readable section description
    "form_type": str,          # Form type (10-K, 10-Q, 8-K)
    "output_format": str       # Output format used (text/html)
}
```

## Contributing

Feel free to submit issues and enhancement requests!

## Implementation History

### Version 9 (Current - Final)
- Added complete section mappings for all form types
- Implemented structured response format
- Added form type detection
- Enhanced HTML cleaning
- Added batch extraction support
- Fixed dotenv loading issues
- Added comprehensive error handling
- Added human-readable section descriptions
- Added content validation
- Added example URLs for testing

#### Key Features
- Complete section mappings for 10-K, 10-Q, and 8-K
- Structured response format with:
  - Content
  - Section ID
  - Section Name
  - Form Type
  - Success Status
  - Error Messages
- Automatic form type detection
- Human-readable section names

#### Test Results
Successfully tested all documentation examples with enhanced output:
1. 10-K (Tesla):
   - Risk Factors (Section 1A):
     - Success: True
     - Form Type: 10-K
     - Section Name: Risk Factors
     - Content Length: 84,688 characters
   - MD&A (Section 7):
     - Success: True
     - Form Type: 10-K
     - Section Name: Management Discussion
     - Content Length: 793,247 characters

2. 10-Q (Tesla):
   - Risk Factors (Part 2, Item 1A):
     - Success: True
     - Form Type: 10-Q
     - Section Name: Risk Factors
     - Content Length: 89,544 characters

3. 8-K:
   - Material Agreement (Section 1-1):
     - Success: True
     - Form Type: 8-K
     - Section Name: Entry into Material Agreement
     - Content Length: 1,641 characters

#### Example Usage for Agents
```python
from sec_api import ExtractorApi

# Initialize
extractor = SECExtractorTool()

# Get a section with metadata
result = extractor.get_section(
    filing_url="https://www.sec.gov/Archives/edgar/data/...",
    section_id="1A",
    output_format="text"
)

# Access structured data
if result['success']:
    content = result['content']
    section_name = result['section_name']
    form_type = result['form_type']
else:
    error = result['error']
```

#### Next Steps for Version 10
1. Add helper methods for common queries (e.g., get_risk_factors(), get_mda())
2. Add batch extraction capability
3. Add content validation
4. Add section availability checking
5. Add example queries for agents 