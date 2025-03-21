"""
SEC Filing Analysis Agent - Fixed Version

A LangChain agent that uses SEC-API tools to analyze SEC filings.
Focused on extracting sections, financial data, and finding patterns.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from sec_api import QueryApi, ExtractorApi, XbrlApi
from langchain.agents.agent_types import AgentType
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure environment
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

if not SEC_API_KEY or not OPENAI_API_KEY:
    logger.error("SEC_API_KEY or OPENAI_API_KEY not found in .env file")
    raise ValueError("API keys not found. Please add them to your .env file.")

# Initialize API clients
query_api = QueryApi(api_key=SEC_API_KEY)
extractor_api = ExtractorApi(api_key=SEC_API_KEY)
xbrl_api = XbrlApi(api_key=SEC_API_KEY)

#################################################
# Tool 1: SEC Query API
#################################################
def search_sec_filings(
    query: str,
    from_param: str = "0",
    size: str = "10"
) -> str:
    """
    Search SEC filings using the Query API.
    
    Args:
        query: Search query in SEC-API format (e.g., 'ticker:MSFT AND formType:"10-K"')
        from_param: Starting position for pagination
        size: Number of results to return
        
    Returns:
        Formatted search results
    """
    try:
        # Build query parameters
        search_params = {
            "query": query,
            "from": from_param,
            "size": size,
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        # Call the API
        filings = query_api.get_filings(search_params)
        
        if not filings or "filings" not in filings or not filings["filings"]:
            return "No results found matching your criteria."
        
        # Format results
        total_filings = filings.get("total", {}).get("value", 0)
        formatted_results = [f"Found {total_filings} results. Showing top {min(5, len(filings['filings']))}:"]
        
        for i, filing in enumerate(filings.get("filings", [])[:5], 1):
            formatted_results.append(f"\nResult {i}:")
            formatted_results.append(f"Company: {filing.get('companyName', 'N/A')} (Ticker: {filing.get('ticker', 'N/A')})")
            formatted_results.append(f"Form Type: {filing.get('formType', 'N/A')}")
            formatted_results.append(f"Filed At: {filing.get('filedAt', 'N/A')}")
            formatted_results.append(f"Accession Number: {filing.get('accessionNo', 'N/A')}")
            formatted_results.append(f"Filing URL: {filing.get('linkToFilingDetails', filing.get('linkToHtml', 'N/A'))}")
            
            # Add items for 8-K filings
            if filing.get('formType') == '8-K' and filing.get('items'):
                formatted_results.append(f"Items: {filing.get('items', 'N/A')}")
        
        return "\n".join(formatted_results)
    
    except Exception as e:
        logger.error(f"Error in search_sec_filings: {str(e)}")
        return f"An error occurred while searching SEC filings: {str(e)}"

#################################################
# Tool 2: SEC Extractor API
#################################################
def extract_section(
    filing_url: str,
    section_id: str,
    output_format: str = "text"
) -> Dict[str, Any]:
    """
    Extract a section from an SEC filing with enhanced error handling.
    
    Args:
        filing_url: URL to the SEC filing (must be a sec.gov URL ending in .htm or .html)
        section_id: Section identifier (e.g., "7", "1A", "part2item1a")
        output_format: Either "text" or "html" format
        
    Returns:
        Dictionary with section content and metadata
    """
    try:
        # Section ID mappings for common sections
        section_name_mapping = {
            "1": "Business",
            "1A": "Risk Factors",
            "1B": "Unresolved Staff Comments",
            "1C": "Cybersecurity",
            "2": "Properties",
            "3": "Legal Proceedings",
            "4": "Mine Safety",
            "5": "Market Information",
            "6": "Selected Financial Data",
            "7": "Management Discussion and Analysis",
            "7A": "Market Risk",
            "8": "Financial Statements",
            "9": "Accountant Changes",
            "9A": "Controls and Procedures",
            "9B": "Other Information",
            "10": "Directors and Officers",
            "11": "Executive Compensation",
            "12": "Security Ownership",
            "13": "Related Transactions",
            "14": "Principal Accountant Fees",
            # 10-Q Sections
            "part1item1": "Financial Statements",
            "part1item2": "Management Discussion",
            "part1item3": "Market Risk",
            "part1item4": "Controls and Procedures",
            "part2item1": "Legal Proceedings",
            "part2item1a": "Risk Factors",
            "part2item2": "Unregistered Sales",
            "part2item3": "Defaults",
            "part2item4": "Mine Safety",
            "part2item5": "Other Information",
            "part2item6": "Exhibits"
        }
        
        # Fix section_id format - strip any "item_" prefix
        if section_id.startswith("item_"):
            logger.info(f"Converting section ID format from '{section_id}' to '{section_id[5:]}'")
            section_id = section_id[5:]  # Remove "item_" prefix
        
        # Verify URL format
        if not filing_url.startswith("https://www.sec.gov/") or not (filing_url.endswith('.htm') or filing_url.endswith('.html')):
            return {
                "is_error": True,
                "error": "Invalid URL format. Must be a sec.gov URL ending in .htm or .html",
                "content": None,
                "section_id": section_id,
                "section_name": section_name_mapping.get(section_id, "Unknown Section")
            }
        
        # Extract section
        section_content = extractor_api.get_section(filing_url, section_id, output_format)
        
        if not section_content or len(section_content.strip()) < 10:
            return {
                "is_error": False,
                "error": None,
                "content": None,
                "is_empty": True,
                "section_id": section_id,
                "section_name": section_name_mapping.get(section_id, "Unknown Section"),
                "status": "Section exists but appears to be empty or not available"
            }
        
        return {
            "is_error": False,
            "error": None,
            "content": section_content,
            "is_empty": False,
            "section_id": section_id,
            "section_name": section_name_mapping.get(section_id, "Unknown Section"),
            "status": "Success"
        }
    
    except Exception as e:
        logger.error(f"Error in extract_section: {str(e)}")
        return {
            "is_error": True,
            "error": str(e),
            "content": None,
            "section_id": section_id,
            "section_name": section_name_mapping.get(section_id, "Unknown Section"),
            "status": "Error"
        }

#################################################
# Tool 3: SEC XBRL API (Financial Data)
#################################################
def xbrl_to_json(
    htm_url: Optional[str] = None,
    xbrl_url: Optional[str] = None,
    accession_no: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert XBRL to JSON and extract financial data.
    
    Args:
        htm_url: URL to the filing HTML
        xbrl_url: URL to the XBRL file
        accession_no: Filing accession number
        
    Returns:
        Dictionary containing either the XBRL data or error information
    """
    try:
        # Validate inputs
        input_count = sum(x is not None for x in [htm_url, xbrl_url, accession_no])
        if input_count == 0:
            return {
                "is_error": True,
                "error": "At least one of htm_url, xbrl_url, or accession_no must be provided",
                "data": None
            }
        if input_count > 1:
            return {
                "is_error": True,
                "error": "Please provide only one of htm_url, xbrl_url, or accession_no",
                "data": None
            }
        
        # Call appropriate API method
        if htm_url:
            xbrl_data = xbrl_api.xbrl_to_json(htm_url=htm_url)
        elif xbrl_url:
            xbrl_data = xbrl_api.xbrl_to_json(xbrl_url=xbrl_url)
        else:
            xbrl_data = xbrl_api.xbrl_to_json(accession_no=accession_no)
        
        if not xbrl_data:
            return {
                "is_error": True,
                "error": "No XBRL data found or could not parse XBRL",
                "data": None
            }
        
        # Extract key financial information
        financial_data = {
            "statements": [],
            "key_metrics": {}
        }
        
        # Find statements
        for key in xbrl_data.keys():
            if key.startswith("Statements") or key == "CoverPage":
                financial_data["statements"].append(key)
        
        # Extract key metrics
        if "CoverPage" in xbrl_data:
            cover_data = xbrl_data["CoverPage"]
            if "EntityCommonStockSharesOutstanding" in cover_data:
                financial_data["key_metrics"]["shares_outstanding"] = cover_data["EntityCommonStockSharesOutstanding"]
            if "EntityPublicFloat" in cover_data:
                financial_data["key_metrics"]["public_float"] = cover_data["EntityPublicFloat"]
            if "DocumentFiscalPeriodFocus" in cover_data:
                financial_data["key_metrics"]["fiscal_period"] = cover_data["DocumentFiscalPeriodFocus"]
            if "DocumentFiscalYearFocus" in cover_data:
                financial_data["key_metrics"]["fiscal_year"] = cover_data["DocumentFiscalYearFocus"]
        
        # Check for revenue data
        if "StatementsOfIncome" in xbrl_data:
            income_data = xbrl_data["StatementsOfIncome"]
            # Look for common revenue field names
            revenue_fields = [
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues",
                "SalesRevenueNet",
                "RevenueNet"
            ]
            for field in revenue_fields:
                if field in income_data:
                    financial_data["key_metrics"]["revenue"] = income_data[field]
                    break
        
        return {
            "is_error": False,
            "error": None,
            "data": xbrl_data,
            "summary": financial_data
        }
    
    except Exception as e:
        logger.error(f"Error in xbrl_to_json: {str(e)}")
        return {
            "is_error": True,
            "error": str(e),
            "data": None
        }

#################################################
# System Prompt
#################################################
SYSTEM_PROMPT = """You are an expert SEC filing analyst with access to SEC data tools.

Follow these guidelines when using SEC-API tools:

1. Query API: Use for finding specific filings
   - Format: ticker:TSLA AND formType:"10-K"
   - Include date ranges: filedAt:[2020-01-01 TO 2023-12-31]
   - Common form types: 10-K (annual), 10-Q (quarterly), 8-K (current events)

2. Extractor API: Use for getting specific sections
   - Requires proper SEC.gov URLs ending in .htm or .html
   - IMPORTANT: Use ONLY these exact section IDs (without any prefixes):
     * "7" for Management Discussion and Analysis
     * "1A" for Risk Factors
     * "1C" for Cybersecurity
     * "8" for Financial Statements and Notes
     * For 10-Q sections, use proper format: "part1item2" for MD&A

3. XBRL API: Use for financial data
   - Extract shares outstanding, revenue, etc.
   - Requires valid filing URL or accession number

Process for common tasks:
1. For section analysis: First find the filing with Query API, then extract the section
2. For financial data: Find the filing, then use XBRL API
3. For comparisons: Retrieve multiple filings and compare corresponding sections

When providing your analysis:
- Be concise but thorough
- Quote relevant text when appropriate
- Format financial data clearly
- For comparisons, highlight key differences
"""

#################################################
# LangChain Setup
#################################################
def create_agent():
    """Create and return a LangChain agent with SEC tools"""
    # Create tools
    tools = [
        StructuredTool.from_function(
            func=search_sec_filings,
            name="SECQueryAPI",
            description="Search SEC filings using exact query syntax (e.g., ticker:MSFT AND formType:\"10-K\")"
        ),
        StructuredTool.from_function(
            func=extract_section,
            name="SECExtractSection",
            description="Extract a specific section from an SEC filing using a valid SEC.gov URL. Use section IDs like '7' for Management Discussion and Analysis, '1A' for Risk Factors, without any prefixes."
        ),
        StructuredTool.from_function(
            func=xbrl_to_json,
            name="SECFinancialData",
            description="Extract financial data from a filing using the XBRL API"
        )
    ]
    
    # Create LLM
    llm = ChatOpenAI(
        temperature=0,
        model=OPENAI_MODEL
    )
    
    # Create agent
    agent_prompt = create_structured_chat_agent(
        llm=llm,
        tools=tools,
        system_message=SYSTEM_PROMPT
    )
    
    agent = AgentExecutor(
        agent=agent_prompt,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    
    return agent

#################################################
# Main Functionality
#################################################
def process_query(query: str) -> str:
    """Process a user query using the SEC agent"""
    agent = create_agent()
    try:
        return agent.invoke(query)["output"]
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return f"An error occurred: {str(e)}"

#################################################
# Entry Point
#################################################
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Process command line query
        query = " ".join(sys.argv[1:])
        print(process_query(query))
    else:
        # Interactive mode
        print("SEC Filing Analysis Agent (type 'exit' to quit)")
        while True:
            query = input("\nEnter your question: ")
            if query.lower() in ['exit', 'quit']:
                break
            print("\n" + process_query(query))