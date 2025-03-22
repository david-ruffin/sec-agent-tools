"""
SEC Filing Analyzer

A basic implementation of an SEC filing analyzer using SEC-API
with contextual retrieval enhancement for maintaining critical context.
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from sec_api import QueryApi, ExtractorApi, XbrlApi, MappingApi
import openai
from sec_context_manager import SECContext
import sec_api_knowledge

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
mapping_api = MappingApi(api_key=SEC_API_KEY)

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

# Initialize context manager
context = SECContext()

def resolve_company(company_name_or_ticker: str) -> Dict[str, Any]:
    """
    Resolve a company name or ticker to standardized information.
    
    Args:
        company_name_or_ticker: Company name or ticker symbol
        
    Returns:
        Dictionary containing company information or error message
    """
    logger.info(f"Resolving company: {company_name_or_ticker}")
    
    try:
        # First try to resolve by ticker
        company_info = mapping_api.resolve("ticker", company_name_or_ticker)
        logger.info(f"Resolved by ticker: {company_info}")
        
        if not company_info:
            # If ticker resolution failed, try by name
            company_info = mapping_api.resolve("name", company_name_or_ticker)
            logger.info(f"Resolved by name: {company_info}")
        
        if not company_info:
            error_msg = f"Could not resolve company: {company_name_or_ticker}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Update company context
        context.set_company_context(company_info)
        
        return company_info
    except Exception as e:
        error_msg = f"Error resolving company {company_name_or_ticker}: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

def search_sec_filings(
    ticker: Optional[str] = None,
    form_type: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    size: str = "1"
) -> Dict[str, Any]:
    """
    Search SEC filings using the Query API.
    
    Args:
        ticker: Company ticker symbol
        form_type: Filing form type (e.g., '10-K', '10-Q')
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        size: Number of results to return
        
    Returns:
        Dictionary containing filings information
    """
    logger.info(f"Searching SEC filings: ticker={ticker}, form_type={form_type}")
    
    try:
        # Build query
        query_parts = []
        
        if ticker:
            query_parts.append(f'ticker:"{ticker}"')
            
        if form_type:
            query_parts.append(f'formType:"{form_type}"')
            
        if from_date and to_date:
            query_parts.append(f'filedAt:[{from_date} TO {to_date}]')
        elif from_date:
            query_parts.append(f'filedAt:[{from_date} TO 2099-12-31]')
        elif to_date:
            query_parts.append(f'filedAt:[1900-01-01 TO {to_date}]')
            
        # Join query parts with AND
        query = " AND ".join(query_parts)
        
        # Search parameters
        search_params = {
            "query": query,
            "from": "0",
            "size": size,
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        # Execute search
        filings = query_api.get_filings(search_params)
        
        if not filings or "filings" not in filings or not filings["filings"]:
            error_msg = f"No filings found for {ticker} with form_type {form_type}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Process filings
        result = {
            "filings": filings["filings"],
            "count": len(filings["filings"])
        }
        
        # Update context with the first filing
        if filings["filings"]:
            first_filing = filings["filings"][0]
            context.set_filing_context(first_filing)
        
        return result
    
    except Exception as e:
        error_msg = f"Error searching SEC filings: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

def extract_section(
    filing_url: Optional[str] = None,
    section_id: str = "7"  # Default to MD&A section
) -> Dict[str, Any]:
    """
    Extract a section from an SEC filing.
    
    Args:
        filing_url: URL of the filing document
        section_id: ID of the section to extract (e.g., '7' for MD&A)
        
    Returns:
        Dictionary containing section content or error
    """
    # Use filing URL from context if none provided
    if not filing_url:
        filing_url = context.get_filing_url()
        logger.info(f"Using filing URL from context: {filing_url}")
    
    if not filing_url:
        error_msg = "No filing URL provided or found in context"
        logger.error(error_msg)
        return {
            "is_error": True,
            "error": error_msg,
            "section_id": section_id
        }
    
    # Validate SEC.gov URL
    if not filing_url.startswith("https://www.sec.gov/"):
        error_msg = f"Invalid URL format: {filing_url}. Must be an SEC.gov URL."
        logger.error(error_msg)
        return {
            "is_error": True,
            "error": error_msg,
            "section_id": section_id
        }
    
    # Section name mapping for context
    section_names = {
        "1": "Business",
        "1A": "Risk Factors",
        "1B": "Unresolved Staff Comments",
        "1C": "Cybersecurity",
        "2": "Properties",
        "3": "Legal Proceedings",
        "4": "Mine Safety Disclosures",
        "5": "Market for Registrant's Common Equity",
        "6": "Selected Financial Data",
        "7": "Management's Discussion and Analysis",
        "7A": "Quantitative and Qualitative Disclosures about Market Risk",
        "8": "Financial Statements and Supplementary Data",
        "9": "Changes in and Disagreements with Accountants",
        "9A": "Controls and Procedures",
        "9B": "Other Information",
        "10": "Directors, Executive Officers and Corporate Governance",
        "11": "Executive Compensation",
        "12": "Security Ownership",
        "13": "Certain Relationships and Related Transactions",
        "14": "Principal Accountant Fees and Services"
    }
    
    try:
        logger.info(f"Extracting section {section_id} from {filing_url}")
        
        # Call the extractor API
        section_content = extractor_api.get_section(filing_url, section_id, "text")
        
        if not section_content or len(section_content.strip()) < 10:
            error_msg = f"Section {section_id} not found or empty"
            logger.error(error_msg)
            return {
                "is_error": True,
                "error": error_msg,
                "section_id": section_id,
                "section_name": section_names.get(section_id, "Unknown Section")
            }
        
        # Return successful result
        result = {
            "is_error": False,
            "content": section_content,
            "section_id": section_id,
            "section_name": section_names.get(section_id, "Unknown Section")
        }
        
        # Update context
        context.set_section_context(result)
        
        return result
    
    except Exception as e:
        error_msg = f"Error extracting section {section_id}: {str(e)}"
        logger.error(error_msg)
        return {
            "is_error": True,
            "error": error_msg,
            "section_id": section_id,
            "section_name": section_names.get(section_id, "Unknown Section")
        }

def get_xbrl_data(
    filing_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract XBRL data from a filing.
    
    Args:
        filing_url: URL of the filing document
        
    Returns:
        Dictionary containing XBRL data or error
    """
    # Use filing URL from context if none provided
    if not filing_url:
        filing_url = context.get_filing_url()
        logger.info(f"Using filing URL from context: {filing_url}")
    
    if not filing_url:
        error_msg = "No filing URL provided or found in context"
        logger.error(error_msg)
        return {
            "is_error": True,
            "error": error_msg
        }
    
    try:
        logger.info(f"Extracting XBRL data from {filing_url}")
        
        # Call the XBRL API
        xbrl_data = xbrl_api.xbrl_to_json(htm_url=filing_url)
        
        if not xbrl_data:
            error_msg = "No XBRL data found or couldn't parse XBRL"
            logger.error(error_msg)
            return {
                "is_error": True,
                "error": error_msg
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
                "RevenueNet",
                "TotalRevenuesAndOtherIncome"
            ]
            for field in revenue_fields:
                if field in income_data:
                    financial_data["key_metrics"]["revenue"] = income_data[field]
                    break
        
        # Update context
        context.set_xbrl_context({
            "data": xbrl_data,
            "summary": financial_data
        })
        
        return {
            "is_error": False,
            "data": xbrl_data,
            "summary": financial_data
        }
    
    except Exception as e:
        error_msg = f"Error extracting XBRL data: {str(e)}"
        logger.error(error_msg)
        return {
            "is_error": True,
            "error": error_msg
        }

def analyze_query(query: str) -> Dict[str, Any]:
    """
    Analyze a user query to determine its type and target.
    
    Args:
        query: User query string
        
    Returns:
        Dictionary containing query analysis
    """
    # Update context with query
    context.update_query_context(query)
    
    # Call OpenAI to analyze the query
    try:
        response = openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": """You are an expert in analyzing SEC filing queries.
                Analyze the query and extract the following information:
                1. Company name or ticker mentioned
                2. Filing type(s) mentioned or implied (10-K, 10-Q, 8-K)
                3. Time period mentioned
                4. Section of interest (MD&A, Risk Factors, etc.)
                5. Financial metrics requested (if any)
                6. Query type: financial, textual, comparative, or change-detection
                
                Respond in JSON format only."""},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        
        analysis = json.loads(response.choices[0].message.content)
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing query: {str(e)}")
        # Return basic query info
        return {
            "query": query,
            "error": f"Could not analyze query: {str(e)}"
        }

def summarize_section(section_content: str, section_name: str, query: str) -> str:
    """
    Generate a summary of a section's content based on the user's query.
    
    Args:
        section_content: The text content of the section
        section_name: Name of the section
        query: The user's original query
        
    Returns:
        Summary of the section relevant to the query
    """
    try:
        # Limit content to avoid token limits
        content = section_content[:15000] if len(section_content) > 15000 else section_content
        
        response = openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": f"""You are an expert SEC filing analyst.
                Analyze this {section_name} section and answer the user's query.
                Focus on providing a direct, informative answer based on the content.
                If the information to answer the query is not in the section, state that clearly."""},
                {"role": "user", "content": f"Query: {query}\n\nSection content:\n{content}"}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error summarizing section: {str(e)}")
        return f"Could not summarize section: {str(e)}"

def extract_financial_metric(
    xbrl_data: Dict[str, Any],
    metric_name: str
) -> str:
    """
    Extract and format a specific financial metric from XBRL data.
    
    Args:
        xbrl_data: XBRL data dictionary
        metric_name: Name of the metric to extract (e.g., "revenue", "net income")
        
    Returns:
        Formatted metric value or error message
    """
    logger.info(f"Extracting financial metric: {metric_name}")
    
    try:
        # Make sure xbrl_data contains data
        if not xbrl_data or "data" not in xbrl_data:
            return f"No XBRL data found to extract {metric_name}."
        
        # Map common metric names to potential XBRL fields
        metric_map = {
            "revenue": [
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues", 
                "SalesRevenueNet", 
                "RevenueNet", 
                "TotalRevenuesAndOtherIncome"
            ],
            "net income": [
                "NetIncomeLoss", 
                "ProfitLoss", 
                "NetIncome", 
                "NetEarningsLoss"
            ],
            "assets": [
                "Assets", 
                "TotalAssets"
            ],
            "liabilities": [
                "Liabilities", 
                "TotalLiabilities"
            ],
            "equity": [
                "StockholdersEquity", 
                "TotalEquity", 
                "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"
            ],
            "earnings per share": [
                "EarningsPerShareBasic", 
                "EarningsPerShareDiluted"
            ],
            "cash": [
                "CashAndCashEquivalentsAtCarryingValue", 
                "Cash", 
                "CashAndCashEquivalents"
            ]
        }
        
        data = xbrl_data["data"]
        normalized_metric = metric_name.lower()
        
        # Check for direct match in key_metrics
        if "summary" in xbrl_data and "key_metrics" in xbrl_data["summary"] and normalized_metric in xbrl_data["summary"]["key_metrics"]:
            value = xbrl_data["summary"]["key_metrics"][normalized_metric]
            return f"The {metric_name} is {value}."
        
        # Try to find metric in mapped fields
        if normalized_metric in metric_map:
            for field in metric_map[normalized_metric]:
                # Look in common locations for financial data
                for statement in ["StatementsOfIncome", "BalanceSheets", "StatementsOfCashFlows", "CoverPage"]:
                    if statement in data and field in data[statement]:
                        value = data[statement][field]
                        # Format value based on type
                        if isinstance(value, (int, float)):
                            if normalized_metric in ["revenue", "net income", "assets", "liabilities", "equity", "cash"]:
                                formatted_value = f"${value:,.2f}"
                            elif normalized_metric in ["earnings per share"]:
                                formatted_value = f"${value:.2f} per share"
                            else:
                                formatted_value = f"{value:,.2f}"
                        else:
                            formatted_value = str(value)
                        
                        return f"The {metric_name} is {formatted_value}."
        
        # Direct search if mapping fails
        for statement in data:
            if not statement.startswith("Statements"):
                continue
            
            statement_data = data[statement]
            for field, value in statement_data.items():
                if normalized_metric in field.lower():
                    # Format value based on type
                    if isinstance(value, (int, float)):
                        if any(term in normalized_metric for term in ["revenue", "income", "assets", "liabilities"]):
                            formatted_value = f"${value:,.2f}"
                        elif "per share" in normalized_metric:
                            formatted_value = f"${value:.2f} per share"
                        else:
                            formatted_value = f"{value:,.2f}"
                    else:
                        formatted_value = str(value)
                    
                    return f"The {metric_name} is {formatted_value}."
        
        return f"Could not find {metric_name} in the XBRL data."
    
    except Exception as e:
        logger.error(f"Error extracting {metric_name}: {str(e)}")
        return f"Error extracting {metric_name}: {str(e)}"

def process_query(query: str) -> str:
    """
    Process a query to get revenue from latest 10-K for any company.
    
    Args:
        query: The user's query string
        
    Returns:
        A formatted response with the requested information
    """
    try:
        logger.info(f"Processing query: {query}")
        
        # Update query context
        context.update_query_context(query)
        
        # First resolve company information
        # Try to extract company name or ticker from query
        company_info = None
        if "apple" in query.lower() or "aapl" in query.lower():
            company_info = {"name": "Apple Inc.", "ticker": "AAPL"}
        else:
            # Try to resolve company from query
            try:
                # First try as ticker
                company_info = mapping_api.resolve("ticker", query.split()[-1])
                if not company_info:
                    # Then try as name
                    company_info = mapping_api.resolve("name", query)
            except Exception as e:
                logger.error(f"Error resolving company: {str(e)}")
                return f"Could not resolve company information. Please provide a valid company name or ticker symbol."
        
        if not company_info:
            return "Could not find company information. Please provide a valid company name or ticker symbol."
            
        # Update company context
        context.update_company_context(company_info)
        
        # Search for latest 10-K using resolved ticker
        ticker = company_info.get("ticker")
        if not ticker:
            return "Could not determine ticker symbol for the company."
            
        search_params = {
            "query": f'ticker:"{ticker}" AND formType:"10-K"',
            "from": "0",
            "size": "1",
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        logger.info(f"Searching for latest 10-K filing for {ticker}...")
        filings = query_api.get_filings(search_params)
        if not filings or not filings.get("filings"):
            error_msg = f"No 10-K filings found for {company_info.get('name', ticker)}."
            logger.error(error_msg)
            return error_msg
            
        # Update filing context with the first filing
        filing = filings["filings"][0]
        context.update_filing_context({"filings": [filing]})
        
        # Get the filing URL
        filing_url = filing.get("linkToFilingDetails")
        if isinstance(filing_url, list):
            filing_url = filing_url[0]
            
        if not filing_url:
            error_msg = "Could not find filing URL."
            logger.error(error_msg)
            return error_msg
        
        if not filing_url.startswith("https://www.sec.gov/"):
            error_msg = "Invalid filing URL format. Must be an SEC.gov URL."
            logger.error(error_msg)
            return error_msg
        
        logger.info(f"Found filing URL: {filing_url}")
        
        # Get XBRL data
        logger.info("Extracting XBRL data...")
        try:
            xbrl_data = xbrl_api.xbrl_to_json(htm_url=filing_url)
        except Exception as e:
            error_msg = f"Error extracting XBRL data: {str(e)}"
            logger.error(error_msg)
            return error_msg
            
        if not xbrl_data:
            error_msg = "No XBRL data found in the filing."
            logger.error(error_msg)
            return error_msg
            
        # Extract revenue from XBRL data
        if "StatementsOfIncome" in xbrl_data:
            income_data = xbrl_data["StatementsOfIncome"]
            # Common revenue field names
            revenue_fields = [
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues",
                "SalesRevenueNet",
                "RevenueNet",
                "TotalRevenuesAndOtherIncome",
                "RevenueFromContractWithCustomerIncludingAssessedTax",
                "SalesRevenueGoodsNet",
                "SalesRevenueServicesNet"
            ]
            
            for field in revenue_fields:
                if field in income_data:
                    revenue_data = income_data[field]
                    if isinstance(revenue_data, list) and revenue_data:
                        # Get the most recent period's data
                        revenue_item = revenue_data[0]  # Most recent period is first
                        if isinstance(revenue_item, dict) and "value" in revenue_item:
                            try:
                                # Convert string value to float
                                revenue_value = float(revenue_item["value"])
                                filed_at = filing.get("filedAt", "unknown date")
                                period_end = filing.get("periodOfReport", "unknown period")
                                
                                # Get period information from the XBRL data
                                period_info = revenue_item.get("period", {})
                                start_date = period_info.get("startDate", "unknown")
                                end_date = period_info.get("endDate", "unknown")
                                
                                company_name = company_info.get("name", ticker)
                                response = (
                                    f"{company_name}'s revenue from their latest 10-K:\n"
                                    f"Filing Date: {filed_at}\n"
                                    f"Period: {start_date} to {end_date}\n"
                                    f"Revenue: ${revenue_value:,.2f}"
                                )
                                
                                # Enrich response with context
                                return context.enrich_response(response)
                            except (ValueError, TypeError) as e:
                                logger.error(f"Error formatting revenue value: {str(e)}")
                                continue
                    
            error_msg = "Could not find a valid revenue value in the filing's XBRL data."
            logger.error(error_msg)
            return error_msg
                    
        error_msg = "Could not find income statement data in the filing's XBRL data."
        logger.error(error_msg)
        return error_msg
        
    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        logger.error(error_msg)
        return error_msg

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Process command line query
        query = " ".join(sys.argv[1:])
        result = process_query(query)
        # Add context to response
        enriched_response = context.enrich_response(result)
        print(enriched_response)
    else:
        # Interactive mode
        print("SEC Filing Analyzer with Context Preservation")
        print("Type 'exit' to quit")
        while True:
            query = input("\nEnter your question: ")
            if query.lower() in ['exit', 'quit']:
                break
            result = process_query(query)
            # Add context to response
            enriched_response = context.enrich_response(result)
            print("\n" + enriched_response) 