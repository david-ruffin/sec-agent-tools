# Section Extraction API Agent Plan

## API Overview
The Extractor API returns individual sections from 10-Q, 10-K and 8-K filings. The extracted section is cleaned and standardized - in raw text or in standardized HTML. You can programmatically extract one or multiple sections from any 10-Q, 10-K and 8-K filing.

## Available Methods

The SEC-API Python ExtractorApi class exposes the following methods:

1. **`get_section(filing_url, section_name, return_type='text')`**
   - Extracts a specific section from a filing
   - Supports both standard and custom section names
   - Returns section content in text or HTML format

## Supported Sections

**All 10-K sections can be extracted:**

* 1 - Business
* 1A - Risk Factors
* 1B - Unresolved Staff Comments
* 1C - Cybersecurity (introduced in 2023)
* 2 - Properties
* 3 - Legal Proceedings
* 4 - Mine Safety Disclosures
* 5 - Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities
* 6 - Selected Financial Data (prior to February 2021)
* 7 - Management's Discussion and Analysis of Financial Condition and Results of Operations
* 7A - Quantitative and Qualitative Disclosures about Market Risk
* 8 - Financial Statements and Supplementary Data
* 9 - Changes in and Disagreements with Accountants on Accounting and Financial Disclosure
* 9A - Controls and Procedures
* 9B - Other Information
* 10 - Directors, Executive Officers and Corporate Governance
* 11 - Executive Compensation
* 12 - Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters
* 13 - Certain Relationships and Related Transactions, and Director Independence
* 14 - Principal Accountant Fees and Services

**All 10-Q sections can be extracted:**

Part 1:
* 1 - Financial Statements
* 2 - Management's Discussion and Analysis of Financial Condition and Results of Operations
* 3 - Quantitative and Qualitative Disclosures About Market Risk
* 4 - Controls and Procedures

Part 2:
* 1 - Legal Proceedings
* 1A - Risk Factors
* 2 - Unregistered Sales of Equity Securities and Use of Proceeds
* 3 - Defaults Upon Senior Securities
* 4 - Mine Safety Disclosures
* 5 - Other Information
* 6 - Exhibits

**All 8-K sections can be extracted**

## Response Format
The response includes:

- `section` - Name of the extracted section
- `content` - Section content (text or HTML)
- `metadata`
  - `filing_url` - Source filing URL
  - `company_name` - Company name
  - `cik` - Company CIK
  - `filing_type` - SEC form type
  - `filing_date` - Date filed
  - `section_start` - Start position in document
  - `section_end` - End position in document

## Implementation Notes

The section extraction agent should:

1. Support all section types:
   - All 10-K sections (1-14)
   - All 10-Q sections (Part 1 & 2)
   - All 8-K sections
   - Custom section titles

2. Handle different output formats:
   - Raw text
   - Standardized HTML

3. Validate inputs:
   - Filing URL format
   - Section name validity
   - Return type parameter

4. Handle all error cases:
   - Section not found
   - Invalid filing URL
   - Network/API errors
   - Rate limiting
   - Malformed section content

5. Return standardized response format:
   - Status code
   - Error message (if applicable)
   - Section content
   - Metadata
   - Extraction statistics

The agent should be a "dumb" tool that exposes the full section extraction capabilities of the API while maintaining consistent error handling and response structure. 