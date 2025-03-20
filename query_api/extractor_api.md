# SEC ExtractorAPI Tool

A Python tool for extracting sections from SEC filings using the SEC-API.io ExtractorApi service.

## Overview

The SEC ExtractorAPI Tool provides a simple interface to extract specific sections from SEC filings. It supports various filing types (10-K, 10-Q, 8-K) and can return content in both text and HTML formats.

## Features

- Extract specific sections from SEC filings
- Support for multiple filing types (10-K, 10-Q, 8-K)
- Output in both text (cleaned) and HTML (original) formats
- Error handling and validation
- Environment variable support for API key management

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required packages:
   ```bash
   pip install sec-api python-dotenv
   ```
3. Set up your SEC API key in a `.env` file:
   ```
   SEC_API_KEY=your_api_key_here
   ```

## Usage

### Basic Usage

```python
from extractor_apiv1 import SECExtractorTool

extractor = SECExtractorTool()

# Extract Risk Factors from a 10-K filing
filing_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
risk_factors = extractor.get_section(filing_url, "1A", "text")
```

### Supported Section IDs

- 10-K/10-Q Sections:
  - "1A" - Risk Factors
  - "7" - Management's Discussion
  - "part2item1a" - Risk Factors (10-Q)

- 8-K Sections:
  - "1-1" - Entry into Material Definitive Agreement
  - Other item numbers as per SEC 8-K structure

### Output Formats

- `text`: Returns cleaned, plain text content
- `html`: Returns original HTML content

## Progress Log

### Version 1 (Current)
- Basic ExtractorApi implementation
- Support for 10-K, 10-Q, and 8-K extractions
- Text and HTML output formats
- Example test cases using documented URLs
- Error handling for API calls

## Example Test Cases

1. **10-K Extraction**
   ```python
   # Extract Risk Factors section
   filing_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
   section = extractor.get_section(filing_url, "1A", "text")
   ```

2. **10-Q Extraction**
   ```python
   # Extract Risk Factors from Part 2
   filing_url = "https://www.sec.gov/Archives/edgar/data/1318605/000095017022006034/tsla-20220331.htm"
   section = extractor.get_section(filing_url, "part2item1a", "text")
   ```

3. **8-K Extraction**
   ```python
   # Extract Material Agreement section
   filing_url = "https://www.sec.gov/Archives/edgar/data/66600/000149315222016468/form8-k.htm"
   section = extractor.get_section(filing_url, "1-1", "text")
   ```

## Future Enhancements

1. Add support for batch extraction
2. Implement caching for frequently accessed sections
3. Add section validation
4. Enhance error messages and handling
5. Add support for custom section mappings

## Error Handling

The tool includes basic error handling:
- API key validation
- Exception catching for API calls
- Informative error messages

## Contributing

Feel free to submit issues and enhancement requests! 